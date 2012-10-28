#!/usr/bin/python

import logging
import os
import pakfire

import arches
import bugtracker
import builders
import builds
import cache
import database
import distribution
import keys
import logs
import messages
import mirrors
import packages
import repository
import settings
import sources
import updates
import uploads
import users

from constants import *

# Database access.
MYSQL_SERVER   = "mysql-master.ipfire.org"
MYSQL_USER     = "pakfire"
MYSQL_DB       = "pakfire"
MYSQL_GEOIP_DB = "geoip"

class Pakfire(object):
	def __init__(self):
		self.db = database.Connection(MYSQL_SERVER, MYSQL_DB, user=MYSQL_USER)

		# Global pakfire settings (from database).
		self.settings = settings.Settings(self)

		self.arches      = arches.Arches(self)
		self.builds      = builds.Builds(self)
		self.cache       = cache.Cache(self)
		self.geoip       = mirrors.GeoIP(self, MYSQL_SERVER, MYSQL_GEOIP_DB,
								user=MYSQL_USER)
		self.jobs        = builds.Jobs(self)
		self.builders    = builders.Builders(self)
		self.distros     = distribution.Distributions(self)
		self.keys        = keys.Keys(self)
		self.messages    = messages.Messages(self)
		self.mirrors     = mirrors.Mirrors(self)
		self.packages    = packages.Packages(self)
		self.repos       = repository.Repositories(self)
		self.sources     = sources.Sources(self)
		self.updates     = updates.Updates(self)
		self.uploads     = uploads.Uploads(self)
		self.users       = users.Users(self)

		# Open a connection to bugzilla.
		self.bugzilla    = bugtracker.Bugzilla(self)

		# A pool to store strings (for comparison).
		self.pool        = pakfire.satsolver.Pool("dummy")

	def __del__(self):
		if self.db:
			self.db.close()
			del self.db

	def cleanup_files(self):
		query = self.db.query("SELECT * FROM queue_delete")

		for row in query:
			if not row.path:
				continue

			path = os.path.join(PACKAGES_DIR, row.path)

			try:
				logging.debug("Removing %s..." % path)
				os.unlink(path)
			except OSError, e:
				logging.error("Could not remove %s: %s" % (path, e))

			while True:			
				path = os.path.dirname(path)

				# Stop if we are running outside of the tree.
				if not path.startswith(PACKAGES_DIR):
					break

				# If the directory is not empty, we cannot remove it.
				if os.path.exists(path) and os.listdir(path):
					break

				try:
					logging.debug("Removing %s..." % path)
					os.rmdir(path)
				except OSError, e:
					logging.error("Could not remove %s: %s" % (path, e))
					break

			self.db.execute("DELETE FROM queue_delete WHERE id = %s", row.id)
