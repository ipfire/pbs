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
	def _get_builder(self, query, *args):
		res = self.db.get(query, *args)

		if res:
			return Builder(self.backend, res.id, data=res)

	def _get_builders(self, query, *args):
		res = self.db.query(query, *args)

		for row in res:
			yield Builder(self.backend, row.id, data=row)

	def __iter__(self):
		builders = self._get_builders("SELECT * FROM builders \
			WHERE deleted IS FALSE ORDER BY name")

		return iter(builders)

	def create(self, name, user=None, log=True):
		"""
			Creates a new builder.
		"""
		builder = self._get_builder("INSERT INTO builders(name) \
			VALUES(%s) RETURNING *", name)

		# Generate a new passphrase.
		passphrase = builder.regenerate_passphrase()

		# Log what we have done.
		if log:
			builder.log("created", user=user)

		# The Builder object and the passphrase are returned.
		return builder, passphrase

	def auth(self, name, passphrase):
		# If either name or passphrase is None, we don't check at all.
		if None in (name, passphrase):
			return

		# Search for the hostname in the database.
		builder = self._get_builder("SELECT * FROM builders \
			WHERE name = %s AND deleted IS FALSE", name)

		# If the builder was not found or the passphrase does not match,
		# you have bad luck.
		if not builder or not builder.validate_passphrase(passphrase):
			return

		# Otherwise we return the Builder object.
		return builder

	def get_by_id(self, builder_id):
		return self._get_builder("SELECT * FROM builders WHERE id = %s", builder_id)

	def get_by_name(self, name):
		return self._get_builder("SELECT * FROM builders \
			WHERE name = %s AND deleted IS FALSE", name)

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

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.id == other.id

	def __lt__(self, other):
		if isinstance(other, self.__class__):
			return self.name < other.name

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
		# Generate a random string with 40 chars.
		passphrase = generate_random_string(length=40)

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

	def set_enabled(self, enabled):
		self._set_attribute("enabled", enabled)

	enabled = property(lambda s: s.data.enabled, set_enabled)

	@property
	def disabled(self):
		return not self.enabled

	@property
	def native_arch(self):
		"""
			The native architecture of this builder
		"""
		return self.cpu_arch

	@lazy_property
	def supported_arches(self):
		# Every builder supports noarch
		arches = ["noarch"]

		# We can always build our native architeture
		if self.native_arch:
			arches.append(self.native_arch)

			# Get all compatible architectures
			res = self.db.query("SELECT build_arch FROM arches_compat \
				WHERE native_arch = %s", self.native_arch)

			for row in res:
				if not row.build_arch in arches:
					arches.append(row.build_arch)

		return sorted(arches)

	def set_testmode(self, testmode):
		self._set_attribute("testmode", testmode)

	testmode = property(lambda s: s.data.testmode, set_testmode)

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
	def active_jobs(self):
		jobs = self.backend.jobs._get_jobs("SELECT jobs.* FROM jobs \
			WHERE time_started IS NOT NULL AND time_finished IS NULL \
			AND builder_id = %s ORDER BY time_started", self.id)

		return list(jobs)

	@property
	def too_many_jobs(self):
		"""
			Tell if this host is already running enough or too many jobs.
		"""
		return len(self.active_jobs) >= self.max_jobs

	@lazy_property
	def jobqueue(self):
		return self.backend.jobqueue.for_arches(self.supported_arches)

	def get_next_job(self):
		"""
			Returns the next job in line for this builder.
		"""
		# Don't send any jobs to disabled builders
		if not self.enabled:
			return

		# Don't return anything if the builder has already too many jobs running
		if self.too_many_jobs:
			return

		for job in self.jobqueue:
			# Only allow building test jobs in test mode
			if self.testmode and not job.test:
				continue

			return job

	def get_history(self, *args, **kwargs):
		kwargs["builder"] = self

		return self.pakfire.builders.get_history(*args, **kwargs)
