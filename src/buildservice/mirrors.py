#!/usr/bin/python

import logging
import math
import socket

from . import base
from . import logs

from .decorators import lazy_property

class Mirrors(base.Object):
	def get_all(self):
		mirrors = []

		for mirror in self.db.query("SELECT id FROM mirrors \
				WHERE NOT status = 'deleted' ORDER BY hostname"):
			mirror = Mirror(self.pakfire, mirror.id)
			mirrors.append(mirror)

		return mirrors

	def count(self, status=None):
		query = "SELECT COUNT(*) AS count FROM mirrors"
		args  = []

		if status:
			query += " WHERE status = %s"
			args.append(status)

		query = self.db.get(query, *args)

		return query.count

	def get_random(self, limit=None):
		query = "SELECT id FROM mirrors WHERE status = 'enabled' ORDER BY RAND()"
		args  = []

		if limit:
			query += " LIMIT %s"
			args.append(limit)

		mirrors = []
		for mirror in self.db.query(query, *args):
			mirror = Mirror(self.pakfire, mirror.id)
			mirrors.append(mirror)

		return mirrors

	def get_by_id(self, id):
		mirror = self.db.get("SELECT id FROM mirrors WHERE id = %s", id)
		if not mirror:
			return

		return Mirror(self.pakfire, mirror.id)

	def get_by_hostname(self, hostname):
		mirror = self.db.get("SELECT id FROM mirrors WHERE NOT status = 'deleted' \
			AND hostname = %s", hostname)

		if not mirror:
			return

		return Mirror(self.pakfire, mirror.id)

	def get_for_location(self, addr):
		country_code = self.backend.geoip.guess_from_address(addr)

		# Cannot return any good mirrors if location is unknown
		if not country_code:
			return []

		mirrors = []

		# Walk through all mirrors
		for mirror in self.get_all():
			if not mirror.enabled:
				continue

			if mirror.country_code == country_code:
				mirrors.append(mirror)

			# XXX needs to search for nearby countries

		return mirrors

	def get_history(self, limit=None, offset=None, mirror=None, user=None):
		query = "SELECT * FROM mirrors_history"
		args  = []

		conditions = []

		if mirror:
			conditions.append("mirror_id = %s")
			args.append(mirror.id)

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
			entry = logs.MirrorLogEntry(self.pakfire, entry)
			entries.append(entry)

		return entries


class Mirror(base.Object):
	def __init__(self, pakfire, id):
		base.Object.__init__(self, pakfire)

		self.id = id

		# Cache.
		self._data = None
		self._location = None

	def __cmp__(self, other):
		return cmp(self.id, other.id)

	@classmethod
	def create(cls, pakfire, hostname, path="", owner=None, contact=None, user=None):
		id = pakfire.db.execute("INSERT INTO mirrors(hostname, path, owner, contact) \
			VALUES(%s, %s, %s, %s)", hostname, path, owner, contact)

		mirror = cls(pakfire, id)
		mirror.log("created", user=user)

		return mirror

	def log(self, action, user=None):
		user_id = None
		if user:
			user_id = user.id

		self.db.execute("INSERT INTO mirrors_history(mirror_id, action, user_id, time) \
			VALUES(%s, %s, %s, NOW())", self.id, action, user_id)

	@property
	def data(self):
		if self._data is None:
			self._data = \
				self.db.get("SELECT * FROM mirrors WHERE id = %s", self.id)

		return self._data

	def set_status(self, status, user=None):
		assert status in ("enabled", "disabled", "deleted")

		if self.status == status:
			return

		self.db.execute("UPDATE mirrors SET status = %s WHERE id = %s",
			status, self.id)

		if self._data:
			self._data["status"] = status

		# Log the status change.
		self.log(status, user=user)

	def set_hostname(self, hostname):
		if self.hostname == hostname:
			return

		self.db.execute("UPDATE mirrors SET hostname = %s WHERE id = %s",
			hostname, self.id)

		if self._data:
			self._data["hostname"] = hostname

	hostname = property(lambda self: self.data.hostname, set_hostname)

	@property
	def path(self):
		return self.data.path

	def set_path(self, path):
		if self.path == path:
			return

		self.db.execute("UPDATE mirrors SET path = %s WHERE id = %s",
			path, self.id)

		if self._data:
			self._data["path"] = path

	path = property(lambda self: self.data.path, set_path)

	@property
	def url(self):
		ret = "http://%s" % self.hostname

		if self.path:
			path = self.path

			if not self.path.startswith("/"):
				path = "/%s" % path

			if self.path.endswith("/"):
				path = path[:-1]

			ret += path

		return ret

	def set_owner(self, owner):
		if self.owner == owner:
			return

		self.db.execute("UPDATE mirrors SET owner = %s WHERE id = %s",
			owner, self.id)

		if self._data:
			self._data["owner"] = owner

	owner = property(lambda self: self.data.owner or "", set_owner)

	def set_contact(self, contact):
		if self.contact == contact:
			return

		self.db.execute("UPDATE mirrors SET contact = %s WHERE id = %s",
			contact, self.id)

		if self._data:
			self._data["contact"] = contact

	contact = property(lambda self: self.data.contact or "", set_contact)

	@property
	def status(self):
		return self.data.status

	@property
	def enabled(self):
		return self.status == "enabled"

	@property
	def check_status(self):
		return self.data.check_status

	@property
	def last_check(self):
		return self.data.last_check

	@property
	def address(self):
		return socket.gethostbyname(self.hostname)

	@lazy_property
	def country_code(self):
		return self.backend.geoip.guess_from_address(self.address) or "UNKNOWN"

	def get_history(self, *args, **kwargs):
		kwargs["mirror"] = self

		return self.pakfire.mirrors.get_history(*args, **kwargs)
