#!/usr/bin/python


class Object(object):
	"""
		Main object where all other objects inherit from.
		
		This is used to access the global instance of Pakfire
		and hold the database connection.
	"""
	def __init__(self, pakfire):
		self.pakfire = pakfire

		# Shortcut to the database.
		self.db = self.pakfire.db

		# Shortcut to settings.
		if hasattr(self.pakfire, "settings"):
			self.settings = self.pakfire.settings
