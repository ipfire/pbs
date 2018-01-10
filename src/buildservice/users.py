#!/usr/bin/python

import datetime
import email.utils
import hashlib
import logging
import pytz
import random
import re
import string
import urllib
import ldap

import tornado.locale

log = logging.getLogger("users")
log.propagate = 1

from . import base
from . import ldap

from .decorators import *

# A list of possible random characters.
random_chars = string.ascii_letters + string.digits

def generate_random_string(length=16):
	"""
		Return a string with random chararcters A-Za-z0-9 with given length.
	"""
	return "".join([random.choice(random_chars) for i in range(length)])


def generate_password_hash(password, salt=None, algo="sha512"):
	"""
		This function creates a salted digest of the given password.
	"""
	# Generate the salt (length = 16) of none was given.
	if salt is None:
		salt = generate_random_string(length=16)

	# Compute the hash.
	# <SALT> + <PASSWORD>
	if not algo in hashlib.algorithms:
		raise Exception, "Unsupported password hash algorithm: %s" % algo

	# Calculate the digest.
	h = hashlib.new(algo)
	h.update(salt)
	h.update(password)

	# Output string is of kind "<algo>$<salt>$<hash>".
	return "$".join((algo, salt, h.hexdigest()))

def check_password_hash(password, password_hash):
	"""
		Check a plain-text password with the given digest.
	"""
	# Handle plaintext passwords (plain$<password>).
	if password_hash.startswith("plain$"):
		return password_hash[6:] == password

	try:
		algo, salt, digest = password_hash.split("$", 2)
	except ValueError:
		logging.warning("Unknown password hash: %s" % password_hash)
		return False

	# Re-generate the password hash and compare the result.
	return password_hash == generate_password_hash(password, salt=salt, algo=algo)


class Users(base.Object):
	def init(self):
		self.ldap = ldap.LDAP(self.backend)

	def _get_user(self, query, *args):
		res = self.db.get(query, *args)

		if res:
			return User(self.backend, res.id, data=res)

	def _get_users(self, query, *args):
		res = self.db.query(query, *args)

		for row in res:
			yield User(self.backend, row.id, data=row)

	def _get_user_email(self, query, *args):
		res = self.db.get(query, *args)

		if res:
			return UserEmail(self.backend, res.id, data=res)

	def _get_user_emails(self, query, *args):
		res = self.db.query(query, *args)

		for row in res:
			yield UserEmail(self.backend, row.id, data=row)

	def __iter__(self):
		users = self._get_users("SELECT * FROM users \
			WHERE activated IS TRUE AND deleted IS FALSE ORDER BY name")

		return iter(users)

	def __len__(self):
		res = self.db.get("SELECT COUNT(*) AS count FROM users \
			WHERE activated IS TRUE AND deleted IS FALSE")

		return res.count

	def create(self, name, realname=None, ldap_dn=None):
		# XXX check if username has the correct name

		# Check if name is already taken
		user = self.get_by_name(name)
		if user:
			raise ValueError("Username %s already taken" % name)

		# Create new user
		user = self._get_user("INSERT INTO users(name, realname, ldap_dn) \
			VALUES(%s, %s, %s) RETURNING *", name, realname, ldap_dn)

		# Create row in permissions table.
		self.db.execute("INSERT INTO users_permissions(user_id) VALUES(%s)", user.id)

		log.debug("Created user %s" % user.name)

		return user

	def create_from_ldap(self, name):
		log.debug("Creating user %s from LDAP" % name)

		# Get required attributes from LDAP
		dn, attr = self.ldap.get_user(name, attrlist=["uid", "cn", "mail"])
		assert dn

		# Create regular user
		user = self.create(name, realname=attr["cn"][0], ldap_dn=dn)
		user.activate()

		# Add all email addresses and activate them
		for email in attr["mail"]:
			user.add_email(email, activated=True)

		return user

	def auth(self, name, password):
		# If either name or password is None, we don't check at all.
		if None in (name, password):
			return

		# usually we will get an email address as name
		user = self.get_by_email(name) or self.get_by_name(name)

		if not user:
			# If no user could be found, we search for a matching user in
			# the LDAP database
			if not self.ldap.auth(name, password):
				return

			# If a LDAP user is found (and password matches), we will
			# create a new local user with the information from LDAP.
			user = self.create_from_ldap(name)

		if not user.activated or user.deleted:
			return

		# Check if the password matches
		if user.check_password(password):
			return user

	def email_in_use(self, email):
		return self._get_user_email("SELECT * FROM users_emails \
			WHERE email = %s AND activated IS TRUE", email)

	def get_by_id(self, id):
		return self._get_user("SELECT * FROM users WHERE id = %s", id)

	def get_by_name(self, name):
		return self._get_user("SELECT * FROM users WHERE name = %s", name)

	def get_by_email(self, email):
		return self._get_user("SELECT users.* FROM users \
			LEFT JOIN users_emails ON users.id = users_emails.user_id \
			WHERE users_emails.email = %s", email)

	def get_by_password_recovery_code(self, code):
		return self._get_user("SELECT * FROM users \
			WHERE password_recovery_code = %s AND password_recovery_code_expires_at > NOW()", code)

	def find_maintainers(self, maintainers):
		email_addresses = []

		# Make a unique list of all email addresses
		for maintainer in maintainers:
			name, email_address = email.utils.parseaddr(maintainer)

			if not email_address in email_addresses:
				email_addresses.append(email_address)

		users = self._get_users("SELECT DISTINCT users.* FROM users \
			LEFT JOIN users_emails ON users.id = users_emails.user_id \
			WHERE users_emails.activated IS TRUE \
			AND users_emails.email = ANY(%s)", email_addresses)

		return sorted(users)

	def find_maintainer(self, s):
		name, email_address = email.utils.parseaddr(s)

		# Got invalid input
		if not email_address:
			return

		return self.get_by_email(email_address)

	def search(self, pattern, limit=None):
		pattern = "%%%s%%" % pattern

		users = self._get_users("SELECT * FROM users \
			WHERE (name LIKE %s OR realname LIKE %s) \
			AND activated IS TRUE AND deleted IS FALSE \
			ORDER BY name LIMIT %s", pattern, pattern, limit)

		return list(users)

	@staticmethod
	def check_password_strength(password):
		score = 0
		accepted = False

		# Empty passwords cannot be used.
		if len(password) == 0:
			return False, 0

		# Passwords with less than 6 characters are also too weak.
		if len(password) < 6:
			return False, 1

		# Password with at least 8 characters are secure.
		if len(password) >= 8:
			score += 1

		# 10 characters are even more secure.
		if len(password) >= 10:
			score += 1

		# Digits in the password are good.
		if re.search("\d+", password):
			score += 1

		# Check for lowercase AND uppercase characters.
		if re.search("[a-z]", password) and re.search("[A-Z]", password):
			score += 1

		# Search for special characters.
		if re.search(".[!,@,#,$,%,^,&,*,?,_,~,-,(,)]", password):
			score += 1

		if score >= 3:
			accepted = True

		return accepted, score


