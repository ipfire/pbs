#!/usr/bin/python

import datetime
import logging
import uuid
import time
import tornado.locale

import base
import packages

from constants import *

def Build(pakfire, id):
	"""
		Proxy function that returns the right object depending on the type
		of the build.
	"""
	build = pakfire.db.get("SELECT type FROM builds WHERE id = %s", id)
	if not build:
		raise Exception, "Build not found"

	for cls in (BinaryBuild, SourceBuild):
		if not build.type == cls.type:
			continue

		return cls(pakfire, id)

	raise Exception, "Unknown type: %s" % build.type


class Builds(base.Object):
	"""
		Object that represents all builds.
	"""

	def get_by_id(self, id):
		return Build(self.pakfire, id)

	def get_by_uuid(self, uuid):
		build = self.db.get("SELECT id FROM builds WHERE uuid = %s LIMIT 1", uuid)

		if build:
			return Build(self.pakfire, build.id)

	def get_latest(self, state=None, builder=None, limit=10, type=None):
		query = "SELECT id FROM builds"

		where = []
		if builder:
			where.append("host = '%s'" % builder)

		if state:
			where.append("state = '%s'" % state) 

		if type:
			where.append("type = '%s'" % type)

		if where:
			query += " WHERE %s" % " AND ".join(where)

		query += " ORDER BY updated DESC LIMIT %s"

		builds = self.db.query(query, limit)

		return [Build(self.pakfire, b.id) for b in builds]

	def get_by_pkgid(self, pkg_id):
		builds = self.db.query("""SELECT builds.id as id FROM builds
			LEFT JOIN builds_binary ON builds_binary.id = builds.build_id
			WHERE builds_binary.pkg_id = %s AND type = 'binary'""", pkg_id)

		return [Build(self.pakfire, b.id) for b in builds]

	def get_by_host(self, host_id):
		builds = self.db.query("SELECT id FROM builds WHERE host = %s", host_id)

		return [Build(self.pakfire, b.id) for b in builds]

	def get_by_source(self, source_id):
		builds = self.db.query("""SELECT builds.id as id FROM builds
			LEFT JOIN builds_source	ON builds_source.id = builds.build_id
			WHERE builds_source.source_id = %s""", source_id)

		return [Build(self.pakfire, b.id) for b in builds]

	def get_active(self, type=None, host_id=None):
		running_states = ("dispatching", "running", "uploading",)

		query = "SELECT id FROM builds WHERE (%s)" % \
			" OR ".join(["state = '%s'" % s for s in running_states])

		if type:
			query += " AND type = '%s'" % type

		if host_id:
			query += " AND host = %s" % host_id

		builds = self.db.query(query)

		return [Build(self.pakfire, b.id) for b in builds]

	def get_all_but_finished(self):
		builds = self.db.query("SELECT id FROM builds WHERE"
			" NOT state = 'finished' AND NOT state = 'permanently_failed'")

		return [Build(self.pakfire, b.id) for b in builds]

	def get_next(self, type=None, arches=None, limit=None, offset=None):
		query = "SELECT builds.id as id, build_id FROM builds"

		wheres = ["state = 'pending'", "start_not_before <= NOW()",]

		if type:
			wheres.append("type = '%s'" % type)

		if type == "binary" and arches:
			query += " LEFT JOIN builds_binary ON builds.build_id = builds_binary.id"
			arches = ["builds_binary.arch='%s'" % a for a in arches]

			wheres.append("(%s)" % " OR ".join(arches))
		elif arches:
			raise Exception, "Cannot use arches when type is not 'binary'"

		if wheres:
			query += " WHERE %s" % " AND ".join(wheres)

		# Choose the oldest one at first.
		query += " ORDER BY priority DESC, time_added ASC"

		if limit:
			if offset:
				query += " LIMIT %s,%s" % (limit, offset)
			else:
				query += " LIMIT %s" % limit

		builds = [Build(self.pakfire, b.id) for b in self.db.query(query)]

		if limit == 1 and builds:
			return builds[0]

		return builds

	def count(self, state=None):
		query = "SELECT COUNT(*) as c FROM builds"

		wheres = []
		if state:
			wheres.append("state = '%s'" % state)

		if wheres:
			query += " WHERE %s" % " AND ".join(wheres)

		result = self.db.get(query)

		return result.c

	def average_build_time(self):
		result = self.db.get("SELECT AVG(time_finished - time_started) as average"
			" FROM builds WHERE type = 'binary' AND time_started IS NOT NULL"
			" AND time_finished IS NOT NULL")

		return result.average or 0


