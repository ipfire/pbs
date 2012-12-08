#!/usr/bin/python

import datetime
import hashlib
import logging
import os
import re
import shutil
import uuid

import pakfire
import pakfire.config
import pakfire.packages

import base
import builders
import logs
import packages
import repository
import updates
import users

from constants import *

def import_from_package(_pakfire, filename, distro=None, commit=None, type="release",
		arches=None, check_for_duplicates=True, owner=None):

	if distro is None:
		distro = commit.source.distro

	assert distro

	# Open the package file to read some basic information.
	pkg = pakfire.packages.open(None, None, filename)

	if check_for_duplicates:
		if distro.has_package(pkg.name, pkg.epoch, pkg.version, pkg.release):
			logging.warning("Duplicate package detected: %s. Skipping." % pkg)
			return

	# Open the package and add it to the database.
	pkg = packages.Package.open(_pakfire, filename)
	logging.debug("Created new package: %s" % pkg)

	# Associate the package to the processed commit.
	if commit:
		pkg.commit = commit

	# Create a new build object from the package which
	# is always a release build.
	build = Build.create(_pakfire, pkg, type=type, owner=owner, distro=distro)
	logging.debug("Created new build job: %s" % build)

	# Create all automatic jobs.
	build.create_autojobs(arches=arches)

	return pkg, build


class Builds(base.Object):
	def get_by_id(self, id):
		return Build(self.pakfire, id)

	def get_by_uuid(self, uuid):
		build = self.db.get("SELECT id FROM builds WHERE uuid = %s LIMIT 1", uuid)

		if build:
			return self.get_by_id(build.id)

	def get_all(self, limit=50):
		query = "SELECT id FROM builds ORDER BY time_created DESC"

		if limit:
			query += " LIMIT %d" % limit

		return [self.get_by_id(b.id) for b in self.db.query(query)]

	def get_by_user_iter(self, user, type=None, public=None, order_by="name"):
		args = []
		conditions = []

		if not type or type == "scratch":
			# On scratch builds the user id equals the owner id.
			conditions.append("(builds.type = 'scratch' AND owner_id = %s)")
			args.append(user.id)

		elif not type or type == "release":
			pass # TODO

		if public is True:
			conditions.append("public = 'Y'")
		elif public is False:
			conditions.append("public = 'N'")

		query = "SELECT builds.id AS id FROM builds \
			JOIN packages ON builds.pkg_id = packages.id"

		if conditions:
			query += " WHERE %s" % " AND ".join(conditions)

		if order_by == "name":
			query += " ORDER BY packages.name ASC"
		elif order_by == "date":
			query += " ORDER BY builds.time_created DESC"

		for build in self.db.query(query, *args):
			yield Build(self.pakfire, build.id)

	def get_by_name(self, name, type=None, public=None, user=None):
		args = [name,]
		conditions = [
			"packages.name = %s",
		]

		if type:
			conditions.append("builds.type = %s")
			args.append(type)

		or_conditions = []
		if public is True:
			or_conditions.append("public = 'Y'")
		elif public is False:
			or_conditions.append("public = 'N'")

		if user and not user.is_admin():
			or_conditions.append("builds.owner_id = %s")
			args.append(user.id)

		query = "SELECT builds.id AS id FROM builds \
			JOIN packages ON builds.pkg_id = packages.id"

		if or_conditions:
			conditions.append(" OR ".join(or_conditions))

		if conditions:
			query += " WHERE %s" % " AND ".join(conditions)

		query += " ORDER BY packages.name,packages.epoch,packages.version,packages.release,id ASC"

		return sorted([Build(self.pakfire, b.id) for b in self.db.query(query, *args)])

	def get_latest_by_name(self, name, type=None, public=None):
		if type is None:
			types = ("release", "scratch")
		else:
			types = (type,)

		query = "SELECT builds.id AS id FROM builds \
			JOIN packages ON builds.pkg_id = packages.id \
			WHERE builds.type = %s AND packages.name = %s"
		args = [name,]

		if public is True:
			query += " AND builds.public = 'Y'"
		elif public is False:
			query += " AND builds.public = 'N'"

		for type in types:
			res = self.db.query(query, type, *args)
			if not res:
				continue

			builds = [Build(self.pakfire, b.id) for b in res]
			builds.sort(reverse=True)

			return builds[0]

	def count(self):
		count = self.cache.get("builds_count")
		if count is None:
			builds = self.db.get("SELECT COUNT(*) AS count FROM builds")

			count = builds.count
			self.cache.set("builds_count", count, 3600 / 4)

		return count

	def needs_test(self, threshold, arch, limit=None, randomize=False):
		query = "SELECT id FROM builds \
			WHERE NOT EXISTS \
				(SELECT * FROM jobs WHERE \
					jobs.build_id = builds.id AND \
					(jobs.state != 'finished' OR \
					jobs.time_finished >= %s) \
				) \
			AND EXISTS \
				(SELECT * FROM jobs WHERE \
					jobs.build_id = builds.id AND \
					jobs.arch_id = %s AND \
					jobs.type = 'build' AND \
					jobs.state = 'finished' AND \
					jobs.time_finished < %s \
				) \
			AND builds.type = 'release' AND NOT builds.state = 'broken'"
		args  = [threshold, arch.id, threshold]

		if randomize:
			query += " ORDER BY RAND()"

		if limit:
			query += " LIMIT %s"
			args.append(limit)

		return [Build(self.pakfire, b.id) for b in self.db.query(query, *args)]

	def get_obsolete(self, repo=None):
		"""
			Get all obsoleted builds.

			If repo is True: which are in any repository.
			If repo is some Repository object: which are in this repository.
		"""
		args = []

		if repo is None:
			query = "SELECT id FROM builds WHERE state = 'obsolete'"

		else:
			query = "SELECT build_id AS id FROM repositories_builds \
				JOIN builds ON builds.id = repositories_builds.build_id \
				WHERE builds.state = 'obsolete'"

			if repo and not repo is True:
				query += " AND repositories_builds.repo_id = %s"
				args.append(repo.id)

		res = self.db.query(query, *args)

		builds = []
		for build in res:
			build = Build(self.pakfire, build.id)
			builds.append(build)

		return builds

	def get_changelog(self, name, public=None, limit=5, offset=0):
		query = "SELECT builds.* FROM builds \
			JOIN packages ON builds.pkg_id = packages.id \
			WHERE \
				builds.type = %s \
			AND \
				packages.name = %s"
		args = ["release", name,]

		if public == True:
			query += " AND builds.public = %s"
			args.append("Y")
		elif public == False:
			query += " AND builds.public = %s"
			args.append("N")

		query += " ORDER BY builds.time_created DESC"

		if limit:
			if offset:
				query += " LIMIT %s,%s"
				args += [offset, limit]
			else:
				query += " LIMIT %s"
				args.append(limit)

		builds = []
		for b in self.db.query(query, *args):
			b = Build(self.pakfire, b.id, b)
			builds.append(b)

		builds.sort(reverse=True)

		return builds


