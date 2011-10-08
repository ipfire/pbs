#!/usr/bin/python

import database
import settings
import uploads

from build import Builds
from builders import Builders
from distribution import Distributions
from messages import Messages
from packages import Packages
from repository import Repositories
from sources import Sources
from users import Users

# Database access.
MYSQL_SERVER = "mysql.ipfire.org"
MYSQL_USER   = "pakfire"
MYSQL_DB     = "pakfire"

class Pakfire(object):
	def __init__(self):
		self.db = database.Connection(MYSQL_SERVER, MYSQL_DB, user=MYSQL_USER)

		# Global pakfire settings (from database).
		self.settings = settings.Settings(self)

		self.builds = Builds(self)
		self.builders = Builders(self)
		self.distros = Distributions(self)
		self.messages = Messages(self)
		self.packages = Packages(self)
		self.repos = Repositories(self)
		self.sources = Sources(self)
		self.uploads = uploads.Uploads(self)
		self.users = Users(self)

	def __del__(self):
		if self.db:
			self.db.close()
			del self.db

	def logger(self, message, text=None, build=None, pkg=None):
		if not build and not pkg:
			raise Exception, "need to give at least one parameter for log"

		log_id = self.db.execute("INSERT INTO `log`(message, text) VALUES(%s, %s)", message, text)

		query = "UPDATE `log` SET %s = %%s WHERE id = %%s"

		if build:
			self.db.execute(query % "build_id", build.id, log_id)

			if build.host:
				self.db.execute(query % "host_id", build.host.id, log_id)

			pkg = getattr(build, "pkg", None)

		if pkg:
			self.db.execute(query % "pkg_id", pkg.id, log_id)
			self.db.execute(query % "source_id", pkg.source.id, log_id)

		return log_id

	@property
	def log(self, limit=100):
		return self.db.query("SELECT * FROM log ORDER BY time DESC LIMIT %s", limit)
