#!/usr/bin/python

import datetime
import logging
import os
import pakfire
import pakfire.config
import shutil
import subprocess
import tempfile

from . import base
from . import database
from . import git

from .constants import *
from .decorators import *

class Sources(base.Object):
	def _get_source(self, query, *args):
		res = self.db.get(query, *args)

		if res:
			return Source(self.backend, res.id, data=res)

	def _get_sources(self, query, *args):
		res = self.db.query(query, *args)

		for row in res:
			yield Source(self.backend, row.id, data=row)

	def _get_commit(self, query, *args):
		res = self.db.get(query, *args)

		if res:
			return Commit(self.backend, res.id, data=res)

	def _get_commits(self, query, *args):
		res = self.db.query(query, *args)

		for row in res:
			yield Commit(self.backend, row.id, data=row)

	def __iter__(self):
		return self._get_sources("SELECT * FROM sources")

	def get_by_id(self, id):
		return self._get_source("SELECT * FROM sources \
			WHERE id = %s", id)

	def get_by_distro(self, distro):
		return self._get_sources("SELECT * FROM sources \
			WHERE distro_id = %s", distro.id)

	def update_revision(self, source_id, revision):
		query = "UPDATE sources SET revision = %s WHERE id = %s"

		return self.db.execute(query, revision, source_id)

	def get_commit_by_id(self, commit_id):
		commit = self.db.get("SELECT id FROM sources_commits WHERE id = %s", commit_id)

		if commit:
			return Commit(self.pakfire, commit.id)

	def pull(self):
		for source in self:
			with git.Repo(self.backend, source, mode="mirror") as repo:
				# Fetch the latest updates
				repo.fetch()

				# Import all new revisions
				repo.import_revisions()

	def dist(self):
		# Walk through all source repositories
		for source in self:
			# Get access to the git repo
			with git.Repo(self.pakfire, source) as repo:
				# Walk through all pending commits
				for commit in source.pending_commits:
					commit.state = "running"

					logging.debug("Processing commit %s: %s" % (commit.revision, commit.subject))

					# Navigate to the right revision.
					repo.checkout(commit.revision)

					# Get all changed makefiles.
					deleted_files = []
					updated_files = []

					for file in repo.changed_files(commit.revision):
						# Don't care about files that are not a makefile.
						if not file.endswith(".%s" % MAKEFILE_EXTENSION):
							continue

						if os.path.exists(file):
							updated_files.append(file)
						else:
							deleted_files.append(file)

						if updated_files:
							# Create a temporary directory where to put all the files
							# that are generated here.
							pkg_dir = tempfile.mkdtemp()

							try:
								config = pakfire.config.Config(["general.conf",])
								config.parse(source.distro.get_config())

								p = pakfire.PakfireServer(config=config)

								pkgs = []
								for file in updated_files:
									try:
										pkg_file = p.dist(file, pkg_dir)
										pkgs.append(pkg_file)
									except:
										raise

								# Import all packages in one swoop.
								for pkg in pkgs:
									# Import the package file and create a build out of it.
									from . import builds
									builds.import_from_package(_pakfire, pkg,
										distro=source.distro, commit=commit, type="release")

							except:
								if commit:
									commit.state = "failed"

								raise

							finally:
								if os.path.exists(pkg_dir):
									shutil.rmtree(pkg_dir)

						for file in deleted_files:
							# Determine the name of the package.
							name = os.path.basename(file)
							name = name[:len(MAKEFILE_EXTENSION) + 1]

							source.distro.delete_package(name)

						if commit:
							commit.state = "finished"


class Commit(base.DataObject):
	table = "sources_commits"

	@property
	def revision(self):
		return self.data.revision

	@lazy_property
	def source(self):
		return self.backend.sources.get_by_id(self.data.source_id)

	@property
	def distro(self):
		"""
			A shortcut to the distribution this commit
			belongs to.
		"""
		return self.source.distro

	def set_state(self, state):
		self._set_attribute("state", state)

	state = property(lambda s: s.data.state, set_state)

	@property
	def author(self):
		return self.data.author

	@property
	def committer(self):
		return self.data.committer

	@property
	def subject(self):
		return self.data.subject.strip()

	@property
	def message(self):
		return self.data.body.strip()

	@property
	def message_full(self):
		msg = [self.subject, ""] + self.message.splitlines()

		return "\n".join(msg)

	@property
	def date(self):
		return self.data.date

	@lazy_property
	def packages(self):
		return self.backend.packages._get_packages("SELECT * FROM packages \
			WHERE commit_id = %s", self.id)

	def reset(self):
		"""
			Removes all packages that have been created by this commit and
			resets the state so it will be processed again.
		"""
		# Remove all packages and corresponding builds.
		for pkg in self.packages:
			# Check if there is a build associated with the package.
			# If so, the whole build will be deleted.
			if pkg.build:
				pkg.build.delete()

			else:
				# Delete the package.
				pkg.delete()

		# Clear the cache.
		del self.packages

		# Reset the state to 'pending'.
		self.state = "pending"


class Source(base.DataObject):
	table = "sources"

	def __eq__(self, other):
		return self.id == other.id

	def __len__(self):
		ret = self.db.get("SELECT COUNT(*) AS len FROM sources_commits \
			WHERE source_id = %s", self.id)

		return ret.len

	def create_commit(self, revision, author, committer, subject, body, date):
		commit = self.backend.sources._get_commit("INSERT INTO sources_commits(source_id, \
			revision, author, committer, subject, body, date) VALUES(%s, %s, %s, %s, %s, %s, %s) \
			RETURNING *", self.id, revision, author, committer, subject, body, date)

		# Commit
		commit.source = self

		return commit

	@property
	def info(self):
		return {
			"id"         : self.id,
			"name"       : self.name,
			"url"        : self.url,
			"path"       : self.path,
			"targetpath" : self.targetpath,
			"revision"   : self.revision,
			"branch"     : self.branch,
		}

	@property
	def name(self):
		return self.data.name

	@property
	def identifier(self):
		return self.data.identifier

	@property
	def url(self):
		return self.data.url

	@property
	def gitweb(self):
		return self.data.gitweb

	@property
	def revision(self):
		return self.data.revision

	@property
	def branch(self):
		return self.data.branch

	@property
	def builds(self):
		return self.pakfire.builds.get_by_source(self.id)

	@lazy_property
	def distro(self):
		return self.pakfire.distros.get_by_id(self.data.distro_id)

	@property
	def start_revision(self):
		return self.data.revision

	@lazy_property
	def head_revision(self):
		return self.backend.sources._get_commit("SELECT * FROM sources_commits \
			WHERE source_id = %s ORDER BY id DESC LIMIT 1", self.id)

	def get_commits(self, limit=None, offset=None):
		return self.backend.sources._get_commits("SELECT * FROM sources_commits \
			WHERE source_id = %s ORDER BY id DESC LIMIT %s OFFSET %s", limit, offset)

	def get_commit(self, revision):
		commit = self.backend.sources._get_commit("SELECT * FROM sources_commits \
			WHERE source_id = %s AND revision = %s", self.id, revision)

		if commit:
			commit.source = self
			return commit

	@property
	def pending_commits(self):
		return self.backend.sources._get_commits("SELECT * FROM sources_commits \
			WHERE state = %s ORDER BY imported_at", "pending")
