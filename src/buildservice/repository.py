#!/usr/bin/python

import logging
import os.path

import pakfire

log = logging.getLogger("repositories")
log.propagate = 1

from . import base
from . import logs

from .constants import *
from .decorators import *

class Repositories(base.Object):
	def _get_repository(self, query, *args):
		res = self.db.get(query, *args)

		if res:
			return Repository(self.backend, res.id, data=res)

	def _get_repositories(self, query, *args):
		res = self.db.query(query, *args)

		for row in res:
			yield Repository(self.backend, row.id, data=row)

	def __iter__(self):
		repositories = self._get_repositories("SELECT * FROM repositories \
			WHERE deleted IS FALSE ORDER BY distro_id, name")

		return iter(repositories)

	def create(self, distro, name, description):
		return self._get_repository("INSERT INTO repositories(distro_id, name, description) \
			VALUES(%s, %s, %s) RETURNING *", distro.id, name, description)

	def get_by_id(self, repo_id):
		return self._get_repository("SELECT * FROM repositories \
			WHERE id = %s", repo_id)

	def get_history(self, limit=None, offset=None, build=None, repo=None, user=None):
		query = "SELECT * FROM repositories_history"
		args  = []

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
			entry = logs.RepositoryLogEntry(self.pakfire, entry)
			entries.append(entry)

		return entries

	def remaster(self):
		"""
			Remasters all repositories
		"""
		for repo in self:
			# Skip all repositories that don't need an update
			if not repo.needs_update:
				log.debug("Repository %s does not need an update" % repo)
				continue

			with self.db.transaction():
				repo.remaster()

	def cleanup(self):
		"""
			Cleans up all repositories
		"""
		for repo in self:
			with self.db.transaction():
				repo.cleanup()


