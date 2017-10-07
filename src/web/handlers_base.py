#!/usr/bin/python

import pakfire

import datetime
import httplib
import pytz
import time
import tornado.locale
import tornado.web
import traceback

from .. import misc
from ..decorators import *

class BaseHandler(tornado.web.RequestHandler):
	@property
	def backend(self):
		return self.application.backend

	@property
	def db(self):
		return self.backend.db

	@lazy_property
	def session(self):
		# Get the session from the cookie
		session_id = self.get_cookie("session_id", None)

		# Search for a valid database session
		if session_id:
			session = self.backend.sessions.get(session_id)

			# Found a valid session
			if session:
				return session

	def get_current_user(self):
		if self.session:
			return self.session.impersonated_user or self.session.user

	def get_user_locale(self):
		# Get the locale from the user settings.
		if self.current_user and self.current_user.locale:
			locale = tornado.locale.get(self.current_user.locale)
			if locale:
				return locale

		# If no locale was provided, we take what ever the browser requested.
		return self.get_browser_locale()

	@property
	def current_address(self):
		"""
			Returns the IP address the request came from.
		"""
		return self.request.headers.get("X-Real-IP") or self.request.remote_ip

	@property
	def user_agent(self):
		"""
			Returns the HTTP user agent
		"""
		return self.request.headers.get("User-Agent", None)

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

	def get_template_namespace(self):
		ns = tornado.web.RequestHandler.get_template_namespace(self)

		ns.update({
			"bugtracker"      : self.pakfire.bugzilla,
			"hostname"        : self.request.host,
			"format_date"     : self.format_date,
			"format_size"     : misc.format_size,
			"friendly_time"   : misc.friendly_time,
			"format_email"    : misc.format_email,
			"format_filemode" : misc.format_filemode,
			"lang"            : self.locale.code[:2],
			"pakfire_version" : pakfire.__version__,
			"session"         : self.session,
			"year"            : time.strftime("%Y"),
		})

		return ns

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
		return self.backend

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
