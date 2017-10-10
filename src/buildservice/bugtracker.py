#!/usr/bin/python

import xmlrpclib

from . import base

from .decorators import *

class BugzillaBug(base.Object):
	def __init__(self, bugzilla, bug_id):
		base.Object.__init__(self, bugzilla.pakfire)
		self.bugzilla = bugzilla

		self.bug_id = bug_id
		self._data  = None

	def __cmp__(self, other):
		return cmp(self.bug_id, other.bug_id)

	def call(self, *args, **kwargs):
		args = (("Bug",) + args)

		return self.bugzilla.call(*args, **kwargs)

	@property
	def id(self):
		return self.bug_id

	@lazy_property
	def data(self):
		# Fetch bug information from cache
		data = self.backend.cache.get(self._cache_key)

		# Hit
		if data:
			return data

		# Fetch bug information from Bugzilla
		for data in self.call("get", ids=[self.id,])["bugs"]:
			# Put it into the cache
			self.backend.cache.set(self._cache_key, data, self.backend.bugzilla.cache_lifetime)

			return data

	@property
	def _cache_key(self):
		return "bug-%s" % self.bug_id

	@property
	def url(self):
		return self.bugzilla.bug_url(self.id)

	@property
	def summary(self):
		return self.data.get("summary")

	@property
	def assignee(self):
		return self.data.get("assigned_to")

	@property
	def status(self):
		return self.data.get("status")

	@property
	def resolution(self):
		return self.data.get("resolution")

	@property
	def is_closed(self):
		return not self.data["is_open"]

	def set_status(self, status, resolution=None, comment=None):
		kwargs = { "status" : status }
		if resolution:
			kwargs["resolution"] = resolution
		if comment:
			kwargs["comment"] = { "body" : comment }

		self.call("update", ids=[self.id,], **kwargs)

		# Invalidate cache
		self.backend.cache.delete(self.cache_key)


class Bugzilla(base.Object):
	def __init__(self, pakfire):
		base.Object.__init__(self, pakfire)

		# Open the connection to the server.
		self.server = xmlrpclib.ServerProxy(self.url, use_datetime=True)

		# Cache the credentials.
		self.__credentials = {
			"Bugzilla_login"    : self.user,
			"Bugzilla_password" : self.password,
		}

	def call(self, *args, **kwargs):
		# Add authentication information.
		kwargs.update(self.__credentials)

		method = self.server
		for arg in args:
			method = getattr(method, arg)

		return method(kwargs)

	def bug_url(self, bugid):
		url = self.settings.get("bugzilla_url", None)

		try:
			return url % { "bugid" : bugid }
		except:
			return "#"

	def enter_url(self, component):
		args = {
			"product"   : self.settings.get("bugzilla_product", ""),
			"component" : component,
		}

		url = self.settings.get("bugzilla_url_new")

		return url % args

	def buglist_url(self, component):
		args = {
			"product"   : self.settings.get("bugzilla_product", ""),
			"component" : component,
		}

		url = self.settings.get("bugzilla_url_buglist")

		return url % args

	@property
	def url(self):
		return self.settings.get("bugzilla_url_xmlrpc", None)

	@property
	def user(self):
		return self.settings.get("bugzilla_xmlrpc_user", "")

	@property
	def password(self):
		return self.settings.get("bugzilla_xmlrpc_password")

	@lazy_property
	def cache_lifetime(self):
		return self.settings.get("bugzilla_cache_lifetime", 3600)

	def get_bug(self, bug_id):
		try:
			bug = BugzillaBug(self, bug_id)

		except xmlrpclib.Fault:
			return None

		return bug

	def find_users(self, pattern):
		users = self.call("User", "get", match=[pattern,])
		if users:
			return users["users"]

	def find_user(self, pattern):
		users = self.find_users(pattern)

		if not users:
			return

		elif len(users) > 1:
			raise Exception, "Got more than one result."

		return users[0]

	def get_bugs_from_component(self, component, closed=False):
		kwargs = {
			"product"   : self.settings.get("bugzilla_product", ""),
			"component" : component,
		}

		query = self.call("Bug", "search", include_fields=["id"], **kwargs)

		bugs = []
		for bug in query["bugs"]:
			bug = self.get_bug(bug["id"])

			if not bug.is_closed == closed:
				continue

			bugs.append(bug)

		return bugs

	def send_all(self, limit=100):
		# Get up to ten updates.
		query = self.db.query("SELECT * FROM builds_bugs_updates \
			WHERE error IS FALSE ORDER BY time LIMIT %s", limit)

		# XXX CHECK IF BZ IS ACTUALLY REACHABLE AND WORKING

		for update in query:
			try:
				bug = self.backend.bugzilla.get_bug(update.bug_id)
				if not bug:
					logging.error("Bug #%s does not exist." % update.bug_id)
					continue

				# Set the changes.
				bug.set_status(update.status, update.resolution, update.comment)

			except Exception, e:
				# If there was an error, we save that and go on.
				self.db.execute("UPDATE builds_bugs_updates SET error = 'Y', error_msg = %s \
					WHERE id = %s", "%s" % e, update.id)

			else:
				# Remove the update when it has been done successfully.
				self.db.execute("DELETE FROM builds_bugs_updates WHERE id = %s", update.id)
