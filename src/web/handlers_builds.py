#!/usr/bin/python

import tornado.web

from .handlers_base import BaseHandler

class BuildsHandler(BaseHandler):
	def get(self):
		limit = self.get_argument("limit", None)
		try:
			limit = int(limit)
		except (TypeError, ValueError):
			limit = 25

		builds = self.pakfire.builds.get_all(limit=limit)

		self.render("build-index.html", builds=builds)


class BuildBaseHandler(BaseHandler):
	def get_build(self, uuid):
		build = self.pakfire.builds.get_by_uuid(uuid)
		if not build:
			raise tornado.web.HTTPError(404, "No such build: %s" % uuid)

		return build


class BuildDetailHandler(BuildBaseHandler):
	def get(self, uuid):
		build = self.get_build(uuid)

		# Cache the log.
		log = build.get_log()

		if build.repo:
			next_repo = build.repo.next
		else:
			next_repo = None

		# Bugs.
		bugs = build.get_bugs()

		self.render("build-detail.html", build=build, log=log, pkg=build.pkg,
			distro=build.distro, bugs=bugs, repo=build.repo, next_repo=next_repo)


class BuildDeleteHandler(BuildBaseHandler):
	@tornado.web.authenticated
	def get(self, uuid):
		build = self.get_build(uuid)

		# Check if the user has got sufficient rights to do this modification.
		if not build.has_perm(self.current_user):
			raise tornado.web.HTTPError(403)

		# Check if the user confirmed the action.
		confirmed = self.get_argument("confirmed", None)
		if confirmed:
			# Save the name of the package to redirect the user
			# to the other packages of that name.
			package_name = build.pkg.name

			# Delete the build and everything that comes with it.
			build.delete()

			return self.redirect("/package/%s" % package_name)

		self.render("build-delete.html", build=build)


class BuildBugsHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self, uuid):
		build = self.pakfire.builds.get_by_uuid(uuid)
		if not build:
			raise tornado.web.HTTPError(404, "No such build: %s" % uuid)

		# Check if the user has got the right to alter this build.
		if not build.has_perm(self.current_user):
			raise tornado.web.HTTPError(403)

		# Bugs.
		fixed_bugs = build.get_bugs()
		open_bugs = []

		for bug in self.pakfire.bugzilla.get_bugs_from_component(build.pkg.name):
			if bug in fixed_bugs:
				continue

			open_bugs.append(bug)

		self.render("build-bugs.html", build=build, pkg=build.pkg,
			fixed_bugs=fixed_bugs, open_bugs=open_bugs)

	@tornado.web.authenticated
	def post(self, uuid):
		build = self.pakfire.builds.get_by_uuid(uuid)
		if not build:
			raise tornado.web.HTTPError(404, "No such build: %s" % uuid)

		# Check if the user has got the right to alter this build.
		if not build.has_perm(self.current_user):
			raise tornado.web.HTTPError(403)

		action = self.get_argument("action", None)
		bugid  = self.get_argument("bugid")

		# Convert the bug id to integer.
		try:
			bugid = int(bugid)
		except ValueError:
			raise tornado.web.HTTPError(400, "Bad bug id given: %s" % bugid)

		if action == "add":
			# Add bug to the build.
			build.add_bug(bugid, user=self.current_user)

		elif action == "remove":
			# Remove bug from the build.
			build.rem_bug(bugid, user=self.current_user)

		else:
			raise tornado.web.HTTPError(400, "Unhandled action: %s" % action)

		self.redirect("/build/%s/bugs" % build.uuid)


class BuildsCommentsHandler(BaseHandler):
	def get(self, user_name=None):
		user = None
		if user_name:
			user = self.pakfire.users.get_by_name(user_name)

		limit  = self.get_argument("limit", 10)
		offset = self.get_argument("offset", 0)

		try:
			limit  = int(limit)
			offset = int(offset)
		except:
			raise tornado.web.HTTPError(400)

		# Try to get one more comment than requested and check if there
		# is a next page that it to be shown.
		comments = self.pakfire.builds.get_comments(limit=limit + 1,
			offset=offset, user=user)

		# Set markers for next and prev pages.
		have_next = len(comments) > limit
		have_prev = offset > limit

		# Remove the extra element from the list.
		comments = comments[:limit]

		self.render("builds/comments.html", comments=comments, limit=limit,
			offset=offset + limit, user=user, have_prev=have_prev, have_next=have_next)


