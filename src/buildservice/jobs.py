#!/usr/bin/python

import datetime
import hashlib
import logging
import os
import shutil
import uuid

import pakfire
import pakfire.config

log = logging.getLogger("builds")
log.propagate = 1

from . import arches
from . import base
from . import logs
from . import users

from .constants import *
from .decorators import *

class Jobs(base.Object):
	def _get_job(self, query, *args):
		res = self.db.get(query, *args)

		if res:
			return Job(self.backend, res.id, data=res)

	def _get_jobs(self, query, *args):
		res = self.db.query(query, *args)

		for row in res:
			yield Job(self.backend, row.id, data=row)

	def create(self, build, arch, test=False, superseeds=None):
		job = self._get_job("INSERT INTO jobs(uuid, build_id, arch, test) \
			VALUES(%s, %s, %s, %s) RETURNING *", "%s" % uuid.uuid4(), build.id, arch, test)
		job.log("created")

		# Set cache for Build object.
		job.build = build

		# Mark if the new job superseeds some other job
		if superseeds:
			superseeds.superseeded_by = job

		return job

	def get_by_id(self, id):
		return self._get_job("SELECT * FROM jobs WHERE id = %s", id)

	def get_by_uuid(self, uuid):
		return self._get_job("SELECT * FROM jobs WHERE uuid = %s", uuid)

	def get_active(self, limit=None):
		jobs = self._get_jobs("SELECT jobs.* FROM jobs \
			WHERE time_started IS NOT NULL AND time_finished IS NULL \
			ORDER BY time_started LIMIT %s", limit)

		return jobs

	def get_recently_ended(self, limit=None):
		jobs = self._get_jobs("SELECT jobs.* FROM jobs \
			WHERE time_finished IS NOT NULL ORDER BY time_finished DESC LIMIT %s", limit)

		return jobs

	def restart_failed(self):
		jobs = self._get_jobs("SELECT jobs.* FROM jobs \
			JOIN builds ON builds.id = jobs.build_id \
			WHERE \
				jobs.type = 'build' AND \
				jobs.state = 'failed' AND \
				NOT builds.state = 'broken' AND \
				jobs.time_finished < NOW() - '72 hours'::interval \
			ORDER BY \
				CASE \
					WHEN jobs.type = 'build' THEN 0 \
					WHEN jobs.type = 'test'  THEN 1 \
				END, \
				builds.priority DESC, jobs.time_created ASC")

		# Restart the job
		for job in jobs:
			job.restart()


