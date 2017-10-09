#!/usr/bin/python

import datetime
import logging
import os
import subprocess

from . import base
from . import database
from . import git

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

	def get_pending_commits(self, limit=None):
		query = "SELECT id FROM sources_commits WHERE state = 'pending' ORDER BY id ASC"
		args = []

		if limit:
			query += " LIMIT %s"
			args.append(limit)

		rows = self.db.query(query, *args)

		commits = []
		for row in rows:
			commit = Commit(self.pakfire, row.id)
			commits.append(commit)

		return commits

	def get_commit_by_id(self, commit_id):
		commit = self.db.get("SELECT id FROM sources_commits WHERE id = %s", commit_id)

		if commit:
			return Commit(self.pakfire, commit.id)

	def pull(self):
		for source in self:
			repo = git.Repo(self.backend, source, mode="mirror")

			# If the repository is not yet cloned, we need to make a local
			# clone to work with.
			if not repo.cloned:
				repo.clone()

			# Otherwise we just fetch updates.
			else:
				repo.fetch()

			# Import all new revisions.
			repo.import_revisions()


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
			revision, author, committer, subject, body, date) VALUES(%s, %s, %s, %s, %s, %s, %s)",
			self.id, revision, author, committer, subject, body, date)

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
		return self.backend.sources._get_commit("SELECT id FROM sources_commits \
			WHERE source_id = %s ORDER BY id DESC LIMIT 1", self.id)

	def get_commits(self, limit=None, offset=None):
		return self.backend.sources._get_commits("SELECT id FROM sources_commits \
			WHERE source_id = %s ORDER BY id DESC LIMIT %s OFFSET %s", limit, offset)

	def get_commit(self, revision):
		commit = self.backend.sources._get_commit("SELECT id FROM sources_commits \
			WHERE source_id = %s AND revision = %s", self.id, revision)

		if commit:
			commit.source = self
			return commit
