#!/usr/bin/python

import logging
import tornado.web

from .. import Backend
from . import handlers

class Application(tornado.web.Application):
	def __init__(self, **settings):
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
			(r"/builders/jobs/get", handlers.BuildersGetNextJobHandler),
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

		# Launch backend
		self.backend = Backend()

		logging.info("Successfully initialied application")
