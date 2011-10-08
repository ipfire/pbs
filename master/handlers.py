#!/usr/bin/python

import hashlib
import logging
import os
import tornado.web
import uuid
import xmlrpclib

from backend.build import BinaryBuild, SourceBuild
from backend.packages import Package

class BaseHandler(tornado.web.RequestHandler):
	@property
	def pakfire(self):
		return self.application.pakfire

	# XXX should not be needed
	#@property
	#def db(self):
	#	return self.application.pakfire.db


# From: http://blog.joshmarshall.org/2009/10/its-a-twister-now-with-more-xml/
#
# This is just a very simple implementation from the website above, because
# I badly want to run this software out of the box on any distribution.
#

def private(func):
	# Decorator to make a method, well, private.
	class PrivateMethod(object):
		def __init__(self):
			self.private = True

		__call__ = func

	return PrivateMethod()


class XMLRPCHandler(BaseHandler):
	"""
		Subclass this to add methods -- you can treat them
		just like normal methods, this handles the XML formatting.
	"""
	def post(self):
		"""
			Later we'll make this compatible with "dot" calls like:
			server.namespace.method()
			If you implement this, make sure you do something proper
			with the Exceptions, i.e. follow the XMLRPC spec.
		"""
		try:
			params, method_name = xmlrpclib.loads(self.request.body)
		except:
			# Bad request formatting, bad.
			raise tornado.web.HTTPError(400)

		if method_name in dir(tornado.web.RequestHandler):
			# Pre-existing, not an implemented attribute
			raise AttributeError('%s is not implemented.' % method_name)

		try:
			method = getattr(self, method_name)
		except:
			# Attribute doesn't exist
			raise AttributeError('%s is not a valid method.' % method_name)

		if not callable(method):
			# Not callable, so not a method
			raise Exception('Attribute %s is not a method.' % method_name)

		if method_name.startswith('_') or \
				('private' in dir(method) and method.private is True):
			# No, no. That's private.
			raise Exception('Private function %s called.' % method_name)

		response = method(*params)
		response_xml = xmlrpclib.dumps((response,), methodresponse=True,
			allow_none=True)

		self.set_header("Content-Type", "text/xml")
		self.write(response_xml)


class AuthXMLRPCHandler(XMLRPCHandler):
	"""
		This handler forces the host to authenticate against the server.

		All methods of this class can be sure that they receive 100% okay data.
	"""
	def post(self, hostname, passphrase):
		# Get the builder from the database.
		self.builder = self.pakfire.builders.get_by_name(hostname)
		if not self.builder:
			raise tornado.web.HTTPError(403)

		# Check if the passphrase matches and return 403 Forbidden if
		# the authentication data is invalid.
		if not self.builder.validate_passphrase(passphrase):
			raise tornado.web.HTTPError(403)

		# Parse the actual request.
		XMLRPCHandler.post(self)


