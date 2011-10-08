#!/usr/bin/python

import base
from repository import Repository

class Distributions(base.Object):
	def get_all(self):
		distros = self.db.query("SELECT id FROM distributions ORDER BY name")

		return [Distribution(self.pakfire, d.id) for d in distros]

	def get_by_id(self, id):
		distro = self.db.get("SELECT id FROM distributions WHERE id = %s LIMIT 1", id)

		if distro:
			return Distribution(self.pakfire, distro.id)

	def get_by_name(self, name):
		distro = self.db.get("SELECT id FROM distributions WHERE sname = %s LIMIT 1", name)

		if distro:
			return Distribution(self.pakfire, distro.id)


class Distribution(base.Object):
	def __init__(self, pakfire, id):
		base.Object.__init__(self, pakfire)
		self.id = id

		self._data = \
			self.db.get("SELECT * FROM distributions WHERE id = %s", self.id)

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.name)

	def set(self, key, value):
		self.db.execute("UPDATE distributions SET %s = %%s WHERE id = %%s" % key,
			value, self.id)
		self._data[key] = value

	@property
	def info(self):
		return {
			"name"        : self.name,
			"sname"       : self.sname,
			"slogan"      : self.slogan,
			"arches"      : self.arches,
			"vendor"      : self.vendor,
			"description" : self.description,
		}

	@property
	def name(self):
		return self._data.name

	@property
	def sname(self):
		return self._data.sname

	@property
	def slogan(self):
		return self._data.slogan

	@property
	def arches(self):
		arches = self._data.arches.split()

		return sorted(arches)

	@property
	def vendor(self):
		return self._data.vendor

	@property
	def description(self):
		return self._data.description or ""

	@property
	def repositories(self):
		repos = self.db.query("SELECT id FROM repositories WHERE distro_id = %s", self.id)

		return sorted([Repository(self.pakfire, r.id) for r in repos])

	def get_repo(self, name):
		repo = self.db.get("SELECT id FROM repositories WHERE distro_id = %s AND name = %s",
			self.id, name)

		return Repository(self.pakfire, repo.id)

	@property
	def comprehensive_repositories(self):
		return [r for r in self.repositories if r.comprehensive]

	def add_repository(self, name, description):
		return Repository.new(self.pakfire, self, name, description)

	@property
	def sources(self):
		return self.pakfire.sources.get_by_distro(self)

	@property
	def log(self):
		return self.db.query("SELECT * FROM log WHERE distro_id = %s ORDER BY time DESC", self.id)

