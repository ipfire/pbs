#!/usr/bin/python

import backend.scheduler

class Event(backend.scheduler.Event):
	def __init__(self, pakfire, *args, **kwargs):
		backend.scheduler.Event.__init__(self, *args, **kwargs)

		self.pakfire = pakfire

	@property
	def db(self):
		return self.pakfire.db
