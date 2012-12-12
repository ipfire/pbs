#!/usr/bin/python

import os

import base
import builds

_ = lambda x: x

class LogEntry(base.Object):
	type = None

	def __init__(self, pakfire, data):
		base.Object.__init__(self, pakfire)

		self.data = data

		self._user = None

	def __cmp__(self, other):
		return cmp(other.time, self.time)

	@property
	def time(self):
		return self.data.time

	def get_user(self):
		user_id = getattr(self.data, "user_id", None)

		if user_id is None:
			return

		return self.pakfire.users.get_by_id(self.data.user_id)

	@property
	def user(self):
		if self._user is None:
			self._user = self.get_user()

		return self._user

	def get_title(self, user=None):
		return None

	def get_message(self, user=None):
		raise NotImplementedError

	def get_footer(self, user=None):
		return None


class CreatedLogEntry(LogEntry):
	type = "created"

	@property
	def build(self):
		return self.data

	@property
	def time(self):
		return self.build.created

	def get_user(self):
		if self.build.type == "scratch":
			return self.build.owner

	def get_message(self, user=None):
		return _("Build has been created")


class CommentLogEntry(LogEntry):
	type = "comment"

	@property
	def time(self):
		return self.data.time_created

	@property
	def credit(self):
		return self.data.credit

	@property
	def build_id(self):
		return self.data.build_id

	@property
	def build(self):
		return self.pakfire.builds.get_by_id(self.build_id)

	@property
	def vote(self):
		if self.credit > 0:
			return "up"
		elif self.credit < 0:
			return "down"

		return "none"

	def get_message(self, user=None):
		return self.data.text


class RepositoryLogEntry(LogEntry):
	type = "repo"

	def get_message(self, user=None):
		msg = _("Unknown action.")

		# See if we have done the action by ourself.
		you = self.user == user

		args = {}

		# Add information about the user.
		if self.user:
			args["user"] = self.user.realname
		else:
			args["user"] = _("Unknown")

		# Add information about the repositories.
		if self.data.from_repo_id:
			repo = self.pakfire.repos.get_by_id(self.data.from_repo_id)
			args["from_repo"] = repo.name
		else:
			args["from_repo"] = _("N/A")

		if self.data.to_repo_id:
			repo = self.pakfire.repos.get_by_id(self.data.to_repo_id)
			args["to_repo"] = repo.name
		else:
			args["to_repo"] = _("N/A")

		action = self.data.action

		if action == "added":
			if not self.user:
				msg = _("This build was pushed to the repository '%(to_repo)s'.")
			elif you:
				msg = _("You pushed this build to the repository '%(to_repo)s'.")
			else:
				msg = _("%(user)s pushed this build to the repository '%(to_repo)s'.")

		elif action == "removed":
			if not self.user:
				msg = _("This build was unpushed from the repository '%(from_repo)s'.")
			elif you:
				msg = _("You unpushed this build from the repository '%(from_repo)s'.")
			else:
				msg = _("%(user)s unpushed this build from the repository '%(from_repo)s'.")

		elif action == "moved":
			if not self.user:
				msg = _("This build was pushed from the repository '%(from_repo)s' to '%(to_repo)s'.")
			elif you:
				msg = _("You pushed this build from the repository '%(from_repo)s' to '%(to_repo)s'.")
			else:
				msg = _("%(user)s pushed this build from the repository '%(from_repo)s' to '%(to_repo)s'.")

		return msg % args


class BuilderLogEntry(LogEntry):
	type = "builder"

	def get_builder(self):
		assert self.data.builder_id

		return self.pakfire.builders.get_by_id(self.data.builder_id)

	def get_message(self, user=None):
		msg = _("Unknown action.")

		# See if we have done the action by ourself.
		you = self.user == user

		builder = self.get_builder()
		assert builder

		args = {
			"builder" : builder.hostname,
		}

		# Add information about the user.
		if self.user:
			args["user"] = self.user.realname
		else:
			args["user"] = _("Unknown")

		action = self.data.action

		if action == "enabled":
			if not self.user:
				msg = _("Builder '%(builder)s' has been enabled.")
			elif you:
				msg = _("You enabled builder '%(builder)s'.")
			else:
				msg = _("%(user)s enabled builder '%(builder)s'.")

		elif action == "disabled":
			if not self.user:
				msg = _("Builder '%(builder)s' was has been disabled.")
			elif you:
				msg = _("You disabled builder '%(builder)s'.")
			else:
				msg = _("%(user)s disabled builder '%(builder)s'.")

		elif action == "deleted":
			if you:
				msg = _("You deleted builder '%(builder)s'.")
			else:
				msg = _("%(user)s deleted builder '%(builder)s'.")

		elif action == "created":
			if you:
				msg = _("You created builder '%(builder)s'.")
			else:
				msg = _("%(user)s created builder '%(builder)s'.")

		return msg % args


