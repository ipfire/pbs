#!/usr/bin/python

import tornado.web

from handlers_auth import *
from handlers_base import *
from handlers_builds import *
from handlers_builders import *
from handlers_distro import *
from handlers_jobs import *
from handlers_keys import *
from handlers_mirrors import *
from handlers_packages import *
from handlers_search import *
from handlers_updates import *
from handlers_users import *

class IndexHandler(BaseHandler):
	def get(self):
		kwargs = {
			"active_jobs" : self.pakfire.jobs.get_active(),
			"latest_jobs" : self.pakfire.jobs.get_latest(limit=10),

			"job_queue" : self.pakfire.jobs.count("pending"),
		}

		# Updates
		updates = []
		active = True
		for type in ("stable", "unstable", "testing"):
			u = self.pakfire.updates.get_latest(type=type)
			if u:
				updates.append((type, u, active))
				active = False

		kwargs["updates"] = updates

		self.render("index.html", **kwargs)


class Error404Handler(BaseHandler):
	def get(self):
		raise tornado.web.HTTPError(404)


class AdvancedHandler(BaseHandler):
	def get(self):
		self.render("advanced.html")


class StatisticsMainHandler(BaseHandler):
	def get(self):
		args = {}

		# Build statistics.
		args.update({
			"builds_count" : self.pakfire.builds.count(),
		})

		# Job statistics.
		args.update({
			"jobs_count_all"      : self.pakfire.jobs.count(),
			"jobs_avg_build_time" : self.pakfire.jobs.get_average_build_time(),
		})

		# User statistics.
		args.update({
			"users_count" : self.pakfire.users.count(),
		})

		self.render("statistics-main.html", **args)


class UploadsHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self):
		if not self.current_user.is_admin():
			raise tornado.web.HTTPError(403)

		uploads = self.pakfire.uploads.get_all()

		self.render("uploads-list.html", uploads=uploads)


class DocsIndexHandler(BaseHandler):
	def get(self):
		self.render("docs-index.html")


class DocsBuildsHandler(BaseHandler):
	def get(self):
		self.render("docs-build.html")


class DocsUsersHandler(BaseHandler):
	def get(self):
		self.render("docs-users.html")


class DocsWhatsthisHandler(BaseHandler):
	def get(self):
		self.render("docs-whatsthis.html")


class FileDetailHandler(BaseHandler):
	def get(self, uuid):
		pkg, file = self.pakfire.packages.get_with_file_by_uuid(uuid)

		if not file:
			raise tornado.web.HTTPError(404, "File not found")

		self.render("file-detail.html", pkg=pkg, file=file)


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


class RepositoryEditHandler(BaseHandler):
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


class RepositoryConfHandler(BaseHandler):
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


class RepositoryMirrorlistHandler(BaseHandler):
	def get(self, distro, repo):
		distro = self.pakfire.distros.get_by_name(distro)
		if not distro:
			raise tornado.web.HTTPError(404)

		repo = distro.get_repo(repo)
		if not repo:
			raise tornado.web.HTTPError(404)

		# This is a plaintext file.
		self.set_header("Content-Type", "text/plain")

		arch = self.get_argument("arch", None)
		arch = self.pakfire.arches.get_by_name(arch)

		if not arch:
			raise tornado.web.HTTPError(400, "You must specify the architecture.")

		ret = {
			"type"    : "mirrorlist",
			"version" : 1,
		}

		# A list with mirrors that are sent to the user.
		mirrors = []

		# Only search for mirrors on repositories that are supposed to be found
		# on mirror servers.

		if repo.mirrored:
			# See how many mirrors we can max. find.
			num_mirrors = self.mirrors.count(status="enabled")
			assert num_mirrors > 0

			# Create a list with all mirrors that is up to 50 mirrors long.
			# First add all preferred mirrors and then fill the rest up
			# with other mirrors.
			if num_mirrors >= 10:
				MAX_MIRRORS = 10
			else:
				MAX_MIRRORS = num_mirrors


			for mirror in self.mirrors.get_for_location(self.remote_address):
				mirrors.append({
					"url"       : "/".join((mirror.url, distro.identifier, repo.identifier, arch.name)),
					"location"  : mirror.country_code,
					"preferred" : 1,
				})

			while MAX_MIRRORS - len(mirrors) > 0:
				mirror = self.mirrors.get_random(limit=1)[0]

				mirror = {
					"url"       : "/".join((mirror.url, distro.identifier, repo.identifier, arch.name)),
					"location"  : mirror.country_code,
					"preferred" : 0,
				}

				if not mirror in mirrors:
					mirrors.append(mirror)

		else:
			repo_baseurl = self.pakfire.settings.get("repository_baseurl")
			if repo_baseurl.endswith("/"):
				repo_baseurl = repo_baseurl[:-1]

			for mirror in self.mirrors.get_all():
				print mirror.url, repo_baseurl
				if not mirror.url == repo_baseurl:
					continue

				mirror = {
					"url"       : "/".join((mirror.url, distro.identifier, repo.identifier, arch.name)),
					"location"  : mirror.country_code,
					"preferred" : 0,
				}

				mirrors.append(mirror)
				break

		ret["mirrors"] = mirrors
		self.write(ret)
		


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
