#!/usr/bin/python

import tornado.locale
import tornado.web

from . import base

class UserHandler(base.BaseHandler):
	@tornado.web.authenticated
	def get(self, name=None):
		user = self.current_user

		if name:
			user = self.pakfire.users.get_by_name(name)
			if not user:
				raise tornado.web.HTTPError(404, "User does not exist: %s" % name)

		self.render("user-profile.html", user=user)


class UserImpersonateHandler(base.BaseHandler):
	@tornado.web.authenticated
	def get(self, username):
		# You must be an admin to do this.
		if not self.current_user.is_admin():
			raise tornado.web.HTTPError(403, "You are not allowed to do this")

		user = self.backend.users.get_by_name(username)
		if not user:
			raise tornado.web.HTTPError(404, "User not found: %s" % username)

		self.render("user-impersonation.html", user=user)

	@tornado.web.authenticated
	def post(self, username):
		# You must be an admin to do this.
		if not self.current_user.is_admin():
			raise tornado.web.HTTPError(403, "You are not allowed to do this")

		user = self.backend.users.get_by_name(username)
		if not user:
			raise tornado.web.HTTPError(404, "User not found: %s" % username)

		# Start impersonation
		with self.db.transaction():
			self.session.start_impersonation(user)

		# Redirect to start page.
		self.redirect("/")


class UserActionHandler(base.BaseHandler):
	def get_user(self, name):
		user = self.pakfire.users.get_by_name(name)
		if not user:
			raise tornado.web.HTTPError(404)

		if not self.current_user == user and not self.current_user.is_admin():
			raise tornado.web.HTTPError(403)

		return user


class UserDeleteHandler(base.BaseHandler):
	@tornado.web.authenticated
	def get(self, name):
		user = self.get_user(name)

		confirmed = self.get_argument("confirmed", None)
		if confirmed:
			user.delete()

			if self.current_user == user:
				self.redirect("/logout")
			else:
				self.redirect("/users")

		self.render("user-delete.html", user=user)


class UserPasswdHandler(UserActionHandler):
	@tornado.web.authenticated
	def get(self, name, error_msg=None):
		user = self.get_user(name)

		self.render("user-profile-passwd.html", user=user,
			error_msg=error_msg)

	@tornado.web.authenticated
	def post(self, name):
		_ = self.locale.translate

		# Fetch the user.
		user = self.get_user(name)		

		# If the user who wants to change the password is not an admin,
		# he needs to provide the old password.
		if not self.current_user.is_admin() or self.current_user == user:
			pass0 = self.get_argument("pass0", None)
			if not pass0:
				return self.get(name, error_msg=_("You need to enter you current password."))

			if not self.current_user.check_password(pass0):
				return self.get(name, error_msg=_("The provided account password is wrong."))

		pass1 = self.get_argument("pass1", "")
		pass2 = self.get_argument("pass2", "")

		error_msg = None

		# The password must at least have 8 characters.
		if not pass1 == pass2:
			error_msg = _("The given passwords do not match.")
		elif len(pass1) == 0:
			error_msg = _("The password was blank.")
		else:
			accepted, score = backend.users.check_password_strength(pass1)
			if not accepted:
				error_msg = _("The given password is too weak.")

		if error_msg:
			return self.get(name, error_msg=error_msg)

		# Update the password.
		user.set_passphrase(pass1)

		self.render("user-profile-passwd-ok.html", user=user)


class UserEditHandler(base.BaseHandler):
	@tornado.web.authenticated
	def get(self, name):
		user = self.pakfire.users.get_by_name(name)
		if not user:
			raise tornado.web.HTTPError(404)

		if not self.current_user == user and not self.current_user.is_admin():
			raise tornado.web.HTTPError(403)

		self.render("user-profile-edit.html", user=user)

	@tornado.web.authenticated
	def post(self, name):
		_ = self.locale.translate

		user = self.pakfire.users.get_by_name(name)
		if not user:
			raise tornado.web.HTTPError(404)

		with self.db.transaction():
			email = self.get_argument("primary_email_address")
			realname = self.get_argument("realname", user.realname)
			pass1 = self.get_argument("pass1", None)
			pass2 = self.get_argument("pass2", None)
			locale = self.get_argument("locale", "")

			# Only an admin can alter the state of a user.
			if self.current_user.is_admin():
				state = self.get_argument("state", user.state)
			else:
				state = user.state

			# Collect error messages
			msgs = []

			if not email:
				msgs.append(_("No email address provided."))
			elif not "@" in email:
				msgs.append(_("Email address is invalid."))

			# Check if the passphrase is okay.
			if pass1 and not len(pass1) >= 8:
				msgs.append(_("Password has less than 8 characters."))
			elif not pass1 == pass2:
				msgs.append(_("Passwords do not match."))

			if msgs:
				self.render("user-profile-edit-fail.html", messages=msgs)
				return

			# Everything is okay, we can save the new settings.
			user.locale = locale
			user.set_primary_email(email)
			user.realname = realname
			if pass1:
				user.passphrase = pass1
			user.state = state

			# Get the timezone settings.
			tz = self.get_argument("timezone", None)
			user.timezone = tz

			if not user.activated:
				self.render("user-profile-need-activation.html", user=user)
				return

		self.redirect("/user/%s" % user.name)


class UsersHandler(base.BaseHandler):
	@tornado.web.authenticated
	def get(self):
		self.render("user-list.html", users=self.backend.users)


class UsersBuildsHandler(base.BaseHandler):
	def get(self, name=None):
		if name is None:
			user = self.current_user
		else:
			user = self.pakfire.users.get_by_name(name)
			if not user:
				raise tornado.web.HTTPError(404, "User not found: %s" % name)

		# Get a list of the builds this user has built.
		builds = self.pakfire.builds.get_by_user(user)

		self.render("user-profile-builds.html", user=user, builds=builds)
