#!/usr/bin/python

from . import base

class Settings(base.Object):
	def get(self, key, default=None):
		res = self.db.get("SELECT v FROM settings WHERE k = %s", key)
		if res:
			return res.v

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
		self.db.execute("INSERT INTO settings(k, v) VALUES(%s, %s) \
			ON CONFLICT (k) DO UPDATE v = excluded.v WHERE k = excluded.k",
			key, value)