#!/usr/bin/python

from . import base
from . import users

from .decorators import *

class Sessions(base.Object):
	def __iter__(self):
		query = "SELECT * FROM sessions WHERE valid_until >= NOW() \
			ORDER BY valid_until DESC"

		sessions = []
		for row in self.db.query(query):
			session = Session(self.backend, row.id, data=row)
			sessions.append(session)

		# Sort
		sessions.sort()

		return iter(sessions)

	def create(self, user, address, user_agent=None):
		"""
			Creates a new session in the data.

			The user is not checked and it is assumed that the user exists
			and has the right to log in.
		"""
		session_id = users.generate_random_string(48)

		res = self.db.get("INSERT INTO session(session_id, user_id, address, user_agent) \
			VALUES(%s, %s, %s, %s) RETURNING *", session_id, user.id, address, user_agent)

		return Session(self.backend, res.id, data=res)

	def get_by_session_id(self, session_id):
		res = self.db.get("SELECT * FROM sessions \
			WHERE session_id = %s AND valid_until >= NOW()", session_id)

		if res:
			return Session(self.backend, res.id, data=res)

	# Alias function
	get = get_by_session_id

	def cleanup(self):
		# Delete all sessions that are not valid any more.
		self.db.execute("DELETE FROM sessions WHERE valid_until < NOW()")


class Session(base.DataObject):
	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.id == other.id

	def __lt__(self, other):
		if isinstance(other, self.__class__):
			return self.user < other.user

	def destroy(self):
		self.db.execute("DELETE FROM sessions WHERE id = %s", self.id)

	@lazy_property
	def user(self):
		return self.backend.users.get_by_id(self.data.user_id)

	@lazy_property
	def impersonated_user(self):
		if self.data.impersonated_user_id:
			return self.backend.users.get_by_id(self.data.impersonated_user_id)

	@property
	def created_at(self):
		return self.data.created_at

	@property
	def valid_until(self):
		return self.data.valid_until

	@property
	def address(self):
		return self.data.address

	@property
	def user_agent(self):
		return self.data.user_agent

	def start_impersonation(self, user):
		if not self.user.is_admin():
			raise RuntimeError("Only admins can impersonate other users")

		if self.user == user:
			raise RuntimeError("You cannot impersonate yourself")

		self._set_attribute("impersonated_user_id", user.id)

	def stop_impersonation(self):
		self._set_attribute("impersonated_user_id", None)
