#!/usr/bin/python

from . import base

_priorities = {
	"noarch"   : 0,

	# 64 bit
	"x86_64"   : 1,
	"aarch64"  : 2,

	# 32 bit
	"i686"     : 3,
	"armv7hl"  : 4,
	"armv5tel" : 5,
}

def priority(arch):
	try:
		return _priorities[arch]
	except KeyError:
		return 99

class Arches(base.Object):
	def __iter__(self):
		res = self.db.query("SELECT name FROM arches \
			WHERE NOT name = ANY(%s)", ("noarch", "src"))

		return sorted((a.name for a in res), key=priority)

	def get_all(self, really=False):
		query = "SELECT * FROM arches"

		if not really:
			query += " WHERE binary = 'Y'"
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


class Arch(base.DataObject):
	table = "arches"

	def __cmp__(self, other):
		return cmp(self.prio, other.prio)

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
