#!/usr/bin/python

import backend

from handlers_base import *

class BuilderListHandler(BaseHandler):
	def get(self):
		builders = self.pakfire.builders.get_all()

		self.render("builder-list.html", builders=builders)


class BuilderDetailHandler(BaseHandler):
	def get(self, hostname):
		builder = self.pakfire.builders.get_by_name(hostname)

		self.render("builder-detail.html", builder=builder)


class BuilderNewHandler(BaseHandler):
	def get(self):
		self.render("builder-new.html")

	def post(self):
		name = self.get_argument("name")

		# Create a new builder.
		builder = backend.builders.Builder.new(self.pakfire, name)

		self.render("builder-pass.html", action="new", builder=builder)


class BuilderEditHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self, hostname):
		builder = self.pakfire.builders.get_by_name(hostname)
		if not builder:
			raise tornado.web.HTTPError(404, "Builder not found")

		self.render("builder-edit.html", builder=builder)

	@tornado.web.authenticated
	def post(self, hostname):
		builder = self.pakfire.builders.get_by_name(hostname)
		if not builder:
			raise tornado.web.HTTPError(404, "Builder not found")

		builder.enabled = self.get_argument("enabled", False)
		builder.build_src = self.get_argument("build_src", False)
		builder.build_bin = self.get_argument("build_bin", False)
		builder.build_test = self.get_argument("build_test", False)

		# Save max_jobs.
		max_jobs = self.get_argument("max_jobs", builder.max_jobs)
		try:
			max_jobs = int(max_jobs)
		except TypeError:
			max_jobs = 1

		if not max_jobs in (1, 2, 3, 4, 5, 6, 7, 8,):
			max_jobs = 1
		builder.max_jobs = max_jobs

		self.redirect("/builder/%s" % builder.hostname)


class BuilderRenewPassphraseHandler(BaseHandler):
	def get(self, name):
		builder = self.pakfire.builders.get_by_name(name)

		builder.regenerate_passphrase()

		self.render("builder-pass.html", action="update", builder=builder)


class BuilderDeleteHandler(BaseHandler):
	def get(self, name):
		builder = self.pakfire.builders.get_by_name(name)

		confirmed = self.get_argument("confirmed", None)	
		if confirmed:
			builder.delete()
			self.redirect("/builders")
			return

		self.render("builder-delete.html", builder=builder)