class Build(base.Object):
	def __init__(self, pakfire, id, data=None):
		base.Object.__init__(self, pakfire)

		# ID of this build
		self.id = id

		# Cache data.
		self._data = data
		self._jobs = None
		self._jobs_test = None
		self._depends_on = None
		self._pkg = None
		self._credits = None
		self._owner = None
		self._update = None
		self._repo = None
		self._distro = None

	def __repr__(self):
		return "<%s id=%s %s>" % (self.__class__.__name__, self.id, self.pkg)

	def __cmp__(self, other):
		assert self.pkg
		assert other.pkg

		return cmp(self.pkg, other.pkg)

	@property
	def cache_key(self):
		return "build_%s" % self.id

	def clear_cache(self):
		"""
			Clear the stored data from the cache.
		"""
		self.cache.delete(self.cache_key)

	@classmethod
	def create(cls, pakfire, pkg, type="release", owner=None, distro=None, public=True):
		assert type in ("release", "scratch", "test")
		assert distro, "You need to specify the distribution of this build."

		if public:
			public = "Y"
		else:
			public = "N"

		# Check if scratch build has an owner.
		if type == "scratch" and not owner:
			raise Exception, "Scratch builds require an owner"

		# Set the default priority of this build.
		if type == "release":
			priority = 0

		elif type == "scratch":
			priority = 1

		elif type == "test":
			priority = -1

		id = pakfire.db.execute("""
			INSERT INTO builds(uuid, pkg_id, type, distro_id, time_created, public, priority)
			VALUES(%s, %s, %s, %s, NOW(), %s, %s)""", "%s" % uuid.uuid4(), pkg.id,
			type, distro.id, public, priority)

		# Set the owner of this buildgroup.
		if owner:
			pakfire.db.execute("UPDATE builds SET owner_id = %s WHERE id = %s",
				owner.id, id)

		build = cls(pakfire, id)

		# Log that the build has been created.
		build.log("created", user=owner)

		# Create directory where the files live.
		if not os.path.exists(build.path):
			os.makedirs(build.path)

		# Move package file to the directory of the build.
		source_path = os.path.join(build.path, "src")
		build.pkg.move(source_path)

		# Generate an update id.
		build.generate_update_id()

		# Obsolete all other builds with the same name to track updates.
		build.obsolete_others()

		# Search for possible bug IDs in the commit message.
		build.search_for_bugs()

		return build

	def delete(self):
		"""
			Deletes this build including all jobs, packages and the source
			package.
		"""
		# If the build is in a repository, we need to remove it.
		if self.repo:
			self.repo.rem_build(self)

		for job in self.jobs + self.test_jobs:
			job.delete()

		if self.pkg:
			self.pkg.delete()

		# Delete everything related to this build.
		self.__delete_bugs()
		self.__delete_comments()
		self.__delete_history()
		self.__delete_watchers()

		# Delete the build itself.
		self.db.execute("DELETE FROM builds WHERE id = %s", self.id)
		self.clear_cache()

	def __delete_bugs(self):
		"""
			Delete all associated bugs.
		"""
		self.db.execute("DELETE FROM builds_bugs WHERE build_id = %s", self.id)

	def __delete_comments(self):
		"""
			Delete all comments.
		"""
		self.db.execute("DELETE FROM builds_comments WHERE build_id = %s", self.id)

	def __delete_history(self):
		"""
			Delete the repository history.
		"""
		self.db.execute("DELETE FROM repositories_history WHERE build_id = %s", self.id)

	def __delete_watchers(self):
		"""
			Delete all watchers.
		"""
		self.db.execute("DELETE FROM builds_watchers WHERE build_id = %s", self.id)

	def reset(self):
		"""
			Resets the whole build so it can start again (as it has never
			been started).
		"""
		for job in self.jobs:
			job.reset()

		#self.__delete_bugs()
		self.__delete_comments()
		self.__delete_history()
		self.__delete_watchers()

		self.state = "building"

		# XXX empty log

	@property
	def data(self):
		"""
			Lazy fetching of data for this object.
		"""
		if self._data is None:
			data = self.cache.get(self.cache_key)
			if not data:
				# Fetch the whole row in one call.
				data = self.db.get("SELECT * FROM builds WHERE id = %s", self.id)
				self.cache.set(self.cache_key, data)

			self._data = data
			assert self._data

		return self._data

	@property
	def info(self):
		"""
			A set of information that is sent to the XMLRPC client.
		"""
		return { "uuid" : self.uuid }

	def log(self, action, user=None, bug_id=None):
		user_id = None
		if user:
			user_id = user.id

		self.db.execute("INSERT INTO builds_history(build_id, action, user_id, time, bug_id) \
			VALUES(%s, %s, %s, NOW(), %s)", self.id, action, user_id, bug_id)

	@property
	def uuid(self):
		"""
			The UUID of this build.
		"""
		return self.data.uuid

	@property
	def pkg(self):
		"""
			Get package that is to be built in the build.
		"""
		if self._pkg is None:
			self._pkg = packages.Package(self.pakfire, self.data.pkg_id)

		return self._pkg

	@property
	def name(self):
		return "%s-%s" % (self.pkg.name, self.pkg.friendly_version)

	@property
	def type(self):
		"""
			The type of this build.
		"""
		return self.data.type

	@property
	def owner_id(self):
		"""
			The ID of the owner of this build.
		"""
		return self.data.owner_id

	@property
	def owner(self):
		"""
			The owner of this build.
		"""
		if not self.owner_id:
			return

		if self._owner is None:
			self._owner = self.pakfire.users.get_by_id(self.owner_id)
			assert self._owner

		return self._owner

	@property
	def distro_id(self):
		return self.data.distro_id

	@property
	def distro(self):
		if self._distro is None:
			self._distro = self.pakfire.distros.get_by_id(self.distro_id)
			assert self._distro

		return self._distro

	@property
	def user(self):
		if self.type == "scratch":
			return self.owner

	def get_depends_on(self):
		if self.data.depends_on and self._depends_on is None:
			self._depends_on = Build(self.pakfire, self.data.depends_on)

		return self._depends_on

	def set_depends_on(self, build):
		self.db.execute("UPDATE builds SET depends_on = %s WHERE id = %s",
			build.id, self.id)
		self.clear_cache()

		# Update cache.
		self._depends_on = build
		self._data["depends_on"] = build.id

	depends_on = property(get_depends_on, set_depends_on)

	@property
	def created(self):
		return self.data.time_created

	@property
	def public(self):
		"""
			Is this build public?
		"""
		return self.data.public == "Y"

	#@property
	#def state(self):
	#	# Cache all states.
	#	states = [j.state for j in self.jobs]
	#
	#	target_state = "unknown"
	#
	#	# If at least one job has failed, the whole build has failed.
	#	if "failed" in states:
	#		target_state = "failed"
	#
	#	# It at least one of the jobs is still running, the whole
	#	# build is in running state.
	#	elif "running" in states:
	#		target_state = "running"
	#
	#	# If all jobs are in the finished state, we turn into finished
	#	# state as well.
	#	elif all([s == "finished" for s in states]):
	#		target_state = "finished"
	#
	#	return target_state

	def auto_update_state(self):
		"""
			Check if the state of this build can be updated and perform
			the change if possible.
		"""
		# Do not change the broken/obsolete state automatically.
		if self.state in ("broken", "obsolete"):
			return

		if self.repo and self.repo.type == "stable":
			self.update_state("stable")
			return

		# If any of the build jobs are finished, the build will be put in testing
		# state.
		for job in self.jobs:
			if job.state == "finished":
				self.update_state("testing")
				break

	def update_state(self, state, user=None, remove=False):
		assert state in ("stable", "testing", "obsolete", "broken")

		self.db.execute("UPDATE builds SET state = %s WHERE id = %s", state, self.id)

		if self._data:
			self._data["state"] = state
		self.clear_cache()

		# In broken state, the removal from the repository is forced and
		# all jobs that are not finished yet will be aborted.
		if state == "broken":
			remove = True

			for job in self.jobs:
				if job.state in ("new", "pending", "running", "dependency_error"):
					job.state = "aborted"

		# If this build is in a repository, it will leave it.
		if remove and self.repo:
				self.repo.rem_build(self)

		# If a release build is now in testing state, we put it into the
		# first repository of the distribution.
		elif self.type == "release" and state == "testing":
			# If the build is not in a repository, yet and if there is
			# a first repository, we put the build there.
			if not self.repo and self.distro.first_repo:
				self.distro.first_repo.add_build(self, user=user)

	@property
	def state(self):
		return self.data.state

	def is_broken(self):
		return self.state == "broken"

	def obsolete_others(self):
		if not self.type == "release":
			return

		for build in self.pakfire.builds.get_by_name(self.pkg.name, type="release"):
			# Don't modify ourself.
			if self.id == build.id:
				continue

			# Don't touch broken builds.
			if build.state in ("obsolete", "broken"):
				continue

			# Obsolete the build.
			build.update_state("obsolete")

	def set_severity(self, severity):
		self.db.execute("UPDATE builds SET severity = %s WHERE id = %s", state, self.id)

		if self._data:
			self._data["severity"] = severity
		self.clear_cache()

	def get_severity(self):
		return self.data.severity

	severity = property(get_severity, set_severity)

	@property
	def commit(self):
		if self.pkg and self.pkg.commit:
			return self.pkg.commit

	def update_message(self, msg):
		self.db.execute("UPDATE builds SET message = %s WHERE id = %s", msg, self.id)

		if self._data:
			self._data["message"] = msg
		self.clear_cache()

	def has_perm(self, user):
		"""
			Check, if the given user has the right to perform administrative
			operations on this build.
		"""
		if user is None:
			return False

		if user.is_admin():
			return True

		# Check if the user is allowed to manage packages from the critical path.
		if self.critical_path and not user.has_perm("manage_critical_path"):
			return False

		# Search for maintainers...

		# Scratch builds.
		if self.type == "scratch":
			# The owner of a scratch build has the right to do anything with it.
			if self.owner_id == user.id:
				return True

		# Release builds.
		elif self.type == "release":
			# The maintainer also is allowed to manage the build.
			if self.pkg.maintainer == user:
				return True

		# Deny permission for all other cases.
		return False

	@property
	def message(self):
		message = ""

		if self.data.message:
			message = self.data.message

		elif self.commit:
			if self.commit.message:
				message = "\n".join((self.commit.subject, self.commit.message))
			else:
				message = self.commit.subject

			prefix = "%s: " % self.pkg.name
			if message.startswith(prefix):
				message = message[len(prefix):]

		return message

	def get_priority(self):
		return self.data.priority

	def set_priority(self, priority):
		assert priority in (-2, -1, 0, 1, 2)

		self.db.execute("UPDATE builds SET priority = %s WHERE id = %s", priority,
			self.id)
		self.clear_cache()

		if self._data:
			self._data["priority"] = priority

	priority = property(get_priority, set_priority)

	@property
	def path(self):
		path = []
		if self.type == "scratch":
			path.append(BUILD_SCRATCH_DIR)
			path.append(self.uuid)

		elif self.type == "release":
			path.append(BUILD_RELEASE_DIR)
			path.append("%s/%s-%s-%s" % \
				(self.pkg.name, self.pkg.epoch, self.pkg.version, self.pkg.release))

		else:
			raise Exception, "Unknown build type: %s" % self.type
			
		return os.path.join(*path)

	@property
	def source_filename(self):
		return os.path.basename(self.pkg.path)

	@property
	def download_prefix(self):
		return "/".join((self.pakfire.settings.get("download_baseurl"), "packages"))

	@property
	def source_download(self):
		return "/".join((self.download_prefix, self.pkg.path))

	@property
	def source_hash_sha512(self):
		return self.pkg.hash_sha512

	@property
	def link(self):
		# XXX maybe this should rather live in a uimodule.
		# zlib-1.2.3-2.ip3 [src, i686, blah...]
		s = """<a class="state_%s %s" href="/build/%s">%s</a>""" % \
			(self.state, self.type, self.uuid, self.name)

		s_jobs = []
		for job in self.jobs:
			s_jobs.append("""<a class="state_%s %s" href="/job/%s">%s</a>""" % \
				(job.state, job.type, job.uuid, job.arch.name))

		if s_jobs:
			s += " [%s]" % ", ".join(s_jobs)

		return s

	@property
	def supported_arches(self):
		return self.pkg.supported_arches

	@property
	def critical_path(self):
		return self.pkg.critical_path

	def get_jobs(self, type=None):
		"""
			Returns a list of jobs of this build.
		"""
		return self.pakfire.jobs.get_by_build(self.id, self, type=type)

	@property
	def jobs(self):
		"""
			Get a list of all build jobs that are in this build.
		"""
		if self._jobs is None:
			self._jobs = self.get_jobs(type="build")

		return self._jobs

	@property
	def test_jobs(self):
		if self._jobs_test is None:
			self._jobs_test = self.get_jobs(type="test")

		return self._jobs_test

	@property
	def all_jobs_finished(self):
		ret = True

		for job in self.jobs:
			if not job.state == "finished":
				ret = False
				break

		return ret

	def create_autojobs(self, arches=None, type="build"):
		jobs = []

		# Arches may be passed to this function. If not we use all arches
		# this package supports.
		if arches is None:
			arches = self.supported_arches

		# Create a new job for every given archirecture.
		for arch in self.pakfire.arches.expand(arches):
			# Don't create jobs for src.
			if arch.name == "src":
				continue

			job = self.add_job(arch, type=type)
			jobs.append(job)

		# Return all newly created jobs.
		return jobs

	def add_job(self, arch, type="build"):
		job = Job.create(self.pakfire, self, arch, type=type)

		# Add new job to cache.
		if self._jobs:
			self._jobs.append(job)

		return job

	## Update stuff

	@property
	def update_id(self):
		if not self.type == "release":
			return

		# Generate an update ID if none does exist, yet.
		self.generate_update_id()

		s = [
			"%s" % self.distro.name.replace(" ", "").upper(),
			"%04d" % (self.data.update_year or 0),
			"%04d" % (self.data.update_num or 0),
		]

		return "-".join(s)

	def generate_update_id(self):
		if not self.type == "release":
			return

		if self.data.update_num:
			return

		update = self.db.get("SELECT update_num AS num FROM builds \
			WHERE update_year = YEAR(NOW()) ORDER BY update_num DESC LIMIT 1")

		if update:
			update_num = update.num + 1
		else:
			update_num = 1

		self.db.execute("UPDATE builds SET update_year = YEAR(NOW()), update_num = %s \
			WHERE id = %s", update_num, self.id)

	## Comment stuff

	def get_comments(self, limit=10, offset=0):
		query = "SELECT * FROM builds_comments \
			JOIN users ON builds_comments.user_id = users.id \
			WHERE build_id = %s	ORDER BY time_created ASC"

		comments = []
		for comment in self.db.query(query, self.id):
			comment = logs.CommentLogEntry(self.pakfire, comment)
			comments.append(comment)

		return comments

	def add_comment(self, user, text, credit):
		# Add the new comment to the database.
		id = self.db.execute("INSERT INTO \
			builds_comments(build_id, user_id, text, credit, time_created) \
			VALUES(%s, %s, %s, %s, NOW())",
			self.id, user.id, text, credit)

		# Update the credit cache.
		if not self._credits is None:
			self._credits += credit

		# Send the new comment to all watchers and stuff.
		self.send_comment_message(id)

		# Return the ID of the newly created comment.
		return id

	@property
	def score(self):
		# XXX UPDATE THIS
		if self._credits is None:
			# Get the sum of the credits from the database.
			query = self.db.get(
				"SELECT SUM(credit) as credits FROM builds_comments WHERE build_id = %s",
				self.id
			)

			self._credits = query.credits or 0

		return self._credits

	@property
	def credits(self):
		# XXX COMPAT
		return self.score

	def get_commenters(self):
		users = self.db.query("SELECT DISTINCT users.id AS id FROM builds_comments \
			JOIN users ON builds_comments.user_id = users.id \
			WHERE builds_comments.build_id = %s AND NOT users.deleted = 'Y' \
			AND NOT users.activated = 'Y' ORDER BY users.id", self.id)

		return [users.User(self.pakfire, u.id) for u in users]

	def send_comment_message(self, comment_id):
		comment = self.db.get("SELECT * FROM builds_comments WHERE id = %s",
			comment_id)

		assert comment
		assert comment.build_id == self.id

		# Get user who wrote the comment.
		user = self.pakfire.users.get_by_id(comment.user_id)

		format = {
			"build_name" : self.name,
			"user_name"  : user.realname,
		}

		# XXX create beautiful message

		self.pakfire.messages.send_to_all(self.message_recipients,
			N_("%(user_name)s commented on %(build_name)s"),
			comment.text, format)

	## Logging stuff

	def get_log(self, comments=True, repo=True, limit=None):
		entries = []

		# Created entry.
		created_entry = logs.CreatedLogEntry(self.pakfire, self)
		entries.append(created_entry)

		if comments:
			entries += self.get_comments(limit=limit)

		if repo:
			entries += self.get_repo_moves(limit=limit)

		# Sort all entries in chronological order.
		entries.sort()

		if limit:
			entries = entries[:limit]

		return entries

	## Watchers stuff

	def get_watchers(self):
		query = self.db.query("SELECT DISTINCT user_id AS id FROM builds_watchers \
			JOIN users ON builds_watchers.user_id = users.id \
			WHERE builds_watchers.build_id = %s AND NOT users.deleted = 'Y' \
			AND users.activated = 'Y' ORDER BY users.id", self.id)

		return [users.User(self.pakfire, u.id) for u in query]

	def add_watcher(self, user):
		# Don't add a user twice.
		if user in self.get_watchers():
			return

		self.db.execute("INSERT INTO builds_watchers(build_id, user_id) \
			VALUES(%s, %s)", self.id, user.id)

	@property
	def message_recipients(self):
		ret = []

		for watcher in self.get_watchers():
			ret.append("%s <%s>" % (watcher.realname, watcher.email))

		return ret

	@property
	def update(self):
		if self._update is None:
			update = self.db.get("SELECT update_id AS id FROM updates_builds \
				WHERE build_id = %s", self.id)

			if update:
				self._update = updates.Update(self.pakfire, update.id)

		return self._update

	@property
	def repo(self):
		if self._repo is None:
			repo = self.db.get("SELECT repo_id AS id FROM repositories_builds \
				WHERE build_id = %s", self.id)

			if repo:
				self._repo = repository.Repository(self.pakfire, repo.id)

		return self._repo

	def get_repo_moves(self, limit=None):
		query = "SELECT * FROM repositories_history \
			WHERE build_id = %s ORDER BY time ASC"

		actions = []
		for action in self.db.query(query, self.id):
			action = logs.RepositoryLogEntry(self.pakfire, action)
			actions.append(action)

		return actions

	@property
	def is_loose(self):
		if self.repo:
			return False

		return True

	@property
	def repo_time(self):
		repo = self.db.get("SELECT time_added FROM repositories_builds \
			WHERE build_id = %s", self.id)

		if repo:
			return repo.time_added

	def get_auto_move(self):
		return self.data.auto_move == "Y"

	def set_auto_move(self, state):
		if state:
			state = "Y"
		else:
			state = "N"

		self.db.execute("UPDATE builds SET auto_move = %s WHERE id = %s", self.id)
		if self._data:
			self._data["auto_move"] = state

	auto_move = property(get_auto_move, set_auto_move)

	@property
	def can_move_forward(self):
		if not self.repo:
			return False

		# If there is no next repository, we cannot move anything.
		next_repo = self.repo.next()

		if not next_repo:
			return False

		# If the needed amount of score is reached, we can move forward.
		if self.score >= next_repo.score_needed:
			return True

		# If the repository does not require a minimal time,
		# we can move forward immediately.
		if not self.repo.time_min:
			return True

		query = self.db.get("SELECT NOW() - time_added AS duration FROM repositories_builds \
			WHERE build_id = %s", self.id)
		duration = query.duration

		if duration >= self.repo.time_min:
			return True

		return False

	## Bugs

	def get_bug_ids(self):
		query = self.db.query("SELECT bug_id FROM builds_bugs \
			WHERE build_id = %s", self.id)

		return [b.bug_id for b in query]

	def add_bug(self, bug_id, user=None, log=True):
		# Check if this bug is already in the list of bugs.
		if bug_id in self.get_bug_ids():
			return

		self.db.execute("INSERT INTO builds_bugs(build_id, bug_id) \
			VALUES(%s, %s)", self.id, bug_id)

		# Log the event.
		if log:
			self.log("bug_added", user=user, bug_id=bug_id)

	def rem_bug(self, bug_id, user=None, log=True):
		self.db.execute("DELETE FROM builds_bugs WHERE build_id = %s AND \
			bug_id = %s", self.id, bug_id)

		# Log the event.
		if log:
			self.log("bug_removed", user=user, bug_id=bug_id)

	def search_for_bugs(self):
		if not self.commit:
			return

		pattern = re.compile(r"(bug\s?|#)(\d+)")

		for txt in (self.commit.subject, self.commit.message):
			for bug in re.finditer(pattern, txt):
				try:
					bugid = int(bug.group(2))
				except ValueError:
					continue

				# Check if a bug with the given ID exists in BZ.
				bug = self.pakfire.bugzilla.get_bug(bugid)
				if not bug:
					continue

				self.add_bug(bugid)

	def get_bugs(self):
		bugs = []
		for bug_id in self.get_bug_ids():
			bug = self.pakfire.bugzilla.get_bug(bug_id)
			if not bug:
				continue

			bugs.append(bug)

		return bugs

	def _update_bugs_helper(self, repo):
		"""
			This function takes a new status and generates messages that
			are appended to all bugs.
		"""
		try:
			kwargs = BUG_MESSAGES[repo.type].copy()
		except KeyError:
			return

		baseurl = self.pakfire.settings.get("baseurl", "")
		args = {
			"build_url"    : "%s/build/%s" % (baseurl, self.uuid),
			"distro_name"  : self.distro.name,
			"package_name" : self.name,
			"repo_name"    : repo.name,
		}
		kwargs["comment"] = kwargs["comment"] % args

		self.update_bugs(**kwargs)

	def _update_bug(self, bug_id, status=None, resolution=None, comment=None):
		self.db.execute("INSERT INTO builds_bugs_updates(bug_id, status, resolution, comment, time) \
			VALUES(%s, %s, %s, %s, NOW())", bug_id, status, resolution, comment)

	def update_bugs(self, status, resolution=None, comment=None):
		# Update all bugs linked to this build.
		for bug_id in self.get_bug_ids():
			self._update_bug(bug_id, status=status, resolution=resolution, comment=comment)


