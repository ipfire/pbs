#!/usr/bin/python

from __future__ import division

import datetime
import hashlib
import logging
import random
import string
import time

import base
import logs

from users import generate_password_hash, check_password_hash, generate_random_string

class Builders(base.Object):
	def auth(self, name, passphrase):
		# If either name or passphrase is None, we don't check at all.
		if None in (name, passphrase):
			return

		# Search for the hostname in the database.
		# The builder must not be deleted.
		builder = self.db.get("SELECT id FROM builders WHERE name = %s AND \
			NOT status = 'deleted'", name)

		if not builder:
			return

		# Get the whole Builder object from the database.
		builder = self.get_by_id(builder.id)

		# If the builder was not found or the passphrase does not match,
		# you have bad luck.
		if not builder or not builder.validate_passphrase(passphrase):
			return

		# Otherwise we return the Builder object.
		return builder

	def get_all(self):
		builders = self.db.query("SELECT * FROM builders WHERE NOT status = 'deleted' ORDER BY name")

		return [Builder(self.pakfire, b.id, b) for b in builders]

	def get_by_id(self, id):
		if not id:
			return

		return Builder(self.pakfire, id)

	def get_by_name(self, name):
		builder = self.db.get("SELECT * FROM builders WHERE name = %s LIMIT 1", name)

		if builder:
			return Builder(self.pakfire, builder.id, builder)

	def get_all_arches(self):
		arches = set()

		for result in self.db.query("SELECT DISTINCT arches FROM builders"):
			if not result.arches:
				continue

			_arches = result.arches.split()

			for arch in _arches:
				arches.add(arch)

		return sorted(arches)

	def get_load(self):
		res1 = self.db.get("SELECT SUM(max_jobs) AS max_jobs FROM builders \
			WHERE status = 'enabled'")

		res2 = self.db.get("SELECT COUNT(*) AS count FROM jobs \
			WHERE state = 'dispatching' OR state = 'running' OR state = 'uploading'")

		try:
			return (res2.count * 100 / res1.max_jobs)
		except:
			return 0

	def get_history(self, limit=None, offset=None, builder=None, user=None):
		query = "SELECT * FROM builders_history"
		args  = []

		conditions = []

		if builder:
			conditions.append("builder_id = %s")
			args.append(builder.id)

		if user:
			conditions.append("user_id = %s")
			args.append(user.id)

		if conditions:
			query += " WHERE %s" % " AND ".join(conditions)

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
			entry = logs.BuilderLogEntry(self.pakfire, entry)
			entries.append(entry)

		return entries


