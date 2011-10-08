#!/usr/bin/python

import hashlib
import logging
import os
import pakfire.packages
import uuid

import base
import misc
import packages

from constants import *

class Uploads(base.Object):
	def get_by_uuid(self, _uuid):
		upload = self.db.get("SELECT id FROM uploads WHERE uuid = %s", _uuid)

		return Upload(self.pakfire, upload.id)

	def new(self, *args, **kwargs):
		return Upload.new(self.pakfire, *args, **kwargs)

	def get_all(self):
		uploads = self.db.query("SELECT id FROM uploads")

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
	def new(cls, pakfire, builder, filename, size, hash):
		_uuid = uuid.uuid4()

		id = pakfire.db.execute("INSERT INTO uploads(uuid, builder, filename, size, hash)"
			" VALUES(%s, %s, %s, %s, %s)", _uuid, builder.id, filename, size, hash)

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
	def builder(self):
		return self.pakfire.builders.get_by_id(self.data.builder)

	def append(self, data):
		logging.debug("Writing %s bytes to %s" % (len(data), self.path))

		f = open(self.path, "ab")
		f.write(data)
		f.close()

	def validate(self):
		# Calculate a hash to validate the upload.
		hash = misc.calc_hash1(self.path)

		ret = self.hash == hash

		if not ret:
			logging.error("Hash did not match: %s != %s" % (self.hash, hash))

		return ret

	def remove(self):
		# Remove the uploaded data.
		if os.path.exists(self.path):
			os.unlink(self.path)

		# Delete the upload from the database.
		self.db.execute("DELETE FROM uploads WHERE id = %s", self.id)

	def time_start(self):
		return self.data.time_start

	def commit(self, build):
		# Find out what kind of file this is.
		filetype = misc.guess_filetype(self.path)

		# If the filetype is unhandled, we remove the file and raise an
		# exception.
		if filetype == "unknown":
			self.remove()
			raise Exception, "Cannot handle unknown file."

		# If file is a package we open it and insert its information to the
		# database.
		if filetype == "pkg":
			logging.debug("%s is a package file." % self.path)
			file = pakfire.packages.open(None, None, self.path)

			if file.type == "source":
				packages.Package.new(self.pakfire, file, build)

			elif file.type == "binary":
				build.pkg.add_file(file, build)

		elif filetype == "log":
			build.add_log(self.path)

		# Finally, remove the upload.
		self.remove()

	def cleanup(self):
		# Get the seconds since we are running.
		try:
			time_running = datetime.datetime.utcnow() - self.time_start
			time_running = time_running.total_seconds()
		except:
			time_running = 0

		# Remove uploads that are older than 24 hours.
		if time_running >= 3600 * 24:
			self.remove()