class RPCBaseHandler(AuthXMLRPCHandler):
	@staticmethod
	def chunkPath(id):
		return os.path.join("/var/tmp/pakfire-upload-%s" % id)

	def get_upload_cookie(self, filename, size, hash):
		"""
			Create a new upload object in the database and return a unique ID
			to the uploader.
		"""
		upload = self.pakfire.uploads.new(self.builder, filename, size, hash)

		return upload.uuid

	def upload_chunk(self, upload_id, data):
		upload = self.pakfire.uploads.get_by_uuid(upload_id)
		if not upload:
			raise tornado.web.HTTPError(404, "Invalid upload id.")

		if not upload.builder == self.builder:
			raise tornado.web.HTTPError(403, "Uploading an other hosts file.")

		upload.append(data.data)

	def finish_upload(self, upload_id, build_id):
		upload = self.pakfire.uploads.get_by_uuid(upload_id)
		if not upload:
			raise tornado.web.HTTPError(404, "Invalid upload id.")

		# Get the corresponding build (needed for arch, etc.)
		build = self.pakfire.builds.get_by_uuid(build_id)
		if not build:
			raise tornado.web.HTTPError(400, "Invalid build id.")

		# Validate the uploaded data to its hash.
		ret = upload.validate()

		# If the hash does not match, we delete the upload.
		if not ret:
			upload.remove()
			return ret

		# Save the file to its designated place.
		upload.commit(build)

		# Send the validation result to the uploader.
		return ret

	def chunk_upload(self, id, hash, data):
		if not id:
			id = "%s" % uuid.uuid4()

		# Get the filename of the upload.
		filename = self.chunkPath(id)

		# Extract data.
		data = data.data

		# Check the data integrity.
		if not hash == hashlib.sha1(data).hexdigest():
			raise Exception, "Chunk was corrupted"

		# Write the data to file.
		f = open(filename, "a")
		f.write(data)
		f.close()

		# Return the ID to add more chunks to the data.
		return id

	def package_add_file(self, pkg_id, file_id, info):
		pkg = self.pakfire.packages.get_by_id(pkg_id)

		filename = self.chunkPath(file_id)
		if not os.path.exists(filename):
			raise Exception, "Chunk file not found"

		return pkg.add_file(filename, info)

	def package_add(self, info):
		pkg = self.pakfire.packages.get_by_tuple(info.get("name"), info.get("epoch"),
			info.get("version"), info.get("release"))

		if pkg:
			logging.debug("Package does already exist: %s" % pkg)
			return pkg.id

		pkg = Package.new(self.pakfire, info)

		return pkg.id

	def build_add_log(self, build_id, file_id):
		build = self.pakfire.builds.get_by_uuid(build_id)

		filename = self.chunkPath(file_id)
		if not os.path.exists(filename):
			raise Exception, "Chunk file not found"

		build.add_log(filename)

		return True


class RPCBuilderHandler(RPCBaseHandler):
	def update_host_info(self, loadavg, cpu_model, memory, arches):
		"""
			Receive detailed host information and store it to the database.
		"""
		self.builder.update_info(loadavg, cpu_model, memory, arches)

	def update_build_state(self, build_id, state, message):
		build = self.pakfire.builds.get_by_uuid(build_id)
		if not build:
			return

		# Save information to database.
		build.state, build.message = state, message

		return True

	def build_job(self, type=None):
		if self.builder.disabled:
			logging.warning("Disabled builder wants to get a job: %s" % \
				self.builder.hostname)
			return

		# XXX need to handle type here

		# Check if host has already enough running build jobs.
		if len(self.builder.active_builds) >= self.builder.max_jobs:
			return

		# Determine what kind of builds the host should get.
		build = None
		if self.builder.build_src:
			# Source builds are preferred over binary builds if the host does
			# support this.

			# If there is not already a source job running on this host, we
			# can grab a new one.
			if not "source" in [b.type for b in self.builder.active_builds]:
				build = self.pakfire.builds.get_next(type="source", limit=1)

		if not build and self.builder.build_bin:
			# If the host does not support source builds or there are no source
			# builds to do, we try to grab a binary build in a supported arch.
			build = self.pakfire.builds.get_next(type="binary", limit=1,
				arches=self.builder.arches)

		# If there is no build that we can do, we can skip the rest.
		if not build:
			return

		try:
			# Set build to be dispatching that it won't be taken by another
			# host.
			build.state = "dispatching"

			# Assign the build job to the host that requested this.
			build.host = self.builder.hostname

			if build.type == "source":
				# The source build job build job is immediately changed to running
				# state.
				return {
					"type"      : "source",
					"id"        : build.uuid,
					"revision"  : build.revision,
					"source"    : build.source.info,
				}

			elif build.type == "binary":
				# Get source package.
				source = build.pkg.sourcefile
				assert source

				return {
					"type"      : "binary",
					"arch"      : build.arch,
					"id"        : build.uuid,
					"pkg_id"    : build.pkg_id,
					"source_id" : source.source.id,
					"name"      : source.name,
					"download"  : source.download,
					"hash1"     : source.hash1,
				}
		except:
			# If there has been any error, we reset the build.
			build.state = "pending"

	def get_repos(self, limit=None):
		repos = self.pakfire.repos.get_needs_update(limit=limit)

		# XXX disabled for testing
		#for repo in repos:
		#	repo.needs_update = False

		return [r.info for r in repos]

	def get_repo_packages(self, repo_id):
		repo = self.pakfire.repos.get_by_id(repo_id)

		if not repo:
			return

		pkgs = []
		for pkg in repo.get_packages():
			pkgs += [f.abspath for f in pkg.packagefiles]

		return pkgs
