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
from ..constants import *
from ..decorators import *

from .handlers import *

from . import handlers_api
from . import mirrors
from . import ui_modules

# Enable logging
tornado.options.define("debug", default=False, help="Run in debug mode", type=bool)
tornado.options.parse_command_line()

class Application(tornado.web.Application):
	def __init__(self, **_settings):
		settings = dict(
			debug = tornado.options.options.debug,
			gzip  = True,
			login_url = "/login",
			template_path = TEMPLATESDIR,
			static_path = STATICDIR,
			ui_modules = {
				"Text"               : ui_modules.TextModule,
				"Modal"              : ui_modules.ModalModule,

				"Footer"             : ui_modules.FooterModule,

				# Logging
				"Log"                : ui_modules.LogModule,
				"LogEntry"           : ui_modules.LogEntryModule,
				"LogEntryComment"    : ui_modules.LogEntryCommentModule,

				"BuildHeadline"      : ui_modules.BuildHeadlineModule,
				"BuildStateWarnings" : ui_modules.BuildStateWarningsModule,

				"BugsTable"          : ui_modules.BugsTableModule,
				"BuildLog"           : ui_modules.BuildLogModule,
				"BuildOffset"        : ui_modules.BuildOffsetModule,
				"BuildTable"         : ui_modules.BuildTableModule,

				# Changelog
				"Changelog"          : ui_modules.ChangelogModule,
				"ChangelogEntry"     : ui_modules.ChangelogEntryModule,

				# Jobs
				"JobsList"           : ui_modules.JobsListModule,
				"JobsStatus"         : ui_modules.JobsStatusModule,

				# Packages
				"PackagesDependencyTable" : ui_modules.PackagesDependencyTableModule,

				"CommitMessage"      : ui_modules.CommitMessageModule,
				"CommitsTable"       : ui_modules.CommitsTableModule,
				"JobsBoxes"          : ui_modules.JobsBoxesModule,
				"JobState"           : ui_modules.JobStateModule,
				"JobsTable"          : ui_modules.JobsTableModule,
				"CommentsTable"      : ui_modules.CommentsTableModule,
				"FilesTable"         : ui_modules.FilesTableModule,
				"LogTable"           : ui_modules.LogTableModule,
				"LogFilesTable"      : ui_modules.LogFilesTableModule,
				"Maintainer"         : ui_modules.MaintainerModule,
				"PackagesTable"      : ui_modules.PackagesTableModule,
				"PackageTable2"      : ui_modules.PackageTable2Module,
				"PackageHeader"      : ui_modules.PackageHeaderModule,
				"PackageFilesTable"  : ui_modules.PackageFilesTableModule,
				"RepositoryTable"    : ui_modules.RepositoryTableModule,
				"RepoActionsTable"   : ui_modules.RepoActionsTableModule,
				"SourceTable"        : ui_modules.SourceTableModule,
				"UpdatesTable"       : ui_modules.UpdatesTableModule,
				"UsersTable"         : ui_modules.UsersTableModule,
				"WatchersSidebarTable" : ui_modules.WatchersSidebarTableModule,

				"HeadingDate"        : ui_modules.HeadingDateModule,

				"SelectLocale"       : ui_modules.SelectLocaleModule,
				"SelectTimezone"     : ui_modules.SelectTimezoneModule,
			},
			ui_methods = {
				"format_time"        : self.format_time,
			},
			xsrf_cookies = True,
		)
		settings.update(_settings)

		# Load translations.
		tornado.locale.load_gettext_translations(LOCALEDIR, PACKAGE_NAME)

		tornado.web.Application.__init__(self, [
			# Entry site that lead the user to index
			(r"/", IndexHandler),

			# Handle all the users logins/logouts/registers and stuff.
			(r"/login", LoginHandler),
			(r"/logout", LogoutHandler),
			(r"/register", RegisterHandler),
			(r"/password-recovery", PasswordRecoveryHandler),

			# User profiles
			(r"/users", UsersHandler),
			(r"/user/(\w+)/impersonate", UserImpersonateHandler),
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
			(r"/mirrors",					mirrors.MirrorListHandler),
			(r"/mirror/new",				mirrors.MirrorNewHandler),
			(r"/mirror/([\w\-\.]+)/delete",	mirrors.MirrorDeleteHandler),
			(r"/mirror/([\w\-\.]+)/edit",	mirrors.MirrorEditHandler),
			(r"/mirror/([\w\-\.]+)",		mirrors.MirrorDetailHandler),

			# Key management
			(r"/keys", KeysListHandler),
			(r"/key/import", KeysImportHandler),
			(r"/key/([A-Z0-9]+)", KeysDownloadHandler),
			(r"/key/([A-Z0-9]+)/delete", KeysDeleteHandler),

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
		], **settings)

		logging.info("Successfully initialied application")

	@lazy_property
	def backend(self):
		"""
			Backend connection
		"""
		return Backend()

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
