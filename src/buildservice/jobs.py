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

	def create(self, build, arch, type="build", superseeds=None):
		job = self._get_job("INSERT INTO jobs(uuid, type, build_id, arch, time_created) \
			VALUES(%s, %s, %s, %s, NOW()) RETURNING *", "%s" % uuid.uuid4(), type, build.id, arch)
		job.log("created")

		# Set cache for Build object.
		job.build = build

		# Mark if the new job superseeds some other job
		if superseeds:
			superseeds.superseeded_by = job

		# Jobs are by default in state "new" and wait for being checked
		# for dependencies. Packages that do have no build dependencies
		# can directly be forwarded to "pending" state.
		if not job.pkg.requires:
			job.state = "pending"

		return job

	def get_by_id(self, id, data=None):
		return Job(self.backend, id, data)

	def get_by_uuid(self, uuid):
		job = self.db.get("SELECT id FROM jobs WHERE uuid = %s", uuid)

		if job:
			return self.get_by_id(job.id)

	def get_by_build(self, build_id, build=None, type=None):
		"""
			Get all jobs in the specifies build.
		"""
		query = "SELECT * FROM jobs WHERE build_id = %s"
		args = [build_id,]

		if type:
			query += " AND type = %s"
			args.append(type)

		# Get IDs of all builds in this group.
		jobs = []
		for job in self.db.query(query, *args):
			job = Job(self.backend, job.id, job)

			# If the Build object was set, we set it so it won't be retrieved
			# from the database again.
			if build:
				job._build = build

			jobs.append(job)

		# Return sorted list of jobs.
		return sorted(jobs)

	def get_active(self, host_id=None, builder=None, states=None):
		if builder:
			host_id = builder.id

		if states is None:
			states = ["dispatching", "running", "uploading"]

		query = "SELECT * FROM jobs WHERE state IN (%s)" % ", ".join(["%s"] * len(states))
		args = states

		if host_id:
			query += " AND builder_id = %s" % host_id

		query += " ORDER BY \
			CASE \
				WHEN jobs.state = 'running'     THEN 0 \
				WHEN jobs.state = 'uploading'   THEN 1 \
				WHEN jobs.state = 'dispatching' THEN 2 \
				WHEN jobs.state = 'pending'     THEN 3 \
				WHEN jobs.state = 'new'         THEN 4 \
			END, time_started ASC"

		return [Job(self.backend, j.id, j) for j in self.db.query(query, *args)]

	def get_latest(self, arch=None, builder=None, limit=None, age=None, date=None):
		query = "SELECT * FROM jobs"
		args  = []

		where = ["(state = 'finished' OR state = 'failed' OR state = 'aborted')"]

		if arch:
			where.append("arch = %s")
			args.append(arch)

		if builder:
			where.append("builder_id = %s")
			args.append(builder.id)

		if date:
			try:
				year, month, day = date.split("-", 2)
				date = datetime.date(int(year), int(month), int(day))
			except ValueError:
				pass
			else:
				where.append("(time_created::date = %s OR \
					time_started::date = %s OR time_finished::date = %s)")
				args += (date, date, date)

		if age:
			where.append("time_finished >= NOW() - '%s'::interval" % age)

		if where:
			query += " WHERE %s" % " AND ".join(where)

		query += " ORDER BY time_finished DESC"

		if limit:
			query += " LIMIT %s"
			args.append(limit)

		return [Job(self.backend, j.id, j) for j in self.db.query(query, *args)]

	def get_average_build_time(self):
		"""
			Returns the average build time of all finished builds from the
			last 3 months.
		"""
		result = self.db.get("SELECT AVG(time_finished - time_started) as average \
			FROM jobs WHERE type = 'build' AND state = 'finished' AND \
			time_finished >= NOW() - '3 months'::interval")

		if result:
			return result.average

	def count(self, *states):
		query = "SELECT COUNT(*) AS count FROM jobs"
		args  = []

		if states:
			query += " WHERE state IN %s"
			args.append(states)

		jobs = self.db.get(query, *args)
		if jobs:
			return jobs.count

	def restart_failed(self, max_tries=9):
		jobs = self._get_jobs("SELECT jobs.* FROM jobs \
			JOIN builds ON builds.id = jobs.build_id \
			WHERE \
				jobs.type = 'build' AND \
				jobs.state = 'failed' AND \
				jobs.tries <= %s AND \
				NOT builds.state = 'broken' AND \
				jobs.time_finished < NOW() - '72 hours'::interval \
			ORDER BY \
				CASE \
					WHEN jobs.type = 'build' THEN 0 \
					WHEN jobs.type = 'test'  THEN 1 \
				END, \
				builds.priority DESC, jobs.time_created ASC",
			max_tries)

		# Restart the job
		for job in jobs:
			job.set_state("new", log=False)