class _Build(base.Object):
	STATE2LOG = {
		"pending"				: LOG_BUILD_STATE_PENDING,
		"dispatching"			: LOG_BUILD_STATE_DISPATCHING,
		"running"				: LOG_BUILD_STATE_RUNNING,
		"failed"				: LOG_BUILD_STATE_FAILED,
		"permanently_failed"	: LOG_BUILD_STATE_PERM_FAILED,
		"dependency_error"		: LOG_BUILD_STATE_DEP_ERROR,
		"waiting"				: LOG_BUILD_STATE_WAITING,
		"finished"				: LOG_BUILD_STATE_FINISHED,
		"unknown"				: LOG_BUILD_STATE_UNKNOWN,
		"uploading"				: LOG_BUILD_STATE_UPLOADING,
	}

	def __init__(self, pakfire, id):
		base.Object.__init__(self, pakfire)
		self.id = id

		self._data = self.db.get("SELECT * FROM builds WHERE id = %s LIMIT 1", self.id)

	def set(self, key, value):
		self.db.execute("UPDATE builds SET %s = %%s WHERE id = %%s" % key, value, self.id)
		self._data[key] = value

	@property
	def build_id(self):
		return self._data.build_id

	def get_state(self):
		return self._data.state

	def set_state(self, state):
		try:
			log = self.STATE2LOG[state]
		except KeyErrror:
			raise Exception, "Trying to set an invalid build state: %s" % state

		# Setting state.
		self.set("state", state)

		# Inform everybody what happened to the build job.
		if state == "finished":
			self.db.execute("UPDATE builds SET time_finished = NOW()"
				" WHERE id = %s", self.id)

			self.send_finished_message()

		elif state == "failed":
			self.send_failed_message()

			self.db.execute("UPDATE builds SET time_started = NULL,"
				" time_finished = NULL WHERE id = %s LIMIT 1", self.id)

		elif state == "pending":
			self.retries += 1

		elif state in ("dispatching", "running",):
			self.db.execute("UPDATE builds SET time_started = NOW(),"
				" time_finished = NULL WHERE id = %s LIMIT 1", self.id)

		# Log the state change.
		self.logger(log)

	state = property(get_state, set_state)

	@property
	def finished(self):
		return self.state == "finished"

	def get_message(self):
		return self._data.message

	def set_message(self, message):
		self.set("message", message)

	message = property(get_message, set_message)

	@property
	def uuid(self):
		return self._data.uuid

	def get_host(self):
		return self.pakfire.builders.get_by_id(self._data.host)

	def set_host(self, host):
		builder = self.pakfire.builders.get_by_name(host)

		self.set("host", builder.id)

	host = property(get_host, set_host)

	def get_retries(self):
		return self._data.retries

	def set_retries(self, retries):
		self.set("retries", retries)

	retries = property(get_retries, set_retries)

	@property
	def time_added(self):
		return self._data.time_added

	@property
	def time_started(self):
		return self._data.time_started

	@property
	def time_finished(self):
		return self._data.time_finished

	@property
	def duration(self):
		if not self.time_finished or not self.time_started:
			return

		return self.time_finished - self.time_started

	def get_priority(self):
		return self._data.priority

	def set_priority(self, value):
		self.set("priority", value)

	priority = property(get_priority, set_priority)

	@property
	def log(self):
		return self.db.query("SELECT * FROM log WHERE build_id = %s ORDER BY time DESC, id DESC", self.id)

	def logger(self, message, text=""):
		self.pakfire.logger(message, text, build=self)

	@property
	def source(self):
		return self.pkg.source

	@property
	def files(self):
		files = []

		for p in self.db.query("SELECT id, type FROM package_files WHERE build_id = %s", self.uuid):
			for p_class in (packages.SourcePackageFile, packages.BinaryPackageFile, packages.LogFile):
				if p.type == p_class.type:
					p = p_class(self.pakfire, p.id)
					break
			else:
				continue

			files.append(p)

		return sorted(files)

	@property
	def packagefiles(self):
		return [f for f in self.files if isinstance(f, packages.PackageFile)]

	@property
	def logfiles(self):
		return [f for f in self.files if isinstance(f, packages.LogFile)]

	@property
	def recipients(self):
		return []

	def send_finished_message(self):
		info = {
			"build_name" : self.name,
			"build_host" : self.host.name,
			"build_uuid" : self.uuid,
		}

		self.pakfire.messages.send_to_all(self.recipients, MSG_BUILD_FINISHED_SUBJECT,
			MSG_BUILD_FINISHED, info)

	def send_failed_message(self):
		build_host = "--"
		if self.host:
			build_host = self.host.name

		info = {
			"build_name" : self.name,
			"build_host" : build_host,
			"build_uuid" : self.uuid,
		}

		self.pakfire.messages.send_to_all(self.recipients, MSG_BUILD_FAILED_SUBJECT,
			MSG_BUILD_FAILED, info)

	def keepalive(self):
		"""
			This function is used to prevent build jobs from getting stuck on
			something.
		"""

		# Get the seconds since we are running.
		try:
			time_running = datetime.datetime.utcnow() - self.time_started
			time_running = time_running.total_seconds()
		except:
			time_running = 0

		if self.state == "dispatching":
			# If the dispatching is running more than 15 minutes, we set the
			# build to be failed.
			if time_running >= 900:
				self.state = "failed"

		elif self.state in ("running", "uploading"):
			# If the build is running/uploading more than 24 hours, we kill it.
			if time_running >= 3600 * 24:
				self.state = "failed"

		elif self.state == "dependency_error":
			# Resubmit job when it has waited for twelve hours.
			if time_running >= 3600 * 12:
				self.state = "pending"

		elif self.state == "failed":
			# Automatically resubmit jobs that failed after one day.
			if time_running >= 3600 * 24:
				self.state = "pending"

	def schedule_rebuild(self, offset):
		# You cannot do this if the build job has already finished.
		if self.finished:
			return

		self.db.execute("UPDATE builds SET start_not_before = NOW() + %s"
			" WHERE id = %s LIMIT 1", offset, self.id)
		self.state = "pending"


