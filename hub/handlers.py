#!/usr/bin/python

import base64
import hashlib
import logging
import os
import tornado.web
import uuid
import xmlrpclib

import backend.builds
from backend.builders import Builder
from backend.builds import Build
from backend.packages import Package
from backend.uploads import Upload
from backend.users import User

class BaseHandler(tornado.web.RequestHandler):
	"""
		Handler class that provides very basic things we will need.
	"""
	@property
	def pakfire(self):
		"""
			Reference to the Pakfire object.
		"""
		return self.application.pakfire

	@property
	def remote_address(self):
		"""
			Returns the IP address the request came from.
		"""
		remote_ips = self.request.remote_ip.split(", ")

		return remote_ips[-1]


class RedirectHandler(BaseHandler):
	"""
		This handler redirects from the hub to the main website.
	"""
	def get(self):
		url = self.pakfire.settings.get("baseurl", None)

		# If there was no URL in the database, we cannot do anything.
		if not url:
			raise tornado.web.HTTPError(404)

		self.redirect(url)

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
			print self
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


class CommonHandler(XMLRPCHandler):
	"""
		Subclass that provides very basic functions that do not need any
		kind of authentication and are accessable by any user/builder.
	"""

	def noop(self):
		"""
			No operation. Just check if the connection is working.
		"""
		return True

	def test_code(self, error_code=200):
		"""
			For testing a client.

			This just returns a HTTP response with the given code.
		"""
		raise tornado.web.HTTPError(error_code)

	def get_my_address(self):
		"""
			Return the address of the requesting host.

			This is to discover it through NAT.
		"""
		return self.remote_address

	def get_hub_status(self):
		"""
			Return some status information about the hub.
		"""

		# Return number of pending and running builds.
		ret = {
			"jobs_pending" : self.pakfire.jobs.count(state="pending"),
			"jobs_running" : self.pakfire.jobs.count(state="running"),
		}

		return ret


class AuthHandler(CommonHandler):
	def _auth(self, name, password):
		raise NotImplementedError

	def get_current_user(self):
		"""
			This handles HTTP Basic authentication.
		"""
		auth_header = self.request.headers.get("Authorization", None)

		# If no authentication information was provided, we stop here.
		if not auth_header:
			return

		# No basic auth? We cannot handle that.
		if not auth_header.startswith("Basic "):
			raise tornado.web.HTTPError(400, "Can only handle Basic auth.")

		# Decode the authentication information.
		auth_header = base64.decodestring(auth_header[6:])

		try:
			name, password = auth_header.split(":", 1)
		except:
			raise tornado.web.HTTPError(400, "Authorization data was malformed")

		# Authenticate user to the database.
		return self._auth(name, password)


class UserAuthMixin(object):
	"""
		Mixin to authenticate users.
	"""
	def _auth(self, username, password):
		return self.pakfire.users.auth(username, password)

	@property
	def user(self):
		"""
			Alias for "current_user".
		"""
		return self.current_user

	@property
	def builder(self):
		return None

	def check_auth(self):
		"""
			Tell the user if he authenticated successfully.
		"""
		if self.user:
			return True

		return False


class BuilderAuthMixin(object):
	"""
		Mixin to authenticate builders.
	"""
	def _auth(self, hostname, password):
		return self.pakfire.builders.auth(hostname, password)

	@property
	def builder(self):
		"""
			Alias for "current_user".
		"""
		return self.current_user

	@property
	def user(self):
		return None


