#!/usr/bin/python

from .decorators import *

class Object(object):
	"""
		Main object where all other objects inherit from.
		
		This is used to access the global instance of Pakfire
		and hold the database connection.
	"""
	def __init__(self, pakfire, *args, **kwargs):
		self.pakfire = pakfire

		# Shortcut to the database.
		self.db = self.pakfire.db

		# Shortcut to settings.
		if hasattr(self.pakfire, "settings"):
			self.settings = self.pakfire.settings

		# Private cache.
		self._cache = None

		# Call custom constructor
		self.init(*args, **kwargs)

	def init(self, *args, **kwargs):
		"""
			Custom constructor to be overwritten by inheriting class
		"""
		pass

	@property
	def cache(self):
		"""
			Shortcut to the cache.
		"""
		if self._cache:
			return self._cache

		return self.pakfire.cache

	@property
	def geoip(self):
		return self.pakfire.geoip


class DataObject(Object):
	# Table name
	table = None

	def init(self, id, data=None):
		self.id = id

		if data:
			self.data = data

	@lazy_property
	def data(self):
		assert self.table, "Table name is not set"
		assert self.id

		return self.db.get("SELECT * FROM %s \
			WHERE id = %%s" % self.table, self.id)

	def _set_attribute(self, key, val):
		# Detect if an update is needed
		if self.data[key] == val:
			return

		self.db.execute("UPDATE %s SET %s = %%s \
			WHERE id = %%s" % (self.table, key), val, self.id)

		# Update the cached attribute
		self.data[key] = val
