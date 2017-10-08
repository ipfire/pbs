#!/usr/bin/python

from __future__ import absolute_import, division

import datetime
import hashlib
import logging
import random
import string
import time

from . import base
from . import logs

from .decorators import *

from .users import generate_password_hash, check_password_hash, generate_random_string

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


class Builder(base.DataObject):
	table = "builders"

	def __cmp__(self, other):
		if other is None:
			return -1

		return cmp(self.id, other.id)

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
		self._set_attribute("passphrase", passphrase_hash)

		# Return the clear-text passphrase.
		return passphrase

	def validate_passphrase(self, passphrase):
		"""
			Compare the given passphrase with the one stored in the database.
		"""
		return check_password_hash(passphrase, self.data.passphrase)

	# Description

	def set_description(self, description):
		self._set_attribute("description", description)

	description = property(lambda s: s.data.description or "", set_description)

	@property
	def status(self):
		return self.data.status

	@property
	def keepalive(self):
		"""
			Returns time of last keepalive message from this host.
		"""
		return self.data.time_keepalive

	def update_keepalive(self, loadavg1=None, loadavg5=None, loadavg15=None,
			mem_total=None, mem_free=None, swap_total=None, swap_free=None,
			space_free=None):
		"""
			Update the keepalive timestamp of this machine.
		"""
		self.db.execute("UPDATE builders SET time_keepalive = NOW(), \
			loadavg1 = %s, loadavg5 = %s, loadavg15 = %s, space_free = %s, \
			mem_total = %s, mem_free = %s, swap_total = %s, swap_free = %s \
			WHERE id = %s", loadavg1, loadavg5, loadavg15, space_free,
			mem_total, mem_free, swap_total, swap_free, self.id)

	def update_info(self, cpu_model=None, cpu_count=None, cpu_arch=None, cpu_bogomips=None,
			pakfire_version=None, host_key=None, os_name=None):
		# Update all the rest.
		self.db.execute("UPDATE builders SET time_updated = NOW(), \
			pakfire_version = %s, cpu_model = %s, cpu_count = %s, cpu_arch = %s, \
			cpu_bogomips = %s, host_key_id = %s, os_name = %s WHERE id = %s",
			pakfire_version, cpu_model, cpu_count, cpu_arch, cpu_bogomips,
			host_key, os_name, self.id)

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

		self._set_attribute("status", status)

		if log:
			self.log(status, user=user)

	@lazy_property
	def arches(self):
		if self.cpu_arch:
			res = self.db.query("SELECT build_arch FROM arches_compat \
				WHERE host_arch = %s", self.cpu_arch)

			arches += [r.build_arch for r in res]
			if not self.cpu_arch in arches:
				arches.append(self.cpu_arch)

			return arches

		return []

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

	def set_max_jobs(self, value):
		self._set_attribute("max_jobs", value)

	max_jobs = property(lambda s: s.data.max_jobs, set_max_jobs)

	@property
	def name(self):
		return self.data.name

	@property
	def hostname(self):
		return self.name

	@property
	def passphrase(self):
		return self.data.passphrase

	# Load average

	@property
	def loadavg(self):
		return ", ".join(["%.2f" % l for l in (self.loadavg1, self.loadavg5, self.loadavg15)])

	@property
	def loadavg1(self):
		return self.data.loadavg1 or 0.0

	@property
	def loadavg5(self):
		return self.data.loadavg5 or 0.0

	@property
	def loadavg15(self):
		return self.data.loadavg15 or 0.0

	@property
	def pakfire_version(self):
		return self.data.pakfire_version or ""

	@property
	def os_name(self):
		return self.data.os_name or ""

	@property
	def cpu_model(self):
		return self.data.cpu_model or ""

	@property
	def cpu_count(self):
		return self.data.cpu_count

	@property
	def cpu_arch(self):
		return self.data.cpu_arch

	@property
	def cpu_bogomips(self):
		return self.data.cpu_bogomips or 0.0

	@property
	def mem_percentage(self):
		if not self.mem_total:
			return None

		return self.mem_used * 100 / self.mem_total

	@property
	def mem_total(self):
		return self.data.mem_total

	@property
	def mem_used(self):
		if self.mem_total and self.mem_free:
			return self.mem_total - self.mem_free

	@property
	def mem_free(self):
		return self.data.mem_free

	@property
	def swap_percentage(self):
		if not self.swap_total:
			return None

		return self.swap_used * 100 / self.swap_total

	@property
	def swap_total(self):
		return self.data.swap_total

	@property
	def swap_used(self):
		if self.swap_total and self.swap_free:
			return self.swap_total - self.swap_free

	@property
	def swap_free(self):
		return self.data.swap_free

	@property
	def space_free(self):
		return self.data.space_free

	@property
	def overload(self):
		if not self.cpu_count or not self.loadavg1:
			return None

		return self.loadavg1 >= self.cpu_count

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

	@lazy_property
	def active_jobs(self, *args, **kwargs):
		return self.pakfire.jobs.get_active(builder=self, *args, **kwargs)

	@property
	def too_many_jobs(self):
		"""
			Tell if this host is already running enough or too many jobs.
		"""
		return len(self.active_jobs) >= self.max_jobs

	def get_next_jobs(self, limit=None):
		"""
			Returns a list of jobs that can be built on this host.
		"""
		return self.pakfire.jobs.get_next(arches=self.arches, limit=limit)

	def get_next_job(self):
		"""
			Returns the next job in line for this builder.
		"""
		# Get the first item of all jobs in the list.
		jobs = self.pakfire.jobs.get_next(builder=self, state="pending", limit=1)

		if jobs:
			return jobs[0]

	def get_history(self, *args, **kwargs):
		kwargs["builder"] = self

		return self.pakfire.builders.get_history(*args, **kwargs)