class CommonAuthHandler(AuthHandler):
	"""
		Methods that are usable by both, the real users and the builders
		but they require an authentication.
	"""
	@tornado.web.authenticated
	def build_create(self, upload_id, distro_ident, arches):
		## Check if the user has permission to create a build.
		# Builders do have the permission to create all kinds of builds.
		if isinstance(self.current_user, Builder):
			type = "release"
			check_for_duplicates = True
		#
		# Users only have the permission to create scratch builds.
		elif isinstance(self.current_user, User) and \
				self.current_user.has_perm("create_scratch_builds"):
			type = "scratch"
			check_for_duplicates = False
		#
		# In all other cases, it is not allowed to proceed.
		else:
			raise tornado.web.HTTPError(403, "Not allowed to create a build.")

		# Get previously uploaded file to create this build from.
		upload = self.pakfire.uploads.get_by_uuid(upload_id)
		if not upload:
			raise tornado.web.HTTPError(400, "Upload does not exist: %s" % upload_id)

		# Check if the uploaded file belongs to this user/builder.
		if self.user and not upload.user == self.user:
			raise tornado.web.HTTPError(400, "Upload does not belong to this user.")

		elif self.builder and not upload.builder == self.builder:
			raise tornado.web.HTTPError(400, "Upload does not belong to this builder.")

		# Get distribution this package should be built for.
		distro = self.pakfire.distros.get_by_ident(distro_ident)
		if not distro:
			distro = self.pakfire.distros.get_default()

		# Open the package that was uploaded earlier and add it to
		# the database. Create a new build object from the uploaded package.
		ret = backend.builds.import_from_package(self.pakfire, upload.path,
			distro=distro, type=type, arches=arches, owner=self.current_user,
			check_for_duplicates=check_for_duplicates)

		if not ret:
			raise tornado.web.HTTPError(500, "Could not create build from package.")

		# Creating the build will move the file to the build directory,
		# so we can safely remove the uploaded file.
		upload.remove()

		# Return a bunch of information about the build back to the user.
		pkg, build = ret

		return build.info

	# Upload processing.

	@tornado.web.authenticated
	def upload_create(self, filename, size, hash):
		"""
			Create a new upload object in the database and return a unique ID
			to the uploader.
		"""
		upload = Upload.create(self.pakfire, filename, size, hash,
			user=self.user, builder=self.builder)

		return upload.uuid

	@tornado.web.authenticated
	def upload_chunk(self, upload_id, data):
		upload = self.pakfire.uploads.get_by_uuid(upload_id)
		if not upload:
			raise tornado.web.HTTPError(404, "Invalid upload id.")

		if not upload.builder == self.builder:
			raise tornado.web.HTTPError(403, "Uploading an other host's file.")

		upload.append(data.data)

	@tornado.web.authenticated
	def upload_finished(self, upload_id):
		upload = self.pakfire.uploads.get_by_uuid(upload_id)
		if not upload:
			raise tornado.web.HTTPError(404, "Invalid upload id.")

		if not upload.builder == self.builder:
			raise tornado.web.HTTPError(403, "Uploading an other host's file.")

		# Validate the uploaded data to its hash.
		ret = upload.validate()

		# If the validation was successfull, we mark the upload
		# as finished and send True to the client.
		if ret:
			upload.finished()
			return True

		# In case the download was corrupted or incomplete, we delete it
		# and tell the client to start over.
		upload.remove()
		return False

	@tornado.web.authenticated
	def upload_remove(self, upload_id):
		upload = self.pakfire.uploads.get_by_uuid(upload_id)
		if not upload:
			raise tornado.web.HTTPError(404, "Invalid upload id.")

		if not upload.builder == self.builder:
			raise tornado.web.HTTPError(403, "Removing an other host's file.")

		# Remove the upload from the database and trash the data.
		upload.remove()


