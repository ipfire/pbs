#!/usr/bin/python

import logging
import os.path
import tornado.httpserver
import tornado.locale
import tornado.options
import tornado.web

from .. import Backend
from ..decorators import *

from . import handlers

# Read command line
tornado.options.define("debug", default=False, help="Run in debug mode", type=bool)
tornado.options.parse_command_line()

class Application(tornado.web.Application):
	def __init__(self):
		settings = dict(
			debug = tornado.options.options.debug,
			gzip  = True,
		)

		tornado.web.Application.__init__(self, [
			# Redirect strayed users.
			#(r"/", handlers.RedirectHandler),

			# Test handlers
			(r"/noop", handlers.NoopHandler),
			(r"/error/test", handlers.ErrorTestHandler),
			(r"/error/test/(\d+)", handlers.ErrorTestHandler),

			# Builds
			(r"/builds/create", handlers.BuildsCreateHandler),
			(r"/builds/(.*)", handlers.BuildsGetHandler),

			# Builders
			(r"/builders/info", handlers.BuildersInfoHandler),
			(r"/builders/jobs/queue", handlers.BuildersJobsQueueHandler),
			(r"/builders/jobs/(.*)/addfile/(.*)", handlers.BuildersJobsAddFileHandler),
			(r"/builders/jobs/(.*)/buildroot", handlers.BuildersJobsBuildrootHandler),
			(r"/builders/jobs/(.*)/state/(.*)", handlers.BuildersJobsStateHandler),
			(r"/builders/keepalive", handlers.BuildersKeepaliveHandler),

			# Jobs
			(r"/jobs/active", handlers.JobsGetActiveHandler),
			(r"/jobs/latest", handlers.JobsGetLatestHandler),
			(r"/jobs/queue", handlers.JobsGetQueueHandler),
			(r"/jobs/(.*)", handlers.JobsGetHandler),

			# Packages
			(r"/packages/(.*)", handlers.PackagesGetHandler),

			# Uploads
			(r"/uploads/create", handlers.UploadsCreateHandler),
			(r"/uploads/stream", handlers.UploadsStreamHandler),
			(r"/uploads/(.*)/sendchunk", handlers.UploadsSendChunkHandler),
			(r"/uploads/(.*)/finished", handlers.UploadsFinishedHandler),
			(r"/uploads/(.*)/destroy", handlers.UploadsDestroyHandler),
		], **settings)

		logging.info("Successfully initialied application")

	@lazy_property
	def backend(self):
		return Backend()

	def __del__(self):
		logging.info("Shutting down application")

	@property
	def ioloop(self):
		return tornado.ioloop.IOLoop.instance()

	def shutdown(self, *args):
		logging.debug("Caught shutdown signal")
		self.ioloop.stop()

	def run(self, port=81):
		logging.debug("Going to background")

		http_server = tornado.httpserver.HTTPServer(self, xheaders=True,
			max_body_size=1 * (1024 ** 3))

		# If we are not running in debug mode, we can actually run multiple
		# frontends to get best performance out of our service.
		if not self.settings["debug"]:
			http_server.bind(port)
			http_server.start(num_processes=4)
		else:
			http_server.listen(port)

		# All requests should be done after 30 seconds or they will be killed.
		self.ioloop.set_blocking_log_threshold(30)

		self.ioloop.start()

	def reload(self):
		logging.debug("Caught reload signal")
