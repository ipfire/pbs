#!/usr/bin/python

import tornado.web

import backend.sessions
import backend.users

from handlers_base import *

class LoginHandler(BaseHandler):
	def get(self):
		# If the user is already logged in, we just send him back
		# to the start page.
		if self.current_user:
			self.redirect("/")
			return

		self.render("login.html", failed=False)

	def post(self):
		name = self.get_argument("name", None)
		passphrase = self.get_argument("pass", None)

		user = self.pakfire.users.auth(name, passphrase)

		if user:
			# Create a new session for the user.
			session = backend.sessions.Session.create(self.pakfire, user)

			# Set a cookie and update the current user.
			self.set_cookie("session_id", session.id)
			self._current_user = user

			# If there is "next" given, we redirect the user accordingly.
			# Otherwise we show a nice welcome message and tell the user, that
			# the login was successful.
			next = self.get_argument("next", None)

			if next:
				self.redirect(next)
			else:
				self.render("login-successful.html", user=user)

		else:
			# If the login failed we return an error message.
			self.render("login.html", failed=True)


class RegisterHandler(BaseHandler):
	def get(self):
		# If the user is already logged in, we just send him back
		# to the start page.
		if self.current_user:
			self.redirect("/")
			return

		self.render("register.html")

	def post(self):
		_ = self.locale.translate
		msgs = []

		# Read all information from the request.
		name = self.get_argument("name", None)
		email = self.get_argument("email", None)
		realname = self.get_argument("realname", None)
		pass1 = self.get_argument("pass1", None)
		pass2 = self.get_argument("pass2", None)

		if not name:
			msgs.append(_("No username provided."))
		elif self.pakfire.users.name_is_used(name):
			msgs.append(_("The given username is already taken."))

		if not email:
			msgs.append(_("No email address provided."))
		elif not "@" in email:
			msgs.append(_("Email address is invalid."))
		elif self.pakfire.users.email_is_used(email):
			msgs.append(_("The given email address is already used for another account."))

		# Check if the passphrase is okay.
		if not pass1:
			msgs.append(_("No password provided."))
		elif not pass1 == pass2:
			msgs.append(_("Passwords do not match."))
		else:
			accepted, score = backend.users.check_password_strength(pass1)
			if not accepted:
				msgs.append(_("Your password is too weak."))

		if msgs:
			self.render("register-fail.html", messages=msgs)
			return

		# All provided data seems okay.
		# Register the new user to the database.
		user = self.pakfire.users.register(name, pass1, email, realname,
			self.locale.code)

		self.render("register-success.html", user=user)


class ActivationHandler(BaseHandler):
	def get(self, _user):
		user = self.pakfire.users.get_by_name(_user)
		if not user:
			raise tornado.web.HTTPError(404)

		code = self.get_argument("code")

		# Check if the activation code matches and then activate the account.
		if user.activation_code == code:
			user.activate()

			# If an admin activated another account, he impersonates it.
			if self.current_user and self.current_user.is_admin():
				self.session.start_impersonation(user)

			else:
				# Automatically login the user.
				session = backend.sessions.Session.create(self.pakfire, user)

				# Set a cookie and update the current user.
				self.set_cookie("session_id", session.id)
				self._current_user = user

			self.render("register-activation-success.html", user=user)
			return

		# Otherwise, show an error message.
		self.render("register-activation-fail.html")


class PasswordRecoveryHandler(BaseHandler):
	def get(self):
		return self.render("user-forgot-password.html")

	def post(self):
		username = self.get_argument("name", None)

		if not username:
			return self.get()

		# XXX TODO


class LogoutHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self):
		# Remove the cookie, that identifies the user.
		self.clear_cookie("session_id")

		# Destroy the user's session.
		self.session.destroy()
		self._current_user = None

		# Show a message to the user.
		self.render("logout.html")
