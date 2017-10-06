#!/usr/bin/python

import logging
import smtplib
import subprocess
import tornado.locale

from email.mime.text import MIMEText

from . import base

class Messages(base.Object):
	def add(self, to, subject, text, frm=None):
		subject = "%s %s" % (self.pakfire.settings.get("email_subject_prefix"), subject)

		# Get default sender from the settings.
		if not frm:
			frm = self.pakfire.settings.get("email_from")

		self.db.execute("INSERT INTO user_messages(frm, `to`, subject, text)"
			" VALUES(%s, %s, %s, %s)", frm, to, subject, text)

	def get_all(self, limit=None):
		query = "SELECT * FROM user_messages ORDER BY time_added ASC"
		if limit:
			query += " LIMIT %d" % limit

		return self.db.query(query)

	@property
	def count(self):
		ret = self.db.get("SELECT COUNT(*) as count FROM user_messages")

		return ret.count

	def delete(self, id):
		self.db.execute("DELETE FROM user_messages WHERE id = %s", id)

	def send_to_all(self, recipients, subject, body, format=None):
		"""
			Sends an email to all recipients and does the translation.
		"""
		if not format:
			format = {}

		for recipient in recipients:
			if not recipient:
				logging.warning("Ignoring empty recipient.")
				continue

			# We try to get more information about the user from the database
			# like the locale.
			user = self.pakfire.users.get_by_email(recipient)
			if user:
				# Get locale that the user prefers.
				locale = tornado.locale.get(user.locale)
			else:
				# Get the default locale.
				locale = tornado.locale.get()

			# Translate the message.
			_subject = locale.translate(subject) % format
			_body    = locale.translate(body) % format

			# If we know the real name of the user we add the realname to
			# the recipient field.
			if user:
				recipient = "%s <%s>" % (user.realname, user.email)

			# Add the message to the queue that it is sent.
			self.add(recipient, _subject, _body)

	@staticmethod
	def send_msg(msg):
		if not msg.to:
			logging.warning("Dropping message with empty recipient.")
			return

		logging.debug("Sending mail to %s: %s" % (msg.to, msg.subject))

		# Preparing mail content.
		mail = MIMEText(msg.text.encode("latin-1"))
		mail["From"] = msg.frm.encode("latin-1")
		mail["To"] = msg.to.encode("latin-1")
		mail["Subject"] = msg.subject.encode("latin-1")
		#mail["Content-type"] = "text/plain; charset=utf-8"

		#smtp = smtplib.SMTP("localhost")
		#smtp.sendmail(msg.frm, msg.to.split(", "), mail.as_string())
		#smtp.quit()

		# We use sendmail here to workaround problems with the mailserver
		# communication.
		# So, just call /usr/lib/sendmail, pipe the message in and see
		# what sendmail tells us in return.
		sendmail = ["/usr/lib/sendmail", "-t"]
		p = subprocess.Popen(sendmail, bufsize=0, close_fds=True,
			stdin=subprocess.PIPE, stdout=subprocess.PIPE)

		stdout, stderr = p.communicate(mail.as_string())

		# Wait until sendmail has finished.
		p.wait()

		if p.returncode:
			raise Exception, "Could not send mail: %s" % stderr
