#!/usr/bin/python

import time

from . import base
from . import cache

class Settings(base.Object):
	def __init__(self, pakfire):
		base.Object.__init__(self, pakfire)

		self.next_update = 0

	@property
	def data(self):
		now = time.time()

		# Update the cache if no data is available or the data
		# has timed out.
		if not hasattr(self, "_data") or now >= self.next_update:
			self._data = self.fetch_everything()
			self.next_update = now + 300

		return self._data

	def fetch_everything(self):
		res = self.db.query("SELECT k, v FROM settings")

		ret = {}
		for row in res:
			ret[row.k] = row.v

		return ret

	def get(self, key, default=None):
		try:
			return self.data[key]
		except KeyError:
			return default

	def get_int(self, key, default=None):
		value = self.get(key, default)

		try:
			return int(value)
		except ValueError:
			return None

	def get_float(self, key, default=None):
		value = self.get(key, default)

		try:
			return float(value)
		except ValueError:
			return None

	def set(self, key, value):
		self.db.execute("REPLACE INTO settings(k, v) VALUES(%s, %s)", key, value)

		if hasattr(self, "_data"):
			self._data[key] = value
