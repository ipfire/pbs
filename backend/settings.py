#!/usr/bin/python

import base
import cache

class Settings(base.Object):
	def __init__(self, pakfire):
		base.Object.__init__(self, pakfire)

		# Private cache.
		self._cache = cache.PermanentCache(self.pakfire)

	def query(self, key):
		return self.db.get("SELECT * FROM settings WHERE k = %s", key)

	def get(self, key, default=None, cacheable=True):
		if cacheable and self.cache.has_key(key):
			return self.cache.get(key)

		result = self.query(key)
		if not result:
			return default

		result = result.v

		# Put the item into the cache to access it later.
		if cacheable:
			self.cache.set(key, result)

		return result

	def get_id(self, key):
		return self.query(key)["id"]

	def get_int(self, key, default=None, cacheable=True):
		value = self.get(key, default, cacheable=cacheable)

		if value is None:
			return None

		return int(value)

	def get_float(self, key, default=None, cacheable=True):
		value = self.get(key, default, cacheable=cacheable)

		if value is None:
			return None

		return float(value)

	def set(self, key, value):
		id = self.get(key)

		if not id:
			self.db.execute("INSERT INTO settings(k, v) VALUES(%s, %s)", key, value)
		else:
			self.db.execute("UPDATE settings SET v = %s WHERE id = %s", value, id)

	def get_all(self):
		attrs = {}

		for s in self.db.query("SELECT * FROM settings"):
			attrs[s.k] = s.v

		return attrs
