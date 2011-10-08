#!/usr/bin/python

import datetime
import hashlib
import logging
import random
import string
import time

import base

class Builders(base.Object):
	def get_all(self):
		builders = self.db.query("SELECT id FROM builders WHERE deleted = 'N' ORDER BY name")

		return [Builder(self.pakfire, b.id) for b in builders]

	def get_by_id(self, id):
		if not id:
			return

		return Builder(self.pakfire, id)

	def get_by_name(self, name):
		builder = self.db.get("SELECT id FROM builders WHERE name = %s LIMIT 1", name)

		if builder:
			return Builder(self.pakfire, builder.id)

	def get_all_arches(self):
		arches = set()

		for result in self.db.query("SELECT DISTINCT arches FROM builders"):
			if not result.arches:
				continue

			_arches = result.arches.split()

			for arch in _arches:
				arches.add(arch)

		return sorted(arches)


class Builder(base.Object):
	def __init__(self, pakfire, id):
		base.Object.__init__(self, pakfire)

		self.id = id

		self.data = self.db.get("SELECT * FROM builders WHERE id = %s", self.id)

	def __cmp__(self, other):
		return cmp(self.id, other.id)

	@classmethod
	def new(cls, pakfire, name):
		id = pakfire.db.execute("INSERT INTO builders(name) VALUES(%s)", name)

		builder = cls(pakfire, id)
		builder.regenerate_passphrase()

		return builder

	def set(self, key, value):
		self.db.execute("UPDATE builders SET %s = %%s WHERE id = %%s LIMIT 1" % key,
			value, self.id)
		self.data[key] = value

	def delete(self):
		self.set("disabled", "Y")
		self.set("deleted",  "Y")

	def regenerate_passphrase(self):
		source = string.ascii_letters + string.digits
		passphrase = "".join(random.sample(source * 30, 20))

		self.set("passphrase", passphrase)

	def validate_passphrase(self, passphrase):
		return self.passphrase == passphrase

	def update_info(self, loadavg, cpu_model, memory, arches):
		self.set("loadavg", loadavg)
		self.set("cpu_model", cpu_model)
		self.set("memory", memory)
		self.set("arches", arches)

	def get_enabled(self):
		return not self.disabled

	def set_enabled(self, value):
		if value:
			value = "N"
		else:
			value = "Y"

		self.set("disabled", value)

	enabled = property(get_enabled, set_enabled)

	@property
	def disabled(self):
		return self.data.disabled == "Y"

	@property
	def arches(self):
		arches = ["noarch",]

		if self.build_src:
			arches.append("src")

		if self.data.arches:
			arches += self.data.arches.split()

		return sorted(arches)

	def get_build_src(self):
		return self.data.build_src == "Y"

	def set_build_src(self, value):
		if value:
			value = "Y"
		else:
			value = "N"

		self.set("build_src", value)

	build_src = property(get_build_src, set_build_src)

	def get_build_bin(self):
		return self.data.build_bin == "Y"

	def set_build_bin(self, value):
		if value:
			value = "Y"
		else:
			value = "N"

		self.set("build_bin", value)

	build_bin = property(get_build_bin, set_build_bin)

	def get_build_test(self):
		return self.data.build_test == "Y"

	def set_build_test(self, value):
		if value:
			value = "Y"
		else:
			value = "N"

		self.set("build_test", value)

	build_test = property(get_build_test, set_build_test)

	def get_max_jobs(self):
		return self.data.max_jobs

	def set_max_jobs(self, value):
		self.set("max_jobs", value)

	max_jobs = property(get_max_jobs, set_max_jobs)

	@property
	def name(self):
		return self.data.name

	@property
	def hostname(self):
		return self.name

	@property
	def passphrase(self):
		return self.data.passphrase

	@property
	def loadavg(self):
		if not self.status == "ONLINE":
			return 0

		return self.data.loadavg

	@property
	def cpu_model(self):
		return self.data.cpu_model

	@property
	def memory(self):
		return self.data.memory * 1024

	@property
	def status(self):
		if self.disabled:
			return "DISABLED"

		threshhold = datetime.datetime.utcnow() - datetime.timedelta(minutes=6)

		if self.data.updated < threshhold:
			return "OFFLINE"

		return "ONLINE"

	@property
	def builds(self):
		return self.pakfire.builds.get_by_host(self.id)

	@property
	def active_builds(self):
		return self.pakfire.builds.get_active(host_id=self.id)