class Builder(base.Object):
	def __init__(self, pakfire, id, data=None):
		base.Object.__init__(self, pakfire)

		self.id = id

		# Cache.
		self._data = data
		self._active_jobs = None
		self._arches = None
		self._disabled_arches = None

	def __cmp__(self, other):
		if other is None:
			return -1

		return cmp(self.id, other.id)

	@property
	def data(self):
		if self._data is None:
			self._data = self.db.get("SELECT * FROM builders WHERE id = %s", self.id)
			assert self._data

		return self._data

	@classmethod
	def create(cls, pakfire, name, user=None, log=True):
		"""
			Creates a new builder.
		"""
		builder_id = pakfire.db.execute("INSERT INTO builders(name, time_created) \
			VALUES(%s, NOW())", name)

		# Create Builder object.
		builder = cls(pakfire, builder_id)

		# Generate a new passphrase.
		passphrase = builder.regenerate_passphrase()

		# Log what we have done.
		if log:
			builder.log("created", user=user)

		# The Builder object and the passphrase are returned.
		return builder, passphrase

	def log(self, action, user=None):
		user_id = None
		if user:
			user_id = user.id

		self.db.execute("INSERT INTO builders_history(builder_id, action, user_id, time) \
			VALUES(%s, %s, %s, NOW())", self.id, action, user_id)

	def set(self, key, value):
		self.db.execute("UPDATE builders SET %s = %%s WHERE id = %%s LIMIT 1" % key,
			value, self.id)
		self.data[key] = value

	def regenerate_passphrase(self):
		"""
			Generates a new random passphrase and stores it as a salted hash
			to the database.

			The new passphrase is returned to be sent to the user (once).
		"""
		# Generate a random string with 20 chars.
		passphrase = generate_random_string(length=20)

		# Create salted hash.
		passphrase_hash = generate_password_hash(passphrase)

		# Store the hash in the database.
		self.db.execute("UPDATE builders SET passphrase = %s WHERE id = %s",
			passphrase_hash, self.id)

		# Return the clear-text passphrase.
		return passphrase

	def validate_passphrase(self, passphrase):
		"""
			Compare the given passphrase with the one stored in the database.
		"""
		return check_password_hash(passphrase, self.data.passphrase)

	@property
	def description(self):
		return self.data.description or ""

	@property
	def status(self):
		return self.data.status

	def update_description(self, description):
		self.db.execute("UPDATE builders SET description = %s, time_updated = NOW() \
			WHERE id = %s", description, self.id)

		if self._data:
			self._data["description"] = description

	@property
	def keepalive(self):
		"""
			Returns time of last keepalive message from this host.
		"""
		return self.data.time_keepalive

	def update_keepalive(self, loadavg, free_space):
		"""
			Update the keepalive timestamp of this machine.
		"""
		if free_space is None:
			free_space = 0

		self.db.execute("UPDATE builders SET time_keepalive = NOW(), loadavg = %s, \
			free_space = %s WHERE id = %s", loadavg, free_space, self.id)

		logging.debug("Builder %s updated it keepalive status: %s" \
			% (self.name, loadavg))

	def needs_update(self):
		query = self.db.get("SELECT time_updated, NOW() - time_updated \
			AS seconds FROM builders WHERE id = %s", self.id)

		# If there has been no update at all, we will need a new one.
		if query.time_updated is None:
			return True

		# Require an update after the data is older than 24 hours.
		return query.seconds >= 24*3600

	def update_info(self, arches, cpu_model, cpu_count, memory, pakfire_version=None, host_key_id=None):
		# Update architecture information.
		self.update_arches(arches)

		# Update all the rest.
		self.db.execute("UPDATE builders SET time_updated = NOW(), \
			pakfire_version = %s, cpu_model = %s, cpu_count = %s, memory = %s, \
			host_key_id = %s \
			WHERE id = %s", pakfire_version or "", cpu_model, cpu_count, memory,
			host_key_id, self.id)

	def update_arches(self, arches):
		# Get all arches this builder does currently support.
		supported_arches = [a.name for a in self.get_arches()]

		# Noarch is always supported.
		if not "noarch" in arches:
			arches.append("noarch")

		arches_add = []
		for arch in arches:
			if arch in supported_arches:
				supported_arches.remove(arch)
				continue

			arches_add.append(arch)
		arches_rem = supported_arches

		for arch_name in arches_add:
			arch = self.pakfire.arches.get_by_name(arch_name)
			if not arch:
				logging.info("Client sent unknown architecture: %s" % arch_name)
				continue

			self.db.execute("INSERT INTO builders_arches(builder_id, arch_id) \
				VALUES(%s, %s)", self.id, arch.id)

		for arch_name in arches_rem:
			arch = self.pakfire.arches.get_by_name(arch_name)
			assert arch

			self.db.execute("DELETE FROM builders_arches WHERE builder_id = %s \
				AND arch_id = %s", self.id, arch.id)

	def update_overload(self, overload):
		if overload:
			overload = "Y"
		else:
			overload = "N"

		self.db.execute("UPDATE builders SET overload = %s WHERE id = %s",
			overload, self.id)
		self._data["overload"] = overload

		logging.debug("Builder %s updated it overload status to %s" % \
			(self.name, self.overload))

	def get_enabled(self):
		return self.status == "enabled"

	def set_enabled(self, value):
		# XXX deprecated

		if value:
			value = "enabled"
		else:
			value = "disabled"

		self.set_status(value)

	enabled = property(get_enabled, set_enabled)

	@property
	def disabled(self):
		return not self.enabled

	def set_status(self, status, user=None, log=True):
		assert status in ("created", "enabled", "disabled", "deleted")

		if self.status == status:
			return

		self.db.execute("UPDATE builders SET status = %s WHERE id = %s",
			status, self.id)

		if self._data:
			self._data["status"] = status

		if log:
			self.log(status, user=user)

	def get_arches(self, enabled=None):
		"""
			A list of architectures that are supported by this builder.
		"""
		if enabled is True:
			enabled = "Y"
		elif enabled is False:
			enabled = "N"
		else:
			enabled = None

		query = "SELECT arch_id AS id FROM builders_arches WHERE builder_id = %s"
		args  = [self.id,]

		if enabled:
			query += " AND enabled = %s"
			args.append(enabled)

		# Get all other arches from the database.
		arches = []
		for arch in self.db.query(query, *args):
			arch = self.pakfire.arches.get_by_id(arch.id)
			arches.append(arch)

		# Save a sorted list of supported architectures.
		arches.sort()

		return arches

	@property
	def arches(self):
		if self._arches is None:
			self._arches = self.get_arches(enabled=True)

		return self._arches

	@property
	def disabled_arches(self):
		if self._disabled_arches is None:
			self._disabled_arches = self.get_arches(enabled=False)

		return self._disabled_arches

	def set_arch_status(self, arch, enabled):
		if enabled:
			enabled = "Y"
		else:
			enabled = "N"

		self.db.execute("UPDATE builders_arches SET enabled = %s \
			WHERE builder_id = %s AND arch_id = %s", enabled, self.id, arch.id)

		# Reset the arch cache.
		self._arches = None

	def get_build_release(self):
		return self.data.build_release == "Y"

	def set_build_release(self, value):
		if value:
			value = "Y"
		else:
			value = "N"

		self.db.execute("UPDATE builders SET build_release = %s WHERE id = %s",
			value, self.id)

		# Update the cache.
		if self._data:
			self._data["build_release"] = value

	build_release = property(get_build_release, set_build_release)

	def get_build_scratch(self):
		return self.data.build_scratch == "Y"

	def set_build_scratch(self, value):
		if value:
			value = "Y"
		else:
			value = "N"

		self.db.execute("UPDATE builders SET build_scratch = %s WHERE id = %s",
			value, self.id)

		# Update the cache.
		if self._data:
			self._data["build_scratch"] = value

	build_scratch = property(get_build_scratch, set_build_scratch)

	def get_build_test(self):
		return self.data.build_test == "Y"

	def set_build_test(self, value):
		if value:
			value = "Y"
		else:
			value = "N"

		self.db.execute("UPDATE builders SET build_test = %s WHERE id = %s",
			value, self.id)

		# Update the cache.
		if self._data:
			self._data["build_test"] = value

	build_test = property(get_build_test, set_build_test)

	@property
	def build_types(self):
		ret = []

		if self.build_release:
			ret.append("release")

		if self.build_scratch:
			ret.append("scratch")

		if self.build_test:
			ret.append("test")

		return ret

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
		if self.state == "online":
			return self.data.loadavg

	@property
	def load1(self):
		try:
			load1, load5, load15 = self.loadavg.split(", ")
		except:
			return None

		return load1

	@property
	def pakfire_version(self):
		return self.data.pakfire_version or ""

	@property
	def cpu_model(self):
		return self.data.cpu_model or ""

	@property
	def cpu_count(self):
		return self.data.cpu_count

	@property
	def memory(self):
		return self.data.memory

	@property
	def free_space(self):
		return self.data.free_space or 0

	@property
	def overload(self):
		return self.data.overload == "Y"

	@property
	def host_key_id(self):
		return self.data.host_key_id

	@property
	def state(self):
		if self.disabled:
			return "disabled"

		if self.data.time_keepalive is None:
			return "offline"

		#if self.data.updated >= 5*60:
		#	return "offline"

		return "online"

	def get_active_jobs(self, *args, **kwargs):
		if self._active_jobs is None:
			self._active_jobs = self.pakfire.jobs.get_active(builder=self, *args, **kwargs)

		return self._active_jobs

	def count_active_jobs(self):
		return len(self.get_active_jobs())

	@property
	def too_many_jobs(self):
		"""
			Tell if this host is already running enough or too many jobs.
		"""
		return self.count_active_jobs() >= self.max_jobs

	def get_next_jobs(self, arches=None, limit=None):
		if arches is None:
			arches = self.get_arches()

		return self.pakfire.jobs.get_next(arches=arches, builder=self,
			state="pending", limit=limit)

	def get_next_job(self, *args, **kwargs):
		kwargs["limit"] = 1

		jobs = self.get_next_jobs(*args, **kwargs)

		if jobs:
			return jobs[0]

	def get_history(self, *args, **kwargs):
		kwargs["builder"] = self

		return self.pakfire.builders.get_history(*args, **kwargs)
