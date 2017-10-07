#!/usr/bin/python
# encoding: utf-8

import logging
import multiprocessing
import os.path
import tornado.httpserver
import tornado.locale
import tornado.options
import tornado.web

from .. import Backend

from . import handlers_api

from .handlers import *
from .ui_modules import *

BASEDIR = os.path.join(os.path.dirname(__file__), "..", "data")

# Enable logging
tornado.options.define("debug", default=False, help="Run in debug mode", type=bool)
tornado.options.parse_command_line()

class Application(tornado.web.Application):
	def __init__(self):
		self.__pakfire = None

		settings = dict(
			debug = tornado.options.options.debug,
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

				# Builders
				"BuildersLoad"       : BuildersLoadModule,

				"BuildHeadline"      : BuildHeadlineModule,
				"BuildStateWarnings" : BuildStateWarningsModule,

				"BugsTable"          : BugsTableModule,
				"BuildLog"           : BuildLogModule,
				"BuildOffset"        : BuildOffsetModule,
				"BuildTable"         : BuildTableModule,

				# Changelog
				"Changelog"          : ChangelogModule,
				"ChangelogEntry"     : ChangelogEntryModule,

				# Jobs
				"JobsList"           : JobsListModule,
				"JobsStatus"         : JobsStatusModule,

				# Packages
				"PackagesDependencyTable" : PackagesDependencyTableModule,

				"CommitMessage"      : CommitMessageModule,
				"CommitsTable"       : CommitsTableModule,
				"JobsBoxes"          : JobsBoxesModule,
				"JobState"           : JobStateModule,
				"JobsTable"          : JobsTableModule,
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

				"HeadingDate"        : HeadingDateModule,

				"SelectLocale"       : SelectLocaleModule,
				"SelectTimezone"     : SelectTimezoneModule,
			},
			ui_methods = {
				"format_eta"         : self.format_eta,
				"format_time"        : self.format_time,
			},
			xsrf_cookies = True,
		)

		# Load translations.
		tornado.locale.load_gettext_translations(LOCALEDIR, PACKAGE_NAME)

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
			(r"/password-recovery", PasswordRecoveryHandler),

			# User profiles
			(r"/users", UsersHandler),
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
			(r"/package/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/download(.*)", PackageFileDownloadHandler),
			(r"/package/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/view(.*)", PackageFileViewHandler),
			(r"/package/([\w\-\+]+)", PackageNameHandler),
			(r"/package/([\w\-\+]+)/builds/scratch", PackageScratchBuildsHandler),
			(r"/package/([\w\-\+]+)/builds/times", PackageBuildsTimesHandler),
			(r"/package/([\w\-\+]+)/changelog", PackageChangelogHandler),
			(r"/package/([\w\-\+]+)/properties", PackagePropertiesHandler),

			# Files
			(r"/file/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})", FileDetailHandler),

			# Builds
			(r"/builds", BuildsHandler),
			(r"/builds/filter", BuildFilterHandler),
			(r"/builds/queue", BuildQueueHandler),
			(r"/builds/comments", BuildsCommentsHandler),
			(r"/builds/comments/(\w+)", BuildsCommentsHandler),
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
			(r"/jobs", JobsIndexHandler),
			(r"/jobs/filter", JobsFilterHandler),
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

			# Sessions
			(r"/sessions", SessionsHandler),

			# API handlers
			(r"/api/packages/autocomplete", handlers_api.ApiPackagesAutocomplete),

		] + static_handlers + [

			# Everything else is catched by the 404 handler.
			(r"/.*", Error404Handler),
		])

		logging.info("Successfully initialied application")

	@property
	def pakfire(self):
		if self.__pakfire is None:
			self.__pakfire = Backend()

		return self.__pakfire

	def __del__(self):
		logging.info("Shutting down application")

	@property
	def ioloop(self):
		return tornado.ioloop.IOLoop.instance()

	def shutdown(self, *args):
		logging.debug("Caught shutdown signal")
		self.ioloop.stop()

	def run(self, port=7001):
		logging.debug("Going to background")

		http_server = tornado.httpserver.HTTPServer(self, xheaders=True)

		# If we are not running in debug mode, we can actually run multiple
		# frontends to get best performance out of our service.
		if self.settings.get("debug", False):
			http_server.listen(port)
		else:
			cpu_count = multiprocessing.cpu_count()

			http_server.bind(port)
			http_server.start(num_processes=cpu_count)

		# All requests should be done after 60 seconds or they will be killed.
		self.ioloop.set_blocking_log_threshold(60)

		self.ioloop.start()

	def reload(self):
		logging.debug("Caught reload signal")

	## UI methods

	def format_eta(self, handler, (s, stddev)):
		if s is None:
			_ = handler.locale.translate
			return _("Unknown")

		if s < 0:
			s = 0

		return u"%s ± %s" % (
			self.format_time(handler, s),
			self.format_time_short(handler, stddev / 2),
		)

	def format_time(self, handler, s, shorter=False):
		_ = handler.locale.translate

		hrs, s = divmod(s, 3600)
		min, s = divmod(s, 60)

		if s >= 30:
			min += 1

		if shorter and not hrs:
			return _("%(min)d min") % { "min" : min }

		return _("%(hrs)d:%(min)02d hrs") % {"hrs" : hrs, "min" : min}

	def format_time_short(self, handler, s):
		_ = handler.locale.translate

		hrs = s / 3600
		if hrs >= 1:
			return _("%dh") % hrs

		min = s / 60
		if min >= 1:
			return _("%dm") % min

		return _("%ds") % s
