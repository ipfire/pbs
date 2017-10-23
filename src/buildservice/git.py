#!/usr/bin/python

import datetime
import logging
import os
import subprocess

from . import base
from .decorators import *

class Repo(base.Object):
	def init(self, source, mode="normal"):
		assert mode in ("normal", "bare", "mirror")

		self.source = source
		self.mode = mode

	def __enter__(self):
		return RepoContext(self.backend, self)

	def __exit__(self, type, value, traceback):
		pass

	@lazy_property
	def path(self):
		path = os.path.join("~/.pakfire/cache/git-repos", self.source.identifier, self.mode)

		return os.path.expanduser(path)

	@property
	def cloned(self):
		"""
			Say if the repository is already cloned.
		"""
		return os.path.exists(self.path)


class RepoContext(base.Object):
	def init(self, repo):
		self.repo = repo

		# Clone repository if not cloned, yet
		if not self.repo.cloned:
			self.clone()

		self._lock()

	def __del__(self):
		self._release()

	def _lock(self):
		pass # XXX needs to be implemented

	def _release(self):
		pass

	def git(self, cmd, path=None):
		if not path:
			path = self.repo.path

		cmd = "cd %s && git %s" % (path, cmd)

		logging.debug("Running command: %s" % cmd)

		return subprocess.check_output(["/bin/sh", "-c", cmd])

	def clone(self):
		if self.repo.cloned:
			return

		path, repo = os.path.dirname(self.repo.path), os.path.basename(self.repo.path)

		# Create the repository home directory if not exists.
		if not os.path.exists(path):
			os.makedirs(path)

		command = ["clone"]
		if self.repo.mode == "bare":
			command.append("--bare")
		elif self.repo.mode == "mirror":
			command.append("--mirror")

		command.append(self.repo.source.url)
		command.append(repo)

		# Clone the repository.
		try:
			self.git(" ".join(command), path=path)
		except Exception:
			shutil.rmtree(self.repo.path)
			raise

	def fetch(self):
		self.git("fetch")

	def rev_list(self, revision=None):
		if not revision:
			if self.repo.source.head_revision:
				revision = self.repo.source.head_revision.revision
			else:
				revision = self.repo.source.start_revision

		command = "rev-list %s..%s" % (revision, self.repo.source.branch)

		# Get all merge commits
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
		return self.repo.source.create_commit(revision,
			rev_author, rev_committer, rev_subject, rev_body, rev_date)

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

		return [os.path.join(self.repo.path, f) for f in files.splitlines()]

	def get_all_files(self):
		files = self.git("ls-files")

		return [os.path.join(self.repo.path, f) for f in files.splitlines()]