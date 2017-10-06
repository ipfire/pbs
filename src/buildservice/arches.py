#!/usr/bin/python

from . import base

class Arches(base.Object):
	def get_all(self, really=False):
		query = "SELECT * FROM arches"

		if not really:
			query += " WHERE `binary` = 'Y'"
		else:
			query += " WHERE NOT name = 'src'"

		query += " ORDER BY prio ASC"

		arches = self.db.query(query)

		return [Arch(self.pakfire, a.id, a) for a in arches]

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
	def __init__(self, pakfire, id, data=None):
		base.Object.__init__(self, pakfire)

		# The ID of this architecture.
		self.id = id

		# Cache data.
		self._data = data

	def __cmp__(self, other):
		return cmp(self.prio, other.prio)

	@property
	def data(self):
		if self._data is None:
			self._data = self.db.get("SELECT * FROM arches WHERE id = %s", self.id)
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
