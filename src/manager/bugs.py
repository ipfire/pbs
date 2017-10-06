#!/usr/bin/python

import logging

import base

class BugsUpdateEvent(base.Event):
	# User feedback gets a high priority.
	priority = 1

	@property
	def interval(self):
		return self.pakfire.settings.get_int("bugzilla_update_interval", 60)

	def run(self):
		# Get up to ten updates.
		query = self.db.query("SELECT * FROM builds_bugs_updates \
			WHERE error = 'N' ORDER BY time")

		# XXX CHECK IF BZ IS ACTUALLY REACHABLE AND WORKING

		for update in query:
			try:
				bug = self.pakfire.bugzilla.get_bug(update.bug_id)
				if not bug:
					logging.error("Bug #%s does not exist." % update.bug_id)
					continue

				# Set the changes.
				bug.set_status(update.status, update.resolution, update.comment)

			except Exception, e:
				# If there was an error, we save that and go on.
				self.db.execute("UPDATE builds_bugs_updates SET error = 'Y', error_msg = %s \
					WHERE id = %s", "%s" % e, update.id)

			else:
				# Remove the update when it has been done successfully.
				self.db.execute("DELETE FROM builds_bugs_updates WHERE id = %s", update.id)
