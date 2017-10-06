#!/usr/bin/python

from __future__ import division

import datetime
import itertools
import math
import pytz
import re
import string
import tornado.escape
import tornado.web

from .. import users
from ..constants import *

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

	def split_paragraphs(self, s):
		for group_seperator, line_iteration in itertools.groupby(s.splitlines(True), key=unicode.isspace):
			if group_seperator:
				continue

			paragraph = "".join(line_iteration)
			yield paragraph.replace("\n", " ")

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

		return text


class CommitMessageModule(TextModule):
	def render(self, commit):
		s = "h5. %s\n\n" % commit.subject

		paragraphs = self.split_paragraphs(commit.message)
		s += "\n\n".join(paragraphs)

		return TextModule.render(self, s, remove_linebreaks=False)


class ModalModule(UIModule):
	def render(self, what, **kwargs):
		what = "modules/modal-%s.html" % what

		return self.render_string(what, **kwargs)


class BuildHeadlineModule(UIModule):
	def render(self, build, short=False, shorter=False):
		if shorter:
			short = True

		return self.render_string("modules/build-headline.html",
			build=build, pkg=build.pkg, short=short, shorter=shorter)


class JobsStatusModule(UIModule):
	def render(self, build):
		return self.render_string("modules/jobs/status.html",
			build=build, jobs=build.jobs)


class BuildersLoadModule(UIModule):
	def render(self):
		load = self.pakfire.builders.get_load()

		return self.render_string("modules/builders/load.html", load=load)


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


class HeadingDateModule(UIModule):
	def render(self, date):
		_ = self.locale.translate

		# Check if this is today.
		today = datetime.date.today()
		if date == today:
			return _("Today")

		# Check if this was yesterday.
		yesterday = today - datetime.timedelta(days=1)
		if date == yesterday:
			return _("Yesterday")

		# Convert date to datetime.
		date = datetime.datetime(date.year, date.month, date.day)

		return self.locale.format_date(date, shorter=True, relative=False)


class PackagesTableModule(UIModule):
	def render(self, job, packages):
		return self.render_string("modules/packages-table.html", job=job,
			packages=packages)


class PackagesDependencyTableModule(UIModule):
	def render(self, pkg):
		if pkg.type == "source":
			all_deps = [
				(None, pkg.requires),
			]
		else:
			all_deps = [
				("provides", pkg.provides),
				("requires", pkg.requires),
				("prerequires", pkg.prerequires),
				("conflicts", pkg.conflicts),
				("obsoletes", pkg.obsoletes),
				("recommends", pkg.recommends),
				("suggests", pkg.suggests),
			]

		has_deps = []
		for name, deps in all_deps:
			if deps:
				has_deps.append((name, deps))

		if len(has_deps):
			span = math.floor(12 / len(has_deps))

			if span > 3:
				span = 3
		else:
			span = 12

		return self.render_string("modules/packages/dependency-table.html",
			pkg=pkg, dependencies=has_deps, span=span)


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

		dates = {}

		for b in builds:
			try:
				dates[b.date].append(b)
			except KeyError:
				dates[b.date] = [b,]

		dates = sorted(dates.items(), reverse=True)

		return self.render_string("modules/build-table.html", dates=dates, **settings)


class BuildStateWarningsModule(UIModule):
	def render(self, build):
		return self.render_string("modules/build-state-warnings.html", build=build)


class JobsBoxesModule(UIModule):
	def render(self, build, jobs=None):
		if jobs is None:
			jobs = build.jobs

		return self.render_string("modules/jobs/boxes.html",
			build=build, jobs=jobs)