class BuildStateHandler(BaseHandler):
	def get(self, uuid):
		build = self.pakfire.builds.get_by_uuid(uuid)
		if not build:
			raise tornado.web.HTTPError(404, "No such build: %s" % uuid)

		self.render("build-state.html", build=build)

	@tornado.web.authenticated
	def post(self, uuid):
		build = self.pakfire.builds.get_by_uuid(uuid)
		if not build:
			raise tornado.web.HTTPError(404, "No such build: %s" % uuid)

		# Check if user has the right to perform this action.
		if not build.has_perm(self.current_user):
			raise tornado.web.HTTPError(403, "User is not allowed to perform this action")

		# Check if given state is valid.
		state = self.get_argument("state", None)
		if not state in ("broken", "unbreak", "obsolete"):
			raise tornado.web.HTTPError(400, "Invalid argument given: %s" % state)

		# XXX this is not quite accurate
		if state == "unbreak":
			state = "stable"

		rem_from_repo = self.get_argument("rem_from_repo", False)
		if rem_from_repo == "on":
			rem_from_repo = True

		# Perform the state change.
		build.update_state(state, user=self.current_user, remove=rem_from_repo)

		self.redirect("/build/%s" % build.uuid)


class BuildQueueHandler(BaseHandler):
	def get(self):
		self.render("build-queue.html", jobs=self.backend.jobqueue,
			average_waiting_time=self.backend.jobqueue.average_waiting_time)


class BuildDetailCommentHandler(BaseHandler):
	@tornado.web.authenticated
	def post(self, uuid):
		build = self.pakfire.builds.get_by_uuid(uuid)

		if not build:
			raise tornado.web.HTTPError(404, "Build not found")

		vote = self.get_argument("vote", "none")

		if vote == "up":
			vote = 1
		elif vote == "down":
			vote = -1
		else:
			vote = 0

		text = self.get_argument("text", "")

		# Add a new comment to the build.
		if text or vote:
			build.add_comment(self.current_user, text, vote)

		# Redirect to the build detail page.
		self.redirect("/build/%s" % build.uuid)


class BuildManageHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self, uuid):
		build = self.pakfire.builds.get_by_uuid(uuid)
		if not build:
			raise tornado.web.HTTPError(404, "Build not found: %s" % uuid)

		mode = "user"
		if self.current_user.is_admin():
			mode = self.get_argument("mode", "user")

		# Get the next repo.
		if build.repo:
			next_repo = build.repo.next
		else:
			next_repo = build.distro.first_repo

		self.render("build-manage.html", mode=mode, build=build,
			distro=build.distro, repo=build.repo, next_repo=next_repo)

	@tornado.web.authenticated
	def post(self, uuid):
		build = self.pakfire.builds.get_by_uuid(uuid)
		if not build:
			raise tornado.web.HTTPError(404, "Build not found: %s" % uuid)

		# check for sufficient permissions
		if not build.has_perm(self.current_user):
			raise tornado.web.HTTPError(403)

		action = self.get_argument("action")
		assert action in ("push", "unpush")

		current_repo = build.repo

		if action == "unpush":
			current_repo.rem_build(build, user=self.current_user)

		elif action == "push":
			repo_name = self.get_argument("repo")
			next_repo = build.distro.get_repo(repo_name)

			if not next_repo:
				raise tornado.web.HTTPError(404, "No such repository: %s" % next_repo)

			if not self.current_user.is_admin():
				if not distro.repo.next == next_repo:
					raise tornado.web.HTTPError(403)

			if current_repo:
				current_repo.move_build(build, next_repo, user=self.current_user)
			else:
				next_repo.add_build(build, user=self.current_user)

		self.redirect("/build/%s" % build.uuid)


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


class BuildWatchersHandler(BaseHandler):
	def get(self, uuid):
		build = self.pakfire.builds.get_by_uuid(uuid)

		if not build:
			raise tornado.web.HTTPError(404, "Build not found")

		# Get a list of all watchers and sort them by their realname.
		watchers = build.get_watchers()
		watchers.sort(key=lambda watcher: watcher.realname)

		self.render("builds-watchers-list.html", build=build, watchers=watchers)


class BuildWatchersAddHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self, uuid, error_msg=None):
		build = self.pakfire.builds.get_by_uuid(uuid)

		if not build:
			raise tornado.web.HTTPError(404, "Build not found")

		# Get a list of all users that are currently watching this build.
		watchers = build.get_watchers()

		self.render("builds-watchers-add.html", error_msg=error_msg,
			build=build, users=self.pakfire.users.get_all(), watchers=watchers)

	@tornado.web.authenticated
	def post(self, uuid):
		build = self.pakfire.builds.get_by_uuid(uuid)

		if not build:
			raise tornado.web.HTTPError(404, "Build not found")

		# Get the user id of the new watcher.
		user_id = self.current_user.id

		if self.current_user.is_admin():
			user_id = self.get_argument("user_id", self.current_user.id)
		assert user_id

		user = self.pakfire.users.get_by_id(user_id)
		if not user:
			_ = self.locale.translate
			error_msg = _("User not found.")

			return self.get(uuid, error_msg=error_msg)

		# Actually add the user to the list of watchers.
		build.add_watcher(user)

		# Send user back to the build detail page.
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
		distros  = self.pakfire.distros.get_all()

		self.render("build-filter.html", builders=builders, distros=distros)

