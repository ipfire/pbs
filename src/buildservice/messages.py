#!/usr/bin/python

import email
import email.mime.multipart
import email.mime.text
import logging
import markdown
import subprocess
import tornado.locale
import tornado.template

from . import base
from . import users

from .constants import TEMPLATESDIR

class Messages(base.Object):
	def init(self):
		self.templates = tornado.template.Loader(TEMPLATESDIR)

	def __iter__(self):
		messages = self.db.query("SELECT * FROM messages \
			WHERE sent_at IS NULL ORDER BY queued_at")

		return iter(messages)

	def __len__(self):
		res = self.db.get("SELECT COUNT(*) AS count FROM messages \
			WHERE sent_at IS NULL")

		return res.count

	def process_queue(self):
		"""
			Sends all emails in the queue
		"""
		for message in self:
			with self.db.transaction():
				self.__sendmail(message)

		# Delete all old emails
		with self.db.transaction():
			self.cleanup()

	def cleanup(self):
		self.db.execute("DELETE FROM messages WHERE sent_at <= NOW() - INTERVAL '24 hours'")

	def send_to(self, recipient, message, sender=None, headers={}):
		# Parse the message
		if not isinstance(message, email.message.Message):
			message = email.message_from_string(message)

		if not sender:
			sender = self.backend.settings.get("email_from", "Pakfire Build Service <no-reply@ipfire.org>")

		# Add sender
		message.add_header("From", sender)

		# Add recipient
		message.add_header("To", recipient)

		# Sending this message now
		message.add_header("Date", email.utils.formatdate())

		# Add sender program
		message.add_header("X-Mailer", "Pakfire Build Service %s" % self.backend.version)

		# Add any headers
		for k, v in headers.items():
			message.add_header(k, v)

		# Queue the message
		self.queue(message.as_string())

	def send_template(self, recipient, name, sender=None, headers={}, **kwargs):
		# Get user (if we have one)
		if isinstance(recipient, users.User):
			user = recipient
		else:
			user = self.backend.users.find_maintainer(recipient)

		# Get the user's locale or use default
		if user:
			locale = user.locale
		else:
			locale = tornado.locale.get()

		# Create namespace
		namespace = {
			"baseurl"	: self.settings.get("baseurl"),
			"recipient"	: recipient,
			"user"		: user,

			# Locale
			"locale"	: locale,
			"_"			: locale.translate,
		}
		namespace.update(kwargs)

		# Create a MIMEMultipart message.
		message = email.mime.multipart.MIMEMultipart()

		# Create an alternating multipart message to show HTML or text
		alternative = email.mime.multipart.MIMEMultipart("alternative")

		for fmt, mimetype in (("txt", "plain"), ("html", "html"), ("markdown", "html")):
			try:
				t = self.templates.load("%s.%s" % (name, fmt))
			except IOError:
				continue

			# Render the message
			try:
				part = t.generate(**namespace)

			# Reset the rendered template when it could not be rendered
			except:
				self.templates.reset()
				raise

			# Parse the message
			part = email.message_from_string(part)

			# Extract the headers
			for k, v in part.items():
				message.add_header(k, v)

			body = part.get_payload()

			# Render markdown
			if fmt == "markdown":
				body = markdown.markdown(body)

			# Compile part again
			part = email.mime.text.MIMEText(body, mimetype, "utf-8")

			# Attach the parts to the mime container
			# According to RFC2046, the last part of a multipart message is preferred
			alternative.attach(part)

		# Add alternative section to outer message
		message.attach(alternative)

		# Send the message
		self.send_to(user.email.recipient if user else recipient, message, sender=sender, headers=headers)

	def queue(self, message):
		res = self.db.get("INSERT INTO messages(message) VALUES(%s) RETURNING id", message)

		logging.info("Message queued as %s", res.id)

	def __sendmail(self, message):
		# Convert message from string
		msg = email.message_from_string(message.message)

		# Get some headers
		recipient = msg.get("To")
		subject   = msg.get("Subject")

		logging.info("Sending mail to %s: %s" % (recipient, subject))

		# Run sendmail and the email in
		p = subprocess.Popen(["/usr/lib/sendmail", "-t"], bufsize=0, close_fds=True,
			stdin=subprocess.PIPE, stdout=subprocess.PIPE)

		stdout, stderr = p.communicate(msg.as_string())

		# Wait until sendmail has finished.
		p.wait()

		if p.returncode:
			raise Exception, "Could not send mail: %s" % stderr

		# Mark message as sent
		self.db.execute("UPDATE messages SET sent_at = NOW() WHERE id = %s", message.id)
