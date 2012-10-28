#!/usr/bin/python

import base

class Settings(base.Object):
	"""
		The cache is not available here.
	"""

	def query(self, key):
		return self.db.get("SELECT * FROM settings WHERE k = %s", key)

	def get(self, key, default=None):
		result = self.query(key)
		if not result:
			return default

		return "%s" % result.v

	def get_id(self, key):
		return self.query(key)["id"]

	def get_int(self, key, default=None):
		value = self.get(key, default)

		if value is None:
			return None

		return int(value)

	def get_float(self, key, default=None):
		value = self.get(key, default)

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
