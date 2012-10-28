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
		self.__pakfire = None

		settings = dict(
			debug = True,
			gzip  = True,
			login_url = "/login",
			template_path = os.path.join(BASEDIR, "templates"),
			ui_modules = {
				"Text"               : TextModule,
				"Modal"              : ModalModule,

				"Footer"             : FooterModule,

				# Logging
				"Log"                : LogModule,
				"LogEntry"           : LogEntryModule,
				"LogEntryComment"    : LogEntryCommentModule,

				"BuildHeadline"      : BuildHeadlineModule,
				"BuildStateWarnings" : BuildStateWarningsModule,

				"BugsTable"          : BugsTableModule,
				"BuildLog"           : BuildLogModule,
				"BuildOffset"        : BuildOffsetModule,
				"BuildTable"         : BuildTableModule,
				"CommitsTable"       : CommitsTableModule,
				"JobsTable"          : JobsTableModule,
				"JobsList"           : JobsListModule,
				"CommentsTable"      : CommentsTableModule,
				"FilesTable"         : FilesTableModule,
				"LogTable"           : LogTableModule,
				"LogFilesTable"      : LogFilesTableModule,
				"Maintainer"         : MaintainerModule,
				"PackagesTable"      : PackagesTableModule,
				"PackageTable2"      : PackageTable2Module,
				"PackageHeader"      : PackageHeaderModule,
				"PackageFilesTable"  : PackageFilesTableModule,
				"RepositoryTable"    : RepositoryTableModule,
				"RepoActionsTable"   : RepoActionsTableModule,
				"SourceTable"        : SourceTableModule,
				"UpdatesTable"       : UpdatesTableModule,
				"UsersTable"         : UsersTableModule,
				"WatchersSidebarTable" : WatchersSidebarTableModule,
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

			# Advanced options for logged in users.
			(r"/advanced", AdvancedHandler),

			# Handle all the users logins/logouts/registers and stuff.
			(r"/login", LoginHandler),
			(r"/logout", LogoutHandler),
			(r"/register", RegisterHandler),
			(r"/password-recovery", PasswordRecoveryHandler),

			# User profiles
			(r"/users", UsersHandler),
			(r"/users/comments", UsersCommentsHandler),
			(r"/user/impersonate", UserImpersonateHandler),
			(r"/user/(\w+)/passwd", UserPasswdHandler),
			(r"/user/(\w+)/delete", UserDeleteHandler),
			(r"/user/(\w+)/edit", UserEditHandler),
			(r"/user/(\w+)/activate", ActivationHandler),
			(r"/user/(\w+)", UserHandler),
			(r"/profile", UserHandler),
			(r"/profile/builds", UsersBuildsHandler),

			# Packages
			(r"/packages", PackageListHandler),
			(r"/package/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})", PackageDetailHandler),
			(r"/package/([\w\-\+]+)/properties", PackagePropertiesHandler),
			(r"/package/([\w\-\+]+)", PackageNameHandler),

			# Files
			(r"/file/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})", FileDetailHandler),

			# Builds
			(r"/builds", BuildsHandler),
			(r"/builds/filter", BuildFilterHandler),
			(r"/builds/queue", BuildQueueHandler),
			(r"/build/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})", BuildDetailHandler),
			(r"/build/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/bugs", BuildBugsHandler),
			(r"/build/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/manage", BuildManageHandler),
			(r"/build/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/comment", BuildDetailCommentHandler),
			(r"/build/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/priority", BuildPriorityHandler),
			(r"/build/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/state", BuildStateHandler),
			(r"/build/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/watch", BuildWatchersAddHandler),
			(r"/build/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/watchers", BuildWatchersHandler),
			(r"/build/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/delete", BuildDeleteHandler),

			# Jobs
			(r"/job/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})", JobDetailHandler),
			(r"/job/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/abort", JobAbortHandler),
			(r"/job/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/buildroot", JobBuildrootHandler),
			(r"/job/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/schedule", JobScheduleHandler),

			# Builders
			(r"/builders", BuilderListHandler),
			(r"/builder/new", BuilderNewHandler),
			(r"/builder/([A-Za-z0-9\-\.]+)/enable", BuilderEnableHander),
			(r"/builder/([A-Za-z0-9\-\.]+)/disable", BuilderDisableHander),
			(r"/builder/([A-Za-z0-9\-\.]+)/delete", BuilderDeleteHandler),
			(r"/builder/([A-Za-z0-9\-\.]+)/edit", BuilderEditHandler),
			(r"/builder/([A-Za-z0-9\-\.]+)/renew", BuilderRenewPassphraseHandler),
			(r"/builder/([A-Za-z0-9\-\.]+)", BuilderDetailHandler),

			# Distributions
			(r"/distros", DistributionListHandler),
			(r"/distro/([A-Za-z0-9\-\.]+)", DistributionDetailHandler),

			# XXX THOSE URLS ARE DEPRECATED
			(r"/distribution/delete/([A-Za-z0-9\-\.]+)", DistributionDetailHandler),
			(r"/distribution/edit/([A-Za-z0-9\-\.]+)", DistributionEditHandler),

			(r"/distro/([A-Za-z0-9\-\.]+)/repo/([A-Za-z0-9\-]+)",
				RepositoryDetailHandler),
			(r"/distro/([A-Za-z0-9\-\.]+)/repo/([A-Za-z0-9\-]+)\.repo",
				RepositoryConfHandler),
			(r"/distro/([A-Za-z0-9\-\.]+)/repo/([A-Za-z0-9\-]+)/mirrorlist",
				RepositoryMirrorlistHandler),
			(r"/distro/([A-Za-z0-9\-\.]+)/repo/([A-Za-z0-9\-]+)/edit",
				RepositoryEditHandler),

			(r"/distro/([A-Za-z0-9\-\.]+)/source/([A-Za-z0-9\-\.]+)",
				DistroSourceDetailHandler),
			(r"/distro/([A-Za-z0-9\-\.]+)/source/([A-Za-z0-9\-\.]+)/commits",
				DistroSourceCommitsHandler),
			(r"/distro/([A-Za-z0-9\-\.]+)/source/([A-Za-z0-9\-\.]+)/([\w]{40})",
				DistroSourceCommitDetailHandler),
			(r"/distro/([A-Za-z0-9\-\.]+)/source/([A-Za-z0-9\-\.]+)/([\w]{40})/reset",
				DistroSourceCommitResetHandler),

			(r"/distro/([A-Za-z0-9\-\.]+)/update/create",
				DistroUpdateCreateHandler),
			(r"/distro/([A-Za-z0-9\-\.]+)/update/(\d+)/(\d+)",
				DistroUpdateDetailHandler),

			# Updates
			(r"/updates", UpdatesHandler),

			# Mirrors
			(r"/mirrors", MirrorListHandler),
			(r"/mirror/new", MirrorNewHandler),
			(r"/mirror/([A-Za-z0-9\-\.]+)/delete", MirrorDeleteHandler),
			(r"/mirror/([A-Za-z0-9\-\.]+)/edit", MirrorEditHandler),
			(r"/mirror/([A-Za-z0-9\-\.]+)", MirrorDetailHandler),

			# Key management
			(r"/keys", KeysListHandler),
			(r"/key/import", KeysImportHandler),
			(r"/key/([A-Z0-9]+)", KeysDownloadHandler),
			(r"/key/([A-Z0-9]+)/delete", KeysDeleteHandler),

			# Statistics
			(r"/statistics", StatisticsMainHandler),

			# Documents
			(r"/documents", DocsIndexHandler),
			(r"/documents/builds", DocsBuildsHandler),
			(r"/documents/users", DocsUsersHandler),
			(r"/documents/what-is-the-pakfire-build-service", DocsWhatsthisHandler),

			# Search
			(r"/search", SearchHandler),

			# Uploads
			(r"/uploads", UploadsHandler),

			# Log
			(r"/log", LogHandler),

		] + static_handlers + [

			# Everything else is catched by the 404 handler.
			(r"/.*", Error404Handler),
		])

		logging.info("Successfully initialied application")

	@property
	def pakfire(self):
		if self.__pakfire is None:
			self.__pakfire = backend.Pakfire()

		return self.__pakfire

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

		http_server = tornado.httpserver.HTTPServer(self, xheaders=True)

		# If we are not running in debug mode, we can actually run multiple
		# frontends to get best performance out of our service.
		if not self.settings["debug"]:
			http_server.bind(port)
			http_server.start(num_processes=4)
		else:
			http_server.listen(port)

		# All requests should be done after 60 seconds or they will be killed.
		self.ioloop.set_blocking_log_threshold(60)

		self.ioloop.start()

	def reload(self):
		logging.debug("Caught reload signal")
