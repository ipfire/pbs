#!/usr/bin/python

import datetime
import logging
import os
import subprocess

from . import base

class Repo(base.Object):
	def __init__(self, pakfire, source, mode="normal"):
		base.Object.__init__(self, pakfire)

		assert mode in ("normal", "bare", "mirror")

		# Get the source object.
		self.source = source
		self.mode = mode

	@property
	def path(self):
		return os.path.join("/var/cache/pakfire/git-repos", self.source.identifier, self.mode)

	def git(self, cmd, path=None):
		if not path:
			path = self.path

		cmd = "cd %s && git %s" % (path, cmd)

		logging.debug("Running command: %s" % cmd)

		return subprocess.check_output(["/bin/sh", "-c", cmd])

	@property
	def cloned(self):
		"""
			Say if the repository is already cloned.
		"""
		return os.path.exists(self.path)

	def clone(self):
		if self.cloned:
			return

		path = os.path.dirname(self.path)
		repo = os.path.basename(self.path)

		# Create the repository home directory if not exists.
		if not os.path.exists(path):
			os.makedirs(path)

		command = ["clone"]
		if self.mode == "bare":
			command.append("--bare")
		elif self.mode == "mirror":
			command.append("--mirror")

		command.append(self.source.url)
		command.append(repo)

		# Clone the repository.
		try:
			self.git(" ".join(command), path=path)
		except Exception:
			shutil.rmtree(self.path)
			raise

	def fetch(self):
		# Make sure, the repository was already cloned.
		if not self.cloned:
			self.clone()

		self.git("fetch")

	def rev_list(self, revision=None):
		if not revision:
			if self.source.head_revision:
				revision = self.source.head_revision.revision
			else:
				revision = self.source.start_revision

		command = "rev-list %s..%s" % (revision, self.source.branch)

		# Get all merge commits.
		merges = self.git("%s --merges" % command).splitlines()

		revisions = []
		for commit in self.git(command).splitlines():
			# Check if commit is a normal commit or merge commit.
			merge = commit in merges

			revisions.append((commit, merge))

		return [r for r in reversed(revisions)]

	def import_revisions(self):
		# Get all pending revisions.
		revisions = self.rev_list()

		for revision, merge in revisions:
			# Actually import the revision.
			self._import_revision(revision, merge)

	def _import_revision(self, revision, merge):
		logging.debug("Going to import revision %s (merge: %s)." % (revision, merge))

		rev_author    = self.git("log -1 --format=\"%%an <%%ae>\" %s" % revision)
		rev_committer = self.git("log -1 --format=\"%%cn <%%ce>\" %s" % revision)
		rev_subject   = self.git("log -1 --format=\"%%s\" %s" % revision)
		rev_body      = self.git("log -1 --format=\"%%b\" %s" % revision)
		rev_date      = self.git("log -1 --format=\"%%at\" %s" % revision)
		rev_date      = datetime.datetime.utcfromtimestamp(float(rev_date))

		# Create a new commit object in the database
		return self.source.create_commit(revision, rev_author, rev_committer,
			rev_subject, rev_body, rev_date)

	def checkout(self, revision, update=False):
		for update in (0, 1):
			if update:
				self.fetch()

			try:
				self.git("checkout %s" % revision)

			except subprocess.CalledProcessError:
				if not update:
					continue

				raise

	def changed_files(self, revision):
		files = self.git("diff --name-only %s^ %s" % (revision, revision))

		return [os.path.join(self.path, f) for f in files.splitlines()]

	def get_all_files(self):
		files = self.git("ls-files")

		return [os.path.join(self.path, f) for f in files.splitlines()]
