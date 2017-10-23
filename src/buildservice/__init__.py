#!/usr/bin/python

from __future__ import absolute_import

import ConfigParser
import logging
import os
import pakfire

from . import arches
from . import bugtracker
from . import builders
from . import builds
from . import cache
from . import database
from . import distribution
from . import geoip
from . import jobqueue
from . import jobs
from . import keys
from . import logs
from . import messages
from . import mirrors
from . import packages
from . import repository
from . import settings
from . import sessions
from . import sources
from . import updates
from . import uploads
from . import users

log = logging.getLogger("backend")
log.propagate = 1

# Import version
from .__version__ import VERSION as __version__

from .decorators import *
from .constants import *

class Backend(object):
	def __init__(self, config_file=None):
		# Read configuration file.
		self.config = self.read_config(config_file)

		# Global pakfire settings (from database).
		self.settings = settings.Settings(self)

		self.arches      = arches.Arches(self)
		self.builds      = builds.Builds(self)
		self.cache       = cache.Cache(self)
		self.geoip       = geoip.GeoIP(self)
		self.jobs        = jobs.Jobs(self)
		self.builders    = builders.Builders(self)
		self.distros     = distribution.Distributions(self)
		self.jobqueue    = jobqueue.JobQueue(self)
		self.keys        = keys.Keys(self)
		self.messages    = messages.Messages(self)
		self.mirrors     = mirrors.Mirrors(self)
		self.packages    = packages.Packages(self)
		self.repos       = repository.Repositories(self)
		self.sessions    = sessions.Sessions(self)
		self.sources     = sources.Sources(self)
		self.updates     = updates.Updates(self)
		self.uploads     = uploads.Uploads(self)
		self.users       = users.Users(self)

		# Open a connection to bugzilla.
		self.bugzilla    = bugtracker.Bugzilla(self)

		# A pool to store strings (for comparison).
		self.pool        = pakfire.satsolver.Pool("dummy")

	@lazy_property
	def _environment_configuration(self):
		env = {}

		# Get database configuration
		env["database"] = {
			"name"     : os.environ.get("PBS_DATABASE_NAME"),
			"hostname" : os.environ.get("PBS_DATABASE_HOSTNAME"),
			"user"     : os.environ.get("PBS_DATABASE_USER"),
			"password" : os.environ.get("PBS_DATABASE_PASSWORD"),
		}

		return env

	def read_config(self, path):
		c = ConfigParser.SafeConfigParser()

		# Import configuration from environment
		for section in self._environment_configuration:
			c.add_section(section)

			for k in self._environment_configuration[section]:
				c.set(section, k, self._environment_configuration[section][k] or "")

		# Load default configuration file first
		paths = [
			os.path.join(CONFIGSDIR, "pbs.conf"),
		]

		if path:
			paths.append(path)

		# Load all configuration files
		for path in paths:
			if os.path.exists(path):
				log.debug("Loading configuration from %s" % path)
				c.read(path)
			else:
				log.error("No such file %s" % path)

		return c

	@lazy_property
	def db(self):
		try:
			name     = self.config.get("database", "name")
			hostname = self.config.get("database", "hostname")
			user     = self.config.get("database", "user")
			password = self.config.get("database", "password")
		except ConfigParser.Error as e:
			log.error("Error parsing the config: %s" % e.message)

		log.debug("Connecting to database %s @ %s" % (name, hostname))

		return database.Connection(hostname, name, user=user, password=password)

	def delete_file(self, path, not_before=None):
		self.db.execute("INSERT INTO queue_delete(path, not_before) \
			VALUES(%s, %s)", path, not_before)

	def cleanup_files(self):
		query = self.db.query("SELECT * FROM queue_delete \
			WHERE (not_before IS NULL OR not_before <= NOW())")

		for row in query:
			if not row.path:
				continue

			path = row.path
			if not path.startswith("/"):
				path = os.path.join(PACKAGES_DIR, path)

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