class UserHandler(UserAuthMixin, CommonAuthHandler):
	"""
		Subclass with methods that are only accessable by users.
	"""
	@tornado.web.authenticated
	def get_user_profile(self):
		"""
			Send a bunch of account information to the user.
		"""
		user = self.current_user

		ret = {
			"name"       : user.name,
			"realname"   : user.realname,
			"role"       : user.state,
			"email"      : user.email,
			"registered" : user.registered,
		}

		return ret

	@tornado.web.authenticated
	def get_builds(self, type=None, limit=10, offset=0):
		if not type in (None, "scratch", "release"):
			return

		builds = self.pakfire.builds.get_by_user_iter(self.current_user, type=type)

		try:
			counter = limit + offset
		except ValueError:
			return []

		ret = []
		for build in builds:
			build = self.get_build(build.id)

			ret.append(build)

			counter -= 1
			if counter <= 0:
				break

		return ret

	@tornado.web.authenticated
	def get_build(self, build_id):
		# Check for empty input.
		if not build_id:
			return None

		build = self.pakfire.builds.get_by_uuid(build_id)
		if not build:
			return {}

		ret = {
			# Identity information.
			"uuid"         : build.uuid,
			"type"         : build.type,
			"state"        : build.state, # XXX do we actually use this?

			"name"         : build.name,
			"sup_arches"   : build.supported_arches,
			"jobs"         : [self.get_job(j.uuid) for j in build.jobs],

			"severity"     : build.severity,
			"priority"     : build.priority,

			# The source package of this build.
			"pkg_id"       : build.pkg.uuid,

			"distro"       : build.distro.id,
			"repo"         : None,

			"time_created" : build.created,
			"score"        : build.credits,
		}

		# If the build is in a repository, update that bit.
		if build.repo:
			ret["repo"] = build.repo.id

		return ret

	@tornado.web.authenticated
	def get_latest_jobs(self):
		jobs = []

		for job in self.pakfire.jobs.get_latest():
			job = self.get_job(job.uuid)
			if job:
				jobs.append(job)

		return jobs

	@tornado.web.authenticated
	def get_active_jobs(self, host_id=None):
		jobs = []

		for job in self.pakfire.jobs.get_active(host_id=host_id):
			job = self.get_job(job.uuid)
			if job:
				jobs.append(job)

		return jobs

	@tornado.web.authenticated
	def get_job(self, job_id):
		job = self.pakfire.jobs.get_by_uuid(job_id)
		if not job:
			return

		# XXX check if user is allowed to view this job.

		ret = {
			# Identity information.
			"uuid"          : job.uuid,
			"type"          : job.type,

			# Name, state, architecture.
			"name"          : job.name,
			"state"         : job.state,
			"arch"          : job.arch.name,

			# Information about the build this job lives in.
			"build_id"      : job.build.uuid,

			# The package that is built in this job.
			"pkg_id"        : job.pkg.uuid,
			"packages"      : [self.get_package(p.uuid) for p in job.packages],

			# The builder that builds this job.
			"builder_id"    : job.builder_id,

			# Time information.
			"duration"      : job.duration,
			"time_created"  : job.time_created,
			"time_started"  : job.time_started,
			"time_finished" : job.time_finished,
		}

		return ret

	@tornado.web.authenticated
	def get_builders(self):
		builders = []

		for builder in self.pakfire.builders.get_all():
			builder = self.get_builder(builder.id)
			if builder:
				builders.append(builder)

		return builders

	@tornado.web.authenticated
	def get_builder(self, builder_id):
		builder = self.pakfire.builders.get_by_id(builder_id)
		if not builder:
			return

		ret = {
			"name"          : builder.name,
			"description"   : builder.description,
			"state"         : builder.state,

			"arches"        : [a.name for a in builder.arches],
			"disabled"      : builder.disabled,

			"cpu_model"     : builder.cpu_model,
			"cpu_count"     : builder.cpu_count,
			"memory"        : builder.memory / 1024,

			"active_jobs"   : [j.uuid for j in builder.get_active_jobs()],
		}

		return ret

	@tornado.web.authenticated
	def get_package(self, pkg_id):
		pkg = self.pakfire.packages.get_by_uuid(pkg_id)
		if not pkg:
			return

		ret = {
			"uuid"             : pkg.uuid,
			"name"             : pkg.name,
			"epoch"            : pkg.epoch,
			"version"          : pkg.version,
			"release"          : pkg.release,
			"arch"             : pkg.arch.name,
			"supported_arches" : pkg.supported_arches,
			"type"             : pkg.type,
			"friendly_name"    : pkg.friendly_name,
			"friendly_version" : pkg.friendly_version,
			"groups"           : pkg.groups,
			"license"          : pkg.license,
			"url"              : pkg.url,
			"summary"          : pkg.summary,
			"description"      : pkg.description,

			"size"             : pkg.size,
			"filesize"         : pkg.filesize,
			"hash_sha512"      : pkg.hash_sha512,

			# Dependencies.
			"prerequires"      : pkg.prerequires,
			"requires"         : pkg.requires,
			"provides"         : pkg.provides,
			"obsoletes"        : pkg.obsoletes,
			"conflicts"        : pkg.conflicts,

			# Build infos.
			"build_id"         : pkg.build_id,
			"build_host"       : pkg.build_host,
			"build_time"       : pkg.build_time,
		}

		if isinstance(pkg.maintainer, User):
			ret["maintainer"] = "%s <%s>" % (pkg.maintainer.realname, pkg.maintainer.email)
		elif pkg.maintainer:
			ret["maintainer"] = pkg.maintainer

		if pkg.distro:
			ret["distro_id"] = pkg.distro.id
		else:
			ret["distro_id"] = None

		return ret


