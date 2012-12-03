#!/usr/bin/python

import tornado.web

from handlers_base import BaseHandler


class JobDetailHandler(BaseHandler):
	def get(self, uuid):
		job = self.pakfire.jobs.get_by_uuid(uuid)
		if not job:
			raise tornado.web.HTTPError(404, "No such job: %s" % job)

		# Cache the log.
		log = job.get_log()

		self.render("jobs-detail.html", job=job, build=job.build, log=log)


class JobBuildrootHandler(BaseHandler):
	def get(self, uuid):
		job = self.pakfire.jobs.get_by_uuid(uuid)
		if not job:
			raise tornado.web.HTTPError(404, "Job not found: %s" % uuid)

		tries = self.get_argument("tries", None)
		buildroot = job.get_buildroot(tries)

		# Calculate the download size and buildroot size.
		download_size = 0
		buildroot_size = 0

		for name, uuid, pkg in buildroot:
			if not pkg:
				continue

			download_size += pkg.filesize
			buildroot_size += pkg.size

		self.render("jobs-buildroot.html", job=job, build=job.build,
			buildroot=buildroot, download_size=download_size,
			buildroot_size=buildroot_size)


class JobScheduleHandler(BaseHandler):
	allowed_types = ("test", "rebuild",)

	@tornado.web.authenticated
	def get(self, uuid):
		type = self.get_argument("type")
		assert type in self.allowed_types

		job = self.pakfire.jobs.get_by_uuid(uuid)
		if not job:
			raise tornado.web.HTTPError(404, "Job not found: %s" % uuid)

		self.render("job-schedule-%s.html" % type, type=type, job=job, build=job.build)

	@tornado.web.authenticated
	def post(self, uuid):
		type = self.get_argument("type")
		assert type in self.allowed_types

		job = self.pakfire.jobs.get_by_uuid(uuid)
		if not job:
			raise tornado.web.HTTPError(404, "Job not found: %s" % uuid)

		# Get the start offset.
		offset = self.get_argument("offset", 0)
		try:
			offset = int(offset)
		except TypeError:
			offset = 0

		# Submit the build.
		if type == "test":
			job = job.schedule_test(offset)

		elif type == "rebuild":
			job.schedule_rebuild(offset)

		self.redirect("/job/%s" % job.uuid)


class JobAbortHandler(BaseHandler):
	def get_job(self, uuid):
		job = self.pakfire.jobs.get_by_uuid(uuid)
		if not job:
			raise tornado.web.HTTPError(404, "Job not found: %s" % uuid)

		return job

	@tornado.web.authenticated
	def get(self, uuid):
		job = self.get_job(uuid)

		# XXX Check if user has the right to manage the job.

		self.render("jobs-abort.html", job=job)

	@tornado.web.authenticated
	def post(self, uuid):
		job = self.get_job(uuid)

		# XXX Check if user has the right to manage the job.

		# Only running builds can be set to aborted state.
		if not job.state == "running":
			# XXX send the user a nicer error message.
			self.redirect("/job/%s" % job.uuid)
			return

		# Set the job into aborted state.
		job.state = "aborted"

		# 0 means the job was aborted by the user.
		job.aborted_state = 0

		self.redirect("/job/%s" % job.uuid)
