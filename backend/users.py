#!/usr/bin/python

import hashlib
import logging
import random
import string
import urllib

import tornado.locale

import base

class Users(base.Object):
	def auth(self, name, passphrase):
		# If either name or passphrase is None, we don't check at all.
		if None in (name, passphrase):
			return

		user = self.db.get("""SELECT id FROM users WHERE name = %s
			AND passphrase = SHA1(%s) AND activated = 'Y' AND deleted = 'N'""",
			name, passphrase)

		if user:
			return User(self.pakfire, user.id)

	def register(self, name, passphrase, email, realname, locale=None):
		return User.new(self.pakfire, name, passphrase, email, realname, locale)

	def name_is_used(self, name):
		users = self.db.query("SELECT id FROM users WHERE name = %s", name)

		if users:
			return True

		return False

	def email_is_used(self, email):
		users = self.db.query("SELECT id FROM users WHERE email = %s", email)

		if users:
			return True

		return False

	def get_all(self):
		users = self.db.query("""SELECT id FROM users WHERE activated = 'Y' AND
			deleted = 'N' ORDER BY realname, name""")

		return [User(self.pakfire, u.id) for u in users]

	def get_by_id(self, id):
		user = self.db.get("SELECT id FROM users WHERE id = %s LIMIT 1", id)

		if user:
			return User(self.pakfire, user.id)

	def get_by_name(self, name):
		user = self.db.get("SELECT id FROM users WHERE name = %s LIMIT 1", name)

		if user:
			return User(self.pakfire, user.id)

	def get_by_email(self, email):
		user = self.db.get("SELECT id FROM users WHERE email = %s LIMIT 1", email)

		if user:
			return User(self.pakfire, user.id)


class User(base.Object):
	def __init__(self, pakfire, id):
		base.Object.__init__(self, pakfire)
		self.id = id

		self.data = self.db.get("SELECT * FROM users WHERE id = %s" % self.id)

	def __cmp__(self, other):
		return cmp(self.id, other.id)

	@classmethod
	def new(cls, pakfire, name, passphrase, email, realname, locale=None):

		id = pakfire.db.execute("""INSERT INTO users(name, passphrase, email, realname)
			VALUES(%s, SHA1(%s), %s, %s)""", name, passphrase, email, realname)

		user = cls(pakfire, id)

		# If we have a guessed locale, we save it (for sending emails).
		if locale:
			user.locale = locale

		user.send_activation_mail()

		return user

	def delete(self):
		self.db.execute("UPDATE users SET deleted = 'Y' WHERE id = %s", self.id)

	def activate(self):
		self.db.execute("UPDATE users SET activated = 'Y' WHERE id = %s", self.id)

	def set_passphrase(self, passphrase):
		"""
			Update the passphrase the users uses to log on.
		"""
		self.db.execute("UPDATE users SET passphrase = SHA1(%s) WHERE id = %s",
			passphrase, self.id)

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

	def get_email(self):
		return self.data.email

	def set_email(self, email):
		if email == self.email:
			return

		self.db.execute("""UPDATE users SET email = %s, activated = 'N'
			WHERE id = %s""", email, self.id)

		self.data.update({
			"email" : email,
			"activated" : "N",
		})

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
		message += "    http://pakfire.ipfire.org/user/%(name)s/activate/%(activation_code)s" \
			% { "name" : self.name, "activation_code" : self.activation_code, }
		message += "\n"*2
		message += "Sincerely,\n    The Pakfire Build Service"

		self.pakfire.messages.add("%s <%s>" % (self.realname, self.email), subject, message)

	@property
	def comments(self, limit=5):
		comments = self.db.query("""SELECT * FROM package_comments
			WHERE user_id = %s ORDER BY time DESC LIMIT %s""", self.id, limit)

		return comments

	@property
	def log(self):
		log = self.db.query("SELECT * FROM log WHERE user_id = %s ORDER BY time DESC",
			self.id)

		return log