class User(base.DataObject):
	table = "users"

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.realname)

	def __hash__(self):
		return hash(self.id)

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.id == other.id

	def __lt__(self, other):
		if isinstance(other, self.__class__):
			return self.name < other.name

		elif isinstance(other, str):
			return self.name < other

	def delete(self):
		self._set_attribute("deleted", True)

	def activate(self):
		self._set_attribute("activated", True)

	def check_password(self, password):
		"""
			Compare the given password with the one stored in the database.
		"""
		if self.ldap_dn:
			return self.backend.users.ldap.bind(self.ldap_dn, password)

		return check_password_hash(password, self.data.passphrase)

	def set_passphrase(self, passphrase):
		"""
			Update the passphrase the users uses to log on.
		"""
		# We cannot set the password for ldap users
		if self.ldap_dn:
			raise AttributeError("Cannot set passphrase for LDAP user")

		self.db.execute("UPDATE users SET passphrase = %s WHERE id = %s",
			generate_password_hash(passphrase), self.id)

	passphrase = property(lambda x: None, set_passphrase)

	def get_realname(self):
		return self.data.realname or self.name

	def set_realname(self, realname):
		self._set_attribute("realname", realname)

	realname = property(get_realname, set_realname)

	@property
	def name(self):
		return self.data.name

	@property
	def ldap_dn(self):
		return self.data.ldap_dn

	@property
	def firstname(self):
		# Try to split the string into first and last name.
		# If that is not successful, return the entire realname.
		try:
			firstname, rest = self.realname.split(" ", 1)
		except:
			return self.realname

		return firstname

	@property
	def envelope_from(self):
		return "%s <%s>" % (self.realname, self.email)

	@lazy_property
	def emails(self):
		res = self.backend.users._get_user_emails("SELECT * FROM users_emails \
			WHERE user_id = %s AND activated IS TRUE ORDER BY email", self.id)

		return list(res)

	@property
	def email(self):
		for email in self.emails:
			if email.primary:
				return email

	def get_email(self, email):
		for e in self.emails:
			if e == email:
				return e

	def set_primary_email(self, email):
		if not email in self.emails:
			raise ValueError("Email address does not belong to user")

		# Mark previous primary email as non-primary
		self.db.execute("UPDATE users_emails SET \"primary\" = FALSE \
			WHERE user_id = %s AND \"primary\" IS TRUE" % self.id)

		# Mark new primary email
		self.db.execute("UPDATE users_emails SET \"primary\" = TRUE \
			WHERE user_id = %s AND email = %s AND activated IS TRUE",
			self.id, email)

	def has_email_address(self, email_address):
		try:
			mail, email_address = email.utils.parseaddr(email_address)
		except:
			pass

		return email_address in self.emails

	def activate_email(self, code):
		# Search email by activation code
		email = self.backend.users._get_user_email("SELECT * FROM users_emails \
			WHERE user_id = %s AND activated IS FALSE AND activation_code = %s", self.id, code)

		if not email:
			return False

		# Activate email address
		email.activate()
		return True

	# Te activated flag is useful for LDAP users
	def add_email(self, email, activated=False):
		# Check if the email is in use
		if self.backend.users.email_in_use(email):
			raise ValueError("Email %s is already in use" % email)

		activation_code = None
		if not activated:
			activation_code = generate_random_string(64)

		user_email = self.backend.users._get_user_email("INSERT INTO users_emails(user_id, email, \
			\"primary\", activated, activation_code) VALUES(%s, %s, %s, %s, %s) RETURNING *",
			self.id, email, not self.emails, activated, activation_code)

		# Set caches
		user_email.user = self
		self.emails.append(user_email)

		# Send activation email if activation is needed
		if not activated:
			user_email.send_activation_mail()

		return user_email

	def send_template(self, *args, **kwargs):
		return self.backend.messages.send_template(self, *args, **kwargs)

	def is_admin(self):
		return self.data.admin is True

	def get_locale(self):
		return tornado.locale.get(self.data.locale)

	def set_locale(self, locale):
		self._set_attribute("locale", locale)

	locale = property(get_locale, set_locale)

	def get_timezone(self, tz=None):
		if tz is None:
			tz = self.data.timezone or ""

		try:
			tz = pytz.timezone(tz)
		except pytz.UnknownTimeZoneError:
			tz = pytz.timezone("UTC")

		return tz

	def set_timezone(self, timezone):
		if not timezone is None:
			tz = self.get_timezone(timezone)
			timezone = tz.zone

		self._set_attribute("timezone", timezone)

	timezone = property(get_timezone, set_timezone)

	def get_password_recovery_code(self):
		return self.data.password_recovery_code

	def set_password_recovery_code(self, code):
		self._set_attribute("password_recovery_code", code)

		self._set_attribute("password_recovery_code_expires_at",
			datetime.datetime.utcnow() + datetime.timedelta(days=1))

	password_recovery_code = property(get_password_recovery_code, set_password_recovery_code)

	def forgot_password(self):
		log.debug("User %s reqested password recovery" % self.name)

		# We cannot reset te password for ldap users
		if self.ldap_dn:
			# Maybe we should send an email with an explanation
			return

		# Add a recovery code to the database and a timestamp when this code expires
		self.password_recovery_code = generate_random_string(64)

		# Send an email with the activation code
		self.send_template("messages/users/password-reset", user=self)

	@property
	def activated(self):
		return self.data.activated

	@property
	def deleted(self):
		return self.data.deleted

	@property
	def registered_at(self):
		return self.data.registered_at

	def gravatar_icon(self, size=128):
		h = hashlib.new("md5")
		if self.email:
			h.update("%s" % self.email)

		# construct the url
		gravatar_url = "http://www.gravatar.com/avatar/%s?" % h.hexdigest()
		gravatar_url += urllib.urlencode({'d': "mm", 's': str(size)})

		return gravatar_url

	@lazy_property
	def perms(self):
		return self.db.get("SELECT * FROM users_permissions WHERE user_id = %s", self.id)

	def has_perm(self, perm):
		"""
			Returns True if the user has the requested permission.
		"""
		# Admins have the permission for everything.
		if self.is_admin():
			return True

		# All others must be checked individually.
		return self.perms.get(perm, False) == True

	@property
	def sessions(self):
		return self.backend.sessions._get_sessions("SELECT * FROM sessions \
			WHERE user_id = %s AND valid_until >= NOW() ORDER BY created_at")


