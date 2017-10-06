#!/usr/bin/python

from .. import scheduler

class Event(scheduler.Event):
	def __init__(self, pakfire, *args, **kwargs):
		scheduler.Event.__init__(self, *args, **kwargs)

		self.pakfire = pakfire

	@property
	def db(self):
		return self.pakfire.db
