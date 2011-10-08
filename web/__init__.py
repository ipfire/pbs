#!/usr/bin/python

import logging
import os.path
import tornado.httpserver
import tornado.locale
import tornado.options
import tornado.web

from handlers import *
from ui_modules import *

BASEDIR = os.path.join(os.path.dirname(__file__), "..", "data")

# Enable logging
tornado.options.parse_command_line()

class Application(tornado.web.Application):
	def __init__(self):
		settings = dict(
			cookie_secret = "12345",
			debug = True,
			gzip = True,
			login_url = "/login",
			template_path = os.path.join(BASEDIR, "templates"),
			ui_modules = {
				"BuildLog"        : BuildLogModule,
				"BuildOffset"     : BuildOffsetModule,
				"BuildTable"      : BuildTableModule,
				"CommentsTable"   : CommentsTableModule,
				"FilesTable"      : FilesTableModule,
				"LogTable"        : LogTableModule,
				"PackageTable"    : PackageTableModule,
				"PackageTable2"   : PackageTable2Module,
				"PackageFilesTable" : PackageFilesTableModule,
				"RepositoryTable" : RepositoryTableModule,
				"RepoActionsTable": RepoActionsTableModule,
				"SourceTable"     : SourceTableModule,
				"UsersTable"      : UsersTableModule,
			},
			xsrf_cookies = True,
		)

		# Load translations.
		tornado.locale.load_gettext_translations(
			os.path.join(BASEDIR, "translations"), "pakfire")

		tornado.web.Application.__init__(self, **settings)

		self.settings["static_path"] = static_path = os.path.join(BASEDIR, "static")
		static_handlers = [
			(r"/static/(.*)", tornado.web.StaticFileHandler, dict(path = static_path)),
			(r"/(favicon\.ico)", tornado.web.StaticFileHandler, dict(path = static_path)),
			(r"/(robots\.txt)", tornado.web.StaticFileHandler, dict(path = static_path)),
		]

		self.add_handlers(r".*", [
			# Entry site that lead the user to index
			(r"/", IndexHandler),

			# Handle all the users logins/logouts/registers and stuff.
			(r"/login", LoginHandler),
			(r"/logout", LogoutHandler),
			(r"/register", RegisterHandler),
			(r"/users", UsersHandler),
			(r"/users/comments", UsersCommentsHandler),
			(r"/user/delete/(\w+)", UserDeleteHandler),
			(r"/user/edit/(\w+)", UserEditHandler),
			(r"/user/(\w+)", UserHandler),
			(r"/user/(\w+)/activate/(\w+)", ActivationHandler),
			(r"/profile", UserHandler),

			# Packages
			(r"/packages", PackageListHandler),
			(r"/package/([\w\-\+]+)/([\d]+)/([\w\.\-]+)/([\w\.]+)", PackageDetailHandler),
			(r"/package/([\w\-\+]+)", PackageNameHandler),

			# Files
			(r"/file/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})", FileDetailHandler),

			# Builds
			(r"/builds", BuildListHandler),
			(r"/builds/filter", BuildFilterHandler),
			(r"/build/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})", BuildDetailHandler),
			(r"/build/priority/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})", BuildPriorityHandler),
			(r"/build/schedule/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})", BuildScheduleHandler),

			# Builders
			(r"/builders", BuilderListHandler),
			(r"/builder/new", BuilderNewHandler),
			(r"/builder/delete/([A-Za-z0-9\-\.]+)", BuilderDeleteHandler),
			(r"/builder/edit/([A-Za-z0-9\-\.]+)", BuilderEditHandler),
			(r"/builder/renew/([A-Za-z0-9\-\.]+)", BuilderRenewPassphraseHandler),
			(r"/builder/([A-Za-z0-9\-\.]+)", BuilderDetailHandler),

			# Sources
			(r"/sources", SourceListHandler),
			(r"/source/([0-9]+)", SourceDetailHandler),

			# Distributions
			(r"/distributions", DistributionListHandler),
			(r"/distribution/delete/([A-Za-z0-9\-\.]+)", DistributionDetailHandler),
			(r"/distribution/edit/([A-Za-z0-9\-\.]+)", DistributionEditHandler),
			(r"/distribution/([A-Za-z0-9\-\.]+)", DistributionDetailHandler),
			(r"/distribution/([A-Za-z0-9\-\.]+)/repository/([A-Za-z0-9\-\.]+)", RepositoryDetailHandler),

			# Documents
			(r"/documents", DocsIndexHandler),
			(r"/documents/builds", DocsBuildsHandler),
			(r"/documents/users", DocsUsersHandler),

			# Search
			(r"/search", SearchHandler),

			# API
			(r"/api/action/(\w+)", RepoActionHandler),

			# Log
			(r"/log", LogHandler),
		] + static_handlers)

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

	def run(self, port=80):
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