class UserEmail(base.DataObject):
	table = "users_emails"

	def __str__(self):
		return self.email

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.id == other.id

		elif isinstance(other, str):
			return self.email == other

	@lazy_property
	def user(self):
		return self.backend.users.get_by_id(self.data.user_id)

	@property
	def recipient(self):
		return "%s <%s>" % (self.user.realname, self.email)

	@property
	def email(self):
		return self.data.email

	def set_primary(self, primary):
		self._set_attribute("primary", primary)

	primary = property(lambda s: s.data.primary, set_primary)

	@property
	def activated(self):
		return self.data.activated

	def activate(self):
		self._set_attribute("activated", True)
		self._set_attribute("activation_code", None)

	@property
	def activation_code(self):
		return self.data.activation_code

	def send_activation_mail(self):
		if not self.primary:
			return self.send_email_activation_email()

		logging.debug("Sending activation mail to %s" % self.email)

		self.user.send_template("messages/users/account-activation")

	def send_email_activation_mail(self):
		logging.debug("Sending email address activation mail to %s" % self.email)

		self.user.send_template("messages/users/email-activation", email=self)


# Some testing code.
if __name__ == "__main__":
	for password in ("1234567890", "abcdefghij"):
		digest = generate_password_hash(password)

		print "%s %s" % (password, digest)
		print "  Matches? %s" % check_password_hash(password, digest)

