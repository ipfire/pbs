#!/usr/bin/python

import base

class MessagesSendEvent(base.Event):
	# Emails should be sent out as quickly as possible.
	priority = 0

	@property
	def interval(self):
		return self.pakfire.settings.get_int("messages_interval", 10)

	def run(self):
		for msg in self.pakfire.messages.get_all():
			try:
				self.pakfire.messages.send_msg(msg)

			except:
				continue

			# If everything was okay, we can delete the message in the database.
			self.pakfire.messages.delete(msg.id)
