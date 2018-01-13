#!/usr/bin/python

import tornado.web

from . import base

class BuilderListHandler(base.BaseHandler):
	def get(self):
		self.render("builders/list.html", builders=self.backend.builders)


class BuilderDetailHandler(base.BaseHandler):
	def get(self, hostname):
		builder = self.backend.builders.get_by_name(hostname)
		if not builder:
			raise tornado.web.HTTPError(404, "Could not find builder %s" % hostname)

		# Get running and pending jobs.
		jobs = builder.active_jobs + list(builder.jobqueue)

		# Get log.
		log = builder.get_history(limit=5)

		self.render("builders/detail.html", builder=builder, jobs=jobs, log=log)

	@tornado.web.authenticated
	def post(self, hostname):
		if not self.current_user.has_perm("maintain_mirrors"):
			raise tornado.web.HTTPError(403, "User is not allowed to do this.")

		builder = self.backend.builders.get_by_name(hostname)

		with self.db.transaction():
			builder.description = self.get_argument("description", None)

		self.redirect("/builder/%s" % builder.hostname)


class BuilderNewHandler(base.BaseHandler):
	def get(self):
		self.render("builders/new.html")

	@tornado.web.authenticated
	def post(self):
		if not self.current_user.has_perm("maintain_builders"):
			raise tornado.web.HTTPError(403)

		name = self.get_argument("name")

		# Create a new builder.
		builder, passphrase = \
			self.backend.builders.create(name, user=self.current_user)

		self.render("builders/pass.html", action="new", builder=builder,
			passphrase=passphrase)


class BuilderEditHandler(base.BaseHandler):
	@tornado.web.authenticated
	def get(self, hostname):
		builder = self.backend.builders.get_by_name(hostname)
		if not builder:
			raise tornado.web.HTTPError(404, "Builder not found")

		self.render("builders/edit.html", builder=builder)

	@tornado.web.authenticated
	def post(self, hostname):
		builder = self.backend.builders.get_by_name(hostname)
		if not builder:
			raise tornado.web.HTTPError(404, "Builder not found: %s" % hostname)

		# Check for sufficient right to edit things.
		if not self.current_user.has_perm("maintain_builders"):
			raise tornado.web.HTTPError(403)

		with self.db.transaction():
			builder.enabled  = self.get_argument("enabled", False)
			builder.testmode = self.get_argument("testmode", True)

			# Save max_jobs.
			max_jobs = self.get_argument("max_jobs", builder.max_jobs)
			try:
				max_jobs = int(max_jobs)
			except TypeError:
				max_jobs = 1

			if not max_jobs in range(1, 100):
				max_jobs = 1
			builder.max_jobs = max_jobs

		self.redirect("/builder/%s" % builder.hostname)


class BuilderRenewPassphraseHandler(base.BaseHandler):
	@tornado.web.authenticated
	def get(self, name):
		builder = self.backend.builders.get_by_name(name)

		passphrase = builder.regenerate_passphrase()

		self.render("builders/pass.html", action="update", builder=builder,
			passphrase=passphrase)


class BuilderDeleteHandler(base.BaseHandler):
	@tornado.web.authenticated
	def get(self, name):
		builder = self.backend.builders.get_by_name(name)
		if not builder:
			raise tornado.web.HTTPError(404, "Builder not found: %s" % name)

		# Check for sufficient right to delete this builder.
		if not self.current_user.has_perm("maintain_builders"):
			raise tornado.web.HTTPError(403)

		confirmed = self.get_argument("confirmed", None)	
		if confirmed:
			with self.db.transaction():
				builder.deleted = True

			self.redirect("/builders")
			return

		self.render("builders/delete.html", builder=builder)


class BuilderStatusChangeHandler(base.BaseHandler):
	enabled = None

	@tornado.web.authenticated
	def get(self, hostname):
		builder = self.backend.builders.get_by_name(hostname)
		if not builder:
			raise tornado.web.HTTPError(404, "Builder not found: %s" % hostname)

		# Check for sufficient right to edit things.
		if self.current_user.has_perm("maintain_builders"):
			with self.db.transaction():
				builder.enabled = self.enabled

		self.redirect("/builder/%s" % builder.name)


class BuilderEnableHander(BuilderStatusChangeHandler):
	enabled = True


class BuilderDisableHander(BuilderStatusChangeHandler):
	enabled = False
