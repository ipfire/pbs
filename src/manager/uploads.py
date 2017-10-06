#!/usr/bin/python

from . import base

class UploadsCleanupEvent(base.Event):
	interval = 3600

	# Rather unimportant when this runs.
	priority = 10

	def run(self):
		self.pakfire.uploads.cleanup()