class BuilderHandler(BuilderAuthMixin, CommonAuthHandler):
	"""
		Subclass with methods that are only accessable by builders.
	"""
	@tornado.web.authenticated
	def send_keepalive(self, loadavg, overload, free_space=None):
		"""
			The client just says hello and we tell it if we it needs to
			send some information about itself.
		"""
		self.builder.update_keepalive(loadavg, free_space)

		# Pass overload argument.
		if overload in (True, False):
			self.builder.update_overload(overload)

		# Tell the client if it should send an update of its infos.
		return self.builder.needs_update()

	@tornado.web.authenticated
	def send_update(self, arches, cpu_model, cpu_count, memory, pakfire_version=None, host_key_id=None):
		self.builder.update_info(arches, cpu_model, cpu_count, memory * 1024,
			pakfire_version=pakfire_version, host_key_id=host_key_id)

	@tornado.web.authenticated
	def build_get_job(self, arches):
		# Disabled buildes do not get any jobs.
		if self.builder.disabled:
			logging.debug("Host requested job but is disabled: %s" % self.builder.name)
			return

		# Check if host has already too many simultaneous jobs.
		if self.builder.too_many_jobs:
			logging.debug("Host has already too many jobs: %s" % self.builder.name)
			return

		# Automatically add noarch if not already present.
		if not "noarch" in arches:
			arches.append("noarch")

		# Get all supported architectures.
		supported_arches = []
		for arch_name in arches:
			arch = self.pakfire.arches.get_by_name(arch_name)
			if not arch:
				logging.debug("Unsupported architecture: %s" % arch_name)
				continue

			# Skip disabled arches.
			if arch in self.builder.disabled_arches:
				continue

			supported_arches.append(arch)

		if not supported_arches:
			logging.warning("Host does not support any arches: %s" % self.builder.name)
			return

		# Get the next job for this builder.
		job = self.builder.get_next_job(supported_arches)
		if not job:
			logging.debug("Could not find a buildable job for %s" % self.builder.name)
			return

		# We got a buildable job, so let's start...
		logging.debug("%s is going to build %s" % (self.builder.name, job))
		build = job.build

		try:
			# Set job to dispatching state.
			job.state = "dispatching"

			# Set our build host.
			job.builder = self.builder

			ret = {
				"id"                 : job.uuid,
				"arch"               : job.arch.name,
				"source_url"         : build.source_download,
				"source_hash_sha512" : build.source_hash_sha512,
				"type"               : job.type,
				"config"             : job.get_config(),
			}

			# Send build information to the builder.
			return ret

		except:
			# If anything went wrong, we reset the state.
			job.state = "pending"
			raise

	def build_job_update_state(self, job_id, state, message=None):
		job = self.pakfire.jobs.get_by_uuid(job_id)
		if not job:
			raise tornado.web.HTTPError(404, "Invalid job id.")

		if not job.builder == self.builder:
			raise tornado.web.HTTPError(403, "Altering another builder's build.")

		# Save information to database.
		job.state = state
		job.update_message(message)

		return True

	def build_job_add_file(self, job_id, upload_id, type):
		assert type in ("package", "log")

		# Fetch job we are working on and check if it is actually ours.
		job = self.pakfire.jobs.get_by_uuid(job_id)
		if not job:
			raise tornado.web.HTTPError(404, "Invalid job id.")

		if not job.builder == self.builder:
			raise tornado.web.HTTPError(403, "Altering another builder's job.")

		# Fetch uploaded file object and check we uploaded it ourself.
		upload = self.pakfire.uploads.get_by_uuid(upload_id)
		if not upload:
			raise tornado.web.HTTPError(404, "Invalid upload id.")

		if not upload.builder == self.builder:
			raise tornado.web.HTTPError(403, "Using an other host's file.")

		# Remove all files that have to be deleted, first.
		self.pakfire.cleanup_files()

		try:
			job.add_file(upload.path)

		finally:
			# Finally, remove the uploaded file.
			upload.remove()

		return True

	def build_job_crashed(self, job_id, exitcode):
		job = self.pakfire.jobs.get_by_uuid(job_id)
		if not job:
			raise tornado.web.HTTPError(404, "Invalid job id.")

		if not job.builder == self.builder:
			raise tornado.web.HTTPError(403, "Altering another builder's build.")

		# Set build into aborted state.
		job.state = "aborted"

		# Set aborted state.
		job.aborted_state = exitcode

	def build_jobs_aborted(self, job_ids):
		"""
			Returns all aborted job ids from the input list.
		"""
		aborted_jobs = []

		for job_id in job_ids:
			job = self.pakfire.jobs.get_by_uuid(job_id)
			if not job:
				logging.debug("Unknown job id: %s" % job_id)
				continue

			# Check if we own this job.
			if not job.builder == self.builder:
				logging.debug("Job %s belongs to another builder." % job_id)
				continue

			if job.state == "aborted":
				aborted_jobs.append(job.uuid)

		return aborted_jobs

	def build_upload_buildroot(self, job_id, pkgs):
		"""
			Saves the buildroot the builder sends.
		"""
		job = self.pakfire.jobs.get_by_uuid(job_id)
		if not job:
			raise tornado.web.HTTPError(404, "Invalid job id.")

		if not job.builder == self.builder:
			raise tornado.web.HTTPError(403, "Altering another builder's build.")

		job.save_buildroot(pkgs)
