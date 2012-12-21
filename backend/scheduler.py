#!/usr/bin/python

import logging
import multiprocessing
import time
import traceback

import backend.main

class Event(object):
	interval = None

	priority = 0

	def __init__(self, *args, **kwargs):
		self.args = args
		self.kwargs = kwargs

		self._next_start_time = 0

		self.scheduler = None

	def __repr__(self):
		if hasattr(self, "_next_start_time"):
			return "<%s next_start_in=%ds>" % \
				(self.__class__.__name__, self._next_start_time - time.time())

		return "<%s>" % self.__class__.__name__

	def run(self, *args, **kwargs):
		raise NotImplemented

	def run_subprocess_background(self, method, *args):
		arguments = [method,] + list(args)

		process = multiprocessing.Process(target=self.fork, args=arguments)
		process.daemon = False

		# Start the process.
		process.start()

		return process

	def run_subprocess(self, *args):
		process = self.run_subprocess_background(*args)

		# Wait until process has finished.
		process.join()

	@staticmethod
	def fork(method, *args, **kwargs):
		# Create new pakfire instance.
		_pakfire = backend.main.Pakfire()

		return method(_pakfire, *args, **kwargs)


class Scheduler(object):
	def __init__(self):
		self._queue = []

	def add_event(self, event, start_time=None):
		event.scheduler = self

		self._queue.append(event)

		# Set initial start time.
		if start_time is None:
			start_time = time.time()

		event._next_start_time = start_time

	def sort_queue(self):
		self._queue.sort(key=lambda e: (e.priority, e._next_start_time))

	def run(self):
		while self._queue:
			self.sort_queue()
			print self._queue

			for event in self._queue:
				# If the event has to be started some time in
				# the future.
				if event._next_start_time <= time.time():
					try:
						logging.info("Running %s..." % event)

						event.run(*event.args, **event.kwargs)

					# In case the user interrupts the scheduler.
					except KeyboardInterrupt:
						# Stop immediately.
						return

					except:
						traceback.print_exc()

					finally:
						# Set the next execution time if the event
						# should be run again.
						if event.interval:
							event._next_start_time = time.time() + event.interval

						# Otherwise remove it from the queue.
						else:
							self._queue.remove(event)

					# Get back to outer loop and sort the queue again.
					break

			# Sleep a bit.
			time.sleep(1)
