#!/usr/bin/python

import uuid

import base
import users

class Sessions(base.Object):
	def get(self, session_id):
		try:
			session = Session(self.pakfire, session_id)
		except:
			return

		return session


class Session(base.Object):
	def __init__(self, pakfire, session_id):
		base.Object.__init__(self, pakfire)

		# Save the session_id.
		self.id = session_id

		self.data = self.db.get("SELECT * FROM sessions WHERE session_id = %s \
			AND valid_until >= NOW()", self.id)

		if not self.data:
			raise Exception, "No such session: %s" % self.id

		# Cache.
		self._user = None
		self._impersonated_user = None

		# Update the valid time of the session.
		#self.update()

	@staticmethod
	def has_session(pakfire, session_id):
		if self.db.get("SELECT session_id FROM sessions WHERE session_id = %s \
				AND valid_until >= NOW()", session_id):
			return True

		return False

	def refresh(self):
		self.db.execute("UPDATE sessions SET valid_until = DATE_ADD(NOW(), INTERVAL 3 DAY) \
			WHERE session_id = %s", self.id)

	def destroy(self):
		self.db.execute("DELETE FROM sessions WHERE session_id = %s", self.id)

	@staticmethod
	def cleanup(pakfire):
		# Remove all sessions that are no more valid.
		pakfire.db.execute("DELETE FROM sessions WHERE valid_until < NOW()")

	@property
	def user(self):
		if self._user is None:
			self._user = users.User(self.pakfire, self.data.user_id)

		return self._user

	@property
	def impersonated_user(self):
		if not self.data.impersonated_user_id:
			return

		if self._impersonated_user is None:
			self._impersonated_user = \
				users.User(self.pakfire, self.data.impersonated_user_id)

		return self._impersonated_user

	def start_impersonation(self, user):
		assert self.user.is_admin(), "Only admins can impersonate other users."

		# You cannot impersonate yourself.
		if self.user == user:
			return

		self.db.execute("UPDATE sessions SET impersonated_user_id = %s \
			WHERE session_id = %s", user.id, self.id)

	def stop_impersonation(self):
		self.db.execute("UPDATE sessions SET impersonated_user_id = NULL \
			WHERE session_id = %s", self.id)

	@classmethod
	def create(cls, pakfire, user):
		"""
			Creates a new session in the data.

			The user is not checked and it is assumed that the user exsists
			and has the right to log in.
		"""
		# Check if user has too much open sessions.
		sessions = pakfire.db.get("SELECT COUNT(*) as count FROM sessions \
			WHERE user_id = %s AND valid_until >= NOW()", user.id)

		sessions_max = pakfire.settings.get_int("sessions_max", 0)

		if sessions.count >= sessions_max:
			raise Exception, "User exceeded maximum number of allowed sessions"

		# Create a new session in the database.
		session_id = "%s" % uuid.uuid4()

		pakfire.db.execute("""
			INSERT INTO sessions(session_id, user_id, creation_time, valid_until)
			VALUES(%s, %s, NOW(), DATE_ADD(NOW(), INTERVAL 3 DAY))
		""", session_id, user.id)

		return cls(pakfire, session_id)

