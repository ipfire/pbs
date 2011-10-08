#!/usr/bin/python

import base
import packages

class Repositories(base.Object):
	def get_all(self):
		repos = self.db.query("SELECT id FROM repositories")

		return [Repository(self.pakfire, r.id) for r in repos]

	def get_by_id(self, repo_id):
		repo = self.db.get("SELECT id FROM repositories WHERE id = %s", repo_id)

		if repo:
			return Repository(self.pakfire, repo.id)

	def get_needs_update(self, limit=None):
		query = "SELECT id FROM repositories WHERE needs_update = 'Y'"
		query += " ORDER BY last_update ASC"

		# Append limit if any
		if limit:
			query += " LIMIT %d" % limit

		repos = self.db.query(query)

		return [Repository(self.pakfire, r.id) for r in repos]

	def get_action_by_id(self, action_id):
		action = self.db.get("SELECT id, repo_id FROM repository_actions WHERE id = %s"
			" LIMIT 1" , action_id)

		assert action

		repo = self.get_by_id(action.repo_id)

		return RepoAction(self.pakfire, repo, action.id)

	def get_actions_by_pkgid(self, pkgid):
		actions = self.db.query("SELECT id FROM repository_actions WHERE pkg_id = %s", pkg_id)

		return [RepoAction(self.pakfire, self, a.id) for a in actions]


class Repository(base.Object):
	def __init__(self, pakfire, id):
		base.Object.__init__(self, pakfire)
		self.id = id

		self.data = self.db.get("SELECT * FROM repositories WHERE id = %s", self.id)

	def __cmp__(self, other):
		if not self.upstream_id or not other.upstream_id:
			return 0

		if self.id == other.upstream_id:
			return -1

		elif self.upstream_id == other.id:
			return 1

	def next(self):
		repo = self.db.get("SELECT id FROM repositories WHERE upstream = %s"
			" LIMIT 1", self.id)

		if repo:
			return self.pakfire.repos.get_by_id(repo.id)

	def last(self):
		if self.upstream_id:
			return self.pakfire.repos.get_by_id(self.upstream_id)

	@property
	def upstream(self):
		return self.last()

	@property
	def is_upstream(self):
		return not self.upstream

	@classmethod
	def new(cls, pakfire, distro, name, description):
		id = pakfire.db.execute("INSERT INTO repositories(distro_id, name, description)"
			" VALUES(%s, %s, %s)", distro.id, name, description)

		return cls(pakfire, id)

	@property
	def distro(self):
		return self.pakfire.distros.get_by_id(self.data.distro_id)

	@property
	def info(self):
		return {
			"id"     : self.id,
			"distro" : self.distro.info,
			"name"   : self.name,
			"arches" : self.arches,
		}

	@property
	def comprehensive(self):
		return not self.upstream_id

	@property
	def name(self):
		return self.data.name

	@property
	def description(self):
		return self.data.description

	@property
	def upstream_id(self):
		return self.data.upstream

	@property
	def arches(self):
		return self.distro.arches

	def get_needs_update(self):
		return self.data.needs_update

	def set_needs_update(self, val):
		if val:
			val = "Y"
		else:
			val = "N"

		self.db.execute("UPDATE repositories SET needs_update = %s WHERE id = %s",
			val, self.id)

	needs_update = property(get_needs_update, set_needs_update)

	@property
	def credits_needed(self):
		return self.data.credits_needed

	def add_package(self, pkg_id):
		id = self.db.execute("INSERT INTO repository_packages(repo_id, pkg_id)"
			" VALUES(%s, %s)", self.id, pkg_id)

		# Mark, that the repository was altered and needs an update.
		self.needs_update = True

		return id

	def get_packages(self, _query=None):
		query = "SELECT pkg_id FROM repository_packages WHERE repo_id = %s"
		if _query:
			query = "%s %s" % (query, _query)

		pkgs = self.db.query(query, self.id)

		return sorted([packages.Package(self.pakfire, p.pkg_id) for p in pkgs])

	@property
	def packages(self):
		return self.get_packages()

	@property
	def waiting_packages(self):
		return self.get_packages("AND state = 'waiting'")

	@property
	def pushed_packages(self):
		return self.get_packages("AND state = 'pushed'")

	@property
	def log(self):
		return self.db.query("SELECT * FROM log WHERE repo_id = %s ORDER BY time DESC", self.id)

	def register_action(self, action, pkg_id, old_pkg_id=None):
		assert action in ("add", "remove",)
		assert pkg_id is not None

		id = self.db.execute("INSERT INTO repository_actions(action, repo_id, pkg_id)"
			" VALUES(%s, %s, %s)", action, self.id, pkg_id)

		# On upstream repositories, all actions are done immediately.
		if self.is_upstream:
			action = RepoAction(self.pakfire, self, id)
			action.run()

		return id

	def has_actions(self):
		actions = self.db.get("SELECT COUNT(*) as c FROM repository_actions"
			" WHERE repo_id = %s", self.id)

		if actions.c:
			return True

		return False

	def get_actions(self):
		actions = self.db.query("SELECT id FROM repository_actions"
			" WHERE repo_id = %s ORDER BY time_added ASC", self.id)

		return [RepoAction(self.pakfire, self, a.id) for a in actions]


class RepoAction(base.Object):
	def __init__(self, pakfire, repo, id):
		base.Object.__init__(self, pakfire)

		self.repo = repo
		self.id = id

		self.data = self.db.get("SELECT * FROM repository_actions WHERE id = %s"
			" LIMIT 1", self.id)
		assert self.data
		assert self.data.repo_id == self.repo.id

	@property
	def action(self):
		return self.data.action

	@property
	def pkg_id(self):
		return self.data.pkg_id

	@property
	def pkg(self):
		return self.pakfire.packages.get_by_id(self.pkg_id)

	@property
	def credits_needed(self):
		return self.repo.credits_needed - self.pkg.credits

	@property
	def time_added(self):
		return self.data.time_added

	def delete(self, who=None):
		"""
			Delete ourself from the database.
		"""
		if who and not self.have_permission(who):
			raise Exception, "Insufficient permissions"

		self.db.execute("DELETE FROM repository_actions WHERE id = %s LIMIT 1", self.id)

	def have_permission(self, who):
		"""
			Check if "who" has the permission to perform this action.
		"""
		if who is None:
			return True

		# Admins are always allowed to do all actions.
		if who.is_admin():
			return True

		# If the maintainer matches, he is also allowed.
		if who.email == self.pkg.maintainer_email:
			return True

		# Everybody else is denied.
		return False

	def is_doable(self):
		return self.credits_needed == 0

	def run(self, who=None):
		if who and not self.have_permission(who):
			raise Exception, "Insufficient permissions"

		if self.action == "add":
			self.repo.add_package(self.pkg_id)

		elif self.action == "remove":
			self.db.excute("DELETE FROM repository_packages WHERE repo_id = %s"
				" AND pkg_id = %s LIMIT 1", self.repo.id, self.pkg_id)

		else:
			raise Exception, "Invalid action"

		# If the action was started by an upstream repository, we add it so
		# the next one.
		next = self.repo.next()
		if next:
			next.register_action(self.action, self.pkg_id)

		# Delete ourself.
		self.delete(who)
