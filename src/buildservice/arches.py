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

		return iter(sorted((a.name for a in res), key=priority))

	def exists(self, name):
		# noarch doesn't really exist
		if name == "noarch":
			return False

		res = self.db.get("SELECT 1 FROM arches \
			WHERE name = %s", name)

		if res:
			return True

		return False

	def expand(self, arches):
		if arches == "all":
			return list(self)

		res = []
		for arch in arches.split():
			if self.exists(arch):
				res.append(arch)

		return res
