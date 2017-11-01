#!/usr/bin/python

import mimetypes
import os.path
import tornado.web

from . import base

from ..constants import BUFFER_SIZE

class IndexHandler(base.BaseHandler):
	def get(self):
		# Sort all packages in an array like "<first char>" --> [packages, ...]
		# to print them in a table for each letter of the alphabet.
		packages = {}

		for pkg in self.backend.packages.get_list():
			c = pkg.name[0].lower()

			try:
				packages[c].append(pkg)
			except KeyError:
				packages[c] = [pkg]

		self.render("packages/index.html", packages=packages)


class PackageIDDetailHandler(base.BaseHandler):
	def get(self, id):
		package = self.packages.get_by_id(id)
		if not package:
			return tornado.web.HTTPError(404, "Package not found: %s" % id)

		self.render("package-detail.html", package=package)


class PackageNameHandler(base.BaseHandler):
	def get(self, name):
		builds = self.backend.builds.get_active_builds(name)
		if not builds:
			raise tornado.web.HTTPError(404, "Package '%s' was not found" % name)

		# Get the latest build to show the package meta information.
		latest_build = builds[0]

		# Get the latest bugs from bugzilla.
		bugs = self.backend.bugzilla.get_bugs_from_component(name)

		self.render("package-detail-list.html", name=name, builds=builds,
			latest_build=latest_build, pkg=latest_build.pkg, bugs=bugs)


class PackageScratchBuildsHandler(base.BaseHandler):
	def get(self, name):
		offset = self.get_argument("offset", 0)
		limit  = self.get_argument("limit", 10)

		scratch_builds = self.backend.builds.get_by_name(name, type="scratch",
			limit=limit, offset=offset)

		if scratch_builds:
			latest_build = scratch_builds[0]
		else:
			release_builds = self.backend.builds.get_by_name(name, type="release", limit=1)
			if not release_builds:
				raise tornado.web.HTTPError(404, "Could not find any build with this name: %s" % name)

			latest_build = release_builds[0]

		self.render("packages/builds/scratch.html", builds=scratch_builds,
			pkg=latest_build.pkg)


class PackageChangelogHandler(base.BaseHandler):
	def get(self, name):
		limit = self.get_argument("limit", 10)
		try:
			limit = int(limit)

		except ValueError:
			limit = 10

		offset = self.get_argument("offset", 0)
		try:
			offset = int(offset)
		except ValueError:
			offset = 0

		# Get one more build than requested to find out if there are more items
		# to display (next button).
		builds = self.backend.builds.get_changelog(name, limit=limit + 1, offset=offset)

		if len(builds) >= limit:
			have_next = True
		else:
			have_next = False

		if offset < limit:
			have_prev = False
		else:
			have_prev = True

		# Clip list to limit.
		builds = builds[:limit]

		self.render("packages/changelog.html", name=name, builds=builds,
			limit=limit, offset=offset, have_prev=have_prev, have_next=have_next)


class PackageDetailHandler(base.BaseHandler):
	def get(self, uuid):
		pkg = self.backend.packages.get_by_uuid(uuid)
		if not pkg:
			raise tornado.web.HTTPError(404, "Package not found: %s" % uuid)

		self.render("package-detail.html", pkg=pkg)

	@tornado.web.authenticated
	def post(self, name, epoch, version, release):
		pkg = self.backend.packages.get_by_tuple(name, epoch, version, release)

		action = self.get_argument("action", None)

		if action == "comment":
			vote = self.get_argument("vote", None)
			if not self.current_user.is_tester() and \
					not self.current_user.is_admin():
				vote = None

			pkg.comment(self.current_user.id, self.get_argument("text"),
				vote or "none")

		self.render("package-detail.html", pkg=pkg)


class PackagePropertiesHandler(base.BaseHandler):
	@tornado.web.authenticated
	def get(self, name):
		build = self.backend.builds.get_latest_by_name(name)

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
		build = self.backend.builds.get_latest_by_name(name)

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


class PackageFileDownloadHandler(base.BaseHandler):
	def get_file(self, pkg_uuid, filename):
		# Fetch package.
		pkg = self.backend.packages.get_by_uuid(pkg_uuid)
		if not pkg:
			raise tornado.web.HTTPError(404, "Package not found: %s" % pkg_uuid)

		# Check if the package has got a file with the given name.
		file = pkg.get_file(filename)
		if not file:
			raise tornado.web.HTTPError(404, "Package %s does not contain file %s" % (pkg, filename))

		# Open the package in the filesystem.
		pkg_file = pkg.open()
		if not pkg_file:
			raise tornado.web.HTTPError(404, "Could not open package %s" % pkg.path)

		# Open the file to transfer it to the client.
		f = pkg_file.open_file(filename)
		if not f:
			raise tornado.web.HTTPError(404, "Package %s does not contain file %s" % (pkg_file, filename))

		# Guess the MIME type of the file.
		(type, encoding) = mimetypes.guess_type(filename)
		if not type:
			type = "text/plain"

		return (pkg, f, type)

	def get(self, pkg_uuid, filename):
		pkg, f, mimetype = self.get_file(pkg_uuid, filename)

		# Send the filename and mimetype in header.
		self.set_header("Content-Disposition", "attachment; filename=%s" % os.path.basename(filename))
		self.set_header("Content-Type", mimetype)

		# Transfer the content chunk by chunk.
		while True:
			buf = f.read(BUFFER_SIZE)
			if not buf:
				break

			self.write(buf)

		f.close()

		# Done.
		self.finish()


class PackageFileViewHandler(PackageFileDownloadHandler):
	def get(self, pkg_uuid, filename):
		pkg, f, mimetype = self.get_file(pkg_uuid, filename)

		# Read in the data.
		content = f.read()
		f.close()

		self.render("packages/view-file.html", pkg=pkg, filename=filename,
			mimetype=mimetype, content=content, filesize=f.size)


class PackageBuildsTimesHandler(base.BaseHandler):
	def get(self, name):
		latest_build = self.backend.builds.get_latest_by_name(name)

		# If no build with this name was found, we cannot go on.
		if not latest_build:
			raise tornado.web.HTTPError(404)

		# Get the summary stats.
		build_times_summary = self.backend.builds.get_build_times_summary(name)

		self.render("packages/builds/times.html", pkg=latest_build.pkg,
			build_times_summary=build_times_summary)
