#!/usr/bin/python

import ConfigParser
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

class Pakfire(object):
	def __init__(self, config_file):
		# Read configuration file.
		self.config = self.read_config(config_file)

		# Connect to databases.
		self.db = self.connect_database()
		self.geoip_db = self.connect_database("geoip-database")

		# Global pakfire settings (from database).
		self.settings = settings.Settings(self)

		self.arches      = arches.Arches(self)
		self.builds      = builds.Builds(self)
		self.cache       = cache.Cache(self)
		self.geoip       = mirrors.GeoIP(self)
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

	def read_config(self, path):
		c = ConfigParser.SafeConfigParser()
		c.read(path)

		return c

	def connect_database(self, section="database"):
		db = self.config.get(section, "db")
		host = self.config.get(section, "host")
		user = self.config.get(section, "user")

		if self.config.has_option(section, "pass"):
			pw = self.config.get(section, "pass")
		else:
			pw = None

		return database.Connection(host, db, user=user, password=pw)

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
