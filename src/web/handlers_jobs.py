#!/usr/bin/python

import tornado.web

from . import base

class JobsIndexHandler(base.BaseHandler):
	def get(self):
		# Filter for a certain arch.
		arch = self.get_argument("arch", None)
		if not arch or not self.backend.arches.exists(arch):
			raise tornado.web.HTTPError(400, "Architecture does not exist")

		# Check if we need to filter for a certain builder.
		builder_name = self.get_argument("builder", None)
		if builder_name:
			builder = self.pakfire.builders.get_by_name(builder_name)
		else:
			builder = None

		# Filter for a certain date.
		date = self.get_argument("date", None)

		# Get all jobs, that fulfill the criteria.
		jobs = self.pakfire.jobs.get_latest(limit=50, arch=arch, builder=builder,
			date=date)

		self.render("jobs-index.html", jobs=jobs, arch=arch, builder=builder,
			date=date)


class JobsFilterHandler(base.BaseHandler):
	def get(self):
		builders = self.pakfire.builders.get_all()

		self.render("jobs-filter.html", arches=self.backend.arches, builders=builders)


class JobDetailHandler(base.BaseHandler):
	def get(self, uuid):
		job = self.pakfire.jobs.get_by_uuid(uuid)
		if not job:
			raise tornado.web.HTTPError(404, "No such job: %s" % job)

		# Cache the log.
		log = job.get_log()

		self.render("jobs-detail.html", job=job, build=job.build, log=log)


class JobBuildrootHandler(base.BaseHandler):
	def get(self, uuid):
		job = self.pakfire.jobs.get_by_uuid(uuid)
		if not job:
			raise tornado.web.HTTPError(404, "Job not found: %s" % uuid)

		# Calculate the download size and buildroot size.
		download_size = 0
		buildroot_size = 0

		for name, uuid, pkg in job.buildroot:
			if not pkg:
				continue

			download_size += pkg.filesize
			buildroot_size += pkg.size

		self.render("jobs-buildroot.html", job=job, build=job.build,
			buildroot=job.buildroot, download_size=download_size,
			buildroot_size=buildroot_size)


class JobScheduleHandler(base.BaseHandler):
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


class JobAbortHandler(base.BaseHandler):
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
