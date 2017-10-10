#!/usr/bin/python

from .handlers_base import *

class DistributionListHandler(BaseHandler):
	def get(self):
		self.render("distro-list.html", distros=self.backend.distros)


class DistributionDetailHandler(BaseHandler):
	def get(self, name):
		distro = self.pakfire.distros.get_by_name(name)
		if not distro:
			raise tornado.web.HTTPError(404, "Distro not found")

		self.render("distro-detail.html", distro=distro)


class DistributionEditHandler(BaseHandler):
	def prepare(self):
		self.sources = self.pakfire.sources.get_all()

	@tornado.web.authenticated
	def get(self, name):
		distro = self.pakfire.distros.get_by_name(name)
		if not distro:
			raise tornado.web.HTTPError(404, "Distro not found")

		self.render("distro-edit.html", distro=distro,
			arches=self.backend.arches, sources=self.sources)

	@tornado.web.authenticated
	def post(self, name):
		distro = self.pakfire.distros.get_by_name(name)
		if not distro:
			raise tornado.web.HTTPError(404, "Distro not found")

		name = self.get_argument("name", distro.name)
		vendor = self.get_argument("vendor", distro.vendor)
		contact = self.get_argument("contact", "")
		slogan = self.get_argument("slogan", distro.slogan)
		tag = self.get_argument("tag", "")

		distro.set("name", name)
		distro.set("vendor", vendor)
		distro.set("slogan", slogan)

		# Update the contact email address.
		distro.contact = contact

		# Update the tag.
		distro.tag = tag

		# Update architectures.
		arches = []
		for arch in self.get_arguments("arches", []):
			# Check if arch exists
			if not self.backend.arches.exists(arch):
				continue

			arches.append(arch)

		distro.arches = arches

		self.redirect("/distribution/%s" % distro.sname)


class DistroSourceDetailHandler(BaseHandler):
	def get(self, distro_ident, source_ident):
		distro = self.pakfire.distros.get_by_name(distro_ident)
		if not distro:
			raise tornado.web.HTTPError(404, "Distro not found")

		source = distro.get_source(source_ident)
		if not source:
			raise tornado.web.HTTPError(404, "Source '%s' not found in distro '%s'" \
				% (source_ident, distro.name))

		# Get the latest commits.
		commits = source.get_commits(limit=5)

		self.render("distro-source-detail.html", distro=distro, source=source,
			commits=commits)


class DistroSourceCommitsHandler(BaseHandler):
	def get(self, distro_ident, source_ident):
		distro = self.pakfire.distros.get_by_name(distro_ident)
		if not distro:
			raise tornado.web.HTTPError(404, "Distro not found")

		source = distro.get_source(source_ident)
		if not source:
			raise tornado.web.HTTPError(404, "Source '%s' not found in distro '%s'" \
				% (source_ident, distro.name))

		offset = self.get_argument("offset", 0)
		try:
			offset = int(offset)
		except ValueError:
			offset = 0

		limit  = self.get_argument("limit", 50)
		try:
			limit = int(limit)
		except ValueError:
			limit = 50

		commits = source.get_commits(limit=limit, offset=offset)

		self.render("distro-source-commits.html", distro=distro, source=source,
			commits=commits, limit=limit, offset=offset, number=50)


class DistroSourceCommitDetailHandler(BaseHandler):
	def get(self, distro_ident, source_ident, commit_ident):
		distro = self.pakfire.distros.get_by_name(distro_ident)
		if not distro:
			raise tornado.web.HTTPError(404, "Distribution '%s' not found" % distro_ident)

		source = distro.get_source(source_ident)
		if not source:
			raise tornado.web.HTTPError(404, "Source '%s' not found in distro '%s'" \
				% (source_ident, distro.name))

		commit = source.get_commit(commit_ident)
		if not commit:
			raise tornado.web.HTTPError(404, "Commit '%s' not found in source '%s'" \
				% (commit_ident, source.name))

		self.render("distro-source-commit-detail.html", distro=distro,
			source=source, commit=commit)


class DistroSourceCommitResetHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self, distro_ident, source_ident, commit_ident):
		distro = self.pakfire.distros.get_by_name(distro_ident)
		if not distro:
			raise tornado.web.HTTPError(404, "Distribution '%s' not found" % distro_ident)

		source = distro.get_source(source_ident)
		if not source:
			raise tornado.web.HTTPError(404, "Source '%s' not found in distro '%s'" \
				% (source_ident, distro.name))

		commit = source.get_commit(commit_ident)
		if not commit:
			raise tornado.web.HTTPError(404, "Commit '%s' not found in source '%s'" \
				% (commit_ident, source.name))

		if not self.current_user.is_admin():
			raise tornado.web.HTTPError(403)

		confirmed = self.get_argument("confirmed", None)
		if confirmed:
			commit.reset()

			self.redirect("/distro/%s/source/%s/%s" % \
				(distro.identifier, source.identifier, commit.revision))
			return

		self.render("distro-source-commit-reset.html", distro=distro,
			source=source, commit=commit)


class DistroUpdateCreateHandler(BaseHandler):
	def get(self, distro_ident):
		distro = self.pakfire.distros.get_by_name(distro_ident)
		if not distro:
			raise tornado.web.HTTPError(404, "Distribution '%s' not found" % distro_ident)

		# Get all preset builds.
		builds = []
		for build in self.get_arguments("builds", []):
			build = self.pakfire.builds.get_by_uuid(build)
			builds.append(build)

		builds.sort()

		self.render("distro-update-edit.html", update=None,
			distro=distro, builds=builds)


class DistroUpdateDetailHandler(BaseHandler):
	def get(self, distro_ident, year, num):
		distro = self.pakfire.distros.get_by_name(distro_ident)
		if not distro:
			raise tornado.web.HTTPError(404, "Distribution '%s' not found" % distro_ident)

		update = distro.get_update(year, num)
		if not update:
			raise tornado.web.HTTPError(404, "Update cannot be found: %s %s" % (year, num))

		self.render("distro-update-detail.html", distro=distro,
			update=update, repo=update.repo, user=update.user)

# XXX currently unused
class SourceListHandler(BaseHandler):
	def get(self):
		sources = self.pakfire.sources.get_all()

		self.render("source-list.html", sources=sources)


class SourceDetailHandler(BaseHandler):
	def get(self, id):
		source = self.pakfire.sources.get_by_id(id)

		self.render("source-detail.html", source=source)
