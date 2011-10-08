#!/usr/bin/python

import tornado.web

from handlers_auth import *
from handlers_base import *
from handlers_builders import *
from handlers_search import *
from handlers_users import *

class IndexHandler(BaseHandler):
	def get(self):
		active_builds = self.pakfire.builds.get_active()
		latest_builds = self.pakfire.builds.get_latest(limit=10)
		next_builds   = self.pakfire.builds.get_next(limit=10)

		# Get counters
		counter_pending = self.pakfire.builds.count(state="pending")

		average_build_time = self.pakfire.builds.average_build_time()

		self.render("index.html", latest_builds=latest_builds,
			active_builds=active_builds, next_builds=next_builds,
			counter_pending=counter_pending, average_build_time=average_build_time)


class PackageIDDetailHandler(BaseHandler):
	def get(self, id):
		package = self.packages.get_by_id(id)
		if not package:
			return tornado.web.HTTPError(404, "Package not found: %s" % id)

		self.render("package-detail.html", package=package)


class PackageListHandler(BaseHandler):
	def get(self):
		packages = {}

		# Sort all packages in an array like "<first char>" --> [packages, ...]
		# to print them in a table for each letter of the alphabet.
		for pkg in self.pakfire.packages.get_all_names():
			c = pkg[0].lower()

			if not packages.has_key(c):
				packages[c] = []

			packages[c].append(pkg)

		self.render("package-list.html", packages=packages)


class PackageNameHandler(BaseHandler):
	def get(self, package):
		packages = self.pakfire.packages.get_by_name(package)

		if not packages:
			raise tornado.web.HTTPError(404, "Package '%s' was not found")

		# Take info from the most recent package.
		pkg = packages[0]

		self.render("package-detail-list.html", pkg=pkg, packages=packages)


class PackageDetailHandler(BaseHandler):
	def get(self, name, epoch, version, release):
		pkg = self.pakfire.packages.get_by_tuple(name, epoch, version, release)
		pkg.update()

		self.render("package-detail.html", pkg=pkg)

	@tornado.web.authenticated
	def post(self, name, epoch, version, release):
		pkg = self.pakfire.packages.get_by_tuple(name, epoch, version, release)

		action = self.get_argument("action", None)

		if action == "comment":
			vote = self.get_argument("vote", None)
			if not self.current_user.is_tester() and \
					not self.current_user.is_admin():
				vote = None

			pkg.comment(self.current_user.id, self.get_argument("text"),
				vote or "none")

		self.render("package-detail.html", pkg=pkg)


class BuildDetailHandler(BaseHandler):
	def get(self, uuid):
		build = self.pakfire.builds.get_by_uuid(uuid)

		if not build:
			raise tornado.web.HTTPError(404, "Build not found")

		self.render("build-detail.html", build=build)


class BuildPriorityHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self, uuid):
		build = self.pakfire.builds.get_by_uuid(uuid)

		if not build:
			raise tornado.web.HTTPError(404, "Build not found")

		self.render("build-priority.html", build=build)

	@tornado.web.authenticated
	def post(self, uuid):
		build = self.pakfire.builds.get_by_uuid(uuid)

		if not build:
			raise tornado.web.HTTPError(404, "Build not found")

		# Get the priority from the request data and convert it to an integer.
		# If that cannot be done, we default to zero.
		prio = self.get_argument("priority")
		try:
			prio = int(prio)
		except TypeError:
			prio = 0

		# Check if the value is in a valid range.
		if not prio in (-2, -1, 0, 1, 2):
			prio = 0

		# Save priority.
		build.priority = prio

		self.redirect("/build/%s" % build.uuid)


class BuildScheduleHandler(BaseHandler):
	allowed_types = ("test", "rebuild",)

	@tornado.web.authenticated
	def get(self, uuid):
		type = self.get_argument("type")
		assert type in self.allowed_types

		build = self.pakfire.builds.get_by_uuid(uuid)
		if not build:
			raise tornado.web.HTTPError(404, "Build not found")

		self.render("build-schedule-%s.html" % type, type=type, build=build)

	@tornado.web.authenticated
	def post(self, uuid):
		type = self.get_argument("type")
		assert type in self.allowed_types

		build = self.pakfire.builds.get_by_uuid(uuid)
		if not build:
			raise tornado.web.HTTPError(404, "Build not found")

		# Get the start offset.
		offset = self.get_argument("offset", 0)
		try:
			offset = int(offset)
		except TypeError:
			offset = 0

		# Submit the build.
		if type == "test":
			build.schedule_test(offset)
		elif type == "rebuild":
			build.schedule_rebuild(offset)

		self.redirect("/build/%s" % build.uuid)