class Job(base.DataObject):
	table = "jobs"

	def __str__(self):
		return "<%s id=%s %s>" % (self.__class__.__name__, self.id, self.name)

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.id == other.id

	def __lt__(self, other):
		if isinstance(other, self.__class__):
			if not self.test and other.test:
				return True

			if self.build == other.build:
				return arches.priority(self.arch) < arches.priority(other.arch)

			return self.time_created < other.time_created

	def __iter__(self):
		packages = self.backend.packages._get_packages("SELECT packages.* FROM jobs_packages \
			LEFT JOIN packages ON jobs_packages.pkg_id = packages.id \
			WHERE jobs_packages.job_id = %s ORDER BY packages.name", self.id)

		return iter(packages)

	def __nonzero__(self):
		return True

	def __len__(self):
		res = self.db.get("SELECT COUNT(*) AS len FROM jobs_packages \
			WHERE job_id = %s", self.id)

		return res.len

	@property
	def uuid(self):
		return self.data.uuid

	@property
	def name(self):
		return "%s-%s.%s" % (self.pkg.name, self.pkg.friendly_version, self.arch)

	@property
	def build_id(self):
		return self.data.build_id

	@lazy_property
	def build(self):
		return self.backend.builds.get_by_id(self.build_id)

	@property
	def test(self):
		return self.data.test

	@property
	def related_jobs(self):
		ret = []

		for job in self.build.jobs:
			if job == self:
				continue

			ret.append(job)

		return ret

	@property
	def pkg(self):
		return self.build.pkg

	@property
	def size(self):
		return sum((p.size for p in self.packages))

	@lazy_property
	def rank(self):
		"""
			Returns the rank in the build queue
		"""
		if not self.state == "pending":
			return

		res = self.db.get("SELECT rank FROM jobs_queue WHERE job_id = %s", self.id)

		if res:
			return res.rank

	@property
	def distro(self):
		return self.build.distro

	def get_superseeded_by(self):
		if self.data.superseeded_by:
			return self.backend.jobs.get_by_id(self.data.superseeded_by)

	def set_superseeded_by(self, superseeded_by):
		assert isinstance(superseeded_by, self.__class__)

		self._set_attribute("superseeded_by", superseeded_by.id)

	superseeded_by = lazy_property(get_superseeded_by, set_superseeded_by)

	def start(self, builder):
		"""
			Starts this job on builder
		"""
		self.builder = builder

		# Start to dispatch the build job
		self.state = "dispatching"

	def running(self):
		self.state = "running"

		# Set start time
		self.time_started  = datetime.datetime.utcnow()
		self.time_finished = None

	def finished(self):
		self.state = "finished"

		# Log end time
		self.time_finished = datetime.datetime.utcnow()

		# Notify users
		self.send_finished_message()

	def failed(self, message):
		self.state = "failed"
		self.message = message

		# Log end time
		self.time_finished = datetime.datetime.utcnow()

		# Notify users
		self.send_failed_message()

	def restart(self, test=None, start_not_before=None):
		# Copy the job and let it build again
		job = self.backend.jobs.create(self.build, self.arch,
			test=test or self.test, superseeds=self)

		if start_not_before:
			job.start_not_before = start_not_before

		return job

	def delete(self):
		"""
			Deletes a job from the database
		"""
		# Remove the buildroot
		self.db.execute("DELETE FROM jobs_buildroots WHERE job_id = %s", self.id)

		# Remove the history
		self.db.execute("DELETE FROM jobs_history WHERE job_id = %s", self.id)

		# Delete all packages
		for pkg in self:
			self.db.execute("DELETE FROM jobs_packages \
				WHERE job_id = %s AND pkg_id = %s", self.id, pkg.id)
			pkg.delete()

		# Remove all logfiles
		for logfile in self.logfiles:
			self.backend.delete_file(os.path.join(PACKAGES_DIR, logfile.path))

		self.db.execute("DELETE FROM logfiles WHERE job_id = %s", self.id)

		# Delete the job itself.
		self.db.execute("DELETE FROM jobs WHERE id = %s", self.id)

	## Logging stuff

	def log(self, action, user=None, state=None, builder=None, test_job=None):
		user_id = None
		if user:
			user_id = user.id

		builder_id = None
		if builder:
			builder_id = builder.id

		test_job_id = None
		if test_job:
			test_job_id = test_job.id

		self.db.execute("INSERT INTO jobs_history(job_id, action, state, user_id, \
			time, builder_id, test_job_id) VALUES(%s, %s, %s, %s, NOW(), %s, %s)",
			self.id, action, state, user_id, builder_id, test_job_id)

	def get_log(self, limit=None, offset=None, user=None):
		query = "SELECT * FROM jobs_history"

		conditions = ["job_id = %s",]
		args  = [self.id,]

		if user:
			conditions.append("user_id = %s")
			args.append(user.id)

		if conditions:
			query += " WHERE %s" % " AND ".join(conditions)

		query += " ORDER BY time DESC"

		if limit:
			if offset:
				query += " LIMIT %s,%s"
				args  += [offset, limit,]
			else:
				query += " LIMIT %s"
				args  += [limit,]

		entries = []
		for entry in self.db.query(query, *args):
			entry = logs.JobLogEntry(self.backend, entry)
			entries.append(entry)

		return entries

	def is_running(self):
		"""
			Returns True if job is in a running state.
		"""
		return self.state in ("pending", "dispatching", "running", "uploading")

	def get_state(self):
		return self.data.state

	def set_state(self, state):
		self._set_attribute("state", state)

		# Automatically update the state of the build (not on test builds)
		if not self.test:
			self.build.auto_update_state()

	state = property(get_state, set_state)

	def set_message(self, message):
		if message:
			message = "%s" % message

		self._set_attribute("message", message)

	message = property(lambda s: s.data.message, set_message)

	def get_builder(self):
		if self.data.builder_id:
			return self.backend.builders.get_by_id(self.data.builder_id)

	def set_builder(self, builder, user=None):
		log.info("Builder %s has been assigned to %s" % (builder.name, self.name))

		self._set_attribute("builder_id", builder.id)

		# Log the event.
		if user:
			self.log("builder_assigned", builder=builder, user=user)

	builder = lazy_property(get_builder, set_builder)

	@property
	def candidate_builders(self):
		"""
			Returns all active builders that could build this job
		"""
		builders = self.backend.builders.get_for_arch(self.arch)

		# Remove all builders that are not available
		builders = (b for b in builders if b.enabled and b.is_online())

		# Remove all builders that have too many jobs
		builders = (b for b in builders if not b.too_many_jobs)

		# Sort them by the fastest builder first
		return sorted(builders, key=lambda b: -b.performance_index)

	@property
	def designated_builder(self):
		"""
			Returns the fastest candidate builder builder
		"""
		if self.candidate_builders:
			return self.candidate_builders[0]

	@property
	def arch(self):
		return self.data.arch

	@property
	def duration(self):
		if not self.time_started:
			return 0

		if self.time_finished:
			delta = self.time_finished - self.time_started
		else:
			delta = datetime.datetime.utcnow() - self.time_started

		return delta.total_seconds()

	@property
	def time_created(self):
		return self.data.time_created

	def set_time_started(self, time_started):
		self._set_attribute("time_started", time_started)

	time_started = property(lambda s: s.data.time_started, set_time_started)

	def set_time_finished(self, time_finished):
		self._set_attribute("time_finished", time_finished)

	time_finished = property(lambda s: s.data.time_finished, set_time_finished)

	def set_start_not_before(self, start_not_before):
		self._set_attribute("start_not_before", start_not_before)

	start_not_before = property(lambda s: s.data.start_not_before, set_start_not_before)

	def get_pkg_by_uuid(self, uuid):
		pkg = self.backend.packages._get_package("SELECT packages.id FROM packages \
			JOIN jobs_packages ON jobs_packages.pkg_id = packages.id \
			WHERE jobs_packages.job_id = %s AND packages.uuid = %s",
			self.id, uuid)

		if pkg:
			pkg.job = self
			return pkg

	@lazy_property
	def logfiles(self):
		logfiles = []

		for log in self.db.query("SELECT id FROM logfiles WHERE job_id = %s", self.id):
			log = logs.LogFile(self.backend, log.id)
			log._job = self

			logfiles.append(log)

		return logfiles

	def add_file(self, filename):
		"""
			Add the specified file to this job.

			The file is copied to the right directory by this function.
		"""
		assert os.path.exists(filename)

		if filename.endswith(".log"):
			self._add_file_log(filename)

		elif filename.endswith(".%s" % PACKAGE_EXTENSION):
			# It is not allowed to upload packages on test builds.
			if self.test:
				return

			self._add_file_package(filename)

	def _add_file_log(self, filename):
		"""
			Attach a log file to this job.
		"""
		target_dirname = os.path.join(self.build.path, "logs")

		if self.test:
			i = 1
			while True:
				target_filename = os.path.join(target_dirname,
					"test.%s.%s.%s.log" % (self.arch, i, self.uuid))

				if os.path.exists(target_filename):
					i += 1
				else:
					break
		else:
			target_filename = os.path.join(target_dirname,
				"build.%s.%s.log" % (self.arch, self.uuid))

		# Make sure the target directory exists.
		if not os.path.exists(target_dirname):
			os.makedirs(target_dirname)

		# Calculate a SHA512 hash from that file.
		f = open(filename, "rb")
		h = hashlib.sha512()
		while True:
			buf = f.read(BUFFER_SIZE)
			if not buf:
				break

			h.update(buf)
		f.close()

		# Copy the file to the final location.
		shutil.copy2(filename, target_filename)

		# Create an entry in the database.
		self.db.execute("INSERT INTO logfiles(job_id, path, filesize, hash_sha512) \
			VALUES(%s, %s, %s, %s)", self.id, os.path.relpath(target_filename, PACKAGES_DIR),
			os.path.getsize(target_filename), h.hexdigest())

	def _add_file_package(self, filename):
		# Open package (creates entry in the database)
		pkg = self.backend.packages.create(filename)

		# Move package to the build directory.
		pkg.move(os.path.join(self.build.path, self.arch))

		# Attach the package to this job.
		self.db.execute("INSERT INTO jobs_packages(job_id, pkg_id) VALUES(%s, %s)",
			self.id, pkg.id)

	def get_aborted_state(self):
		return self.data.aborted_state

	def set_aborted_state(self, state):
		self._set_attribute("aborted_state", state)

	aborted_state = property(get_aborted_state, set_aborted_state)

	@property
	def message_recipients(self):
		l = []

		# Add all people watching the build.
		l += self.build.message_recipients

		# Add the package maintainer on release builds.
		if self.build.type == "release":
			maint = self.pkg.maintainer

			if isinstance(maint, users.User):
				l.append("%s <%s>" % (maint.realname, maint.email))
			elif maint:
				l.append(maint)

			# XXX add committer and commit author.

		# Add the owner of the scratch build on scratch builds.
		elif self.build.type == "scratch" and self.build.user:
			l.append("%s <%s>" % \
				(self.build.user.realname, self.build.user.email))

		return set(l)

	def save_buildroot(self, pkgs):
		# Cleanup old stuff first (for rebuilding packages)
		self.db.execute("DELETE FROM jobs_buildroots WHERE job_id = %s", self.id)

		for pkg_name, pkg_uuid in pkgs:
			self.db.execute("INSERT INTO jobs_buildroots(job_id, pkg_uuid, pkg_name) \
				VALUES(%s, %s, %s)", self.id, pkg_name, pkg_uuid)

	@lazy_property
	def buildroot(self):
		rows = self.db.query("SELECT * FROM jobs_buildroots \
			WHERE jobs_buildroots.job_id = %s ORDER BY pkg_name", self.id)

		pkgs = []
		for row in rows:
			# Search for this package in the packages table.
			pkg = self.backend.packages.get_by_uuid(row.pkg_uuid)
			pkgs.append((row.pkg_name, row.pkg_uuid, pkg))

		return pkgs

	def send_finished_message(self):
		# Send no finished mails for test jobs.
		if self.test:
			return

		logging.debug("Sending finished message for job %s to %s" % \
			(self.name, ", ".join(self.message_recipients)))

		self.backend.messages.send_template_to_many(self.message_recipients,
			"messages/jobs/finished", job=self)

	def send_failed_message(self):
		logging.debug("Sending failed message for job %s to %s" % \
			(self.name, ", ".join(self.message_recipients)))

		self.backend.messages.send_template_to_many(self.message_recipients,
			"messages/jobs/failed", job=self)

	def get_build_repos(self):
		"""
			Returns a list of all repositories that should be used when
			building this job.
		"""
		repo_ids = self.db.query("SELECT repo_id FROM jobs_repos WHERE job_id = %s",
			self.id)

		if not repo_ids:
			return self.distro.get_build_repos()

		repos = []
		for repo in self.distro.repositories:
			if repo.id in [r.id for r in repo_ids]:
				repos.append(repo)

		return repos or self.distro.get_build_repos()

	def get_config(self, local=False):
		"""
			Get configuration file that is sent to the builder.
		"""
		confs = []

		# Add the distribution configuration.
		confs.append(self.distro.get_config())

		# Then add all repositories for this build.
		for repo in self.get_build_repos():
			conf = repo.get_conf(local=local)
			confs.append(conf)

		return "\n\n".join(confs)

	def set_dependency_check_succeeded(self, value):
		self._set_attribute("dependency_check_succeeded", value)
		self._set_attribute("dependency_check_at", datetime.datetime.utcnow())

		# Reset the message
		if value is True:
			self.message = None

	dependency_check_succeeded = property(
		lambda s: s.data.dependency_check_succeeded,
		set_dependency_check_succeeded)

	def resolvdep(self):
		log.info("Processing dependencies for %s..." % self)

		config = pakfire.config.Config(files=["general.conf"])
		config.parse(self.get_config(local=True))

		# The filename of the source file.
		filename = os.path.join(PACKAGES_DIR, self.build.pkg.path)
		assert os.path.exists(filename), filename

		# Create a new pakfire instance with the configuration for
		# this build.
		p = pakfire.PakfireServer(config=config, arch=self.arch)

		# Try to solve the build dependencies.
		try:
			solver = p.resolvdep(filename)

		# Catch dependency errors and log the problem string.
		except DependencyError, e:
			self.dependency_check_succeeded = False
			self.message = e

		# The dependency check has succeeded
		else:
			self.dependency_check_succeeded = True
