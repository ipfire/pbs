#!/usr/bin/python

import tornado.web

import backend

from handlers_base import *

class BuilderListHandler(BaseHandler):
	def get(self):
		builders = self.pakfire.builders.get_all()

		self.render("builders/list.html", builders=builders)


class BuilderDetailHandler(BaseHandler):
	def get(self, hostname):
		builder = self.pakfire.builders.get_by_name(hostname)

		# Get running and pending jobs.
		jobs = self.pakfire.jobs.get_active(builder=builder)
		jobs += self.pakfire.jobs.get_next(builder=builder)

		# Get log.
		log = builder.get_history(limit=5)

		self.render("builders/detail.html", builder=builder, jobs=jobs, log=log)

	@tornado.web.authenticated
	def post(self, hostname):
		if not self.current_user.has_perm("maintain_mirrors"):
			raise tornado.web.HTTPError(403, "User is not allowed to do this.")

		builder = self.pakfire.builders.get_by_name(hostname)

		description = self.get_argument("description", "")
		builder.update_description(description)

		self.redirect("/builder/%s" % builder.hostname)


class BuilderNewHandler(BaseHandler):
	def get(self):
		self.render("builders/new.html")

	@tornado.web.authenticated
	def post(self):
		if not self.current_user.has_perm("maintain_builders"):
			raise tornado.web.HTTPError(403)

		name = self.get_argument("name")

		# Create a new builder.
		builder, passphrase = \
			backend.builders.Builder.create(self.pakfire, name, user=self.current_user)

		self.render("builders/pass.html", action="new", builder=builder,
			passphrase=passphrase)


class BuilderEditHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self, hostname):
		builder = self.pakfire.builders.get_by_name(hostname)
		if not builder:
			raise tornado.web.HTTPError(404, "Builder not found")

		self.render("builders/edit.html", builder=builder)

	@tornado.web.authenticated
	def post(self, hostname):
		builder = self.pakfire.builders.get_by_name(hostname)
		if not builder:
			raise tornado.web.HTTPError(404, "Builder not found: %s" % hostname)

		# Check for sufficient right to edit things.
		if not self.current_user.has_perm("maintain_builders"):
			raise tornado.web.HTTPError(403)

		builder.enabled       = self.get_argument("enabled", False)
		builder.build_release = self.get_argument("build_release", False)
		builder.build_scratch = self.get_argument("build_scratch", False)
		builder.build_test    = self.get_argument("build_test", False)

		# Save max_jobs.
		max_jobs = self.get_argument("max_jobs", builder.max_jobs)
		try:
			max_jobs = int(max_jobs)
		except TypeError:
			max_jobs = 1

		if not max_jobs in range(1, 100):
			max_jobs = 1
		builder.max_jobs = max_jobs


		for arch in builder.get_arches():
			builder.set_arch_status(arch, False)

		for arch in self.get_arguments("arches", []):
			arch = self.pakfire.arches.get_by_name(arch)
			if not arch:
				continue

			builder.set_arch_status(arch, True)

		self.redirect("/builder/%s" % builder.hostname)


class BuilderRenewPassphraseHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self, name):
		builder = self.pakfire.builders.get_by_name(name)

		passphrase = builder.regenerate_passphrase()

		self.render("builders/pass.html", action="update", builder=builder,
			passphrase=passphrase)


class BuilderDeleteHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self, name):
		builder = self.pakfire.builders.get_by_name(name)
		if not builder:
			raise tornado.web.HTTPError(404, "Builder not found: %s" % name)

		# Check for sufficient right to delete this builder.
		if not self.current_user.has_perm("maintain_builders"):
			raise tornado.web.HTTPError(403)

		confirmed = self.get_argument("confirmed", None)	
		if confirmed:
			builder.set_status("deleted", user=self.current_user)

			self.redirect("/builders")
			return

		self.render("builders/delete.html", builder=builder)


class BuilderStatusChangeHandler(BaseHandler):
	new_status = None

	@tornado.web.authenticated
	def get(self, hostname):
		builder = self.pakfire.builders.get_by_name(hostname)
		if not builder:
			raise tornado.web.HTTPError(404, "Builder not found: %s" % hostname)

		# Check for sufficient right to edit things.
		if self.current_user.has_perm("maintain_builders"):
			builder.set_status(self.status, user=self.current_user)

		self.redirect("/builder/%s" % builder.name)


class BuilderEnableHander(BuilderStatusChangeHandler):
	status = "enabled"


class BuilderDisableHander(BuilderStatusChangeHandler):
	status = "disabled"
