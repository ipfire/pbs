#!/usr/bin/python

import tornado.locale
import tornado.web

from handlers_base import *

class UserHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self, name=None):
		user = self.current_user

		if name:
			user = self.pakfire.users.get_by_name(name)
			if not user:
				raise tornado.web.HTTPError(404, "User does not exist: %s" % name)

		self.render("user-profile.html", user=user)


class UserDeleteHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self, name):
		user = self.pakfire.users.get_by_name(name)
		if not user:
			raise tornado.web.HTTPError(404)

		if not self.current_user == user and not self.current_user.is_admin():
			raise tornado.web.HTTPError(403)

		confirmed = self.get_argument("confirmed", None)
		if confirmed:
			user.delete()

			if self.current_user == user:
				self.redirect("/logout")
			else:
				self.redirect("/users")

		self.render("user-delete.html", user=user)


class UserEditHandler(BaseHandler):
	def prepare(self):
		# Make list of all supported locales.
		self.supported_locales = \
			[tornado.locale.get(l) for l in tornado.locale.get_supported_locales(None)]

	@tornado.web.authenticated
	def get(self, name):
		user = self.pakfire.users.get_by_name(name)
		if not user:
			raise tornado.web.HTTPError(404)

		if not self.current_user == user and not self.current_user.is_admin():
			raise tornado.web.HTTPError(403)

		self.render("user-profile-edit.html", user=user,
			supported_locales=self.supported_locales)

	@tornado.web.authenticated
	def post(self, name):
		_ = self.locale.translate

		user = self.pakfire.users.get_by_name(name)
		if not user:
			raise tornado.web.HTTPError(404)

		email = self.get_argument("email", user.email)
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

		# Check if locale is valid.
		if locale and not locale in [l.code for l in self.supported_locales]:
			msg.append(_("The choosen locale is invalid."))

		if msgs:
			self.render("user-profile-edit-fail.html", messages=msgs)
			return

		# Everything is okay, we can save the new settings.
		user.locale = locale
		user.email = email
		user.realname = realname
		if pass1:
			user.passphrase = pass1
		user.state = state

		if not user.activated:
			self.render("user-profile-need-activation.html", user=user)
			return

		self.redirect("/user/%s" % user.name)


class UsersHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self):
		admins, testers, users = [], [], []

		for user in self.pakfire.users.get_all():
			if user.is_admin():
				admins.append(user)
			elif user.is_tester():
				testers.append(user)
			else:
				users.append(user)

		self.render("user-list.html", admins=admins, testers=testers,
			users=users)


class UsersCommentsHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self):
		comments = self.pakfire.packages.get_comments(limit=20)

		self.render("user-comments.html", comments=comments)