class Repository(base.DataObject):
	table = "repositories"

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.id == other.id

	def __lt__(self, other):
		if isinstance(other, self.__class__):
			return self.parent_id == other.id

	def __iter__(self):
		builds = self.backend.builds._get_builds("SELECT builds.* FROM repositories_builds \
			LEFT JOIN builds ON repositories_builds.build_id = builds.id \
			WHERE repositories_builds.repo_id = %s", self.id)

		return iter(builds)

	def __len__(self):
		res = self.db.get("SELECT COUNT(*) AS len FROM repositories_builds \
			WHERE repo_id = %s", self.id)

		return res.len

	def __nonzero__(self):
		return True

	@lazy_property
	def next(self):
		return self.backend.repos._get_repository("SELECT * FROM repositories \
			WHERE parent_id = %s", self.id)

	@lazy_property
	def parent(self):
		if self.data.parent_id:
			return self.backend.repos._get_repository("SELECT * FROM repositories \
				WHERE id = %s", self.data.parent_id)

	@lazy_property
	def distro(self):
		return self.backend.distros.get_by_id(self.data.distro_id)

	def set_priority(self, priority):
		self._set_attribute("priority", priority)

	priority = property(lambda s: s.data.priority, set_priority)

	def get_user(self):
		if self.data.user_id:
			return self.backend.users.get_by_id(self.data.user_id)

	def set_user(self, user):
		self._set_attribute("user_id", user.id)

	user = property(get_user, set_user)

	@property
	def info(self):
		return {
			"id"     : self.id,
			"distro" : self.distro.info,
			"name"   : self.name,
			"arches" : self.arches,
		}

	@property
	def basepath(self):
		return os.path.join(
			self.distro.identifier,
			self.identifier,
		)

	@property
	def path(self):
		return os.path.join(REPOS_DIR, self.basepath)

	@property
	def url(self):
		return "/".join((
			self.settings.get("baseurl", "https://pakfire.ipfire.org"),
			"repositories",
			self.basepath,
		))

	@property
	def mirrorlist(self):
		return "/".join((
			self.settings.get("baseurl", "https://pakfire.ipfire.org"),
			"distro", self.distro.identifier,
			"repo", self.identifier,
			"mirrorlist?arch=%{arch}"
		))

	def get_conf(self, local=False):
		lines = [
			"[repo:%s]" % self.identifier,
			"description = %s - %s" % (self.distro.name, self.summary),
			"enabled = 1",
			"baseurl = %s/%%{arch}" % (self.path if local else self.url),
		]

		if self.mirrored and not local:
			lines.append("mirrors = %s" % self.mirrorlist)

		if self.priority:
			lines.append("priority = %s" % self.priority)

		return "\n".join(lines)

	@property
	def name(self):
		return self.data.name

	@property
	def identifier(self):
		return self.name.lower()

	@property
	def type(self):
		return self.data.type

	@property
	def summary(self):
		lines = self.description.splitlines()

		if lines:
			return lines[0]

		return "N/A"

	@property
	def description(self):
		return self.data.description or ""

	@property
	def parent_id(self):
		return self.data.parent_id

	@lazy_property
	def key(self):
		if not self.data.key_id:
			return

		return self.pakfire.keys.get_by_id(self.data.key_id)

	@property
	def arches(self):
		return self.distro.arches + ["src"]

	def set_mirrored(self, mirrored):
		self._set_attribute("mirrored", mirrored)

	mirrored = property(lambda s: s.data.mirrored, set_mirrored)

	def set_enabled_for_builds(self, state):
		self._set_attribute("enabled_for_builds", state)

	enabled_for_builds = property(lambda s: s.data.enabled_for_builds, set_enabled_for_builds)

	@property
	def score_needed(self):
		return self.data.score_needed

	@property
	def time_min(self):
		return self.data.time_min

	@property
	def time_max(self):
		return self.data.time_max

	def set_update_forced(self, update_forced):
		self._set_attribute("update_forced", update_forced)

	update_forced = property(lambda s: s.data.update_forced, set_update_forced)

	def _log_build(self, action, build, from_repo=None, to_repo=None, user=None):
		user_id = None
		if user:
			user_id = user.id

		from_repo_id = None
		if from_repo:
			from_repo_id = from_repo.id

		to_repo_id = None
		if to_repo:
			to_repo_id = to_repo.id

		self.db.execute("INSERT INTO repositories_history(action, build_id, from_repo_id, to_repo_id, user_id, time) \
			VALUES(%s, %s, %s, %s, %s, NOW())", action, build.id, from_repo_id, to_repo_id, user_id)

	def add_build(self, build, user=None, log=True):
		self.db.execute("INSERT INTO repositories_builds(repo_id, build_id, time_added)"
			" VALUES(%s, %s, NOW())", self.id, build.id)

		# Update bug status.
		build._update_bugs_helper(self)

		if log:
			self._log_build("added", build, to_repo=self, user=user)

	def rem_build(self, build, user=None, log=True):
		self.db.execute("DELETE FROM repositories_builds \
			WHERE repo_id = %s AND build_id = %s", self.id, build.id)

		# Force regenerating the index
		self.update_forced = True

		if log:
			self._log_build("removed", build, from_repo=self, user=user)

	def move_build(self, build, to_repo, user=None, log=True):
		self.db.execute("UPDATE repositories_builds SET repo_id = %s, time_added = NOW() \
			WHERE repo_id = %s AND build_id = %s", to_repo.id, self.id, build.id)

		# Force regenerating the index
		self.update_forced = True

		# Update bug status.
		build._update_bugs_helper(to_repo)

		if log:
			self._log_build("moved", build, from_repo=self, to_repo=to_repo,
				user=user)

	def get_builds(self, limit=None, offset=None):
		query = "SELECT build_id AS id FROM repositories_builds \
			WHERE repo_id = %s ORDER BY time_added DESC"
		args  = [self.id,]

		if limit:
			if offset:
				query += " LIMIT %s,%s"
				args  += [offset, limit,]
			else:
				query += " LIMIT %s"
				args  += [limit,]

		_builds = []
		for build in self.db.query(query, *args):
			build = self.pakfire.builds.get_by_id(build.id)
			build._repo = self

			_builds.append(build)

		return _builds

	def get_builds_by_name(self, name):
		"""
			Returns an ordered list of all builds that match this name
		"""
		builds = self.backend.builds._get_builds("SELECT builds.* FROM repositories_builds \
			LEFT JOIN builds ON repositories_builds.build_id = builds.id \
			LEFT JOIN packages ON builds.pkg_id = packages.id \
			WHERE repositories_builds.repo_id = %s AND packages.name = %s", self.id, name)

		return sorted(builds)

	def get_packages(self, arch):
		if arch == "src":
			return self.backend.packages._get_packages("SELECT packages.* FROM repositories_builds \
				LEFT JOIN builds ON repositories_builds.build_id = builds.id \
				LEFT JOIN packages ON builds.pkg_id = packages.id \
				WHERE repositories_builds.repo_id = %s", self.id)

		return self.backend.packages._get_packages("SELECT packages.* FROM repositories_builds \
				LEFT JOIN builds ON repositories_builds.build_id = builds.id \
				LEFT JOIN jobs ON builds.id = jobs.build_id \
				LEFT JOIN jobs_packages ON jobs.id = jobs_packages.job_id \
				LEFT JOIN packages ON jobs_packages.pkg_id = packages.id \
				WHERE repositories_builds.repo_id = %s \
					AND (jobs.arch = %s OR jobs.arch = %s) \
					AND (packages.arch = %s OR packages.arch = %s)",
				self.id, arch, "noarch", arch, "noarch")

	@property
	def unpushed_builds(self):
		return self.backend.builds._get_builds("SELECT builds.* FROM repositories \
			LEFT JOIN repositories_builds ON repositories.id = repositories_builds.repo_id \
			LEFT JOIN builds ON repositories_builds.build_id = builds.id \
			WHERE repositories.id = %s \
				AND repositories_builds.time_added >= repositories.last_update", self.id)

	def get_obsolete_builds(self):
		return self.pakfire.builds.get_obsolete(self)

	@property
	def needs_update(self):
		if self.unpushed_builds:
			return True

		return False

	def updated(self):
		self.db.execute("UPDATE repositories SET last_update = NOW() \
			WHERE id = %s", self.id)

		# Reset forced update flag
		self.update_forced = False

	def remaster(self):
		log.info("Going to update repository %s..." % self.name)

		for arch in self.arches:
			changed = False

			repo_path = os.path.join(self.path, arch)
			log.debug("  Path: %s" % repo_path)

			if not os.path.exists(repo_path):
				os.makedirs(repo_path)

			# Get all packages that are to be included in this repository
			packages = []
			for p in self.get_packages(arch):
				path = os.path.join(repo_path, p.filename)
				packages.append(path)

				# Nothing to do if the package already exists
				if os.path.exists(path):
					continue

				# Copy the package into the repository
				log.info("Adding %s..." % p)
				p.copy(repo_path)

				# XXX need to sign the new package here

				# The repository has been changed
				changed = True

			# No need to regenerate the index if the repository hasn't changed
			if not changed and not self.update_forced:
				continue

			# Find the key to sign the package.
			key_id = None
			if self.key:
				key_id = self.key.fingerprint

			# Create package index.
			p = pakfire.PakfireServer(arch=arch)
			p.repo_create(repo_path, packages,
				name="%s - %s.%s" % (self.distro.name, self.name, arch),
				key_id=key_id)

		# Update the timestamp when we started at last
		self.updated()

	def cleanup(self):
		log.info("Cleaning up repository %s..." % self.name)

		for arch in self.arches:
			repo_path = os.path.join(self.path, arch)

			# Get a list of all files in the repository directory right now
			filelist = [e for e in os.listdir(repo_path)
				if os.path.isfile(os.path.join(repo_path, e))]

			# Get a list of all packages that should be in the repository
			# and remove them from the filelist
			for p in self.get_packages(arch):
				try:
					filelist.remove(p.filename)
				except ValueError:
					pass

			# For any files that do not belong into the repository
			# any more, we will just delete them
			for filename in filelist:
				path = os.path.join(repo_path, filename)
				self.backend.delete_file(path)

	def get_history(self, **kwargs):
		kwargs.update({
			"repo" : self,
		})

		return self.pakfire.repos.get_history(**kwargs)

	def get_build_times(self):
		times = []
		for arch in self.arches:
			time = self.db.get("SELECT SUM(jobs.time_finished - jobs.time_started) AS time FROM jobs \
				JOIN builds ON builds.id = jobs.build_id \
				JOIN repositories_builds ON builds.id = repositories_builds.build_id \
				WHERE (jobs.arch = %s OR jobs.arch = %s) AND \
				jobs.type = 'build' AND \
				repositories_builds.repo_id = %s", arch, "noarch", self.id)

			times.append((arch, time.time.total_seconds()))

		return times


class RepositoryAux(base.DataObject):
	table = "repositories_aux"

	@property
	def name(self):
		return self.data.name

	@property
	def description(self):
		return self.data.description or ""

	@property
	def url(self):
		return self.data.url

	@property
	def identifier(self):
		return self.name.lower()

	@property
	def distro(self):
		return self.pakfire.distros.get_by_id(self.data.distro_id)

	def get_conf(self, local=False):
		lines = [
			"[repo:%s]" % self.identifier,
			"description = %s - %s" % (self.distro.name, self.name),
			"enabled = 1",
			"baseurl = %s" % self.url,
			"priority = 0",
		]

		return "\n".join(lines)
