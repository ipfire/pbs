#!/usr/bin/python

import base

class Arches(base.Object):
	def get_all(self):
		arches = self.db.query("SELECT id FROM arches WHERE `binary` = 'Y'")

		return sorted([Arch(self.pakfire, a.id) for a in arches])

	def get_name_by_id(self, id):
		arch = self.db.get("SELECT name FROM arches WHERE id = %s", id)

		return arch.name

	def get_id_by_name(self, name):
		arch = self.db.get("SELECT id FROM arches WHERE name = %s", name)

		if arch:
			return arch.id

	def get_by_name(self, name):
		id = self.get_id_by_name(name)

		if id:
			return self.get_by_id(id)

	def get_by_id(self, id):
		return Arch(self.pakfire, id)

	def exists(self, id):
		arch = self.db.get("SELECT id FROM arches WHERE id = %s", id)

		if arch:
			return True

		return False

	def expand(self, arches):
		args = []

		if arches == "all":
			query = "SELECT id FROM arches WHERE name != 'noarch'"
		else:
			query = []

			for arch in arches.split():
				args.append(arch)
				query.append("name = %s")

			query = "SELECT id FROM arches WHERE (%s)" % " OR ".join(query)

		return sorted([self.get_by_id(a.id) for a in self.db.query(query, *args)])


class Arch(base.Object):
	def __init__(self, pakfire, id):
		base.Object.__init__(self, pakfire)

		# The ID of this architecture.
		self.id = id

		# Cache data.
		self._data = None

	def __cmp__(self, other):
		return cmp(self.prio, other.prio)

	@property
	def data(self):
		if self._data is None:
			cache_key = "arch_%s" % self.id

			# Search for the data in the cache.
			# If nothing was found, we get everything from the database.
			data = self.cache.get(cache_key)
			if not data:
				data = self.db.get("SELECT * FROM arches WHERE id = %s", self.id)

				# Store the data in the cache.
				self.cache.set(cache_key, data)

			self._data = data
			assert self._data

		return self._data

	@property
	def name(self):
		return self.data.name

	@property
	def prio(self):
		return self.data.prio

	@property
	def build_type(self):
		if self.name == "src":
			return "source"

		return "binary"
