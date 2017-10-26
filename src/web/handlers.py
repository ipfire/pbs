#!/usr/bin/python

import random
import tornado.web

from . import base

from .handlers_builds import *
from .handlers_builders import *
from .handlers_distro import *
from .handlers_jobs import *
from .handlers_keys import *
from .handlers_packages import *
from .handlers_search import *
from .handlers_updates import *
from .handlers_users import *

class IndexHandler(base.BaseHandler):
	def get(self):
		jobs = self.pakfire.jobs.get_active()
		jobs += self.pakfire.jobs.get_latest(age="24 hours", limit=5)

		# Updates
		updates = []
		active = True
		for type in ("stable", "unstable", "testing"):
			u = self.pakfire.updates.get_latest(type=type)
			if u:
				updates.append((type, u, active))
				active = False

		self.render("index.html", jobs=jobs, updates=updates)


class UploadsHandler(base.BaseHandler):
	@tornado.web.authenticated
	def get(self):
		if not self.current_user.is_admin():
			raise tornado.web.HTTPError(403)

		self.render("uploads-list.html", uploads=self.backend.uploads)


class DocsIndexHandler(base.BaseHandler):
	def get(self):
		self.render("docs-index.html")


class DocsBuildsHandler(base.BaseHandler):
	def get(self):
		self.render("docs-build.html")


class DocsUsersHandler(base.BaseHandler):
	def get(self):
		self.render("docs-users.html")


class DocsWhatsthisHandler(base.BaseHandler):
	def get(self):
		self.render("docs-whatsthis.html")


class FileDetailHandler(base.BaseHandler):
	def get(self, uuid):
		pkg, file = self.pakfire.packages.get_with_file_by_uuid(uuid)

		if not file:
			raise tornado.web.HTTPError(404, "File not found")

		self.render("file-detail.html", pkg=pkg, file=file)


class LogHandler(base.BaseHandler):
	def get(self):
		self.render("log.html", log=self.pakfire.log)


class SessionsHandler(base.BaseHandler):
	def prepare(self):
		# This is only accessible for administrators.
		if not self.current_user.is_admin():
			raise tornado.web.HTTPError(403)

	@tornado.web.authenticated
	def get(self):
		# Sort the sessions by user.
		users = {}

		for s in self.backend.sessions:
			print s.user, s.user in users
			try:
				users[s.user].append(s)
			except KeyError:
				users[s.user] = [s]

		sessions = sorted(users.items())

		self.render("sessions/index.html", sessions=sessions)


class RepositoryDetailHandler(base.BaseHandler):
	def get(self, distro, repo):
		distro = self.pakfire.distros.get_by_name(distro)
		if not distro:
			raise tornado.web.HTTPError(404)

		repo = distro.get_repo(repo)
		if not repo:
			raise tornado.web.HTTPError(404)

		limit = self.get_argument("limit", 50)
		try:
			limit = int(limit)
		except ValueError:
			limit = None

		offset = self.get_argument("offset", 0)
		try:
			offset = int(offset)
		except ValueError:
			offset = None

		builds = repo.get_builds(limit=limit, offset=offset)
		unpushed_builds = repo.get_unpushed_builds()
		obsolete_builds = repo.get_obsolete_builds()

		# Get the build times of this repository.
		build_times = repo.get_build_times()

		self.render("repository-detail.html", distro=distro, repo=repo,
			builds=builds, unpushed_builds=unpushed_builds,
			obsolete_builds=obsolete_builds, build_times=build_times)


class RepositoryEditHandler(base.BaseHandler):
	@tornado.web.authenticated
	def get(self, distro, repo):
		distro = self.pakfire.distros.get_by_name(distro)
		if not distro:
			raise tornado.web.HTTPError(404)

		repo = distro.get_repo(repo)
		if not repo:
			raise tornado.web.HTTPError(404)

		# XXX check if user has permissions to do this

		self.render("repository-edit.html", distro=distro, repo=repo)


class RepositoryConfHandler(base.BaseHandler):
	def get(self, distro, repo):
		distro = self.pakfire.distros.get_by_name(distro)
		if not distro:
			raise tornado.web.HTTPError(404)

		repo = distro.get_repo(repo)
		if not repo:
			raise tornado.web.HTTPError(404)

		# This is a plaintext file.
		self.set_header("Content-Type", "text/plain")

		# Write the header.
		self.write("# Downloaded from the pakfire build service on %s.\n\n" \
			% datetime.datetime.utcnow())
		self.write(repo.get_conf())
		self.finish()


class RepositoryMirrorlistHandler(base.BaseHandler):
	def get(self, distro, repo):
		distro = self.pakfire.distros.get_by_name(distro)
		if not distro:
			raise tornado.web.HTTPError(404)

		repo = distro.get_repo(repo)
		if not repo:
			raise tornado.web.HTTPError(404)

		# Send nothing if repository isn't supposed to be mirrored
		if not repo.mirrored:
			raise tornado.web.HTTPError(404)

		# This is a plaintext file.
		self.set_header("Content-Type", "text/plain")

		arch = self.get_argument("arch", None)
		if not arch or not self.backend.arches.exists(arch):
			raise tornado.web.HTTPError(400, "You must specify a valid architecture")

		ret = {
			"type"    : "mirrorlist",
			"version" : 1,
		}

		mirrors = []
		for mirror in self.backend.mirrors.make_mirrorlist(self.current_address):
			mirrors.append({
				"url"       : "/".join((mirror.url, repo.basepath, arch)),
				"location"  : mirror.country_code,
			})

		# Always use the buildservice itself as last resort
		mirrors.append({
			"url" : repo.url,
		})

		ret["mirrors"] = mirrors
		self.finish(ret)


class RepoActionHandler(base.BaseHandler):
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
