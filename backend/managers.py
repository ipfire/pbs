#!/usr/bin/python

import datetime
import logging
import multiprocessing
import os
import shutil
import subprocess
import tempfile
import time
import tornado.ioloop

import pakfire
import pakfire.api
import pakfire.config
from pakfire.constants import *

import base
import builds
import main
import packages
import sources

from constants import *

managers = []

class Manager(base.Object):
	def __init__(self, pakfire):
		base.Object.__init__(self, pakfire)

		self.pc = tornado.ioloop.PeriodicCallback(self, self.timeout * 1000)

		logging.info("%s was initialized." % self.__class__.__name__)

		self()

	def __call__(self):
		logging.info("%s main method was called." % self.__class__.__name__)

		timeout = self.do()

		if timeout is None:
			timeout = self.timeout

		# Update callback_time.
		self.pc.callback_time = timeout * 1000
		logging.debug("Next call will be in ~%.2f seconds." % timeout)

	@property
	def timeout(self):
		"""
			Return a new callback timeout in seconds.
		"""
		raise NotImplementedError

	def do(self):
		raise NotImplementedError


	# Helper functions

	def wait_for_processes(self):
		ALIVE_CHECK_INTERVAL = 0.5

		logging.debug("There are %s process(es) in the queue." % len(self.processes))

		# Nothing to do, if there are no processes running.
		if not self.processes:
			return

		# Get the currently running? process.
		process = self.processes[0]

		# If the first process is running, everything is okay and
		# we'll have to wait.
		if process.is_alive():
			return ALIVE_CHECK_INTERVAL

		# If the process has not been run, it is started now.
		if process.exitcode is None:
			logging.debug("Process %s is being started..." % process)

			process.start()
			return ALIVE_CHECK_INTERVAL

		# If the process has stopped working we check why...
		elif process.exitcode == 0:
			logging.debug("Process %s has successfully finished." % process)

		elif process.exitcode > 0:
			logging.error("Process %s has exited with code: %s" % \
				(process, process.exitcode))

		elif process.exitcode < 0:
			logging.error("Process %s has ended with signal %s" % \
				(process, process.exitcode))

		# Remove process from process queue.
		self.processes.remove(process)

		# If there are still processes in the queue, we start this function
		# again...
		if self.processes:
			return self.wait_for_processes()


class MessagesManager(Manager):
	@property
	def messages(self):
		"""
			Shortcut to messages object.
		"""
		return self.pakfire.messages

	@property
	def timeout(self):
		# If we have messages, we should run as soon as possible.
		if self.messages.count:
			return 0

		# Otherwise we sleep for "mesages_interval"
		return self.settings.get_int("messages_interval", 10)

	def do(self):
		logging.info("Sending a bunch of messages.")

		# Send up to 25 messages and return.
		i = 0
		for msg in self.messages.get_all(limit=25):
			try:
				self.messages.send_msg(msg)

			except Exception, e:
				logging.critical("There was an error sending mail: %s" % e)
				raise

			else:
				# If everything was okay, we can delete the message in the database.
				self.messages.delete(msg.id)
				i += 1

		count = self.messages.count

		logging.debug("Successfully sent %s message(s). %s still in queue." \
			% (i, count))

		# If there are still mails left, we start again as soon as possible.
		if count:
			return 0

		return self.settings.get_int("messages_interval", 10)


managers.append(MessagesManager)

class BugsUpdateManager(Manager):
	@property
	def timeout(self):
		return self.settings.get_int("bugzilla_update_interval", 60)

	def do(self):
		# Get up to ten updates.
		query = self.db.query("SELECT * FROM builds_bugs_updates \
			WHERE error = 'N' ORDER BY time LIMIT 10")

		# XXX CHECK IF BZ IS ACTUALLY REACHABLE AND WORKING

		for update in query:
			try:
				bug = self.pakfire.bugzilla.get_bug(update.bug_id)
				if not bug:
					logging.error("Bug #%s does not exist." % update.bug_id)
					continue

				# Set the changes.
				bug.set_status(update.status, update.resolution, update.comment)

			except Exception, e:
				# If there was an error, we save that and go on.
				self.db.execute("UPDATE builds_bugs_updates SET error = 'Y', error_msg = %s \
					WHERE id = %s", "%s" % e, update.id)

			else:
				# Remove the update when it has been done successfully.
				self.db.execute("DELETE FROM builds_bugs_updates WHERE id = %s", update.id)


managers.append(BugsUpdateManager)	

