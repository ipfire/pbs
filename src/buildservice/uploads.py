#!/usr/bin/python

from __future__ import division

import datetime
import hashlib
import logging
import os
import shutil
import uuid

import pakfire.packages

import base
import misc
import packages

from constants import *

class Uploads(base.Object):
	def get_by_uuid(self, _uuid):
		upload = self.db.get("SELECT id FROM uploads WHERE uuid = %s", _uuid)

		return Upload(self.pakfire, upload.id)

	def get_all(self):
		uploads = self.db.query("SELECT id FROM uploads ORDER BY time_started DESC")

		return [Upload(self.pakfire, u.id) for u in uploads]

	def cleanup(self):
		for upload in self.get_all():
			upload.cleanup()


class Upload(base.Object):
	def __init__(self, pakfire, id):
		base.Object.__init__(self, pakfire)

		self.id = id
		self.data = self.db.get("SELECT * FROM uploads WHERE id = %s", self.id)

	@classmethod
	def create(cls, pakfire, filename, size, hash, builder=None, user=None):
		assert builder or user

		id = pakfire.db.execute("INSERT INTO uploads(uuid, filename, size, hash) \
			VALUES(%s, %s, %s, %s)", "%s" % uuid.uuid4(), filename, size, hash)

		if builder:
			pakfire.db.execute("UPDATE uploads SET builder_id = %s WHERE id = %s",
				builder.id, id)

		elif user:
			pakfire.db.execute("UPDATE uploads SET user_id = %s WHERE id = %s",
				user.id, id)

		upload = cls(pakfire, id)

		# Create space to where we save the data.
		dirname = os.path.dirname(upload.path)
		if not os.path.exists(dirname):
			os.makedirs(dirname)

		# Create empty file.
		f = open(upload.path, "w")
		f.close()

		return upload

	@property
	def uuid(self):
		return self.data.uuid

	@property
	def hash(self):
		return self.data.hash

	@property
	def filename(self):
		return self.data.filename

	@property
	def path(self):
		return os.path.join(UPLOADS_DIR, self.uuid, self.filename)

	@property
	def size(self):
		return self.data.size

	@property
	def progress(self):
		return self.data.progress / self.size

	@property
	def builder(self):
		if self.data.builder_id:
			return self.pakfire.builders.get_by_id(self.data.builder_id)

	@property
	def user(self):
		if self.data.user_id:
			return self.pakfire.users.get_by_id(self.data.user_id)

	def append(self, data):
		# Check if the filesize was exceeded.
		size = os.path.getsize(self.path) + len(data)
		if size > self.data.size:
			raise Exception, "Given filesize was exceeded for upload %s" % self.uuid

		logging.debug("Writing %s bytes to %s" % (len(data), self.path))

		f = open(self.path, "ab")
		f.write(data)
		f.close()

		self.db.execute("UPDATE uploads SET progress = %s WHERE id = %s",
			size, self.id)

	def validate(self):
		size = os.path.getsize(self.path)
		if not size == self.data.size:
			logging.error("Filesize is not okay: %s" % (self.uuid))
			return False

		# Calculate a hash to validate the upload.
		hash = misc.calc_hash1(self.path)

		if not self.hash == hash:
			logging.error("Hash did not match: %s != %s" % (self.hash, hash))
			return False

		return True

	def finished(self):
		"""
			Update the status of the upload in the database to "finished".
		"""
		# Check if the file was completely uploaded and the hash is correct.
		# If not, the upload has failed.
		if not self.validate():
			return False

		self.db.execute("UPDATE uploads SET finished = 'Y', time_finished = NOW() \
			WHERE id = %s", self.id)

		return True

	def remove(self):
		# Remove the uploaded data.
		path = os.path.dirname(self.path)
		if os.path.exists(path):
			shutil.rmtree(path, ignore_errors=True)

		# Delete the upload from the database.
		self.db.execute("DELETE FROM uploads WHERE id = %s", self.id)

	@property
	def time_started(self):
		return self.data.time_started

	@property
	def time_running(self):
		# Get the seconds since we are running.
		try:
			time_running = datetime.datetime.utcnow() - self.time_started
			time_running = time_running.total_seconds()
		except:
			time_running = 0

		return time_running

	@property
	def speed(self):
		if not self.time_running:
			return 0

		return self.data.progress / self.time_running

	def cleanup(self):
		# Remove uploads that are older than 2 hours.
		if self.time_running >= 3600 * 2:
			self.remove()
