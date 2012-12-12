#!/usr/bin/python

import pakfire

import datetime
import httplib
import pytz
import time
import tornado.locale
import tornado.web
import traceback

import backend
import backend.misc

class BaseHandler(tornado.web.RequestHandler):
	@property
	def cache(self):
		return self.pakfire.cache

	def get_current_user(self):
		session_id = self.get_cookie("session_id")
		if not session_id:
			return

		# Get the session from the database.
		session = self.pakfire.sessions.get(session_id)

		# Return nothing, if no session was found.
		if not session:
			return

		# Update the session lifetime.
		session.refresh(self.request.remote_ip)
		self.set_cookie("session_id", session.id, expires=session.valid_until)

		# If the session impersonated a user, we return that one.
		if session.impersonated_user:
			return session.impersonated_user

		# By default, we return the user of this session.
		return session.user

	def get_user_locale(self):
		DEFAULT_LOCALE = tornado.locale.get("en_US")
		ALLOWED_LOCALES = \
			[tornado.locale.get(l) for l in tornado.locale.get_supported_locales(None)]

		# One can append "?locale=de" to mostly and URI on the site and
		# another output that guessed.
		locale = self.get_argument("locale", None)
		if locale:
			locale = tornado.locale.get(locale)
			for locale in ALLOWED_LOCALES:
				return locale

		# Get the locale from the user settings.
		if self.current_user and self.current_user.locale:
			locale = tornado.locale.get(self.current_user.locale)
			if locale in ALLOWED_LOCALES:
				return locale

		# If no locale was provided we guess what the browser sends us
		locale = self.get_browser_locale()
		if locale in ALLOWED_LOCALES:
			return locale

		# If no one of the cases above worked we use our default locale
		return DEFAULT_LOCALE

	@property
	def remote_address(self):
		"""
			Returns the IP address the request came from.
		"""
		remote_ips = self.request.remote_ip.split(", ")

		return remote_ips[-1]

	@property
	def timezone(self):
		if self.current_user:
			return self.current_user.timezone

		return pytz.utc

	def format_date(self, date, relative=True, shorter=False,
			full_format=False):
		# XXX not very precise but working for now.
		gmt_offset = self.timezone.utcoffset(date).total_seconds() / -60

		return self.locale.format_date(date, gmt_offset=gmt_offset,
			relative=relative, shorter=shorter, full_format=full_format)

	@property
	def render_args(self):
		session = None
		if self.current_user:
			session = self.current_user.session

		ret = {
			"bugtracker"      : self.pakfire.bugzilla,
			"hostname"        : self.request.host,
			"format_date"     : self.format_date,
			"format_size"     : backend.misc.format_size,
			"friendly_time"   : backend.misc.friendly_time,
			"format_email"    : backend.misc.format_email,
			"format_filemode" : backend.misc.format_filemode,
			"lang"            : self.locale.code[:2],
			"pakfire_version" : pakfire.__version__,
			"session"         : session,
			"year"            : time.strftime("%Y"),
		}

		return ret

	def render(self, *args, **kwargs):
		kwargs.update(self.render_args)
		tornado.web.RequestHandler.render(self, *args, **kwargs)

	def render_string(self, *args, **kwargs):
		kwargs.update(self.render_args)
		return tornado.web.RequestHandler.render_string(self, *args, **kwargs)

	def get_error_html(self, status_code, exception=None, **kwargs):
		error_document = "errors/error.html"

		kwargs.update({
			"code"      : status_code,
			"message"   : httplib.responses[status_code],
		})

		if status_code in (400, 403, 404):
			error_document = "errors/error-%s.html" % status_code

		# Collect more information about the exception if possible.
		if exception:
			exception = traceback.format_exc()

		return self.render_string(error_document, exception=exception, **kwargs)

	@property
	def pakfire(self):
		return self.application.pakfire

	@property
	def arches(self):
		return self.pakfire.arches

	@property
	def mirrors(self):
		return self.pakfire.mirrors

	@property
	def public(self):
		"""
			Indicates what level of public/non-public things a user
			may see.
		"""
		if self.current_user and self.current_user.is_admin():
			public = None
		else:
			public = True

		return public