class GitRepo(base.Object):
	def __init__(self, pakfire, id, mode="normal"):
		base.Object.__init__(self, pakfire)

		assert mode in ("normal", "bare", "mirror")

		# Get the source object.
		self.source = sources.Source(pakfire, id)
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

		# Convert strings properly. No idea why I have to do that.
		#rev_author    = rev_author.decode("latin-1").strip()
		#rev_committer = rev_committer.decode("latin-1").strip()
		#rev_subject   = rev_subject.decode("latin-1").strip()
		#rev_body      = rev_body.decode("latin-1").rstrip()

		# Create a new commit object in the database
		commit = sources.Commit.create(self.pakfire, self.source, revision,
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

		return [os.path.join(self.path, f) for f in files.splitlines()]

	def get_all_files(self):
		files = self.git("ls-files")

		return [os.path.join(self.path, f) for f in files.splitlines()]


class SourceManager(Manager):
	@property
	def sources(self):
		return self.pakfire.sources

	@property
	def timeout(self):
		return self.settings.get_int("source_update_interval", 60)

	def do(self):
		for source in self.sources.get_all():
			repo = GitRepo(self.pakfire, source.id, mode="mirror")

			# If the repository is not yet cloned, we need to make a local
			# clone to work with.
			if not repo.cloned:
				repo.clone()

				# If we have cloned a new repository, we exit to not get over
				# the time treshold.
				return 0

			# Otherwise we just fetch updates.
			else:
				repo.fetch()

			# Import all new revisions.
			repo.import_revisions()


managers.append(SourceManager)

class DistManager(Manager):
	process = None

	first_run = True

	def get_next_commit(self):
		commits = self.pakfire.sources.get_pending_commits(limit=1)

		if not commits:
			return

		return commits[0]

	@property
	def timeout(self):
		# If there are commits standing in line, we try to restart as soon
		# as possible.
		if self.get_next_commit():
			return 0

		# Otherwise we wait at least for a minute.
		return 60

	def do(self):
		if self.first_run:
			self.first_run = False

			self.process = self.init_repos()

		if self.process:
			# If the process is still running, we check back in a couple of
			# seconds.
			if self.process.is_alive():
				return 1

			# The process has finished its work. Clear everything up and
			# go on.
			self.commit = self.process = None

		# Search for a new commit to proceed with.
		self.commit = commit = self.get_next_commit()

		# If no commit is there, we just wait for a minute.
		if not commit:
			return 60

		# Got a commit to process.
		commit.state = "running"

		logging.debug("Processing commit %s: %s" % (commit.revision, commit.subject))

		# Get the repository of this commit.
		repo = GitRepo(self.pakfire, commit.source_id)

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

		self.process = self.fork(commit_id=commit.id, updated_files=updated_files,
			deleted_files=deleted_files)

		return 1

	def fork(self, source_id=None, commit_id=None, updated_files=[], deleted_files=[]):
		# Create the Process object.
		process = multiprocessing.Process(
			target=self._process,
			args=(source_id, commit_id, updated_files, deleted_files)
		)

		# The process is running in daemon mode so it will try to kill
		# all child processes when exiting.
		process.daemon = True

		# Start the process.
		process.start()
		logging.debug("Started new process pid=%s." % process.pid)

		return process

	def init_repos(self):
		# Create the Process object.
		process = multiprocessing.Process(
			target=self._init_repos,
		)

		# The process is running in daemon mode so it will try to kill
		# all child processes when exiting.
		#process.daemon = True

		# Start the process.
		process.start()
		logging.debug("Started new process pid=%s." % process.pid)

		return process

	def _init_repos(self):
		_pakfire = main.Pakfire()
		sources = _pakfire.sources.get_all()

		for source in sources:
			if source.revision:
				continue

			repo = GitRepo(_pakfire, source.id)
			if not repo.cloned:
				repo.clone()

			files = repo.get_all_files()

			for file in files:
				if not file.endswith(".%s" % MAKEFILE_EXTENSION):
					continue

				#files = [f for f in files if f.endswith(".%s" % MAKEFILE_EXTENSION)]

				process = self.fork(source_id=source.id, updated_files=[file,], deleted_files=[])

				while process.is_alive():
					time.sleep(1)
					continue

	@staticmethod
	def _process(source_id, commit_id, updated_files, deleted_files):
		_pakfire = main.Pakfire()

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

				p = pakfire.Pakfire(mode="server", config=config)

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

				if commit:
					commit.distro.delete_package(name)

			if commit:
				commit.state = "finished"


managers.append(DistManager)

class BuildsManager(Manager):
	@property
	def timeout(self):
		return self.settings.get_int("build_keepalive_interval", 900)

	def do(self):
		threshold = datetime.datetime.utcnow() - datetime.timedelta(hours=72)

		for job in self.pakfire.jobs.get_next_iter(type="build", max_tries=9, states=["failed"]):
			if job.build.state == "broken":
				continue

			if not job.time_finished or job.time_finished > threshold:
				continue

			# Restart the job.
			logging.info("Restarting build job: %s" % job)
			job.set_state("new", log=False)


managers.append(BuildsManager)

class UploadsManager(Manager):
	@property
	def timeout(self):
		return self.settings.get_int("uploads_remove_interval", 3600)

	def do(self):
		self.pakfire.uploads.cleanup()


managers.append(UploadsManager)

class RepositoryManager(Manager):
	processes = []

	@property
	def timeout(self):
		return self.settings.get_int("repository_update_interval", 600)

	def do(self):
		for process in self.processes[:]:
			# If the first process is running, everything is okay and
			# we'll have to wait.
			if process.is_alive():
				return 0.5

			# If the process has not been run, it is started now.
			if process.exitcode is None:
				logging.debug("Process %s is being started..." % process)

				process.start()
				return 1

			# If the process has stopped working we check why...
			else:
				if process.exitcode == 0:
					logging.debug("Process %s has successfully finished." % process)

				elif process.exitcode > 0:
					logging.error("Process %s has exited with code: %s" % \
						(process, process.exitcode))

				elif process.exitcode < 0:
					logging.error("Process %s has ended with signal %s" % \
						(process, process.exitcode))

				# Remove process from process queue.
				self.processes.remove(process)

				# Start the loop again if there any processes left
				# that need to be started.
				if self.processes:
					continue

				# Otherwise wait some time and start from the beginning.
				else:
					return self.settings.get_int("repository_update_interval", 600)

		for distro in self.pakfire.distros.get_all():
			for repo in distro.repositories:
				# Skip repostories that do not need an update at all.
				if not repo.needs_update():
					logging.info("Repository %s - %s is already up to date." % (distro.name, repo.name))
					continue

				# Create the Process object.
				process = multiprocessing.Process(
					target=self._process,
					args=(repo.id,)
				)

				# Run the process in daemon mode.
				process.daemon = True

				# Add the process to the process queue.
				self.processes.append(process)

		# XXX DEVEL
		#if self.processes:
		#	return 0
		#else:
		#	return

		# Create dependency updater after all repositories have been
		# updated.
		#jobs = self.pakfire.jobs.get_next_iter(states=["new", "dependency_error", "failed",])

		#for job in jobs:
		#	process = multiprocessing.Process(
		#		target=self._dependency_update_process,
		#		args=(job.id,)
		#	)
		#	process.daemon = True
		#	self.processes.append(process)

		# Start again as soon as possible.
		#if self.processes:
		#	return 0

	@staticmethod
	def _process(repo_id):
		_pakfire = main.Pakfire()

		repo = _pakfire.repos.get_by_id(repo_id)
		assert repo

		logging.info("Going to update repository %s..." % repo.name)

		# Update the timestamp when we started at last.
		repo.updated()

		# Find out for which arches this repository is created.
		arches = repo.arches

		# Add the source repository.
		arches.append(_pakfire.arches.get_by_name("src"))

		for arch in arches:
			changed = False

			# Get all packages that are to be included in this repository.
			pkgs = repo.get_packages(arch)

			# Log all packages.
			for pkg in pkgs:
				logging.info("  %s" % pkg)

			repo_path = os.path.join(
				REPOS_DIR,
				repo.distro.identifier,
				repo.identifier,
				arch.name
			)

			if not os.path.exists(repo_path):
				os.makedirs(repo_path)

			source_files = []
			remove_files = []

			for filename in os.listdir(repo_path):
				path = os.path.join(repo_path, filename)

				if not os.path.isfile(path):
					continue

				remove_files.append(path)

			for pkg in pkgs:
				filename = os.path.basename(pkg.path)

				source_file = os.path.join(PACKAGES_DIR, pkg.path)
				target_file = os.path.join(repo_path, filename)

				# Do not add duplicate files twice.
				if source_file in source_files:
					#logging.warning("Duplicate file detected: %s" % source_file)
					continue

				source_files.append(source_file)

				try:
					remove_files.remove(target_file)
				except ValueError:
					changed = True

			if remove_files:
				changed = True

			# If nothing in the repository data has changed, there
			# is nothing to do.
			if changed:
				logging.info("The repository has updates...")
			else:
				logging.info("Nothing to update.")
				continue

			# Find the key to sign the package.
			key_id = None
			if repo.key:
				key_id = repo.key.fingerprint

			# Create package index.
			pakfire.api.repo_create(repo_path, source_files,
				name="%s - %s.%s" % (repo.distro.name, repo.name, arch.name),
				key_id=key_id, type=arch.build_type, mode="server")

			# Remove files afterwards.
			for file in remove_files:
				file = os.path.join(repo_path, file)

				try:
					os.remove(file)
				except OSError:
					logging.warning("Could not remove %s." % file)

	@staticmethod
	def _dependency_update_process(job_id):
		_pakfire = main.Pakfire()

		job = _pakfire.jobs.get_by_id(job_id)
		assert job

		job.resolvdep()


managers.append(RepositoryManager)

class TestManager(Manager):
	@property
	def timeout(self):
		return 300

	@property
	def test_threshold(self):
		threshold_days = self.pakfire.settings.get_int("test_threshold_days", 14)

		return datetime.datetime.utcnow() - datetime.timedelta(days=threshold_days)

	def do(self):
		max_queue_length = self.pakfire.settings.get_int("test_queue_limit", 10)

		# Get a list with all feasible architectures.
		arches = self.pakfire.arches.get_all()
		noarch = self.pakfire.arches.get_by_name("noarch")
		if noarch:
			arches.append(noarch)

		for arch in arches:
			# Get the job queue for each architecture.
			queue = self.pakfire.jobs.get_next(arches=[arch,])

			# Skip adding new jobs if there are more too many jobs in the queue.
			limit = max_queue_length - len(queue)
			if limit <= 0:
				logging.debug("Already too many jobs in queue of %s to create tests." % arch.name)
				continue

			# Get a list of builds, with potentially need a test build.
			# Randomize the output and do not return more jobs than we are
			# allowed to put into the build queue.
			builds = self.pakfire.builds.needs_test(self.test_threshold,
				arch=arch, limit=limit, randomize=True)

			if not builds:
				logging.debug("No builds needs a test for %s." % arch.name)
				continue

			# Search for the job with the right architecture in each
			# build and schedule a test job.
			for build in builds:
				for job in build.jobs:
					if not job.arch == arch:
						continue

					job.schedule("test")
					break


managers.append(TestManager)


class DependencyChecker(Manager):
	processes = []

	@property
	def timeout(self):
		return self.settings.get_int("dependency_checker_interval", 30)

	def do(self):
		if self.processes:
			return self.wait_for_processes()

		return self.search_jobs()

	def search_jobs(self):
		# Find the jobs who need the update the most.
		job_ids = []

		# Get all jobs in new state, no matter how many these are.
		query = self.db.query("SELECT id FROM jobs WHERE state = 'new'")
		for job in query:
			job_ids.append(job.id)

		# If there are no jobs to check, search deeper.
		if not job_ids:
			query = self.db.query("SELECT id FROM jobs \
				WHERE state = 'dependency_error' AND time_finished < DATE_SUB(NOW(), INTERVAL 5 MINUTE) \
				ORDER BY time_finished LIMIT 50")

			for job in query:
				job_ids.append(job.id)

		# Create a subprocess for every single job we have to work on.
		for job_id in job_ids:
			process = multiprocessing.Process(
				target=self._process, args=(job_id,)
			)
			process.daemon = True
			self.processes.append(process)

		# Start immediately again if we have running subprocesses.
		if self.processes:		
			return 0

	@staticmethod
	def _process(job_id):
		# Create a new pakfire instance.
		_pakfire = main.Pakfire()

		# Get the build job we are working on.
		job = _pakfire.jobs.get_by_id(job_id)
		assert job

		# Check if the job status has changed in the meanwhile.
		if not job.state in ("new", "dependency_error", "failed"):
			logging.warning("Job status has already changed: %s - %s" % (job.name, job.state))
			return

		# Resolve the dependencies.
		job.resolvdep()


managers.append(DependencyChecker)


class DeleteManager(Manager):
	@property
	def timeout(self):
		return 300

	def do(self):
		self.pakfire.cleanup_files()


managers.append(DeleteManager)

class SessionsManager(Manager):
	"""
		Cleans up sessions that are not valid anymore.
		Keeps the database smaller.
	"""

	@property
	def timeout(self):
		return 3600

	def do(self):
		self.pakfire.sessions.cleanup()


managers.append(SessionsManager)
