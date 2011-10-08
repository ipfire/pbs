#!/usr/bin/python

import logging
import tornado.ioloop

import base

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

		# Send up to 10 messages and return.
		self.messages.send_messages(limit=10)


managers.append(MessagesManager)


class SourceManager(Manager):
	@property
	def sources(self):
		return self.pakfire.sources

	@property
	def timeout(self):
		return self.settings.get_int("source_update_interval", 60)

	def do(self):
		for source in self.sources.get_all():
			# If the repository is not yet cloned, we need to make a local
			# clone to work with.
			if not source.is_cloned():
				source.clone()

				# If we have cloned a new repository, we exit to not get over
				# the time treshold.
				return 0

			# Otherwise we just fetch updates.
			else:
				source.fetch()

			# Import all new revisions.
			source.import_revisions()

			# If there are revisions left, we exit and want be called immediately
			# again.
			if source._git_rev_list():
				return 0


managers.append(SourceManager)


class BuildsManager(Manager):
	@property
	def timeout(self):
		return self.settings.get_int("build_keepalive_interval", 900)

	def do(self):
		for build in self.pakfire.builds.get_all_but_finished():
			logging.debug("Processing unfinished build: %s" % build.name)
			build.keepalive()


managers.append(BuildsManager)


class UploadsManager(Manager):
	@property
	def timeout(self):
		return self.settings.get_int("uploads_remove_interval", 3600)

	def do(self):
		self.pakfire.uploads.cleanup()


managers.append(UploadsManager)

#class NotificationManager(Manager):
#	@property
#	def timeout(self):
#		return Settings().get_int("notification_interval")
#
#	def do(self):
#		tasks = self.tasks.get(type="notification", state="pending")
#
#		for task in tasks:
#			logging.debug("Running task %s" % task)
#
#			task.run()
#
#managers.append(NotificationManager)
#
#
#class RepositoryUpdateManager(Manager):
#	@property
#	def timeout(self):
#		return Settings().get_int("repository_update_interval")
#
#	def do(self):
#		tasks = self.tasks.get(type="repository_update", state="pending")
#
#		for task in tasks:
#			logging.debug("Running task %s" % task)
#
#			task.run()
#
#managers.append(RepositoryUpdateManager)
