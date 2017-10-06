#!/usr/bin/python

from . import base

class SessionsCleanupEvent(base.Event):
	"""
		Cleans up sessions that are not valid anymore.
		Keeps the database smaller.
	"""
	# Run once in an hour.
	interval = 3600

	# Rather unimportant when this runs.
	priority = 10

	def run(self):
		self.pakfire.sessions.cleanup()
