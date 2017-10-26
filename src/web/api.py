#!/usr/bin/python

import tornado.web

from . import base

class ApiPackagesAutocomplete(base.ApiBaseHandler):
	def get(self):
		query = self.get_argument("q")
		if not query:
			raise tornado.web.HTTPError(400)

		# Query database.
		packages = self.backend.packages.autocomplete(query, limit=8)

		res = {
			"query"    : query,
			"packages" : packages,
		}

		self.write(res)
