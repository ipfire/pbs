#!/usr/bin/python

import datetime
import logging
import os
import subprocess

import base
import build

class Sources(base.Object):
	def get_all(self):
		sources = self.db.query("SELECT id FROM sources ORDER BY id")

		return [Source(self.pakfire, s.id) for s in sources]

	def get_by_id(self, id):
		source = self.db.get("SELECT id FROM sources WHERE id = %s", id)

		if source:
			return Source(self.pakfire, source.id)

	def get_by_distro(self, distro):
		sources = self.db.query("SELECT id FROM sources WHERE distro_id = %s", distro.id)

		return [Source(self.pakfire, s.id) for s in sources]

	def update_revision(self, source_id, revision):
		query = "UPDATE sources SET revision = %s WHERE id = %s"

		return self.db.execute(query, revision, source_id)


class Source(base.Object):
	def __init__(self, pakfire, id):
		base.Object.__init__(self, pakfire)

		self.id = id

		self._data = self.db.get("SELECT * FROM sources WHERE id = %s", self.id)

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

	def _git(self, cmd, path=None):
		if not path:
			path = self.path

		cmd = "cd %s && git %s" % (path, cmd)

		logging.debug("Running command: %s" % cmd)

		return subprocess.check_output(["/bin/sh", "-c", cmd])

	def _git_rev_list(self, revision=None):
		if not revision:
			revision = self.revision

		command = "rev-list %s..origin/%s" % (revision, self.branch)

		# Get all merge commits.
		merges = self._git("%s --merges" % command)
		merges = merges.splitlines()

		revisions = []
		for commit in self._git(command).splitlines():
			# Check if commit is a normal commit or merge commit.
			merge = commit in merges

			revisions.append((commit, merge))

		return [r for r in reversed(revisions)]

	def is_cloned(self):
		"""
			Say if the repository is already cloned.
		"""
		return os.path.exists(self.path)

	def clone(self):
		if self.is_cloned():
			return

		if not os.path.exists(dirname):
			os.makedirs(dirname)

		self._git("clone --bare %s %s" % (self.url, basename), path=dirname)

	def fetch(self):
		if not self.is_cloned():
			raise Exception, "Repository was not cloned, yet."

		self._git("fetch")

	def import_revisions(self):
		# Get all pending revisions.
		revisions = self._git_rev_list()

		for revision, merge in revisions:
			# If the revision is not a merge, we do import it.
			if not merge:
				self._import_revision(revision)

			# Save revision in database.
			self.db.execute("UPDATE sources SET revision = %s WHERE id = %s",
				revision, self.id)
			self._data["revision"] = revision

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
		return self._data.name

	@property
	def url(self):
		return self._data.url

	@property
	def path(self):
		return self._data.path

	@property
	def targetpath(self):
		return self._data.targetpath

	@property
	def revision(self):
		return self._data.revision

	@property
	def branch(self):
		return self._data.branch

	@property
	def builds(self):
		return self.pakfire.builds.get_by_source(self.id)

	@property
	def distro(self):
		return self.pakfire.distros.get_by_id(self._data.distro_id)
