#!/usr/bin/python

import hashlib
import logging
import pytz
import random
import re
import string
import urllib

import tornado.locale

import base

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

def maintainer_split(s):
	m = re.match(r"(.*) <(.*)>", s)
	if m:
		name, email = m.groups()
	else:
		name, email = None, None

	return name, email

class Users(base.Object):
	def auth(self, name, password):
		# If either name or password is None, we don't check at all.
		if None in (name, password):
			return

		# Search for the username in the database.
		# The user must not be deleted and must be activated.
		user = self.db.get("SELECT id FROM users WHERE name = %s AND \
			activated = 'Y' AND deleted = 'N'", name)

		if not user:
			return

		# Get the whole User object from the database.
		user = self.get_by_id(user.id)

		# If the user was not found or the password does not match,
		# you aren't lucky.
		if not user or not user.check_password(password):
			return

		# Otherwise we return the User object.
		return user

	def register(self, name, password, email, realname, locale=None):
		return User.new(self.pakfire, name, password, email, realname, locale)

	def name_is_used(self, name):
		users = self.db.query("SELECT id FROM users WHERE name = %s", name)

		if users:
			return True

		return False

	def email_is_used(self, email):
		users = self.db.query("SELECT id FROM users_emails WHERE email = %s", email)

		if users:
			return True

		return False

	def get_all(self):
		users = self.db.query("""SELECT id FROM users WHERE activated = 'Y' AND
			deleted = 'N' ORDER BY name ASC""")

		return [User(self.pakfire, u.id) for u in users]

	def get_by_id(self, id):
		return User(self.pakfire, id)

	def get_by_name(self, name):
		user = self.db.get("SELECT id FROM users WHERE name = %s LIMIT 1", name)

		if user:
			return User(self.pakfire, user.id)

	def get_by_email(self, email):
		user = self.db.get("SELECT user_id AS id FROM users_emails \
			WHERE email = %s LIMIT 1", email)

		if user:
			return User(self.pakfire, user.id)

	def count(self):
		count = self.cache.get("users_count")
		if count is None:
			users = self.db.get("SELECT COUNT(*) AS count FROM users \
				WHERE activated = 'Y' AND deleted = 'N'")

			count = users.count
			self.cache.set("users_count", count, 3600)

		return count

	def search(self, pattern, limit=None):
		query = "SELECT id FROM users \
			WHERE (name LIKE %s OR MATCH(name, realname) AGAINST(%s)) \
				AND activated = 'Y' AND deleted = 'N'"
		args  = [pattern, pattern,]

		if limit:
			query += " LIMIT %s"
			args.append(limit)

		users = []
		for user in self.db.query(query, *args):
			user = User(self.pakfire, user.id)
			users.append(user)

		return users

	def find_maintainer(self, s):
		if not s:
			return

		name, email = maintainer_split(s)
		if not email:
			return

		user = self.db.get("SELECT user_id FROM users_emails WHERE email = %s LIMIT 1", email)
		if not user:
			return

		return self.get_by_id(user.user_id)


