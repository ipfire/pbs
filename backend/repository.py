#!/usr/bin/python

import os.path

import base
import builds
import logs
import packages

class Repositories(base.Object):
	def get_all(self):
		repos = self.db.query("SELECT * FROM repositories")

		return [Repository(self.pakfire, r.id, r) for r in repos]

	def get_by_id(self, repo_id):
		repo = self.db.get("SELECT * FROM repositories WHERE id = %s", repo_id)

		if repo:
			return Repository(self.pakfire, repo.id, repo)

	def get_needs_update(self, limit=None):
		query = "SELECT id FROM repositories WHERE needs_update = 'Y'"
		query += " ORDER BY last_update ASC"

		# Append limit if any
		if limit:
			query += " LIMIT %d" % limit

		repos = self.db.query(query)

		return [Repository(self.pakfire, r.id) for r in repos]

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


class Repository(base.Object):
	def __init__(self, pakfire, id, data=None):
		base.Object.__init__(self, pakfire)
		self.id = id

		# Cache.
		self._data = data
		self._next = None
		self._prev = None
		self._key  = None
		self._distro = None

	@property
	def data(self):
		if self._data is None:
			self._data = self.db.get("SELECT * FROM repositories WHERE id = %s", self.id)

		return self._data

	def __cmp__(self, other):
		if other is None:
			return 1

		if self.id == other.id:
			return 0

		elif self.id == other.parent_id:
			return 1

		elif self.parent_id == other.id:
			return -1

		return 1

	def next(self):
		if self._next is None:
			repo = self.db.get("SELECT id FROM repositories \
				WHERE parent_id = %s LIMIT 1", self.id)

			if not repo:
				return

			self._next = Repository(self.pakfire, repo.id)

		return self._next

	def prev(self):
		if not self.parent_id:
			return

		if self._prev is None:
			self._prev = Repository(self.pakfire, self.parent_id)

		return self._prev

	@property
	def parent(self):
		return self.prev()

	@classmethod
	def create(cls, pakfire, distro, name, description):
		id = pakfire.db.execute("INSERT INTO repositories(distro_id, name, description)"
			" VALUES(%s, %s, %s)", distro.id, name, description)

		return cls(pakfire, id)

	@property
	def distro(self):
		if self._distro is None:
			self._distro = self.pakfire.distros.get_by_id(self.data.distro_id)
			assert self._distro

		return self._distro

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
		prioritymap = {
			"stable"   : 500,
			"unstable" : 200,
			"testing"  : 100,
		}

		try:
			priority = prioritymap[self.type]
		except KeyError:
			priority = None

		lines = [
			"[repo:%s]" % self.identifier,
			"description = %s - %s" % (self.distro.name, self.summary),
			"enabled = 1",
			"baseurl = %s" % self.url,
			"mirrors = %s" % self.mirrorlist,
		]

		if priority:
			lines.append("priority = %s" % priority)

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

	@property
	def key(self):
		if not self.data.key_id:
			return

		if self._key is None:
			self._key = self.pakfire.keys.get_by_id(self.data.key_id)
			assert self._key

		return self._key

	@property
	def arches(self):
		return self.distro.arches

	@property
	def mirrored(self):
		return self.data.mirrored == "Y"

	def get_enabled_for_builds(self):
		return self.data.enabled_for_builds == "Y"

	def set_enabled_for_builds(self, state):
		if state:
			state = "Y"
		else:
			state = "N"

		self.db.execute("UPDATE repositories SET enabled_for_builds = %s WHERE id = %s",
			state, self.id)

		if self._data:
			self._data["enabled_for_builds"] = state

	enabled_for_builds = property(get_enabled_for_builds, set_enabled_for_builds)

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

	def build_count(self):
		query = self.db.get("SELECT COUNT(*) AS count FROM repositories_builds \
			WHERE repo_id = %s", self.id)

		if query:
			return query.count

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
			build = builds.Build(self.pakfire, build.id)
			build._repo = self

			_builds.append(build)

		return _builds

	def get_packages(self, arch):
		if arch.name == "src":
			pkgs = self.db.query("SELECT packages.id AS id FROM packages \
				JOIN builds ON builds.pkg_id = packages.id \
				JOIN repositories_builds ON builds.id = repositories_builds.build_id \
				WHERE packages.arch = %s AND repositories_builds.repo_id = %s",
				arch.id, self.id)

		else:
			noarch = self.pakfire.arches.get_by_name("noarch")
			assert noarch

			pkgs = self.db.query("SELECT packages.id AS id FROM packages \
				JOIN jobs_packages ON jobs_packages.pkg_id = packages.id \
				JOIN jobs ON jobs_packages.job_id = jobs.id \
				JOIN builds ON builds.id = jobs.build_id \
				JOIN repositories_builds ON builds.id = repositories_builds.build_id \
				WHERE (jobs.arch_id = %s OR jobs.arch_id = %s) AND \
				repositories_builds.repo_id = %s",
				arch.id, noarch.id, self.id)

		return sorted([packages.Package(self.pakfire, p.id) for p in pkgs])

	@property
	def packages(self):
		return self.get_packages()

	def get_unpushed_builds(self):
		query = self.db.query("SELECT build_id FROM repositories_builds \
			WHERE repo_id = %s AND \
			time_added > (SELECT last_update FROM repositories WHERE id = %s)",
			self.id, self.id)

		ret = []
		for row in query:
			b = builds.Build(self.pakfire, row.build_id)
			ret.append(b)

		return ret

	def get_obsolete_builds(self):
		#query = self.db.query("SELECT build_id AS id FROM repositories_builds \
		#	JOIN builds ON repositories.build_id = builds.id \
		#	WHERE repositories_builds.repo_id = %s AND builds.state = 'obsolete'",
		#	self.id)
		#
		#ret = []
		#for row in query:
		#	b = builds.Build(self.pakfire, row.id)
		#	ret.append(b)
		#
		#return ret
		return self.pakfire.builds.get_obsolete(self)

	def needs_update(self):
		if self.get_unpushed_builds:
			return True

		return False

	def updated(self):
		self.db.execute("UPDATE repositories SET last_update = NOW() \
			WHERE id = %s", self.id)

	def get_history(self, **kwargs):
		kwargs.update({
			"repo" : self,
		})

		return self.pakfire.repos.get_history(**kwargs)

	def get_build_times(self):
		noarch = self.pakfire.arches.get_by_name("noarch")
		assert noarch

		times = []
		for arch in self.pakfire.arches.get_all():
			time = self.db.get("SELECT SUM(jobs.time_finished - jobs.time_started) AS time FROM jobs \
				JOIN builds ON builds.id = jobs.build_id \
				JOIN repositories_builds ON builds.id = repositories_builds.build_id \
				WHERE (jobs.arch_id = %s OR jobs.arch_id = %s) AND \
				repositories_builds.repo_id = %s", arch.id, noarch.id, self.id)

			times.append((arch, time.time))

		return times


class RepositoryAux(base.Object):
	def __init__(self, pakfire, id):
		base.Object.__init__(self, pakfire)

		self.id = id

		# Cache.
		self._data = None
		self._distro = None

	@property
	def data(self):
		if self._data is None:
			self._data = self.db.get("SELECT * FROM repositories_aux WHERE id = %s", self.id)
			assert self._data

		return self._data

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
		if self._distro is None:
			self._distro = self.pakfire.distros.get_by_id(self.data.distro_id)
			assert self._distro

		return self._distro

	def get_conf(self):
		lines = [
			"[repo:%s]" % self.identifier,
			"description = %s - %s" % (self.distro.name, self.name),
			"enabled = 1",
			"baseurl = %s" % self.url,
			"priority = 0",
		]

		return "\n".join(lines)