class JobStateModule(UIModule):
	def render(self, job, cls=None, show_arch=False, show_icon=False, plain=False):
		state = job.state

		_ = self.locale.translate
		classes = []

		icon = None
		if state == "aborted":
			text = _("Aborted")
			classes.append("muted")
			icon = "icon-warning-sign"

		elif state == "dependency_error":
			text = _("Dependency problem")
			classes.append("text-warning")
			icon = "icon-random"

		elif state == "dispatching":
			text = _("Dispatching")
			classes.append("text-info")
			icon = "icon-download-alt"

		elif state == "failed":
			text = _("Failed")
			classes.append("text-error")
			icon = "icon-remove"

		elif state == "finished":
			text = _("Finished")
			classes.append("text-success")
			icon = "icon-ok"

		elif state == "new":
			text = _("New")
			classes.append("muted")
			icon = "icon-asterisk"

		elif state == "pending":
			text = _("Pending")
			classes.append("muted")
			icon = "icon-time"

		elif state == "running":
			text = _("Running")
			classes.append("text-info")
			icon = "icon-cogs"

		elif state == "uploading":
			text = _("Uploading")
			classes.append("text-info")
			icon = "icon-upload-alt"

		# Return just the string, is state is unknown.
		else:
			text = _("Unknown: %s") % state
			classes.append("muted")

		if plain:
			return text

		if cls:
			classes.append(cls)

		if show_arch:
			text = job.arch.name

		if show_icon and icon:
			text = """<i class="%s"></i> %s""" % (icon, text)

		return """<span class="%s">%s</span>""" % (" ".join(classes), text)


class JobsTableModule(UIModule):
	def render(self, build, jobs=None, type="release"):
		if jobs is None:
			jobs = build.jobs

		return self.render_string("modules/jobs-table.html", build=build,
			jobs=jobs, type=type)


class JobsListModule(UIModule):
	def render(self, jobs):
		return self.render_string("modules/jobs/list.html", jobs=jobs)


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
		if small or not entry.user:
			template = "modules/log-entry-small.html"
		else:
			template = "modules/log-entry.html"

		return self.render_string(template, entry=entry, u=entry.user,
			show_build=False, **args)


class LogEntryCommentModule(LogEntryModule):
	def render(self, entry, show_build=False, **args):
		return self.render_string("modules/log-entry-comment.html",
			entry=entry, u=entry.user, show_build=show_build, **args)


class MaintainerModule(UIModule):
	def render(self, maintainer):
		if isinstance(maintainer, users.User):
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


class SelectLocaleModule(UIModule):
	LOCALE_NAMES = [
		# local code, English name, name
		("ca_ES", u"Catalan", "Catal\xc3\xa0"),
		("da_DK", u"Danish", u"Dansk"),
		("de_DE", u"German", u"Deutsch"),
		("en_GB", u"English (UK)", u"English (UK)"),
		("en_US", u"English (US)", u"English (US)"),
		("es_ES", u"Spanish (Spain)", u"Espa\xf1ol (Espa\xf1a)"),
		("es_LA", u"Spanish", u"Espa\xf1ol"),
		("fr_CA", u"French (Canada)", u"Fran\xe7ais (Canada)"),
		("fr_FR", u"French", u"Fran\xe7ais"),
		("it_IT", u"Italian", u"Italiano"),
		("km_KH", u"Khmer", u"\u1797\u17b6\u179f\u17b6\u1781\u17d2\u1798\u17c2\u179a"),
		("nl_NL", u"Dutch", u"Nederlands"),
		("pt_BR", u"Portuguese (Brazil)", u"Portugu\xeas (Brasil)"),
		("pt_PT", u"Portuguese (Portugal)", u"Portugu\xeas (Portugal)"),
		("ro_RO", u"Romanian", u"Rom\xe2n\u0103"),
		("ru_RU", u"Russian", u"\u0440\u0443\u0441\u0441\u043a\u0438\u0439"),
		("uk_UA", u"Ukrainian", u"\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430"),
	]

	# Sort the list of locales by their English name.
	LOCALE_NAMES.sort(key=lambda x: x[1])

	def render(self, name=None, id=None, preselect=None):
		return self.render_string("modules/select/locale.html",
			name=name, id=id, preselect=preselect, supported_locales=self.LOCALE_NAMES)


class SelectTimezoneModule(UIModule):
	def render(self, name=None, id=None, preselect=None):
		return self.render_string("modules/select/timezone.html",
			name=name, id=id, preselect=preselect,
			supported_timezones=pytz.common_timezones)
