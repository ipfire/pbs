#!/usr/bin/python

import logging
import os
import re
import uuid

import pakfire.packages

from . import base
from . import logs
from . import updates
from . import users

log = logging.getLogger("builds")
log.propagate = 1

from .constants import *
from .decorators import *

class Builds(base.Object):
	def _get_build(self, query, *args):
		res = self.db.get(query, *args)

		if res:
			return Build(self.backend, res.id, data=res)

	def _get_builds(self, query, *args):
		res = self.db.query(query, *args)

		for row in res:
			yield Build(self.backend, row.id, data=row)

	def get_by_id(self, id, data=None):
		return Build(self.backend, id, data=data)

	def get_by_uuid(self, uuid):
		build = self.db.get("SELECT id FROM builds WHERE uuid = %s LIMIT 1", uuid)

		if build:
			return self.get_by_id(build.id)

	def get_all(self, limit=50):
		query = "SELECT * FROM builds ORDER BY time_created DESC"

		if limit:
			query += " LIMIT %d" % limit

		return [self.get_by_id(b.id, b) for b in self.db.query(query)]

	def get_by_user(self, user, type=None, public=None):
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

		query = "SELECT builds.* AS id FROM builds \
			JOIN packages ON builds.pkg_id = packages.id"

		if conditions:
			query += " WHERE %s" % " AND ".join(conditions)

		query += " ORDER BY builds.time_created DESC"

		builds = []
		for build in self.db.query(query, *args):
			build = Build(self.backend, build.id, build)
			builds.append(build)

		return builds

	def get_by_name(self, name, type=None, public=None, user=None, limit=None, offset=None):
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

		query = "SELECT builds.* AS id FROM builds \
			JOIN packages ON builds.pkg_id = packages.id"

		if or_conditions:
			conditions.append(" OR ".join(or_conditions))

		if conditions:
			query += " WHERE %s" % " AND ".join(conditions)

		if type == "release":
			query += " ORDER BY packages.name,packages.epoch,packages.version,packages.release,id ASC"
		elif type == "scratch":
			query += " ORDER BY time_created DESC"

		if limit:
			if offset:
				query += " LIMIT %s,%s"
				args.extend([offset, limit])
			else:
				query += " LIMIT %s"
				args.append(limit)

		return [Build(self.backend, b.id, b) for b in self.db.query(query, *args)]

	def get_latest_by_name(self, name, type=None, public=None):
		query = "\
			SELECT * FROM builds \
				LEFT JOIN builds_latest ON builds.id = builds_latest.build_id \
			WHERE builds_latest.package_name = %s"
		args = [name,]

		if type:
			query += " AND builds_latest.build_type = %s"
			args.append(type)

		if public is True:
			query += " AND builds.public = %s"
			args.append("Y")
		elif public is False:
			query += " AND builds.public = %s"
			args.append("N")

		# Get the last one only.
		# Prefer release builds over scratch builds.
		query += "\
			ORDER BY \
				CASE builds.type WHEN 'release' THEN 0 ELSE 1 END, \
				builds.time_created DESC \
			LIMIT 1"

		res = self.db.get(query, *args)

		if res:
			return Build(self.backend, res.id, res)

	def get_active_builds(self, name, public=None):
		query = "\
			SELECT * FROM builds \
				LEFT JOIN builds_latest ON builds.id = builds_latest.build_id \
			WHERE builds_latest.package_name = %s AND builds.type = %s"
		args = [name, "release"]

		if public is True:
			query += " AND builds.public = %s"
			args.append("Y")
		elif public is False:
			query += " AND builds.public = %s"
			args.append("N")

		builds = []
		for row in self.db.query(query, *args):
			b = Build(self.backend, row.id, row)
			builds.append(b)

		# Sort the result. Lastest build first.
		builds.sort(reverse=True)

		return builds

	def count(self):
		builds = self.db.get("SELECT COUNT(*) AS count FROM builds")
		if builds:
			return builds.count

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
			build = Build(self.backend, build.id)
			builds.append(build)

		return builds

	def create(self, pkg, type="release", owner=None, distro=None):
		assert type in ("release", "scratch", "test")
		assert distro, "You need to specify the distribution of this build."

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

		# Create build in database
		build = self._get_build("INSERT INTO builds(uuid, pkg_id, type, distro_id, priority) \
			VALUES(%s, %s, %s, %s, %s) RETURNING *", "%s" % uuid.uuid4(), pkg.id, type, distro.id, priority)

		# Set the owner of this build
		if owner:
			build.owner = owner

		# Log that the build has been created.
		build.log("created", user=owner)

		# Create directory where the files live
		if not os.path.exists(build.path):
			os.makedirs(build.path)

		# Move package file to the directory of the build.
		build.pkg.move(os.path.join(build.path, "src"))

		# Generate an update id.
		build.generate_update_id()

		# Obsolete all other builds with the same name to track updates.
		build.obsolete_others()

		# Search for possible bug IDs in the commit message.
		build.search_for_bugs()

		return build

	def create_from_source_package(self, filename, distro, commit=None, type="release",
			arches=None, check_for_duplicates=True, owner=None):
		assert distro

		# Open the package file to read some basic information.
		pkg = pakfire.packages.open(None, None, filename)

		if check_for_duplicates:
			if distro.has_package(pkg.name, pkg.epoch, pkg.version, pkg.release):
				log.warning("Duplicate package detected: %s. Skipping." % pkg)
				return

		# Open the package and add it to the database
		pkg = self.backend.packages.create(filename)

		# Associate the package to the processed commit
		if commit:
			pkg.commit = commit

		# Create a new build object from the package
		build = self.create(pkg, type=type, owner=owner, distro=distro)

		# Create all automatic jobs
		build.create_autojobs(arches=arches)

		return build

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
			b = Build(self.backend, b.id, b)
			builds.append(b)

		builds.sort(reverse=True)

		return builds

	def get_comments(self, limit=10, offset=None, user=None):
		query = "SELECT * FROM builds_comments \
			JOIN users ON builds_comments.user_id = users.id"
		args = []

		wheres = []
		if user:
			wheres.append("users.id = %s")
			args.append(user.id)

		if wheres:
			query += " WHERE %s" % " AND ".join(wheres)

		# Sort everything.
		query += " ORDER BY time_created DESC"

		# Limits.
		if limit:
			if offset:
				query += " LIMIT %s,%s"
				args.append(offset)
			else:
				query += " LIMIT %s"

			args.append(limit)

		comments = []
		for comment in self.db.query(query, *args):
			comment = logs.CommentLogEntry(self.backend, comment)
			comments.append(comment)

		return comments

	def get_build_times_summary(self, name=None, job_type=None, arch=None):
		query = "\
			SELECT \
				builds_times.arch AS arch, \
				MAX(duration) AS maximum, \
				MIN(duration) AS minimum, \
				AVG(duration) AS average, \
				SUM(duration) AS sum, \
				STDDEV_POP(duration) AS stddev \
			FROM builds_times \
				LEFT JOIN builds ON builds_times.build_id = builds.id \
				LEFT JOIN packages ON builds.pkg_id = packages.id"

		args = []
		conditions = []

		# Filter for name.
		if name:
			conditions.append("packages.name = %s")
			args.append(name)

		# Filter by job types.
		if job_type:
			conditions.append("builds_times.job_type = %s")
			args.append(job_type)

		# Filter by arch.
		if arch:
			conditions.append("builds_times.arch = %s")
			args.append(arch)

		# Add conditions.
		if conditions:
			query += " WHERE %s" % " AND ".join(conditions)

		# Grouping and sorting.
		query += " GROUP BY arch ORDER BY arch DESC"

		return self.db.query(query, *args)

	def get_build_times_by_arch(self, arch, **kwargs):
		kwargs.update({
			"arch" : arch,
		})

		build_times = self.get_build_times_summary(**kwargs)
		if build_times:
			return build_times[0]


