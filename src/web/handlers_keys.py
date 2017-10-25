#!/usr/bin/python

import tornado.web

from . import base

class KeysActionHandler(base.BaseHandler):
	def prepare(self):
		if not self.current_user.has_perm("manage_keys"):
			raise tornado.web.HTTPError(403)


class KeysImportHandler(KeysActionHandler):
	@tornado.web.authenticated
	def get(self):
		self.render("keys-import.html")

	@tornado.web.authenticated
	def post(self):
		data = self.get_argument("data")

		key = self.pakfire.keys.create(data)
		assert key

		self.redirect("/keys")


class KeysDeleteHandler(KeysActionHandler):
	@tornado.web.authenticated
	def get(self, fingerprint):
		key = self.pakfire.keys.get_by_fpr(fingerprint)
		if not key:
			raise tornado.web.HTTPError(404, "Could not find key: %s" % fingerprint)

		confirmed = self.get_argument("confirmed", False)
		if confirmed:
			key.delete()

			return self.redirect("/keys")

		self.render("keys-delete.html", key=key)


class KeysListHandler(base.BaseHandler):
	def get(self):
		keys = self.pakfire.keys.get_all()

		self.render("keys-list.html", keys=keys)


class KeysDownloadHandler(base.BaseHandler):
	def get(self, fingerprint):
		key = self.pakfire.keys.get_by_fpr(fingerprint)
		if not key:
			raise tornado.web.HTTPError(404, "Could not find key: %s" % fingerprint)

		# Send the key data.
		self.set_header("Content-Type", "text/plain")
		self.write(key.key)
