#!/usr/bin/python

import re
import string
import textile
import tornado.escape
import tornado.web

import backend.users
from backend.constants import *

class UIModule(tornado.web.UIModule):
	@property
	def pakfire(self):
		return self.handler.application.pakfire

	@property
	def settings(self):
		return self.pakfire.settings


class TextModule(UIModule):
	__cache = {}

	LINK = """<a href="%s" target="_blank">%s</a>"""

	@property
	def bugzilla_url(self):
		return self.settings.get("bugzilla_url", "")

	@property
	def bugzilla_pattern(self):
		if not self.__cache.has_key("bugzilla_pattern"):
			self.__cache["bugzilla_pattern"] = re.compile(BUGZILLA_PATTERN)

		return self.__cache["bugzilla_pattern"]

	@property
	def bugzilla_repl(self):
		return self.LINK % (self.bugzilla_url % { "bugid" : r"\2" }, r"\1\2")

	@property
	def cve_url(self):
		return self.settings.get("cve_url", "")

	@property
	def cve_pattern(self):
		if not self.__cache.has_key("cve_pattern"):
			self.__cache["cve_pattern"] = re.compile(CVE_PATTERN)

		return self.__cache["cve_pattern"]

	@property
	def cve_repl(self):
		return self.LINK % (self.cve_url % r"\3", r"\1\2\3")

	def render(self, text, pre=False, remove_linebreaks=True):
		link = """<a href="%s" target="_blank">%s</a>"""

		if remove_linebreaks:
			text = text.replace("\n", " ")

		# Escape the text and create make urls clickable.
		text = tornado.escape.xhtml_escape(text)
		text = tornado.escape.linkify(text, shorten=True,
			extra_params='target="_blank"')

		# Search for bug ids that need to be linked to bugzilla.
		if self.bugzilla_url:
			text = re.sub(self.bugzilla_pattern, self.bugzilla_repl, text, re.I|re.U)

		# Search for CVE numbers and create hyperlinks.
		if self.cve_url:
			text = re.sub(self.cve_pattern, self.cve_repl, text, re.I|re.U)

		if pre:
			return "<pre>%s</pre>" % text

		return textile.textile(text)


class ModalModule(UIModule):
	def render(self, what, **kwargs):
		what = "modules/modal-%s.html" % what

		return self.render_string(what, **kwargs)


class BuildHeadlineModule(UIModule):
	def render(self, prefix, build, short=False, shorter=False):
		if shorter:
			short = True

		return self.render_string("modules/build-headline.html",
			prefix=prefix, build=build, pkg=build.pkg, short=short, shorter=shorter)


class BugsTableModule(UIModule):
	def render(self, pkg, bugs):
		return self.render_string("modules/bugs-table.html",
			pkg=pkg, bugs=bugs)


class ChangelogModule(UIModule):
	def render(self, name=None, builds=None, *args, **kwargs):
		if not builds:
			builds = self.pakfire.builds.get_changelog(name, *args, **kwargs)

		return self.render_string("modules/changelog/index.html", builds=builds)


class ChangelogEntryModule(UIModule):
	def render(self, build):
		return self.render_string("modules/changelog/entry.html", build=build)


class CommitsTableModule(UIModule):
	def render(self, distro, source, commits, full_format=True):
		return self.render_string("modules/commits-table.html",
			distro=distro, source=source, commits=commits,
			full_format=full_format)


class FooterModule(UIModule):
	def render(self):
		return self.render_string("modules/footer.html")


class PackagesTableModule(UIModule):
	def render(self, job, packages):
		return self.render_string("modules/packages-table.html", job=job,
			packages=packages)


class PackageTable2Module(UIModule):
	def render(self, packages):
		return self.render_string("modules/package-table-detail.html",
			packages=packages)


class FilesTableModule(UIModule):
	def render(self, files):
		return self.render_string("modules/files-table.html", files=files)


class LogFilesTableModule(UIModule):
	def render(self, job, files):
		return self.render_string("modules/log-files-table.html", job=job,
			files=files)


class PackageHeaderModule(UIModule):
	def render(self, pkg):
		return self.render_string("modules/package-header.html", pkg=pkg)


class PackageFilesTableModule(UIModule):
	def render(self, pkg, filelist):
		return self.render_string("modules/packages-files-table.html",
			pkg=pkg, filelist=filelist)


