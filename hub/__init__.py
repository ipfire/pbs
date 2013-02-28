#!/usr/bin/python

import logging
import os.path
import tornado.httpserver
import tornado.locale
import tornado.options
import tornado.web

import backend
import handlers

BASEDIR = os.path.join(os.path.dirname(__file__), "..", "data")

# Read command line
tornado.options.define("debug", default=False, help="Run in debug mode", type=bool)
tornado.options.parse_command_line()

class Application(tornado.web.Application):
	def __init__(self):
		self.__pakfire = None

		settings = dict(
			debug = tornado.options.options.debug,
			gzip  = True,
		)

		# Load translations.
		tornado.locale.load_gettext_translations(
			os.path.join(BASEDIR, "translations"), "pakfire")

		tornado.web.Application.__init__(self, **settings)

		self.add_handlers(r"pakfirehub.ipfire.org", [
			# Redirect strayed users.
			#(r"/", handlers.RedirectHandler),

			# Test handlers
			(r"/noop", handlers.NoopHandler),
			(r"/error/test", handlers.ErrorTestHandler),
			(r"/error/test/(\d+)", handlers.ErrorTestHandler),

			# Statistics
			(r"/statistics/jobs/queue", handlers.StatsJobsQueueHandler),

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
			(r"/jobs/(.*)", handlers.JobsGetHandler),

			# Packages
			(r"/packages/(.*)", handlers.PackagesGetHandler),

			# Uploads
			(r"/uploads/create", handlers.UploadsCreateHandler),
			(r"/uploads/(.*)/sendchunk", handlers.UploadsSendChunkHandler),
			(r"/uploads/(.*)/finished", handlers.UploadsFinishedHandler),
			(r"/uploads/(.*)/destroy", handlers.UploadsDestroyHandler),
		])

		logging.info("Successfully initialied application")

	@property
	def pakfire(self):
		if self.__pakfire is None:
			config_file = os.path.join(BASEDIR, "..", "pbs.conf")

			self.__pakfire = backend.Pakfire(config_file=config_file)

		return self.__pakfire

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

		http_server = tornado.httpserver.HTTPServer(self, xheaders=True)

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
