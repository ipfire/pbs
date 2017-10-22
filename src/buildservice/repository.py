#!/usr/bin/python

import logging
import os.path

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
	def url(self):
		url = os.path.join(
			self.settings.get("repository_baseurl", "http://pakfire.ipfire.org/repositories/"),
			self.distro.identifier,
			self.identifier,
			"%{arch}"
		)

		return url

	@property
	def mirrorlist(self):
		url = os.path.join(
			self.settings.get("mirrorlist_baseurl", "https://pakfire.ipfire.org/"),
			"distro", self.distro.identifier,
			"repo", self.identifier,
			"mirrorlist?arch=%{arch}"
		)

		return url

	def get_conf(self):
		lines = [
			"[repo:%s]" % self.identifier,
			"description = %s - %s" % (self.distro.name, self.summary),
			"enabled = 1",
			"baseurl = %s" % self.url,
		]

		if self.mirrored:
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

		if log:
			self._log_build("removed", build, from_repo=self, user=user)

	def move_build(self, build, to_repo, user=None, log=True):
		self.db.execute("UPDATE repositories_builds SET repo_id = %s, time_added = NOW() \
			WHERE repo_id = %s AND build_id = %s", to_repo.id, self.id, build.id)

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

	def _get_packages(self, arch):
		if arch.name == "src":
			pkgs = self.db.query("SELECT packages.id AS id, packages.path AS path FROM packages \
				JOIN builds ON builds.pkg_id = packages.id \
				JOIN repositories_builds ON builds.id = repositories_builds.build_id \
				WHERE packages.arch = %s AND repositories_builds.repo_id = %s",
				arch.name, self.id)

		else:
			pkgs = self.db.query("SELECT packages.id AS id, packages.path AS path FROM packages \
				JOIN jobs_packages ON jobs_packages.pkg_id = packages.id \
				JOIN jobs ON jobs_packages.job_id = jobs.id \
				JOIN builds ON builds.id = jobs.build_id \
				JOIN repositories_builds ON builds.id = repositories_builds.build_id \
				WHERE (jobs.arch = %s OR jobs.arch = %s) AND \
				repositories_builds.repo_id = %s",
				arch.name, "noarch", self.id)

		return pkgs

	def get_packages(self, arch):
		pkgs =  [self.pakfire.packages.get_by_id(p.id) for p in self._get_packages(arch)]
		pkgs.sort()

		return pkgs

	def get_paths(self, arch):
		paths = [p.path for p in self._get_packages(arch)]
		paths.sort()

		return paths

	@property
	def packages(self):
		return self.get_packages()

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

	def remaster(self):
		log.info("Going to update repository %s..." % self.name)

		# Update the timestamp when we started at last.
		self.updated()

		for arch in self.arches:
			changed = False

			# Get all package paths that are to be included in this repository.
			paths = self.get_paths(arch)

			repo_path = os.path.join(
				REPOS_DIR,
				self.distro.identifier,
				self.identifier,
				arch
			)

			if not os.path.exists(repo_path):
				os.makedirs(repo_path)

			source_files = []
			remove_files = []

			for filename in os.listdir(repo_path):
				path = os.path.join(repo_path, filename)

				if not os.path.isfile(path):
					continue

				remove_files.append(path)

			for path in paths:
				filename = os.path.basename(path)

				source_file = os.path.join(PACKAGES_DIR, path)
				target_file = os.path.join(repo_path, filename)

				# Do not add duplicate files twice.
				if source_file in source_files:
					continue

				source_files.append(source_file)

				try:
					remove_files.remove(target_file)
				except ValueError:
					changed = True

			if remove_files:
				changed = True

			# If nothing in the repository data has changed, there
			# is nothing to do.
			if changed:
				log.info("The repository has updates...")
			else:
				log.info("Nothing to update.")
				continue

			# Find the key to sign the package.
			key_id = None
			if repo.key:
				key_id = self.key.fingerprint

			# Create package index.
			p = pakfire.PakfireServer(arch=arch)

			p.repo_create(repo_path, source_files,
				name="%s - %s.%s" % (self.distro.name, self.name, arch),
				key_id=key_id)

			# Remove files afterwards.
			for file in remove_files:
				file = os.path.join(repo_path, file)

				try:
					os.remove(file)
				except OSError:
					log.warning("Could not remove %s." % file)

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

	def get_conf(self):
		lines = [
			"[repo:%s]" % self.identifier,
			"description = %s - %s" % (self.distro.name, self.name),
			"enabled = 1",
			"baseurl = %s" % self.url,
			"priority = 0",
		]

		return "\n".join(lines)
