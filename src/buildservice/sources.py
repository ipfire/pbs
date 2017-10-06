#!/usr/bin/python

import datetime
import logging
import os
import subprocess

from . import base
from . import database

class Sources(base.Object):
	def get_all(self):
		sources = self.db.query("SELECT id FROM sources ORDER BY id")

		return [Source(self.pakfire, s.id) for s in sources]

	def get_by_id(self, id):
		return Source(self.pakfire, id)

	def get_by_distro(self, distro):
		sources = self.db.query("SELECT id FROM sources WHERE distro_id = %s", distro.id)

		return [Source(self.pakfire, s.id) for s in sources]

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


class Commit(base.Object):
	def __init__(self, pakfire, id):
		base.Object.__init__(self, pakfire)

		self.id = id

		# Cache.
		self._data = None
		self._source = None
		self._packages = None

	@classmethod
	def create(cls, pakfire, source, revision, author, committer, subject, body, date):
		try:
			id = pakfire.db.execute("INSERT INTO sources_commits(source_id, revision, \
				author, committer, subject, body, date) VALUES(%s, %s, %s, %s, %s, %s, %s)",
				source.id, revision, author, committer, subject, body, date)
		except database.IntegrityError:
			# If the commit (apperently) already existed, we return nothing.
			return

		return cls(pakfire, id)

	@property
	def data(self):
		if self._data is None:
			data = self.db.get("SELECT * FROM sources_commits WHERE id = %s", self.id)

			self._data = data
			assert self._data

		return self._data

	@property
	def revision(self):
		return self.data.revision

	@property
	def source_id(self):
		return self.data.source_id

	@property
	def source(self):
		if self._source is None:
			self._source = Source(self.pakfire, self.source_id)

		return self._source

	@property
	def distro(self):
		"""
			A shortcut to the distribution this commit
			belongs to.
		"""
		return self.source.distro

	def get_state(self):
		return self.data.state

	def set_state(self, state):
		self.db.execute("UPDATE sources_commits SET state = %s WHERE id = %s",
			state, self.id)

		if self._data:
			self._data["state"] = state

	state = property(get_state, set_state)

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

	@property
	def packages(self):
		if self._packages is None:
			self._packages = []

			for pkg in self.db.query("SELECT id FROM packages WHERE commit_id = %s", self.id):
				pkg = self.pakfire.packages.get_by_id(pkg.id)
				self._packages.append(pkg)

			self._packages.sort()

		return self._packages

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
		self._packages = None

		# Reset the state to 'pending'.
		self.state = "pending"


class Source(base.Object):
	def __init__(self, pakfire, id):
		base.Object.__init__(self, pakfire)

		self.id = id

		self._data = None
		self._head_revision = None

	@property
	def data(self):
		if self._data is None:
			data = self.db.get("SELECT * FROM sources WHERE id = %s", self.id)

			self._data = data
			assert self._data

		return self._data

	def __cmp__(self, other):
		return cmp(self.id, other.id)

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

	def _import_revision(self, revision):
		logging.debug("Going to import revision: %s" % revision)

		rev_author    = self._git("log -1 --format=\"%%an <%%ae>\" %s" % revision)
		rev_committer = self._git("log -1 --format=\"%%cn <%%ce>\" %s" % revision)
		rev_subject   = self._git("log -1 --format=\"%%s\" %s" % revision)
		rev_body      = self._git("log -1 --format=\"%%b\" %s" % revision)
		rev_date      = self._git("log -1 --format=\"%%at\" %s" % revision)
		rev_date      = datetime.datetime.utcfromtimestamp(float(rev_date))

		# Convert strings properly. No idea why I have to do that.
		rev_author    = rev_author.decode("latin-1").strip()
		rev_committer = rev_committer.decode("latin-1").strip()
		rev_subject   = rev_subject.decode("latin-1").strip()
		rev_body      = rev_body.decode("latin-1").rstrip()

		# Create a new source build object.
		build.SourceBuild.new(self.pakfire, self.id, revision, rev_author,
			rev_committer, rev_subject, rev_body, rev_date)

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

	@property
	def distro(self):
		return self.pakfire.distros.get_by_id(self.data.distro_id)

	@property
	def start_revision(self):
		return self.data.revision

	@property
	def head_revision(self):
		if self._head_revision is None:
			commit = self.db.get("SELECT id FROM sources_commits \
				WHERE source_id = %s ORDER BY id DESC LIMIT 1", self.id)

			if commit:
				self._head_revision = Commit(self.pakfire, commit.id)

		return self._head_revision

	@property
	def num_commits(self):
		ret = self.db.get("SELECT COUNT(*) AS num FROM sources_commits \
			WHERE source_id = %s", self.id)

		return ret.num

	def get_commits(self, limit=None, offset=None):
		query = "SELECT id FROM sources_commits WHERE source_id = %s \
			ORDER BY id DESC"
		args = [self.id,]

		if limit:
			if offset:
				query += " LIMIT %s,%s"
				args += [offset, limit]
			else:
				query += " LIMIT %s"
				args += [limit,]

		commits = []
		for commit in self.db.query(query, *args):
			commit = Commit(self.pakfire, commit.id)
			commits.append(commit)

		return commits

	def get_commit(self, revision):
		commit = self.db.get("SELECT id FROM sources_commits WHERE source_id = %s \
			AND revision = %s LIMIT 1", self.id, revision)

		if not commit:
			return

		commit = Commit(self.pakfire, commit.id)
		commit._source = self

		return commit
