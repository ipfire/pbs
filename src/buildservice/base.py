#!/usr/bin/python

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