class BinaryBuild(_Build):
	type = "binary"

	def __init__(self, *args, **kwargs):
		_Build.__init__(self, *args, **kwargs)

		_data = self.db.get("SELECT * FROM builds_binary WHERE id = %s", self.build_id)
		del _data["id"]
		self._data.update(_data)

		self.pkg = self.pakfire.packages.get_by_id(self.pkg_id)

	@classmethod
	def new(cls, pakfire, pkg, arch):
		now = datetime.datetime.utcnow()

		build_id = pakfire.db.execute("INSERT INTO builds_binary(pkg_id, arch)"
			" VALUES(%s, %s)", pkg.id, arch)

		id = pakfire.db.execute("INSERT INTO builds(uuid, build_id, time_added)"
			" VALUES(%s, %s, %s)", uuid.uuid4(), build_id, now)

		build = cls(pakfire, id)
		build.logger(LOG_BUILD_CREATED)

		return build

	@property
	def name(self):
		return "%s.%s" % (self.pkg.friendly_name, self.arch)

	@property
	def arch(self):
		return self._data.arch

	@property
	def distro(self):
		return self.pkg.distro

	@property
	def pkg_id(self):
		return self._data.pkg_id

	@property
	def source_build(self):
		return self.pkg.source_build

	@property
	def recipients(self):
		l = set()

		# Get all recipients from the source build (like committer and author).
		for r in self.source_build.recipients:
			l.add(r)

		# Add the package maintainer.
		l.add(self.pkg.maintainer)

		return l

	def add_log(self, filename):
		self.pkg.add_log(filename, self)

	def schedule_test(self, offset):
		pass # XXX TBD


class SourceBuild(_Build):
	type = "source"

	def __init__(self, *args, **kwargs):
		_Build.__init__(self, *args, **kwargs)

		_data = self.db.get("SELECT * FROM builds_source WHERE id = %s", self.build_id)
		del _data["id"]
		self._data.update(_data)

	@classmethod
	def new(cls, pakfire, source_id, revision, author, committer, subject, body, date):
		now = datetime.datetime.utcnow()

		# Check if the revision does already exist. If so, just return.
		if pakfire.db.query("SELECT id FROM builds_source WHERE revision = %s", revision):
			logging.warning("There is already a source build job for rev %s" % revision)
			return

		build_id = pakfire.db.execute("INSERT INTO builds_source(source_id,"
			" revision, author, committer, subject, body, date) VALUES(%s, %s, %s, %s,"
			" %s, %s, %s)", source_id, revision, author, committer, subject, body, date)

		id = pakfire.db.execute("INSERT INTO builds(uuid, type, build_id, time_added)"
			" VALUES(%s, %s, %s, %s)", uuid.uuid4(), "source", build_id, now)

		build = cls(pakfire, id)
		build.logger(LOG_BUILD_CREATED)

		# Source builds are immediately pending.
		build.state = "pending"

		return build

	@property
	def arch(self):
		return "src"

	@property
	def name(self):
		s = "%s:" % self.source.name

		if self.commit_subject:
			s += " %s" % self.commit_subject[:60]
			if len(self.commit_subject) > 60:
				s += "..."
		else:
			s += self.revision[:7]

		return s

	@property
	def source(self):
		return self.pakfire.sources.get_by_id(self._data.source_id)

	@property
	def revision(self):
		return self._data.revision

	@property
	def commit_author(self):
		return self._data.author

	@property
	def commit_committer(self):
		return self._data.committer

	@property
	def commit_subject(self):
		return self._data.subject

	@property
	def commit_body(self):
		return self._data.body

	@property
	def commit_date(self):
		return self._data.date

	@property
	def recipients(self):
		l = [self.commit_author, self.commit_committer,]

		return set(l)

	def send_finished_message(self):
		# We do not send finish messages on source build jobs.
		pass
