#!/usr/bin/python

from . import base

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