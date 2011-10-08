#!/usr/bin/python

from handlers_base import *

class SearchHandler(BaseHandler):
	def get(self):
		query = self.get_argument("q", "")
		if not query:
			self.render("search-form.html")
			return

		pkgs = self.pakfire.packages.search(query)

		self.render("search-results.html", query=query, pkgs=pkgs)
