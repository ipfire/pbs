#!/usr/bin/python

from .decorators import *

class Object(object):
	"""
		Main object where all other objects inherit from.
		
		This is used to access the global instance of Pakfire
		and hold the database connection.
	"""
	def __init__(self, backend, *args, **kwargs):
		self.backend = backend

		# Shortcut to settings.
		if hasattr(self.pakfire, "settings"):
			self.settings = self.backend.settings

		# Call custom constructor
		self.init(*args, **kwargs)

	def init(self, *args, **kwargs):
		"""
			Custom constructor to be overwritten by inheriting class
		"""
		pass

	@lazy_property
	def db(self):
		"""
			Shortcut to database
		"""
		return self.backend.db

	@lazy_property
	def pakfire(self):
		"""
			DEPRECATED: This attribute is only kept until
			all other code has been updated to use self.backend.
		"""
		return self.backend

	@property
	def geoip(self):
		return self.backend.geoip


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