class BuildListHandler(BaseHandler):
	def get(self):
		builder = self.get_argument("builder", None)
		state = self.get_argument("state", None)

		builds = self.pakfire.builds.get_latest(state=state, builder=builder,
			limit=25)

		self.render("build-list.html", builds=builds)


class BuildFilterHandler(BaseHandler):
	def get(self):
		builders = self.pakfire.builders.get_all()

		self.render("build-filter.html", builders=builders)


class DocsIndexHandler(BaseHandler):
	def get(self):
		self.render("docs-index.html")


class DocsBuildsHandler(BaseHandler):
	def get(self):
		self.render("docs-build.html")


class DocsUsersHandler(BaseHandler):
	def get(self):
		self.render("docs-users.html")


class SourceListHandler(BaseHandler):
	def get(self):
		sources = self.pakfire.sources.get_all()

		self.render("source-list.html", sources=sources)


class SourceDetailHandler(BaseHandler):
	def get(self, id):
		source = self.pakfire.sources.get_by_id(id)

		self.render("source-detail.html", source=source)


class FileDetailHandler(BaseHandler):
	def get(self, uuid):
		pkg, file = self.pakfire.packages.get_with_file_by_uuid(uuid)

		if not file:
			raise tornado.web.HTTPError(404, "File not found")

		self.render("file-detail.html", pkg=pkg, file=file)


class DistributionListHandler(BaseHandler):
	def get(self):
		distros = self.pakfire.distros.get_all()

		self.render("distro-list.html", distros=distros)


class DistributionDetailHandler(BaseHandler):
	def get(self, name):
		distro = self.pakfire.distros.get_by_name(name)
		if not distro:
			raise tornado.web.HTTPError(404, "Distro not found")

		self.render("distro-detail.html", distro=distro)


class DistributionEditHandler(BaseHandler):
	def prepare(self):
		self.arches = self.pakfire.builders.get_all_arches()
		self.sources = self.pakfire.sources.get_all()

	@tornado.web.authenticated
	def get(self, name):
		distro = self.pakfire.distros.get_by_name(name)
		if not distro:
			raise tornado.web.HTTPError(404, "Distro not found")

		self.render("distro-edit.html", distro=distro, arches=self.arches,
			sources=self.sources)

	@tornado.web.authenticated
	def post(self, name):
		distro = self.pakfire.distros.get_by_name(name)
		if not distro:
			raise tornado.web.HTTPError(404, "Distro not found")

		name = self.get_argument("name", distro.name)
		vendor = self.get_argument("vendor", distro.vendor)
		slogan = self.get_argument("slogan", distro.slogan)
		arches = self.get_argument("arches", distro.arches)
		sources = self.get_argument("sources", distro.sources)

		distro.set("name", name)
		distro.set("vendor", vendor)
		distro.set("slogan", slogan)
		distro.set("arches", arches)
		distro.set("sources", sources)

		self.redirect("/distribution/%s" % distro.sname)


class LogHandler(BaseHandler):
	def get(self):
		self.render("log.html", log=self.pakfire.log)


class RepositoryDetailHandler(BaseHandler):
	def get(self, distro, repo):
		distro = self.pakfire.distros.get_by_name(distro)
		if not distro:
			raise tornado.web.HTTPError(404)

		repo = distro.get_repo(repo)
		if not repo:
			raise tornado.web.HTTPError(404)

		self.render("repository-detail.html", distro=distro, repo=repo)


class RepoActionHandler(BaseHandler):
	@tornado.web.authenticated
	def post(self, type):
		assert type in ("run", "remove")

		action_id = self.get_argument("id")

		action = self.pakfire.repos.get_action_by_id(action_id)
		if not action:
			raise tornado.web.HTTPError(400)

		if type == "run":
			action.run(self.current_user)

		elif type == "remove":
			action.delete(self.current_user)