class Jobs(base.Object):
	def get_by_id(self, id):
		return Job(self.pakfire, id)

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
			job = Job(self.pakfire, job.id, job)

			# If the Build object was set, we set it so it won't be retrieved
			# from the database again.
			if build:
				job._build = build

			jobs.append(job)

		# Return sorted list of jobs.
		return sorted(jobs)

	def get_active(self, host_id=None, uploads=True):
		running_states = ["dispatching", "new", "pending", "running"]

		if uploads:
			running_states.append("uploading")

		query = "SELECT * FROM jobs WHERE (%s)" % \
			" OR ".join(["state = '%s'" % s for s in running_states])

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

		return [Job(self.pakfire, j.id, j) for j in self.db.query(query)]

	def get_next_iter(self, arches=None, limit=None, offset=None, type=None, states=["pending", "new"], max_tries=None):
		args = []
		conditions = [
			"(start_not_before IS NULL OR start_not_before <= NOW())",
		]

		if type:
			conditions.append("jobs.type = %s")
			args.append(type)

		if states:
			conditions.append("(%s)" % " OR ".join(["jobs.state = %s" for state in states]))
			args += states

		if arches:
			conditions.append("(%s)" % " OR ".join(["jobs.arch_id = %s" for a in arches]))
			args += [a.id for a in arches]

		# Only return jobs with up to max_tries tries.
		if max_tries:
			conditions.append("jobs.tries <= %s")
			args.append(max_tries)

		query = "SELECT jobs.* FROM jobs \
			JOIN builds ON jobs.build_id = builds.id"

		if conditions:
			query += " WHERE %s" % " AND ".join(conditions)

		# Choose the oldest one at first, but prefer real builds instead of
		# test builds.
		query += " ORDER BY \
			CASE \
				WHEN jobs.type = 'build' THEN 0 \
				WHEN jobs.type = 'test'  THEN 1 \
			END, \
			builds.priority DESC, jobs.time_created ASC"

		if limit:
			if offset:
				query += " LIMIT %s,%s"
				args += [limit, offset]
			else:
				query += " LIMIT %s"
				args += [limit]

		for job in self.db.query(query, *args):
			yield Job(self.pakfire, job.id, job)

	def get_next(self, *args, **kwargs):
		jobs = []

		# Fetch all objects right now.
		for job in self.get_next_iter(*args, **kwargs):
			jobs.append(job)

		return jobs

	def get_latest(self, builder=None, limit=None, age=None, date=None):
		query = "SELECT * FROM jobs"
		args  = []

		where = ["(state = 'finished' OR state = 'failed' OR state = 'aborted')"]
		if builder:
			where.append("builder_id = %s")
			args.append(builder.id)

		if date:
			year, month, day = date.split("-", 2)

			try:
				date = datetime.date(int(year), int(month), int(day))
			except ValueError:
				pass

			else:
				where.append("DATE(time_created) = %s")
				args.append(date)
				where.append("DATE(time_started) = %s")
				args.append(date)
				where.append("DATE(time_finished) = %s")
				args.append(date)

		if age:
			where.append("time_finished >= DATE_SUB(NOW(), INTERVAL %s)" % age)

		if where:
			query += " WHERE %s" % " AND ".join(where)

		query += " ORDER BY time_finished DESC"

		if limit:
			query += " LIMIT %s"
			args.append(limit)

		return [Job(self.pakfire, j.id, j) for j in self.db.query(query, *args)]

	def get_average_build_time(self):
		"""
			Returns the average build time of all finished builds from the
			last 3 months.
		"""
		cache_key = "jobs_avg_build_time"

		build_time = self.cache.get(cache_key)
		if not build_time:
			result = self.db.get("SELECT AVG(time_finished - time_started) as average \
				FROM jobs WHERE type = 'build' AND state = 'finished' AND \
				time_finished >= DATE_SUB(NOW(), INTERVAL 3 MONTH)")

			build_time = result.average or 0
			self.cache.set(cache_key, build_time, 3600)

		return build_time

	def count(self, *states):
		states = sorted(states)

		cache_key = "jobs_count_%s" % ("-".join(states) or "all")

		count = self.cache.get(cache_key)
		if count is None:
			query = "SELECT COUNT(*) AS count FROM jobs"
			args  = []

			if states:
				query += " WHERE %s" % " OR ".join("state = %s" for s in states)
				args += states

			jobs = self.db.get(query, *args)

			count = jobs.count
			self.cache.set(cache_key, count, 60)

		return count


