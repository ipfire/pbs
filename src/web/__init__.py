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

# Import all handlers
from . import api
from . import auth
from . import builders
from . import builds
from . import distributions
from . import errors
from . import jobs
from . import keys
from . import mirrors
from . import packages
from . import search
from . import updates
from . import users
from .handlers import *

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
			(r"/login", auth.LoginHandler),
			(r"/logout", auth.LogoutHandler),
			(r"/register", auth.RegisterHandler),
			(r"/password-recovery", auth.PasswordRecoveryHandler),

			# User profiles
			(r"/users", users.UsersHandler),
			(r"/user/(\w+)/impersonate", users.UserImpersonateHandler),
			(r"/user/(\w+)/passwd", users.UserPasswdHandler),
			(r"/user/(\w+)/delete", users.UserDeleteHandler),
			(r"/user/(\w+)/edit", users.UserEditHandler),
			(r"/user/(\w+)/activate", auth.ActivationHandler),
			(r"/user/(\w+)", users.UserHandler),
			(r"/profile", users.UserHandler),
			(r"/profile/builds", users.UsersBuildsHandler),

			# Packages
			(r"/packages", packages.IndexHandler),
			(r"/package/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})", packages.PackageDetailHandler),
			(r"/package/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/download(.*)", packages.PackageFileDownloadHandler),
			(r"/package/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/view(.*)", packages.PackageFileViewHandler),
			(r"/package/([\w\-\+]+)", packages.PackageNameHandler),
			(r"/package/([\w\-\+]+)/builds/scratch", packages.PackageScratchBuildsHandler),
			(r"/package/([\w\-\+]+)/builds/times", packages.PackageBuildsTimesHandler),
			(r"/package/([\w\-\+]+)/changelog", packages.PackageChangelogHandler),
			(r"/package/([\w\-\+]+)/properties", packages.PackagePropertiesHandler),

			# Files
			(r"/file/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})", FileDetailHandler),

			# Builds
			(r"/builds", builds.BuildsHandler),
			(r"/builds/filter", builds.BuildFilterHandler),
			(r"/builds/queue", builds.BuildQueueHandler),
			(r"/builds/comments", builds.BuildsCommentsHandler),
			(r"/builds/comments/(\w+)", builds.BuildsCommentsHandler),
			(r"/build/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})", builds.BuildDetailHandler),
			(r"/build/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/bugs", builds.BuildBugsHandler),
			(r"/build/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/manage", builds.BuildManageHandler),
			(r"/build/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/comment", builds.BuildDetailCommentHandler),
			(r"/build/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/priority", builds.BuildPriorityHandler),
			(r"/build/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/state", builds.BuildStateHandler),
			(r"/build/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/watch", builds.BuildWatchersAddHandler),
			(r"/build/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/watchers", builds.BuildWatchersHandler),
			(r"/build/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/delete", builds.BuildDeleteHandler),

			(r"/queue", jobs.ShowQueueHandler),
			(r"/queue/([\w_]+)", jobs.ShowQueueHandler),

			# Jobs
			(r"/job/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})", jobs.JobDetailHandler),
			(r"/job/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/abort", jobs.JobAbortHandler),
			(r"/job/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/buildroot", jobs.JobBuildrootHandler),
			(r"/job/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})/schedule", jobs.JobScheduleHandler),

			# Builders
			(r"/builders", builders.BuilderListHandler),
			(r"/builder/new", builders.BuilderNewHandler),
			(r"/builder/([A-Za-z0-9\-\.]+)/enable", builders.BuilderEnableHander),
			(r"/builder/([A-Za-z0-9\-\.]+)/disable", builders.BuilderDisableHander),
			(r"/builder/([A-Za-z0-9\-\.]+)/delete", builders.BuilderDeleteHandler),
			(r"/builder/([A-Za-z0-9\-\.]+)/edit", builders.BuilderEditHandler),
			(r"/builder/([A-Za-z0-9\-\.]+)/renew", builders.BuilderRenewPassphraseHandler),
			(r"/builder/([A-Za-z0-9\-\.]+)", builders.BuilderDetailHandler),

			# Distributions
			(r"/distros", distributions.DistributionListHandler),
			(r"/distro/([A-Za-z0-9\-\.]+)", distributions.DistributionDetailHandler),

			# XXX THOSE URLS ARE DEPRECATED
			(r"/distribution/delete/([A-Za-z0-9\-\.]+)", distributions.DistributionDetailHandler),
			(r"/distribution/edit/([A-Za-z0-9\-\.]+)", distributions.DistributionEditHandler),

			(r"/distro/([A-Za-z0-9\-\.]+)/repo/([A-Za-z0-9\-]+)",
				RepositoryDetailHandler),
			(r"/distro/([A-Za-z0-9\-\.]+)/repo/([A-Za-z0-9\-]+)\.repo",
				RepositoryConfHandler),
			(r"/distro/([A-Za-z0-9\-\.]+)/repo/([A-Za-z0-9\-]+)/mirrorlist",
				RepositoryMirrorlistHandler),
			(r"/distro/([A-Za-z0-9\-\.]+)/repo/([A-Za-z0-9\-]+)/edit",
				RepositoryEditHandler),

			(r"/distro/([A-Za-z0-9\-\.]+)/source/([A-Za-z0-9\-\.]+)",
				distributions.DistroSourceDetailHandler),
			(r"/distro/([A-Za-z0-9\-\.]+)/source/([A-Za-z0-9\-\.]+)/commits",
				distributions.DistroSourceCommitsHandler),
			(r"/distro/([A-Za-z0-9\-\.]+)/source/([A-Za-z0-9\-\.]+)/([\w]{40})",
				distributions.DistroSourceCommitDetailHandler),
			(r"/distro/([A-Za-z0-9\-\.]+)/source/([A-Za-z0-9\-\.]+)/([\w]{40})/reset",
				distributions.DistroSourceCommitResetHandler),

			(r"/distro/([A-Za-z0-9\-\.]+)/update/create",
				distributions.DistroUpdateCreateHandler),
			(r"/distro/([A-Za-z0-9\-\.]+)/update/(\d+)/(\d+)",
				distributions.DistroUpdateDetailHandler),

			# Updates
			(r"/updates", updates.UpdatesHandler),

			# Mirrors
			(r"/mirrors",					mirrors.MirrorListHandler),
			(r"/mirror/new",				mirrors.MirrorNewHandler),
			(r"/mirror/([\w\-\.]+)/delete",	mirrors.MirrorDeleteHandler),
			(r"/mirror/([\w\-\.]+)/edit",	mirrors.MirrorEditHandler),
			(r"/mirror/([\w\-\.]+)",		mirrors.MirrorDetailHandler),

			# Key management
			(r"/keys", keys.KeysListHandler),
			(r"/key/import", keys.KeysImportHandler),
			(r"/key/([A-Z0-9]+)", keys.KeysDownloadHandler),
			(r"/key/([A-Z0-9]+)/delete", keys.KeysDeleteHandler),

			# Documents
			(r"/documents", DocsIndexHandler),
			(r"/documents/builds", DocsBuildsHandler),
			(r"/documents/users", DocsUsersHandler),
			(r"/documents/what-is-the-pakfire-build-service", DocsWhatsthisHandler),

			# Search
			(r"/search", search.SearchHandler),

			# Uploads
			(r"/uploads", UploadsHandler),

			# Log
			(r"/log", LogHandler),

			# Sessions
			(r"/sessions", SessionsHandler),

			# API handlers
			(r"/api/packages/autocomplete", api.ApiPackagesAutocomplete),
		], default_handler_class=errors.Error404Handler, **settings)

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
