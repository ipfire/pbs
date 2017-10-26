#!/usr/bin/python

import re

from . import base

class SearchHandler(base.BaseHandler):
	def get(self):
		pattern = self.get_argument("q", "")
		if not pattern:
			self.render("search-form.html", pattern="")
			return

		# Check if the given search pattern is a UUID.
		if re.match(r"^([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})$", pattern):
			# Search for a matching object and redirect to it.

			# Search in packages.
			pkg = self.backend.packages.get_by_uuid(pattern)
			if pkg:
				self.redirect("/package/%s" % pkg.uuid)
				return

			# Search in builds.
			build = self.backend.builds.get_by_uuid(pattern)
			if build:
				self.redirect("/build/%s" % build.uuid)
				return

			# Search in jobs.
			job = self.backend.jobs.get_by_uuid(pattern)
			if job:
				self.redirect("/job/%s" % job.uuid)
				return

		pkgs = files = users = []

		if pattern.startswith("/"):
			# Do a file search.
			files = self.backend.packages.search_by_filename(pattern, limit=50)

		else:
			# Make fulltext search in the packages.
			pkgs = self.backend.packages.search(pattern, limit=50)

			# Search for users.
			users = self.backend.users.search(pattern, limit=50)

		if len(pkgs) == 1 and not files and not users:
			pkg = pkgs[0]

			self.redirect("/package/%s" % pkg.name)
			return

		# If we have results, we show them.
		if pkgs or files or users:
			self.render("search-results.html", pattern=pattern,
				pkgs=pkgs, files=files, users=users)
			return

		# If there were no results, we show the advanced search site.
		self.render("search-form.html", pattern=pattern)
