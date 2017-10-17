#!/usr/bin/python

import datetime
import logging
import pakfire
import pakfire.config
import shutil
import tempfile

from .. import builds
from .. import git

from . import base

from ..constants import *

class CheckBuildDependenciesEvent(base.Event):
	# Process them as quickly as possible, but there may be more important events.
	priority = 3

	@property
	def interval(self):
		return self.pakfire.settings.get_int("dependency_checker_interval", 30)

	def run(self):
		query = self.db.query("SELECT id FROM jobs \
			WHERE state = 'new' OR \
				(state = 'dependency_error' AND \
				time_finished < NOW() - '5 minutes'::interval) \
			ORDER BY time_finished LIMIT 50")

		for row in query:
			e = CheckBuildDependencyEvent(self.pakfire, row.id)
			self.scheduler.add_event(e)


class CheckBuildDependencyEvent(base.Event):
	# Process them as quickly as possible, but there may be more important events.
	priority = 3

	def run(self, job_id):
		self.run_subprocess(self._run, job_id)

	@staticmethod
	def _run(_pakfire, job_id):
		# Get the build job we are working on.
		job = _pakfire.jobs.get_by_id(job_id)
		if not job:
			logging.debug("Job %s does not exist." % job_id)
			return

		# Check if the job status has changed in the meanwhile.
		if not job.state in ("new", "dependency_error", "failed"):
			logging.warning("Job status has already changed: %s - %s" % (job.name, job.state))
			return

		# Resolve the dependencies.
		job.resolvdep()


class DistEvent(base.Event):
	interval = 60

	first_run = True

	def run(self):
		if self.first_run:
			self.first_run = False

			self.process = self.init_repos()

		for commit in self.pakfire.sources.get_pending_commits():
			commit.state = "running"

			logging.debug("Processing commit %s: %s" % (commit.revision, commit.subject))

			# Get the repository of this commit.
			repo = git.Repo(self.pakfire, commit.source)

			# Make sure, it is checked out.
			if not repo.cloned:
				repo.clone()

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

			e = DistFileEvent(self.pakfire, None, commit.id, updated_files, deleted_files)
			self.scheduler.add_event(e)

	def init_repos(self):
		"""
			Initialize all repositories.
		"""
		for source in self.pakfire.sources.get_all():
			# Skip those which already have a revision.
			if source.revision:
				continue

			# Initialize the repository or and clone it if necessary.
			repo = git.Repo(self.pakfire, source)
			if not repo.cloned:
				repo.clone()

			# Get a list of all files in the repository.
			files = repo.get_all_files()

			for file in [f for f in files if file.endswith(".%s" % MAKEFILE_EXTENSION)]:
				e = DistFileEvent(self.pakfire, source.id, None, [file,], [])
				self.scheduler.add_event(e)


class DistFileEvent(base.Event):
	def run(self, *args):
		self.run_subprocess(self._run, *args)

	@staticmethod
	def _run(_pakfire, source_id, commit_id, updated_files, deleted_files):
		commit = None
		source = None

		if commit_id:
			commit = _pakfire.sources.get_commit_by_id(commit_id)
			assert commit

			source = commit.source

		if source_id and not source:
			source = _pakfire.sources.get_by_id(source_id)

		assert source

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
