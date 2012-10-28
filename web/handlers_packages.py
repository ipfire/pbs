#!/usr/bin/python

import tornado.web

from handlers_base import BaseHandler

class PackageIDDetailHandler(BaseHandler):
	def get(self, id):
		package = self.packages.get_by_id(id)
		if not package:
			return tornado.web.HTTPError(404, "Package not found: %s" % id)

		self.render("package-detail.html", package=package)


class PackageListHandler(BaseHandler):
	def get(self):
		packages = {}

		show = self.get_argument("show", None)
		if show == "all":
			states = None
		elif show == "obsoletes":
			states = ["obsolete"]
		elif show == "broken":
			states = ["broken"]
		else:
			states = ["building", "stable", "testing"]

		# Get all packages that fulfill the required parameters.
		pkgs = self.pakfire.packages.get_all_names(public=self.public,
			user=self.current_user, states=states)

		# Sort all packages in an array like "<first char>" --> [packages, ...]
		# to print them in a table for each letter of the alphabet.
		for pkg in pkgs:
			c = pkg[0][0].lower()

			if not packages.has_key(c):
				packages[c] = []

			packages[c].append(pkg)

		self.render("packages-list.html", packages=packages)


class PackageNameHandler(BaseHandler):
	def get(self, name):
		builds = {
			"release" : [],
			"scratch" : [],
		}

		query = self.pakfire.builds.get_by_name(name, public=self.public,
			user=self.current_user)

		if not query:
			raise tornado.web.HTTPError(404, "Package '%s' was not found" % name)

		for build in query:
			try:
				builds[build.type].append(build)
			except KeyError:
				logging.warning("Unknown build type: %s" % build.type)

		latest_build = None
		for type in builds.keys():
			# Take info from the most recent package.
			if builds[type]:
				latest_build = builds[type][-1]
				break

		assert latest_build

		# Move the latest builds to the top.
		for type in builds.keys():
			builds[type].reverse()

		# Get the average build times of this package.
		build_times = self.pakfire.packages.get_avg_build_times(name)

		# Get the latest bugs from bugzilla.
		bugs = self.pakfire.bugzilla.get_bugs_from_component(name)

		kwargs = {
			"release_builds" : builds["release"],
			"scratch_builds" : builds["scratch"],
		}

		self.render("package-detail-list.html", builds=builds,
			latest_build=latest_build, pkg=latest_build.pkg,
			build_times=build_times, bugs=bugs, **kwargs)


class PackageDetailHandler(BaseHandler):
	def get(self, uuid):
		pkg = self.pakfire.packages.get_by_uuid(uuid)
		if not pkg:
			raise tornado.web.HTTPError(404, "Package not found: %s" % uuid)

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


class PackagePropertiesHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self, name):
		build = self.pakfire.builds.get_latest_by_name(name, public=self.public)

		if not build:
			raise tornado.web.HTTPError(404, "Package '%s' was not found" % name)

		# Check if the user has sufficient permissions.
		if not build.has_perm(self.current_user):
			raise tornado.web.HTTPError(403, "User %s is not allowed to manage build %s" \
				% (self.current_user, build))

		self.render("package-properties.html", build=build,
			pkg=build.pkg, properties=build.pkg.properties)

	@tornado.web.authenticated
	def post(self, name):
		build = self.pakfire.builds.get_latest_by_name(name, public=self.public)

		if not build:
			raise tornado.web.HTTPError(404, "Package '%s' was not found" % name)

		# Check if the user has sufficient permissions.
		if not build.has_perm(self.current_user):
			raise tornado.web.HTTPError(403, "User %s is not allowed to manage build %s" \
				% (self.current_user, build))

		critical_path = self.get_argument("critical_path", False)
		if critical_path:
			critical_path = True
		else:
			critical_path = False
		build.pkg.update_property("critical_path", critical_path)
