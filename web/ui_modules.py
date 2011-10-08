
import tornado.web

from backend.constants import *

class UIModule(tornado.web.UIModule):
	@property
	def pakfire(self):
		return self.handler.application.pakfire


class PackageTableModule(UIModule):
	def render(self, letter, packages):
		return self.render_string("modules/package-table.html",
			letter=letter, packages=packages)


class PackageTable2Module(UIModule):
	def render(self, packages):
		return self.render_string("modules/package-table-detail.html",
			packages=packages)


class FilesTableModule(UIModule):
	def render(self, files):
		return self.render_string("modules/files-table.html", files=files)


class PackageFilesTableModule(UIModule):
	def render(self, files):
		return self.render_string("modules/package-files-table.html", files=files)


class BuildTableModule(UIModule):
	def render(self, builds):
		return self.render_string("modules/build-table.html", builds=builds)


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