class Job(base.Object):
	def __init__(self, pakfire, id, data=None):
		base.Object.__init__(self, pakfire)

		# The ID of this Job object.
		self.id = id

		# Cache the data of this object.
		self._data = data
		self._build = None
		self._builder = None
		self._packages = None
		self._logfiles = None

	def __str__(self):
		return "<%s id=%s %s>" % (self.__class__.__name__, self.id, self.name)

	def __cmp__(self, other):
		if self.type == "build" and other.type == "test":
			return  -1
		elif self.type == "test" and other.type == "build":
			return 1

		if self.build_id == other.build_id:
			return cmp(self.arch, other.arch)

		ret = cmp(self.pkg, other.pkg)

		if not ret:
			ret = cmp(self.time_created, other.time_created)

		return ret

	@property
	def distro(self):
		assert self.build.distro
		return self.build.distro

	@property
	def cache_key(self):
		return "job_%s" % self.id

	def clear_cache(self):
		"""
			Clear the stored data from the cache.
		"""
		self.cache.delete(self.cache_key)

	@classmethod
	def create(cls, pakfire, build, arch, type="build"):
		id = pakfire.db.execute("INSERT INTO jobs(uuid, type, build_id, arch_id, time_created) \
			VALUES(%s, %s, %s, %s, NOW())",	"%s" % uuid.uuid4(), type, build.id, arch.id)

		job = Job(pakfire, id)
		job.log("created")

		# Set cache for Build object.
		job._build = build

		# Jobs are by default in state "new" and wait for being checked
		# for dependencies. Packages that do have no build dependencies
		# can directly be forwarded to "pending" state.
		if not job.pkg.requires:
			job.state = "pending"

		return job

	def delete(self):
		self.__delete_buildroots()
		self.__delete_history()
		self.__delete_packages()
		self.__delete_logfiles()

		# Delete the job itself.
		self.db.execute("DELETE FROM jobs WHERE id = %s", self.id)
		self.clear_cache()

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

	@property
	def data(self):
		if self._data is None:
			data = self.cache.get(self.cache_key)
			if not data:
				data = self.db.get("SELECT * FROM jobs WHERE id = %s", self.id)
				self.cache.set(self.cache_key, data)

			self._data = data
			assert self._data

		return self._data

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
			entry = logs.JobLogEntry(self.pakfire, entry)
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

	@property
	def build(self):
		if self._build is None:
			self._build = self.pakfire.builds.get_by_id(self.build_id)
			assert self._build

		return self._build

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
		return "%s-%s.%s" % (self.pkg.name, self.pkg.friendly_version, self.arch.name)

	def get_state(self):
		return self.data.state

	def set_state(self, state, user=None, log=True):
		# Nothing to do if the state remains.
		if not self.state == state:
			self.db.execute("UPDATE jobs SET state = %s WHERE id = %s", state, self.id)
			self.clear_cache()

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
			# Set finish time.
			self.db.execute("UPDATE jobs SET time_finished = NOW() WHERE id = %s",
				self.id)

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
		self.clear_cache()

		if self._data:
			self._data["message"] = msg

	@property
	def builder_id(self):
		return self.data.builder_id

	def get_builder(self):
		if not self.builder_id:
			return

		if self._builder is None:
			self._builder = builders.Builder(self.pakfire, self.builder_id)
			assert self._builder

		return self._builder

	def set_builder(self, builder, user=None):
		self.db.execute("UPDATE jobs SET builder_id = %s WHERE id = %s",
			builder.id, self.id)

		# Update cache.
		if self._data:
			self._data["builder_id"] = builder.id
		self.clear_cache()

		self._builder = builder

		# Log the event.
		if user:
			self.log("builder_assigned", builder=builder, user=user)

	builder = property(get_builder, set_builder)

	@property
	def arch_id(self):
		return self.data.arch_id

	@property
	def arch(self):
		return self.pakfire.arches.get_by_id(self.arch_id)

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
	def tries(self):
		return self.data.tries

	@property
	def packages(self):
		if self._packages is None:
			self._packages = []

			query = "SELECT pkg_id AS id FROM jobs_packages \
				JOIN packages ON packages.id = jobs_packages.pkg_id \
				WHERE jobs_packages.job_id = %s ORDER BY packages.name"

			for pkg in self.db.query(query, self.id):
				pkg = packages.Package(self.pakfire, pkg.id)
				pkg._job = self

				self._packages.append(pkg)

		return self._packages

	def get_pkg_by_uuid(self, uuid):
		pkg = self.db.get("SELECT packages.id FROM packages \
			JOIN jobs_packages ON jobs_packages.pkg_id = packages.id \
			WHERE jobs_packages.job_id = %s AND packages.uuid = %s",
			self.id, uuid)

		if not pkg:
			return

		pkg = packages.Package(self.pakfire, pkg.id)
		pkg._job = self

		return pkg

	@property
	def logfiles(self):
		if self._logfiles is None:
			self._logfiles = []

			for log in self.db.query("SELECT id FROM logfiles WHERE job_id = %s", self.id):
				log = logs.LogFile(self.pakfire, log.id)
				log._job = self

				self._logfiles.append(log)

		return self._logfiles

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
					"test.%s.%s.%s.log" % (self.arch.name, i, self.tries))

				if os.path.exists(target_filename):
					i += 1
				else:
					break
		else:
			target_filename = os.path.join(target_dirname,
				"build.%s.%s.log" % (self.arch.name, self.tries))

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
		# Open package (creates entry in the database).
		pkg = packages.Package.open(self.pakfire, filename)

		# Move package to the build directory.
		pkg.move(os.path.join(self.build.path, self.arch.name))

		# Attach the package to this job.
		self.db.execute("INSERT INTO jobs_packages(job_id, pkg_id) VALUES(%s, %s)",
			self.id, pkg.id)

	def get_aborted_state(self):
		return self.data.aborted_state

	def set_aborted_state(self, state):
		self.db.execute("UPDATE jobs SET aborted_state = %s WHERE id = %s",
			state, self.id)
		self.clear_cache()

		if self._data:
			self._data["aborted_state"] = state

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
			WHERE jobs_buildroots.job_id = %s AND jobs_buildroots.tries = %s \
			ORDER BY pkg_name", self.id, tries)

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
			pkg = self.pakfire.packages.get_by_uuid(row.pkg_uuid)
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

		self.pakfire.messages.send_to_all(self.message_recipients,
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

		self.pakfire.messages.send_to_all(self.message_recipients,
			MSG_BUILD_FAILED_SUBJECT, MSG_BUILD_FAILED, info)

	def set_start_time(self, start_time):
		if start_time is None:
			return

		self.db.execute("UPDATE jobs SET start_not_before = NOW() + %s \
			WHERE id = %s LIMIT 1", start_time, self.id)

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
			job = self.create(self.pakfire, self.build, self.arch, type="test")
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

	def used_by(self):
		if not self.packages:
			return []

		conditions = []
		args = []

		for pkg in self.packages:
			conditions.append(" pkg_uuid = %s")
			args.append(pkg.uuid)

		query = "SELECT DISTINCT job_id AS id FROM jobs_buildroots"
		query += " WHERE %s" % " OR ".join(conditions)

		job_ids = self.db.query(query, *args)

		print job_ids

	def resolvdep(self):
		config = pakfire.config.Config(files=["general.conf"])
		config.parse(self.get_config())

		# The filename of the source file.
		filename = os.path.join(PACKAGES_DIR, self.build.pkg.path)
		assert os.path.exists(filename), filename

		# Create a new pakfire instance with the configuration for
		# this build.
		p = pakfire.Pakfire(mode="server", config=config, arch=self.arch.name)

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
