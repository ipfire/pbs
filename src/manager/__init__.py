#!/usr/bin/python

from . import base

from .bugs         import BugsUpdateEvent
from .builds       import BuildsFailedRestartEvent, CheckBuildDependenciesEvent
from .builds       import CreateTestBuildsEvent, DistEvent
from .repositories import RepositoriesUpdateEvent
from .sources      import SourcesPullEvent


# Events that do not fit anywhere else.

class CleanupFilesEvent(base.Event):
	"""
		Removes all files that are not needed anymore.
		(scratch builds, logs, etc.)
	"""
	# Run once in 5 minutes.
	interval = 300

	# Intermediate priority.
	priority = 5

	def run(self):
		self.pakfire.cleanup_files()
