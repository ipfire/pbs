#!/usr/bin/python

import datetime
import pytz

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

		log = user.get_history(limit=10)
		comments = user.get_comments(limit=5)

		self.render("user-profile.html", user=user, log=log, comments=comments)


class UserImpersonateHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self):
		action = self.get_argument("action", "start")

		if action == "stop":
			self.session.stop_impersonation()
			self.redirect("/")
			return

		# You must be an admin to do this.
		if not self.current_user.is_admin():
			raise tornado.web.HTTPError(403, "You are not allowed to do this.")

		username = self.get_argument("user", "")
		user = self.pakfire.users.get_by_name(username)
		if not user:
			raise tornado.web.HTTPError(404, "User not found: %s" % username)

		self.render("user-impersonation.html", user=user)

	@tornado.web.authenticated
	def post(self):
		# You must be an admin to do this.
		if not self.current_user.is_admin():
			raise tornado.web.HTTPError(403, "You are not allowed to do this.")

		username = self.get_argument("user")
		user = self.pakfire.users.get_by_name(username)
		if not user:
			raise tornado.web.HTTPError(404, "User does not exist: %s" % username)

		self.session.start_impersonation(user)

		# Redirect to start page.
		self.redirect("/")


class UserActionHandler(BaseHandler):
	def get_user(self, name):
		user = self.pakfire.users.get_by_name(name)
		if not user:
			raise tornado.web.HTTPError(404)

		if not self.current_user == user and not self.current_user.is_admin():
			raise tornado.web.HTTPError(403)

		return user


class UserDeleteHandler(BaseHandler):
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
			supported_timezones=pytz.common_timezones,
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

		# Get the timezone settings.
		tz = self.get_argument("timezone", None)
		user.timezone = tz

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


class UsersBuildsHandler(BaseHandler):
	def __chunk_by_name(self, _builds):
		builds = {}

		for build in _builds:
			i = build.pkg.name[0]
			try:
				builds[i].append(build)
			except KeyError:
				builds[i] = [build,]
		
		return builds
		#return [v for k,v in sorted(builds.items())]

	def __chunk_by_date(self, _builds):
		# XXX dummy function
		builds = {
			datetime.datetime.utcnow() : _builds,
		}

		return builds

		for build in _builds:
			builds.append([build,])

		return builds

	def get(self, name=None):
		if name:
			user = self.pakfire.users.get_by_name(name)
			if not user:
				raise tornado.web.HTTPError(404, "User not found: %s" % name)
		else:
			user = self.current_user

		# By default users see only public builds.
		# Admins are allowed to see all builds.
		public = True
		if self.current_user and self.current_user.is_admin():
			public = None

		# Select the type of the builds that are shown.
		# None for all.
		type = self.get_argument("type", None)

		# Select how to order the results. The default is by date.
		order_by = self.get_argument("order_by", "date")
		if not order_by in ("date", "name"):
			order_by = "date"

		# Get a list of the builds this user has built.
		builds = self.pakfire.builds.get_by_user_iter(user, type=type,
			public=public, order_by=order_by)

		if builds:
			# Chunk the list for a better presentation.
			if order_by == "date":
				builds = self.__chunk_by_date(builds)
			elif order_by == "name":
				builds = self.__chunk_by_name(builds)

		self.render("user-profile-builds.html", user=user, builds=builds)