class Build(base.DataObject):
	table = "builds"

	def __repr__(self):
		return "<%s id=%s %s>" % (self.__class__.__name__, self.id, self.pkg)

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.id == other.id

	def __lt__(self, other):
		if isinstance(other, self.__class__):
			return self.pkg < other.pkg

	def __iter__(self):
		jobs = self.backend.jobs._get_jobs("SELECT * FROM jobs \
			WHERE build_id = %s", self.id)

		return iter(sorted(jobs))

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

	@lazy_property
	def pkg(self):
		"""
			Get package that is to be built in the build.
		"""
		return self.backend.packages.get_by_id(self.data.pkg_id)

	@property
	def name(self):
		return "%s-%s" % (self.pkg.name, self.pkg.friendly_version)

	@property
	def type(self):
		"""
			The type of this build.
		"""
		return self.data.type

	def get_owner(self):
		"""
			The owner of this build.
		"""
		if self.data.owner_id:
			return self.backend.users.get_by_id(self.data.owner_id)

	def set_owner(self, owner):
		if owner:
			self._set_attribute("owner_id", owner.id)
		else:
			self._set_attribute("owner_id", None)

	owner = lazy_property(get_owner, set_owner)

	@lazy_property
	def distro(self):
		return self.backend.distros.get_by_id(self.data.distro_id)

	@property
	def user(self):
		if self.type == "scratch":
			return self.owner

	def get_depends_on(self):
		if self.data.depends_on:
			return self.backend.builds.get_by_id(self.data.depends_on)

	def set_depends_on(self, build):
		self._set_attribute("depends_on", build.id)

	depends_on = lazy_property(get_depends_on, set_depends_on)

	@property
	def created(self):
		return self.data.time_created

	@property
	def date(self):
		return self.created.date()

	@property
	def public(self):
		"""
			Is this build public?
		"""
		return self.data.public

	@lazy_property
	def size(self):
		"""
			Returns the size on disk of this build.
		"""
		s = 0

		# Add the source package.
		if self.pkg:
			s += self.pkg.size

		# Add all jobs.
		s += sum((j.size for j in self.jobs))

		return s

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

		self._set_attribute("state", state)

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

		for build in self.backend.builds.get_by_name(self.pkg.name, type="release"):
			# Don't modify ourself.
			if self.id == build.id:
				continue

			# Don't touch broken builds.
			if build.state in ("obsolete", "broken"):
				continue

			# Obsolete the build.
			build.update_state("obsolete")

	def set_severity(self, severity):
		self._set_attribute("severity", severity)

	def get_severity(self):
		return self.data.severity

	severity = property(get_severity, set_severity)

	@lazy_property
	def commit(self):
		if self.pkg and self.pkg.commit:
			return self.pkg.commit

	def update_message(self, message):
		self._set_attribute("message", message)

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

		self._set_attribute("priority", priority)

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
		return "/".join((self.backend.settings.get("download_baseurl"), "packages"))

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
				(job.state, job.type, job.uuid, job.arch))

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
		return self.backend.jobs.get_by_build(self.id, self, type=type)

	@lazy_property
	def jobs(self):
		"""
			Get a list of all build jobs that are in this build.
		"""
		return self.get_jobs(type="build")

	@property
	def test_jobs(self):
		return self.get_jobs(type="test")

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
		for arch in self.backend.arches.expand(arches):
			# Don't create jobs for src
			if arch == "src":
				continue

			job = self.add_job(arch, type=type)
			jobs.append(job)

		# Return all newly created jobs.
		return jobs

	def add_job(self, arch, type="build"):
		job = self.backend.jobs.create(self, arch, type=type)

		# Add new job to cache.
		self.jobs.append(job)

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
			WHERE update_year = EXTRACT(year FROM NOW()) ORDER BY update_num DESC LIMIT 1")

		if update:
			update_num = update.num + 1
		else:
			update_num = 1

		self.db.execute("UPDATE builds SET update_year = EXTRACT(year FROM NOW()), update_num = %s \
			WHERE id = %s", update_num, self.id)

	## Comment stuff

	def get_comments(self, limit=10, offset=0):
		query = "SELECT * FROM builds_comments \
			JOIN users ON builds_comments.user_id = users.id \
			WHERE build_id = %s	ORDER BY time_created ASC"

		comments = []
		for comment in self.db.query(query, self.id):
			comment = logs.CommentLogEntry(self.backend, comment)
			comments.append(comment)

		return comments

	def add_comment(self, user, text, score):
		# Add the new comment to the database.
		id = self.db.execute("INSERT INTO \
			builds_comments(build_id, user_id, text, credit, time_created) \
			VALUES(%s, %s, %s, %s, NOW())",
			self.id, user.id, text, score)

		# Update the credit cache
		self.score += score

		# Send the new comment to all watchers and stuff.
		self.send_comment_message(id)

		# Return the ID of the newly created comment.
		return id

	@lazy_property
	def score(self):
		res = self.db.get("SELECT SUM(credit) AS score \
			FROM builds_comments WHERE build_id = %s", self.id)

		return res.score or 0

	@property
	def credits(self):
		# XXX COMPAT
		return self.score

	def get_commenters(self):
		users = self.db.query("SELECT DISTINCT users.id AS id FROM builds_comments \
			JOIN users ON builds_comments.user_id = users.id \
			WHERE builds_comments.build_id = %s AND NOT users.deleted = 'Y' \
			AND NOT users.activated = 'Y' ORDER BY users.id", self.id)

		return [users.User(self.backend, u.id) for u in users]

	def send_comment_message(self, comment_id):
		comment = self.db.get("SELECT * FROM builds_comments WHERE id = %s",
			comment_id)

		assert comment
		assert comment.build_id == self.id

		# Get user who wrote the comment.
		user = self.backend.users.get_by_id(comment.user_id)

		format = {
			"build_name" : self.name,
			"user_name"  : user.realname,
		}

		# XXX create beautiful message

		self.backend.messages.send_to_all(self.message_recipients,
			N_("%(user_name)s commented on %(build_name)s"),
			comment.text, format)

	## Logging stuff

	def get_log(self, comments=True, repo=True, limit=None):
		entries = []

		# Created entry.
		created_entry = logs.CreatedLogEntry(self.backend, self)
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
		query = self.db.query("SELECT DISTINCT users.id AS id FROM builds_watchers \
			JOIN users ON builds_watchers.user_id = users.id \
			WHERE builds_watchers.build_id = %s AND NOT users.deleted = 'Y' \
			AND users.activated = 'Y' ORDER BY users.id", self.id)

		return [users.User(self.backend, u.id) for u in query]

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
				self._update = updates.Update(self.backend, update.id)

		return self._update

	@lazy_property
	def repo(self):
		res = self.db.get("SELECT repo_id FROM repositories_builds \
			WHERE build_id = %s", self.id)

		if res:
			return self.backend.repos.get_by_id(res.repo_id)

	def get_repo_moves(self, limit=None):
		query = "SELECT * FROM repositories_history \
			WHERE build_id = %s ORDER BY time ASC"

		actions = []
		for action in self.db.query(query, self.id):
			action = logs.RepositoryLogEntry(self.backend, action)
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
		self._set_attribute("auto_move", state)

	auto_move = property(get_auto_move, set_auto_move)

	@property
	def can_move_forward(self):
		if not self.repo:
			return False

		# If there is no next repository, we cannot move anything.
		if not self.repo.next:
			return False

		# If the needed amount of score is reached, we can move forward.
		if self.score >= self.repo.next.score_needed:
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
				bug = self.backend.bugzilla.get_bug(bugid)
				if not bug:
					continue

				self.add_bug(bugid)

	def get_bugs(self):
		bugs = []
		for bug_id in self.get_bug_ids():
			bug = self.backend.bugzilla.get_bug(bug_id)
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

		baseurl = self.backend.settings.get("baseurl", "")
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
