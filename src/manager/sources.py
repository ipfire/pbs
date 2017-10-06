#!/usr/bin/python

from .. import git

from . import base

class SourcesPullEvent(base.Event):
	# This should run whenever possible, so the user can see his commits
	# very quickly in the build service.
	priority = 1

	@property
	def interval(self):
		return self.pakfire.settings.get_int("source_update_interval", 60)

	def run(self):
		for source in self.pakfire.sources.get_all():
			repo = git.Repo(self.pakfire, source.id, mode="mirror")

			# If the repository is not yet cloned, we need to make a local
			# clone to work with.
			if not repo.cloned:
				repo.clone()

			# Otherwise we just fetch updates.
			else:
				repo.fetch()

			# Import all new revisions.
			repo.import_revisions()
