#!/usr/bin/python

import datetime
import logging
import math
import socket
import time
import tornado.httpclient
import urlparse

from . import base
from . import logs

log = logging.getLogger("mirrors")
log.propagate = 1

from .decorators import lazy_property

class Mirrors(base.Object):
	def __iter__(self):
		res = self.db.query("SELECT * FROM mirrors \
			WHERE deleted IS FALSE ORDER BY hostname")

		mirrors = []
		for row in res:
			mirror = Mirror(self.backend, row.id, data=row)
			mirrors.append(mirror)

		return iter(mirrors)

	def _get_mirror(self, query, *args):
		res = self.db.get(query, *args)

		if res:
			return Mirror(self.backend, res.id, data=res)

	def create(self, hostname, path="", owner=None, contact=None, user=None):
		mirror = self._get_mirror("INSERT INTO mirrors(hostname, path, owner, contact) \
			VALUES(%s, %s, %s, %s) RETURNING *", hostname, path, owner, contact)

		# Log creation
		mirror.log("created", user=user)

		return mirror

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
		return self._get_mirror("SELECT * FROM mirrors WHERE id = %s", id)

	def get_by_hostname(self, hostname):
		return self._get_mirror("SELECT * FROM mirrors \
			WHERE hostname = %s AND deleted IS FALSE", hostname)

	def get_for_location(self, address):
		country_code = self.backend.geoip.guess_from_address(address)

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

	def check(self, **kwargs):
		"""
			Runs the mirror check for all mirrors
		"""
		for mirror in self:
			with self.db.transaction():
				mirror.check(**kwargs)


class Mirror(base.DataObject):
	table = "mirrors"

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.id == other.id

	def log(self, action, user=None):
		user_id = None
		if user:
			user_id = user.id

		self.db.execute("INSERT INTO mirrors_history(mirror_id, action, user_id, time) \
			VALUES(%s, %s, %s, NOW())", self.id, action, user_id)

	def set_hostname(self, hostname):
		self._set_attribute("hostname", hostname)

	hostname = property(lambda self: self.data.hostname, set_hostname)

	@property
	def path(self):
		return self.data.path

	def set_path(self, path):
		self._set_attribute("path", path)

	path = property(lambda self: self.data.path, set_path)

	@property
	def url(self):
		return self.make_url()

	def make_url(self, path=""):
		url = "http://%s%s" % (self.hostname, self.path)

		if path.startswith("/"):
			path = path[1:]

		return urlparse.urljoin(url, path)

	def set_owner(self, owner):
		self._set_attribute("owner", owner)

	owner = property(lambda self: self.data.owner or "", set_owner)

	def set_contact(self, contact):
		self._set_attribute("contact", contact)

	contact = property(lambda self: self.data.contact or "", set_contact)

	def check(self, connect_timeout=10, request_timeout=10):
		log.info("Running mirror check for %s" % self.hostname)

		client = tornado.httpclient.HTTPClient()

		# Get URL for .timestamp
		url = self.make_url(".timestamp")
		log.debug("  Fetching %s..." % url)

		# Record start time
		time_start = time.time()

		http_status = None
		last_sync_at = None
		status = "OK"

		# XXX needs to catch connection resets, DNS errors, etc.

		try:
			response = client.fetch(url,
				connect_timeout=connect_timeout,
				request_timeout=request_timeout)

			# We expect the response to be an integer
			# which holds the timestamp of the last sync
			# in seconds since epoch UTC
			try:
				timestamp = int(response.body)
			except ValueError:
				raise

			# Convert to datetime
			last_sync_at = datetime.datetime.utcfromtimestamp(timestamp)

			# Must have synced within 24 hours
			now = datetime.datetime.utcnow()
			if now - last_sync_at >= datetime.timedelta(hours=24):
				status = "OUTOFSYNC"

		except tornado.httpclient.HTTPError as e:
			http_status = e.code
			status = "ERROR"

		finally:
			response_time = time.time() - time_start

		# Log check
		self.db.execute("INSERT INTO mirrors_checks(mirror_id, response_time, \
			http_status, last_sync_at, status) VALUES(%s, %s, %s, %s, %s)",
			self.id, response_time, http_status, last_sync_at, status)

	@lazy_property
	def last_check(self):
		res = self.db.get("SELECT * FROM mirrors_checks \
			WHERE mirror_id = %s ORDER BY timestamp DESC LIMIT 1", self.id)

		return res

	@property
	def status(self):
		if self.last_check:
			return self.last_check.status

	@property
	def average_response_time(self):
		res = self.db.get("SELECT AVG(response_time) AS response_time \
			FROM mirrors_checks WHERE mirror_id = %s \
				AND timestamp >= NOW() - '24 hours'::interval", self.id)

		return res.response_time

	@property
	def address(self):
		return socket.gethostbyname(self.hostname)

	@lazy_property
	def country_code(self):
		return self.backend.geoip.guess_from_address(self.address) or "UNKNOWN"

	def get_history(self, *args, **kwargs):
		kwargs["mirror"] = self

		return self.pakfire.mirrors.get_history(*args, **kwargs)