class JobLogEntry(LogEntry):
	type = "job"

	def get_job(self):
		assert self.data.job_id

		return self.pakfire.jobs.get_by_id(self.data.job_id)

	def get_message(self, user=None):
		msg = _("Unknown action.")

		# See if we have done the action by ourself.
		you = self.user == user

		job = self.get_job()
		assert job

		args = {
			"job"   : job.name,
			"state" : self.data.state,
		}

		# Add information about the user.
		if self.user:
			args["user"] = self.user.realname
		else:
			args["user"] = _("Unknown")

		action = self.data.action

		if action == "created":
			if not self.user:
				msg = _("Job '%(job)s' has been created.")
			elif you:
				msg = _("You created job '%(job)s'.")
			else:
				msg = _("%(user)s created job '%(job)s'.")

		elif action == "state_change":
			if not self.user:
				msg = _("Job '%(job)s' has changed its state to: %(state)s.")
			elif you:
				msg = _("You changed the state of job '%(job)s' to: %(state)s.")
			else:
				msg = _("%(user)s changed the state of job '%(job)s' to: %(state)s.")

		elif action == "reset":
			if not self.user:
				msg = _("Job '%(job)s' has been reset.")
			elif you:
				msg = _("You reset job '%(job)s'.")
			else:
				msg = _("%(user)s has reset job '%(job)s'.")

		elif action == "schedule_rebuild":
			if not self.user:
				msg = _("Job '%(job)s' has been scheduled for rebuild.")
			elif you:
				msg = _("You scheduled job '%(job)s' for rebuild.")
			else:
				msg = _("%(user)s scheduled job '%(job)s' for rebuild.")

		elif action == "schedule_test_job":
			# XXX add link to the test job

			if not self.user:
				msg = _("A test job for '%(job)s' has been scheduled.")
			elif you:
				msg = _("You scheduled a test job for '%(job)s'.")
			else:
				msg = _("%(user)s scheduled a test job for '%(job)s'.")

		return msg % args


class MirrorLogEntry(LogEntry):
	type = "mirror"

	def get_mirror(self):
		assert self.data.mirror_id

		return self.pakfire.mirrors.get_by_id(self.data.mirror_id)

	def get_message(self, user=None):
		msg = _("Unknown action.")

		# See if we have done the action by ourself.
		you = self.user == user

		mirror = self.get_mirror()
		assert mirror

		args = {
			"mirror" : mirror.hostname,
		}

		# Add information about the user.
		if self.user:
			args["user"] = self.user.realname
		else:
			args["user"] = _("Unknown")

		action = self.data.action

		if action == "enabled":
			if not self.user:
				msg = _("Mirror '%(mirror)s' has been enabled.")
			elif you:
				msg = _("You enabled mirror '%(mirror)s'.")
			else:
				msg = _("%(user)s enabled mirror '%(mirror)s'.")

		elif action == "disabled":
			if not self.user:
				msg = _("Mirror '%(mirror)s' has been disabled.")
			elif you:
				msg = _("You disabled mirror '%(mirror)s'.")
			else:
				msg = _("%(user)s disabled mirror '%(mirror)s'.")

		elif action == "deleted":
			if you:
				msg = _("You deleted mirror '%(mirror)s'.")
			else:
				msg = _("%(user)s deleted mirror '%(mirror)s'.")

		elif action == "created":
			if you:
				msg = _("You created mirror '%(mirror)s'.")
			else:
				msg = _("%(user)s created mirror '%(mirror)s'.")

		return msg % args


class LogFile(base.Object):
	def __init__(self, pakfire, id):
		base.Object.__init__(self, pakfire)

		# Save the ID of the item.
		self.id = id

		# Cache.
		self._data = None
		self._job = None

	@property
	def data(self):
		if self._data is None:
			self._data = self.db.get("SELECT * FROM logfiles WHERE id = %s", self.id)
			assert self._data

		return self._data

	@property
	def name(self):
		return os.path.basename(self.path)

	@property
	def path(self):
		return self.data.path

	@property
	def job(self):
		if self._job is None:
			self._job = self.pakfire.jobs.get_by_id(self.data.job_id)
			assert self._job

		return self._job

	@property
	def build(self):
		return self.job.build

	@property
	def download_url(self):
		return "/".join((self.build.download_prefix, self.path))

	@property
	def filesize(self):
		return self.data.filesize
