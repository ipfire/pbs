#!/usr/bin/python

import logging
import os.path
import tornado.httpserver
import tornado.locale
import tornado.options
import tornado.web

import backend

from handlers import *

BASEDIR = os.path.join(os.path.dirname(__file__), "..", "data")

# Enable logging
tornado.options.parse_command_line()

class MasterApplication(tornado.web.Application):
	def __init__(self):
		settings = dict(
			debug = True,
			gzip = False,
		)

		# Load translations.
		tornado.locale.load_gettext_translations(
			os.path.join(BASEDIR, "translations"), "pakfire")

		tornado.web.Application.__init__(self, **settings)

		self.add_handlers(r".*", [
			# API
			(r"/api/builder/([A-Za-z0-9\-\.]+)/(\w+)", RPCBuilderHandler),
		])

		self.pakfire = backend.Pakfire()

		logging.info("Successfully initialied application")

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

		# All requests should be done after 30 seconds or they will be killed.
		self.ioloop.set_blocking_log_threshold(30)

		http_server = tornado.httpserver.HTTPServer(self, xheaders=True)

		# If we are not running in debug mode, we can actually run multiple
		# frontends to get best performance out of our service.
		if not self.settings["debug"]:
			http_server.bind(port)
			http_server.start(num_processes=4)
		else:
			http_server.listen(port)

		self.ioloop.start()

	def reload(self):
		logging.debug("Caught reload signal")
