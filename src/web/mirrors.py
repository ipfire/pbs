#!/usr/bin/python

import tornado.web

from .. import mirrors

from .handlers_base import BaseHandler

class MirrorListHandler(BaseHandler):
	def get(self):
		mirrors = self.backend.mirrors
		mirrors_nearby = self.backend.mirrors.get_for_location(self.current_address)

		mirrors_worldwide = []
		for mirror in mirrors:
			if mirror in mirrors_nearby:
				continue

			mirrors_worldwide.append(mirror)

		kwargs = {
			"mirrors" : mirrors,
			"mirrors_nearby" : mirrors_nearby,
			"mirrors_worldwide" : mirrors_worldwide,
		}

		# Get recent log messages.
		kwargs["log"] = self.backend.mirrors.get_history(limit=5)

		self.render("mirrors/list.html", **kwargs)


class MirrorDetailHandler(BaseHandler):
	def get(self, hostname):
		mirror = self.backend.mirrors.get_by_hostname(hostname)
		if not mirror:
			raise tornado.web.HTTPError(404, "Could not find mirror: %s" % hostname)

		log = self.backend.mirrors.get_history(mirror=mirror, limit=10)

		self.render("mirrors/detail.html", mirror=mirror, log=log)


class MirrorActionHandler(BaseHandler):
	"""
		A handler that makes sure if the user has got sufficent rights to
		do actions.
	"""
	def prepare(self):
		# Check if the user has sufficient rights to create a new mirror.
		if not self.current_user.has_perm("manage_mirrors"):
			raise tornado.web.HTTPError(403)


class MirrorNewHandler(MirrorActionHandler):
	@tornado.web.authenticated
	def get(self, hostname="", path="", hostname_missing=False, path_invalid=False):
		self.render("mirrors/new.html", _hostname=hostname, path=path,
			hostname_missing=hostname_missing, path_invalid=path_invalid)

	@tornado.web.authenticated
	def post(self):
		errors = {}

		hostname = self.get_argument("name", None)
		if not hostname:
			errors["hostname_missing"] = True

		path = self.get_argument("path", "")
		if path is None:
			errors["path_invalid"] = True

		if errors:
			errors.update({
				"hostname" : hostname,
				"path" : path,
			})
			return self.get(**errors)

		# Create mirror
		with self.db.transaction():
			mirror = self.backend.mirrors.create(hostname, path, user=self.current_user)

		self.redirect("/mirror/%s" % mirror.hostname)


class MirrorEditHandler(MirrorActionHandler):
	@tornado.web.authenticated
	def get(self, hostname):
		mirror = self.backend.mirrors.get_by_hostname(hostname)
		if not mirror:
			raise tornado.web.HTTPError(404, "Could not find mirror: %s" % hostname)

		self.render("mirrors/edit.html", mirror=mirror)

	@tornado.web.authenticated
	def post(self, hostname):
		mirror = self.backend.mirrors.get_by_hostname(hostname)
		if not mirror:
			raise tornado.web.HTTPError(404, "Could not find mirror: %s" % hostname)

		with self.db.transaction():
			mirror.hostname       = self.get_argument("name")
			mirror.path           = self.get_argument("path", "")
			mirror.owner          = self.get_argument("owner", None)
			mirror.contact        = self.get_argument("contact", None)
			mirror.supports_https = self.get_argument("supports_https", False)

		self.redirect("/mirror/%s" % mirror.hostname)


class MirrorDeleteHandler(MirrorActionHandler):
	@tornado.web.authenticated
	def get(self, hostname):
		mirror = self.backend.mirrors.get_by_hostname(hostname)
		if not mirror:
			raise tornado.web.HTTPError(404, "Could not find mirror: %s" % hostname)

		confirmed = self.get_argument("confirmed", None)	
		if confirmed:
			with self.db.transaction():
				mirror.deleted = True

			self.redirect("/mirrors")
			return

		self.render("mirrors/delete.html", mirror=mirror)
