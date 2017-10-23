#!/usr/bin/python

from __future__ import division

import datetime
import hashlib
import logging
import os
import shutil

import pakfire.packages

from . import base
from . import misc
from . import packages
from . import users

from .constants import *
from .decorators import *

class Uploads(base.Object):
	def _get_upload(self, query, *args):
		res = self.db.get(query, *args)

		if res:
			return Upload(self.backend, res.id, data=res)

	def _get_uploads(self, query, *args):
		res = self.db.query(query, *args)

		for row in res:
			yield Upload(self.backend, row.id, data=row)

	def __iter__(self):
		uploads = self._get_uploads("SELECT * FROM uploads ORDER BY time_started DESC")

		return iter(uploads)

	def get_by_uuid(self, uuid):
		return self._get_upload("SELECT * FROM uploads WHERE uuid = %s", uuid)

	def create(self, filename, size, hash, builder=None, user=None):
		assert builder or user

		# Create a random ID for this upload
		uuid = users.generate_random_string(64)

		upload = self._get_upload("INSERT INTO uploads(uuid, filename, size, hash) \
			VALUES(%s, %s, %s, %s) RETURNING *", uuid, filename, size, hash)

		if builder:
			upload.builder = builder

		elif user:
			upload.user = user

		# Create space to where we save the data.
		dirname = os.path.dirname(upload.path)
		if not os.path.exists(dirname):
			os.makedirs(dirname)

		# Create empty file.
		f = open(upload.path, "w")
		f.close()

		return upload

	def cleanup(self):
		for upload in self.get_all():
			upload.cleanup()


class Upload(base.DataObject):
	table = "uploads"

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

	# Builder

	def get_builder(self):
		if self.data.builder_id:
			return self.backend.builders.get_by_id(self.data.builder_id)

	def set_builder(self, builder):
		self._set_attribute("builder_id", builder.id)

	builder = lazy_property(get_builder, set_builder)

	# User

	def get_user(self):
		if self.data.user_id:
			return self.backend.users.get_by_id(self.data.user_id)

	def set_user(self, user):
		self._set_attribute("user_id", user.id)

	user = lazy_property(get_user, set_user)

	def append(self, data):
		# Check if the filesize was exceeded.
		size = os.path.getsize(self.path) + len(data)
		if size > self.data.size:
			raise Exception, "Given filesize was exceeded for upload %s" % self.uuid

		logging.debug("Writing %s bytes to %s" % (len(data), self.path))

		with open(self.path, "ab") as f:
			f.write(data)

		self._set_attribute("progress", size)

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

		self._set_attribute("finished", True)
		self._set_attribute("time_finished", datetime.datetime.utcnow())

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