class Job(base.DataObject):
	table = "jobs"

	def __str__(self):
		return "<%s id=%s %s>" % (self.__class__.__name__, self.id, self.name)

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.id == other.id

	def __lt__(self, other):
		if isinstance(other, self.__class__):
			if (self.type, other.type) == ("build", "test"):
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
	def distro(self):
		return self.build.distro

	def get_superseeded_by(self):
		if self.data.superseeded_by:
			return self.backend.jobs.get_by_id(self.data.superseeded_by)

	def set_superseeded_by(self, superseeded_by):
		assert isinstance(superseeded_by, self.__class__)

		self._set_attribute("superseeded_by", superseeded_by.id)
		self.superseeded_by = superseeded_by

	superseeded_by = lazy_property(get_superseeded_by, set_superseeded_by)

	def delete(self):
		self.__delete_buildroots()
		self.__delete_history()
		self.__delete_packages()
		self.__delete_logfiles()

		# Delete the job itself.
		self.db.execute("DELETE FROM jobs WHERE id = %s", self.id)

	def __delete_buildroots(self):
		"""
			Removes all buildroots.
		"""
		self.db.execute("DELETE FROM jobs_buildroots WHERE job_id = %s", self.id)

	def __delete_history(self):
		"""
			Removes all references in the history to this build job.
		"""
		self.db.execute("DELETE FROM jobs_history WHERE job_id = %s", self.id)

	def __delete_packages(self):
		"""
			Deletes all uploaded files from the job.
		"""
		for pkg in self.packages:
			pkg.delete()

		self.db.execute("DELETE FROM jobs_packages WHERE job_id = %s", self.id)

	def __delete_logfiles(self):
		for logfile in self.logfiles:
			self.db.execute("INSERT INTO queue_delete(path) VALUES(%s)", logfile.path)

	def reset(self, user=None):
		self.__delete_buildroots()
		self.__delete_packages()
		self.__delete_history()
		self.__delete_logfiles()

		self.state = "new"
		self.log("reset", user=user)

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

	@property
	def uuid(self):
		return self.data.uuid

	@property
	def type(self):
		return self.data.type

	@property
	def build_id(self):
		return self.data.build_id

	@lazy_property
	def build(self):
		return self.backend.builds.get_by_id(self.build_id)

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
	def name(self):
		return "%s-%s.%s" % (self.pkg.name, self.pkg.friendly_version, self.arch)

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

	def is_running(self):
		"""
			Returns True if job is in a running state.
		"""
		return self.state in ("pending", "dispatching", "running", "uploading")

	def get_state(self):
		return self.data.state

	def set_state(self, state, user=None, log=True):
		# Nothing to do if the state remains.
		if not self.state == state:
			self.db.execute("UPDATE jobs SET state = %s WHERE id = %s", state, self.id)

			# Log the event.
			if log and not state == "new":
				self.log("state_change", state=state, user=user)

			# Update cache.
			if self._data:
				self._data["state"] = state

		# Always clear the message when the status is changed.
		self.update_message(None)

		# Update some more informations.
		if state == "dispatching":
			# Set start time.
			self.db.execute("UPDATE jobs SET time_started = NOW(), time_finished = NULL \
				WHERE id = %s", self.id)

		elif state == "pending":
			self.db.execute("UPDATE jobs SET tries = tries + 1, time_started = NULL, \
				time_finished = NULL WHERE id = %s", self.id)

		elif state in ("aborted", "dependency_error", "finished", "failed"):
			# Set finish time and reset builder..
			self.db.execute("UPDATE jobs SET time_finished = NOW() WHERE id = %s", self.id)

			# Send messages to the user.
			if state == "finished":
				self.send_finished_message()

			elif state == "failed":
				# Remove all package files if a job is set to failed state.
				self.__delete_packages()

				self.send_failed_message()

		# Automatically update the state of the build (not on test builds).
		if self.type == "build":
			self.build.auto_update_state()

	state = property(get_state, set_state)

	@property
	def message(self):
		return self.data.message

	def update_message(self, msg):
		self.db.execute("UPDATE jobs SET message = %s WHERE id = %s",
			msg, self.id)

		if self._data:
			self._data["message"] = msg

	def get_builder(self):
		if self.data.builder_id:
			return self.backend.builders.get_by_id(self.data.builder_id)

	def set_builder(self, builder, user=None):
		self.db.execute("UPDATE jobs SET builder_id = %s WHERE id = %s",
			builder.id, self.id)

		# Update cache.
		if self._data:
			self._data["builder_id"] = builder.id

		self._builder = builder

		# Log the event.
		if user:
			self.log("builder_assigned", builder=builder, user=user)

	builder = lazy_property(get_builder, set_builder)

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

	@property
	def time_started(self):
		return self.data.time_started

	@property
	def time_finished(self):
		return self.data.time_finished

	@property
	def expected_runtime(self):
		"""
			Returns the estimated time and stddev, this job takes to finish.
		"""
		# Get the average build time.
		build_times = self.backend.builds.get_build_times_by_arch(self.arch,
			name=self.pkg.name)

		# If there is no statistical data, we cannot estimate anything.
		if not build_times:
			return None, None

		return build_times.average, build_times.stddev

	@property
	def eta(self):
		expected_runtime, stddev = self.expected_runtime

		if expected_runtime:
			return expected_runtime - int(self.duration), stddev

	@property
	def tries(self):
		return self.data.tries

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
			if self.type == "test":
				return

			self._add_file_package(filename)

	def _add_file_log(self, filename):
		"""
			Attach a log file to this job.
		"""
		target_dirname = os.path.join(self.build.path, "logs")

		if self.type == "test":
			i = 1
			while True:
				target_filename = os.path.join(target_dirname,
					"test.%s.%s.%s.log" % (self.arch, i, self.tries))

				if os.path.exists(target_filename):
					i += 1
				else:
					break
		else:
			target_filename = os.path.join(target_dirname,
				"build.%s.%s.log" % (self.arch, self.tries))

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
		rows = []

		for pkg_name, pkg_uuid in pkgs:
			rows.append((self.id, self.tries, pkg_uuid, pkg_name))

		# Cleanup old stuff first (for rebuilding packages).
		self.db.execute("DELETE FROM jobs_buildroots WHERE job_id = %s AND tries = %s",
			self.id, self.tries)

		self.db.executemany("INSERT INTO \
			jobs_buildroots(job_id, tries, pkg_uuid, pkg_name) \
			VALUES(%s, %s, %s, %s)", rows)

	def has_buildroot(self, tries=None):
		if tries is None:
			tries = self.tries

		res = self.db.get("SELECT COUNT(*) AS num FROM jobs_buildroots \
			WHERE jobs_buildroots.job_id = %s AND jobs_buildroots.tries = %s",
			self.id, tries)

		if res:
			return res.num

		return 0

	def get_buildroot(self, tries=None):
		if tries is None:
			tries = self.tries

		rows = self.db.query("SELECT * FROM jobs_buildroots \
			WHERE jobs_buildroots.job_id = %s AND jobs_buildroots.tries = %s \
			ORDER BY pkg_name", self.id, tries)

		pkgs = []
		for row in rows:
			# Search for this package in the packages table.
			pkg = self.backend.packages.get_by_uuid(row.pkg_uuid)
			pkgs.append((row.pkg_name, row.pkg_uuid, pkg))

		return pkgs

	def send_finished_message(self):
		# Send no finished mails for test jobs.
		if self.type == "test":
			return

		logging.debug("Sending finished message for job %s to %s" % \
			(self.name, ", ".join(self.message_recipients)))

		info = {
			"build_name" : self.name,
			"build_host" : self.builder.name,
			"build_uuid" : self.uuid,
		}

		self.backend.messages.send_to_all(self.message_recipients,
			MSG_BUILD_FINISHED_SUBJECT, MSG_BUILD_FINISHED, info)

	def send_failed_message(self):
		logging.debug("Sending failed message for job %s to %s" % \
			(self.name, ", ".join(self.message_recipients)))

		build_host = "--"
		if self.builder:
			build_host = self.builder.name

		info = {
			"build_name" : self.name,
			"build_host" : build_host,
			"build_uuid" : self.uuid,
		}

		self.backend.messages.send_to_all(self.message_recipients,
			MSG_BUILD_FAILED_SUBJECT, MSG_BUILD_FAILED, info)

	def set_start_time(self, start_not_before):
		self._set_attribute("start_not_before", start_not_before)

	def schedule(self, type, start_time=None, user=None):
		assert type in ("rebuild", "test")

		if type == "rebuild":
			if self.state == "finished":
				return

			self.set_state("new", user=user, log=False)
			self.set_start_time(start_time)

			# Log the event.
			self.log("schedule_rebuild", user=user)

		elif type == "test":
			if not self.state == "finished":
				return

			# Create a new job with same build and arch.
			job = self.create(self.backend, self.build, self.arch, type="test")
			job.set_start_time(start_time)

			# Log the event.
			self.log("schedule_test_job", test_job=job, user=user)

			return job

	def schedule_test(self, start_not_before=None, user=None):
		# XXX to be removed
		return self.schedule("test", start_time=start_not_before, user=user)

	def schedule_rebuild(self, start_not_before=None, user=None):
		# XXX to be removed
		return self.schedule("rebuild", start_time=start_not_before, user=user)

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

	def get_repo_config(self):
		"""
			Get repository configuration file that is sent to the builder.
		"""
		confs = []

		for repo in self.get_build_repos():
			confs.append(repo.get_conf())

		return "\n\n".join(confs)

	def get_config(self):
		"""
			Get configuration file that is sent to the builder.
		"""
		confs = []

		# Add the distribution configuration.
		confs.append(self.distro.get_config())

		# Then add all repositories for this build.
		confs.append(self.get_repo_config())

		return "\n\n".join(confs)

	def resolvdep(self):
		config = pakfire.config.Config(files=["general.conf"])
		config.parse(self.get_config())

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
			self.state = "dependency_error"
			self.update_message(e)

		else:
			# If the build dependencies can be resolved, we set the build in
			# pending state.
			if solver.status is True:
				if self.state in ("failed",):
					return

				self.state = "pending"
