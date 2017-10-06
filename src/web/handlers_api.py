#!/usr/bin/python

import tornado.web

from handlers_base import *

class ApiBaseHandler(BaseHandler):
	pass


class ApiPackagesAutocomplete(BaseHandler):
	def get(self):
		query = self.get_argument("q")
		if not query:
			raise tornado.web.HTTPError(400)

		# Query database.
		packages = self.pakfire.packages.autocomplete(query, limit=8)

		res = {
			"query"    : query,
			"packages" : packages,
		}

		self.write(res)
