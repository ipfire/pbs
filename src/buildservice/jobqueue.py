#!/usr/bin/python

import datetime
import logging

from . import base

log = logging.getLogger("jobqueue")
log.propagate = 1

PENDING_STATE = "pending"

class JobQueue(base.Object):
	def __iter__(self):
		jobs = self.backend.jobs._get_jobs("SELECT jobs.* FROM jobs_queue queue \
			LEFT JOIN jobs ON queue.job_id = jobs.id")

		return iter(jobs)

	def __len__(self):
		res = self.db.get("SELECT COUNT(*) AS len FROM jobs_queue")

		return res.len

	def for_arches(self, arches, limit=None):
		jobs = self.backend.jobs._get_jobs("SELECT jobs.* FROM jobs_queue queue \
			LEFT JOIN jobs ON queue.job_id = jobs.id \
				WHERE jobs.arch = ANY(%s) LIMIT %s", arches, limit)

		return jobs

	def get_length_for_arch(self, arch):
		res = self.db.get("SELECT COUNT(*) AS len FROM jobs_queue queue \
			LEFT JOIN jobs on queue.job_id = jobs.id \
				WHERE jobs.arch = %s", arch)

		return res.len

	@property
	def average_waiting_time(self):
		"""
			Returns how long the jobs in the queue have been waiting on average
		"""
		res = self.db.get("SELECT AVG(NOW() - COALESCE(jobs.start_not_before, jobs.time_created)) AS avg \
			FROM jobs_queue queue LEFT JOIN jobs ON queue.job_id = jobs.id")

		return res.avg

	def create_test_jobs(self):
		max_queue_length = self.backend.settings.get_int("test_queue_limit", 25)

		threshold_days = self.backend.settings.get_int("test_threshold_days", 14)
		threshold = datetime.datetime.utcnow() - datetime.timedelta(days=threshold_days)

		for arch in self.backend.arches:
			# Skip adding new jobs if there are more too many jobs in the queue.
			limit = max_queue_length - self.backend.jobqueue.get_length_for_arch(arch)
			if limit <= 0:
				log.debug("Already too many jobs in queue of %s to create tests." % arch)
				continue

			# Get a list of builds, with potentially need a test build.
			# Randomize the output and do not return more jobs than we are
			# allowed to put into the build queue.
			builds = self.backend.builds._get_builds("SELECT builds.* FROM builds \
				LEFT JOIN jobs ON builds.id = jobs.build_id \
				WHERE builds.type = %s AND builds.state = ANY(%s) AND jobs.state = %s \
					AND NOT EXISTS (SELECT 1 FROM jobs test_jobs \
						WHERE test_jobs.build_id = builds.id AND jobs.test IS %s \
							AND (test_jobs.state <> %s OR test_jobs.state = %s AND test_jobs.time_finished >= %s)) LIMIT %s",
				"release", ["stable", "testing"], "finished", True, "finished", "finished", threshold, limit)

			# Search for the job with the right architecture in each
			# build and schedule a test job.
			for build in builds:
				for job in build:
					if job.arch == arch:
						job.restart()
						break

	def check_build_dependencies(self):
		# Check all jobs that have never being checked before
		self._check_build_dependencies("SELECT * FROM jobs \
			WHERE state = %s AND dependency_check_succeeded IS NULL \
			ORDER BY time_created", "pending")

		# Redo the check for all jobs that have recently failed
		self._check_build_dependencies("SELECT * FROM jobs \
			WHERE state = %s AND dependency_check_succeeeded IS FALSE \
			AND dependency_check_at < NOW() - '5 minutes'::interval \
			ORDER BY dependency_check_at", "pending")

	def _check_build_dependencies(self, query, *args):
		jobs = self.backend.jobs._get_jobs(query, *args)

		for job in jobs:
			with self.db.transaction():
				job.resolvdep()