class User(base.Object):
	def __init__(self, pakfire, id):
		base.Object.__init__(self, pakfire)
		self.id = id

		# A valid session of the user.
		self.session = None

		# Cache.
		self._data = None
		self._emails = None
		self._perms = None

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.realname)

	def __hash__(self):
		return hash(self.id)

	def __cmp__(self, other):
		if other is None:
			return 1

		if isinstance(other, unicode):
			return cmp(self.email, other)

		if self.id == other.id:
			return 0

		return cmp(self.realname, other.realname)

	@classmethod
	def new(cls, pakfire, name, passphrase, email, realname, locale=None):
		id = pakfire.db.execute("INSERT INTO users(name, passphrase, realname) \
			VALUES(%s, %s, %s)", name, generate_password_hash(passphrase), realname)

		# Add email address.
		pakfire.db.execute("INSERT INTO users_emails(user_id, email, `primary`) \
			VALUES(%s, %s, 'Y')", id, email)

		# Create row in permissions table.
		pakfire.db.execute("INSERT INTO users_permissions(user_id) VALUES(%s)", id)

		user = cls(pakfire, id)

		# If we have a guessed locale, we save it (for sending emails).
		if locale:
			user.locale = locale

		user.send_activation_mail()

		return user

	@property
	def data(self):
		if self._data is None:
			self._data = self.db.get("SELECT * FROM users WHERE id = %s" % self.id)
			assert self._data, "User %s not found." % self.id

		return self._data

	def delete(self):
		self.db.execute("UPDATE users SET deleted = 'Y' WHERE id = %s", self.id)
		self._data = None

	def activate(self):
		self.db.execute("UPDATE users SET activated = 'Y', activation_code = NULL \
			WHERE id = %s", self.id)

	def check_password(self, password):
		"""
			Compare the given password with the one stored in the database.
		"""
		return check_password_hash(password, self.data.passphrase)

	def set_passphrase(self, passphrase):
		"""
			Update the passphrase the users uses to log on.
		"""
		self.db.execute("UPDATE users SET passphrase = %s WHERE id = %s",
			generate_password_hash(passphrase), self.id)

	passphrase = property(lambda x: None, set_passphrase)

	@property
	def activation_code(self):
		return self.data.activation_code

	def get_realname(self):
		if not self.data.realname:
			return self.name

		return self.data.realname

	def set_realname(self, realname):
		self.db.execute("UPDATE users SET realname = %s WHERE id = %s",
			realname, self.id)
		self.data["realname"] = realname

	realname = property(get_realname, set_realname)

	@property
	def name(self):
		return self.data.name

	@property
	def firstname(self):
		# Try to split the string into first and last name.
		# If that is not successful, return the entire realname.
		try:
			firstname, rest = self.realname.split(" ", 1)
		except:
			return self.realname

		return firstname

	def get_email(self):
		if self._emails is None:
			self._emails = self.db.query("SELECT * FROM users_emails WHERE user_id = %s", self.id)
			assert self._emails

		for email in self._emails:
			if not email.primary == "Y":
				continue

			return email.email

	def set_email(self, email):
		if email == self.email:
			return

		self.db.execute("UPDATE users_emails SET email = %s \
			WHERE user_id = %s AND primary = 'Y'", email, self.id)

		self.db.execute("UPDATE users SET activated  'N' WHERE id = %s",
			email, self.id)

		# Reset cache.
		self._data = self._emails = None

		# Inform the user, that he or she has to re-activate the account.
		self.send_activation_mail()

	email = property(get_email, set_email)

	def get_state(self):
		return self.data.state

	def set_state(self, state):
		self.db.execute("UPDATE users SET state = %s WHERE id = %s", state,
			self.id)
		self.data["state"] = state

	state = property(get_state, set_state)

	def get_locale(self):
		return self.data.locale or ""

	def set_locale(self, locale):
		self.db.execute("UPDATE users SET locale = %s WHERE id = %s", locale,
			self.id)
		self.data["locale"] = locale

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

		self.db.execute("UPDATE users SET timezone = %s WHERE id = %s",
			timezone, self.id)

	timezone = property(get_timezone, set_timezone)

	@property
	def activated(self):
		return self.data.activated == "Y"

	@property
	def registered(self):
		return self.data.registered

	def gravatar_icon(self, size=128):
		# construct the url
		gravatar_url = "http://www.gravatar.com/avatar/" + \
			hashlib.md5(self.email.lower()).hexdigest() + "?"       
		gravatar_url += urllib.urlencode({'d': "mm", 's': str(size)})

		return gravatar_url

	def is_admin(self):
		return self.state == "admin"

	def is_tester(self):
		return self.state == "tester"

	@property
	def perms(self):
		if self._perms is None:
			self._perms = \
				self.db.get("SELECT * FROM users_permissions WHERE user_id = %s", self.id)

		return self._perms

	def has_perm(self, perm):
		"""
			Returns True if the user has the requested permission.
		"""
		# Admins have the permission for everything.
		if self.is_admin():
			return True

		# Exception for voting. All testers are allowed to vote.
		if perm == "vote" and self.is_tester():
			return True

		# All others must be checked individually.
		return self.perms.get(perm, "N") == "Y"

	def send_activation_mail(self):
		logging.debug("Sending activation mail to %s" % self.email)

		# Generate a random activation code.
		source = string.ascii_letters + string.digits
		self.data["activation_code"] = "".join(random.sample(source * 20, 20))
		self.db.execute("UPDATE users SET activation_code = %s WHERE id = %s",
			self.activation_code, self.id)

		# Get the saved locale from the user.
		locale = tornado.locale.get(self.locale)
		_ = locale.translate

		subject = _("Account Activation")

		message  = _("You, or somebody using you email address, has registered an account on the Pakfire Build Service.")
		message += "\n"*2
		message += _("To activate your account, please click on the link below.")
		message += "\n"*2
		message += "    %(baseurl)s/user/%(name)s/activate?code=%(activation_code)s" \
			% { "baseurl" : self.settings.get("baseurl"), "name" : self.name,
				"activation_code" : self.activation_code, }
		message += "\n"*2
		message += "Sincerely,\n    The Pakfire Build Service"

		self.pakfire.messages.add("%s <%s>" % (self.realname, self.email), subject, message)

	def get_comments(self, limit=5):
		comments = self.db.query("""SELECT * FROM builds_comments
			WHERE user_id = %s ORDER BY time_created DESC LIMIT %s""", self.id, limit)

		return comments

	@property
	def log(self):
		return self.get_history(limit=15)

	def get_history(self, limit=None):
		return [] # XXX TODO


# Some testing code.
if __name__ == "__main__":
	for password in ("1234567890", "abcdefghij"):
		digest = generate_password_hash(password)

		print "%s %s" % (password, digest)
		print "  Matches? %s" % check_password_hash(password, digest)