class BuildTableModule(UIModule):
	def render(self, builds, **kwargs):
		settings = dict(
			show_user = False,
			show_repo = False,
			show_repo_time = False,
			show_can_move_forward = False,
			show_when = True,
		)
		settings.update(kwargs)

		return self.render_string("modules/build-table.html",
			builds=builds, **settings)


class BuildStateWarningsModule(UIModule):
	def render(self, build):
		return self.render_string("modules/build-state-warnings.html", build=build)


class JobsTableModule(UIModule):
	def render(self, build, jobs=None, type="release"):
		if jobs is None:
			jobs = build.jobs

		return self.render_string("modules/jobs-table.html", build=build,
			jobs=jobs, type=type)


class JobsListModule(UIModule):
	def render(self, jobs, show_builder=False):
		return self.render_string("modules/jobs-list.html", jobs=jobs,
			show_builder=show_builder)


class RepositoryTableModule(UIModule):
	def render(self, distro, repos):
		return self.render_string("modules/repository-table.html",
			distro=distro, repos=repos)


class SourceTableModule(UIModule):
	def render(self, distro, sources):
		return self.render_string("modules/source-table.html",
			distro=distro, sources=sources)


class CommentsTableModule(UIModule):
	def render(self, comments, show_package=False, show_user=True):
		pkgs, users = {}, {}
		for comment in comments:
			if show_package:
				try:
					pkg = pkgs[comment.pkg_id]
				except KeyError:
					pkg = pkgs[comment.pkg_id] = \
						self.pakfire.packages.get_by_id(comment.pkg_id)

				comment["pkg"] = pkg

			if show_user:
				try:
					user = users[comment.user_id]
				except KeyError:
					user = users[comment.user_id] = \
						self.pakfire.users.get_by_id(comment.user_id)

				comment["user"] = user

		return self.render_string("modules/comments-table.html",
			comments=comments, show_package=show_package, show_user=show_user)


class LogModule(UIModule):
	def render(self, entries, **args):
		return self.render_string("modules/log.html",
			entries=entries, args=args)


class LogEntryModule(UIModule):
	def render(self, entry, small=None, **args):
		if small or entry.system_msg:
			template = "modules/log-entry-small.html"
		else:
			template = "modules/log-entry.html"

		return self.render_string(template, entry=entry, u=entry.user, **args)


class LogEntryCommentModule(LogEntryModule):
	def render(self, entry, **args):
		return self.render_string("modules/log-entry-comment.html",
			entry=entry, u=entry.user, **args)


class MaintainerModule(UIModule):
	def render(self, maintainer):
		if isinstance(maintainer, backend.users.User):
			type = "user"
		else:
			type = "string"

		return self.render_string("modules/maintainer.html",
			type=type, maintainer=maintainer)


class BuildLogModule(UIModule):
	# XXX deprecated
	def render(self, messages):
		_ = self.locale.translate

		for message in messages:
			try:
				msg = LOG2MSG[message.message]
				message["message"] = _(msg)
			except KeyError:
				pass

		return self.render_string("modules/build-log.html", messages=messages)


class LogTableModule(UIModule):
	def render(self, messages, links=["pkg",]):
		for message in messages:
			try:
				message["message"] = LOG2MSG[message.message]
			except KeyError:
				pass

			if message.build_id:
				message["build"] = self.pakfire.builds.get_by_id(message.build_id)

			elif message.pkg_id:
				message["pkg"] = self.pakfire.packages.get_by_id(message.pkg_id)

		return self.render_string("modules/log-table.html",
			messages=messages, links=links)


class UsersTableModule(UIModule):
	def render(self, users):
		return self.render_string("modules/user-table.html", users=users)


class BuildOffsetModule(UIModule):
	def render(self):
		return self.render_string("modules/build-offset.html")


class RepoActionsTableModule(UIModule):
	def render(self, repo):
		actions = repo.get_actions()

		return self.render_string("modules/repo-actions-table.html",
			repo=repo, actions=actions)


class UpdatesTableModule(UIModule):
	def render(self, updates):
		return self.render_string("modules/updates-table.html", updates=updates)


class WatchersSidebarTableModule(UIModule):
	def css_files(self):
		return "css/watchers-sidebar-table.css"

	def render(self, build, watchers, limit=5):
		# Sort the watchers by their realname.
		watchers.sort(key=lambda watcher: watcher.realname)

		return self.render_string("modules/watchers-sidebar-table.html",
			build=build, watchers=watchers, limit=limit)
