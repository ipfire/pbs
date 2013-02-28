#!/usr/bin/python

import backend

import base64
import hashlib
import json
import logging
import time
import tornado.web

class LongPollMixin(object):
	def initialize(self):
		self._start_time = time.time()

	def add_timeout(self, timeout, callback):
		deadline = time.time() + timeout

		return self.application.ioloop.add_timeout(deadline, callback)

	def on_connection_close(self):
		logging.debug("Connection closed unexpectedly")

	def connection_closed(self):
		return self.request.connection.stream.closed()

	@property
	def runtime(self):
		return time.time() - self._start_time


class BaseHandler(LongPollMixin, tornado.web.RequestHandler):
	@property
	def backend(self):
		"""
			Shortcut handler to pakfire instance.
		"""
		return self.application.pakfire

	def get_basic_auth_credentials(self):
		"""
			This handles HTTP Basic authentication.
		"""
		auth_header = self.request.headers.get("Authorization", None)

		# If no authentication information was provided, we stop here.
		if not auth_header:
			return None, None

		# No basic auth? We cannot handle that.
		if not auth_header.startswith("Basic "):
			raise tornado.web.HTTPError(400, "Can only handle Basic auth.")

		try:
			# Decode the authentication information.
			auth_header = base64.decodestring(auth_header[6:])

			name, password = auth_header.split(":", 1)
		except:
			raise tornado.web.HTTPError(400, "Authorization data was malformed")

		return name, password

	def get_current_user(self):
		name, password = self.get_basic_auth_credentials()
		if name is None:
			return

		builder = self.backend.builders.auth(name, password)
		if builder:
			return builder

		user = self.backend.users.auth(name, password)
		if user:
			return user

	@property
	def builder(self):
		if isinstance(self.current_user, backend.builders.Builder):
			return self.current_user

	@property
	def user(self):
		if isinstance(self.current_user, backend.users.User):
			return self.current_user

	def get_argument_int(self, *args, **kwargs):
		arg = self.get_argument(*args, **kwargs)

		try:
			return int(arg)
		except (TypeError, ValueError):
			return None

	def get_argument_float(self, *args, **kwargs):
		arg = self.get_argument(*args, **kwargs)

		try:
			return float(arg)
		except (TypeError, ValueError):
			return None

	def get_argument_json(self, *args, **kwargs):
		arg = self.get_argument(*args, **kwargs)

		if arg:
			return json.loads(arg)


class NoopHandler(BaseHandler):
	def get(self):
		if self.builder:
			self.write("Welcome to the Pakfire hub, %s!" % self.builder.hostname)
		elif self.user:
			self.write("Welcome to the Pakfire hub, %s!" % self.user.name)
		else:
			self.write("Welcome to the Pakfire hub!")


class ErrorTestHandler(BaseHandler):
	def get(self, error_code=200):
		"""
			For testing a client.

			This just returns a HTTP response with the given code.
		"""
		try:
			error_code = int(error_code)
		except ValueError:
			error_code = 200

		raise tornado.web.HTTPError(error_code)


class StatsJobsQueueHandler(BaseHandler):
	def get(self):
		job_queue_length = self.backend.jobs.get_queue_length()

		ret = {
			"length" : job_queue_length,
		}
		self.write(ret)


# Uploads

class UploadsCreateHandler(BaseHandler):
	"""
		Create a new upload object in the database and return a unique ID
		to the uploader.
	"""

	@tornado.web.authenticated
	def get(self):
		# XXX Check permissions

		filename = self.get_argument("filename")
		filesize = self.get_argument_int("filesize")
		filehash = self.get_argument("hash")

		upload = backend.uploads.Upload.create(self.backend, filename, filesize,
			filehash, user=self.user, builder=self.builder)

		self.finish(upload.uuid)


class UploadsSendChunkHandler(BaseHandler):
	@tornado.web.authenticated
	def post(self, upload_id):
		upload = self.backend.uploads.get_by_uuid(upload_id)
		if not upload:
			raise tornado.web.HTTPError(404, "Invalid upload id.")

		if not upload.builder == self.builder:
			raise tornado.web.HTTPError(403, "Uploading an other host's file.")

		chksum = self.get_argument("chksum")
		data = self.get_argument("data")

		# Decode data.
		data = base64.b64decode(data)

		# Calculate hash and compare.
		h = hashlib.new("sha512")
		h.update(data)

		if not chksum == h.hexdigest():
			raise tornado.web.HTTPError(400, "Checksum mismatch")

		# Append the data to file.
		upload.append(data)


class UploadsFinishedHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self, upload_id):
		upload = self.backend.uploads.get_by_uuid(upload_id)
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
			self.finish("OK")

			return

		# In case the download was corrupted or incomplete, we delete it
		# and tell the client to start over.
		upload.remove()

		self.finish("ERROR: CORRUPTED OR INCOMPLETE FILE")


class UploadsDestroyHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self, upload_id):
		upload = self.backend.uploads.get_by_uuid(upload_id)
		if not upload:
			raise tornado.web.HTTPError(404, "Invalid upload id.")

		if not upload.builder == self.builder:
			raise tornado.web.HTTPError(403, "Removing an other host's file.")

		# Remove the upload from the database and trash the data.
		upload.remove()


# Builds

class BuildsCreateHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self):
		# Get the upload ID of the package file.
		upload_id = self.get_argument("upload_id")

		# Get the identifier of the distribution we build for.
		distro_ident = self.get_argument("distro")

		# Get a list of arches to build for.
		arches = self.get_argument("arches", None)
		if arches == "":
			arches = None

		# Process build type.
		build_type = self.get_argument("build_type")
		if build_type == "release":
			check_for_duplicates = True
		elif build_type == "scratch":
			check_for_duplicates = False
		else:
			raise tornado.web.HTTPError(400, "Invalid build type")

		## Check if the user has permission to create a build.
		# Users only have the permission to create scratch builds.
		if self.user and not build_type == "scratch":
			raise tornado.web.HTTPError(403, "Users are only allowed to upload scratch builds")

		# Get previously uploaded file to create this build from.
		upload = self.backend.uploads.get_by_uuid(upload_id)
		if not upload:
			raise tornado.web.HTTPError(400, "Upload does not exist: %s" % upload_id)

		# Check if the uploaded file belongs to this user/builder.
		if self.user and not upload.user == self.user:
			raise tornado.web.HTTPError(400, "Upload does not belong to this user.")

		elif self.builder and not upload.builder == self.builder:
			raise tornado.web.HTTPError(400, "Upload does not belong to this builder.")

		# Get distribution this package should be built for.
		distro = self.backend.distros.get_by_ident(distro_ident)
		if not distro:
			distro = self.backend.distros.get_default()

		# Open the package that was uploaded earlier and add it to
		# the database. Create a new build object from the uploaded package.
		args = {
			"arches"               : arches,
			"check_for_duplicates" : check_for_duplicates,
			"distro"               : distro,
			"type"                 : build_type,
		}
		if self.user:
			args["owner"] = self.user

		try:
			pkg, build = backend.builds.import_from_package(self.backend, upload.path, **args)

		except:
			# Raise any exception.
			raise

		else:
			# Creating the build will move the file to the build directory,
			# so we can safely remove the uploaded file.
			upload.remove()

		# Send the build ID back to the user.
		self.finish(build.uuid)


class BuildsGetHandler(BaseHandler):
	def get(self, build_uuid):
		build = self.backend.builds.get_by_uuid(build_uuid)
		if not build:
			raise tornado.web.HTTPError(404, "Could not find build: %s" % build_uuid)

		ret = {
			"distro"       : build.distro.identifier,
			"jobs"         : [j.uuid for j in build.jobs],
			"name"         : build.name,
			"package"      : build.pkg.uuid,
			"priority"     : build.priority,
			"score"        : build.credits,
			"severity"     : build.severity,
			"state"        : build.state,
			"sup_arches"   : build.supported_arches,
			"time_created" : build.created.isoformat(),
			"type"         : build.type,
			"uuid"         : build.uuid,
		}

		# If the build is in a repository, update that bit.
		if build.repo:
			ret["repo"] = build.repo.identifier

		self.finish(ret)


# Jobs

class JobsGetHandler(BaseHandler):
	def get(self, job_uuid):
		job = self.backend.jobs.get_by_uuid(job_uuid)
		if not job:
			raise tornado.web.HTTPError(404, "Could not find job: %s" % job_uuid)

		# Check if user is allowed to view this job.
		if job.build.public == False:
			if not self.user:
				raise tornado.web.HTTPError(401)

			# Check if an authenticated user has permission to see this build.
			if not job.build.has_perm(self.user):
				raise tornado.web.HTTPError(403)

		ret = {
			"arch"         : job.arch.name,
			"build"        : job.build.uuid,
			"builder"      : job.builder.hostname,
			"duration"     : job.duration,
			"name"         : job.name,
			"packages"     : [p.uuid for p in job.packages],
			"state"        : job.state,
			"time_created" : job.time_created.isoformat(),
			"type"         : job.type,
			"uuid"         : job.uuid,
		}

		if job.time_started:
			ret["time_started"] = job.time_started.isoformat()

		if job.time_finished:
			ret["time_finished"] = job.time_finished.isoformat()

		self.finish(ret)


# Packages

class PackagesGetHandler(BaseHandler):
	def get(self, package_uuid):
		pkg = self.backend.packages.get_by_uuid(package_uuid)
		if not pkg:
			raise tornado.web.HTTPError(404, "Could not find package: %s" % package_uuid)

		ret = {
			"arch"             : pkg.arch.name,
			"build_id"         : pkg.build_id,
			"build_host"       : pkg.build_host,
			"build_time"       : pkg.build_time.isoformat(),
			"description"      : pkg.description,
			"epoch"            : pkg.epoch,
			"filesize"         : pkg.filesize,
			"friendly_name"    : pkg.friendly_name,
			"friendly_version" : pkg.friendly_version,
			"groups"           : pkg.groups,
			"hash_sha512"      : pkg.hash_sha512,
			"license"          : pkg.license,
			"name"             : pkg.name,
			"release"          : pkg.release,
			"size"             : pkg.size,
			"summary"          : pkg.summary,
			"type"             : pkg.type,
			"url"              : pkg.url,
			"uuid"             : pkg.uuid,
			"version"          : pkg.version,

			# Dependencies.
			"prerequires"      : pkg.prerequires,
			"requires"         : pkg.requires,
			"provides"         : pkg.provides,
			"obsoletes"        : pkg.obsoletes,
			"conflicts"        : pkg.conflicts,
		}

		if pkg.type == "source":
			ret["supported_arches"] = pkg.supported_arches

		if isinstance(pkg.maintainer, backend.users.User):
			ret["maintainer"] = "%s <%s>" % (pkg.maintainer.realname, pkg.maintainer.email)
		elif pkg.maintainer:
			ret["maintainer"] = pkg.maintainer

		if pkg.distro:
			ret["distro"] = pkg.distro.identifier

		self.finish(ret)


# Builders

class BuildersBaseHandler(BaseHandler):
	def prepare(self):
		# The request must come from an authenticated buider.
		if not self.builder:
			raise tornado.web.HTTPError(403)


class BuildersInfoHandler(BuildersBaseHandler):
	@tornado.web.authenticated
	def post(self):
		args = {
			# CPU info
			"cpu_model"    : self.get_argument("cpu_model", None),
			"cpu_count"    : self.get_argument("cpu_count", None),
			"cpu_arch"     : self.get_argument("cpu_arch", None),
			"cpu_bogomips" : self.get_argument("cpu_bogomips", None),

			# Pakfire
			"pakfire_version" : self.get_argument("pakfire_version", None),
			"host_key"     : self.get_argument("host_key", None),

			# OS
			"os_name"      : self.get_argument("os_name", None),
		}
		self.builder.update_info(**args)


class BuildersKeepaliveHandler(BuildersBaseHandler):
	@tornado.web.authenticated
	def post(self):
		args = {
			# Load average
			"loadavg1"   : self.get_argument_float("loadavg1", None),
			"loadavg5"   : self.get_argument_float("loadavg5", None),
			"loadavg15"  : self.get_argument_float("loadavg15", None),

			# Memory
			"mem_total"  : self.get_argument_int("mem_total", None),
			"mem_free"   : self.get_argument_int("mem_free", None),

			# swap
			"swap_total" : self.get_argument_int("swap_total", None),
			"swap_free"  : self.get_argument_int("swap_free", None),

			# Disk space
			"space_free" : self.get_argument_int("space_free", None),
		}
		self.builder.update_keepalive(**args)

		self.finish("OK")


class BuildersJobsQueueHandler(BuildersBaseHandler):
	@tornado.web.asynchronous
	@tornado.web.authenticated
	def get(self):
		self.callback()

	def callback(self):
		# Break if the connection has been closed in the mean time.
		if self.connection_closed():
			logging.warning("Connection closed")
			return

		# Check if there is a job for us.
		job = self.builder.get_next_job()

		# Got no job, wait and try again.
		if not job:
			# Check if we have been running for too long.
			if self.runtime >= self.max_runtime:
				logging.debug("Exceeded max. runtime. Finishing request.")
				return self.finish()

			# Try again in a jiffy.
			self.add_timeout(self.heartbeat, self.callback)
			return

		try:
			# Set job to dispatching state.
			job.state = "dispatching"

			# Set our build host.
			job.builder = self.builder

			ret = {
				"id"                 : job.uuid,
				"arch"               : job.arch.name,
				"source_url"         : job.build.source_download,
				"source_hash_sha512" : job.build.source_hash_sha512,
				"type"               : job.type,
				"config"             : job.get_config(),
			}

			# Send build information to the builder.
			self.finish(ret)
		except:
			# If anything went wrong, we reset the state.
			job.state = "pending"
			raise

	@property
	def heartbeat(self):
		return 15 # 15 seconds

	@property
	def max_runtime(self):
		timeout = self.get_argument_int("timeout", None)
		if timeout:
			return timeout - self.heartbeat

		return 300 # 5 min


class BuildersJobsStateHandler(BuildersBaseHandler):
	@tornado.web.authenticated
	def post(self, job_uuid, state):
		job = self.backend.jobs.get_by_uuid(job_uuid)
		if not job:
			raise tornado.web.HTTPError(404, "Invalid job id.")

		if not job.builder == self.builder:
			raise tornado.web.HTTPError(403, "Altering another builder's build.")

		# Save information to database.
		job.state = state

		message = self.get_argument("message", None)
		job.update_message(message)

		self.finish("OK")


class BuildersJobsBuildrootHandler(BuildersBaseHandler):
	@tornado.web.authenticated
	def post(self, job_uuid):
		job = self.backend.jobs.get_by_uuid(job_uuid)
		if not job:
			raise tornado.web.HTTPError(404, "Invalid job id.")

		if not job.builder == self.builder:
			raise tornado.web.HTTPError(403, "Altering another builder's build.")

		# Get buildroot.
		buildroot = self.get_argument_json("buildroot", None)
		if buildroot:
			job.save_buildroot(buildroot)

		self.finish("OK")


class BuildersJobsAddFileHandler(BuildersBaseHandler):
	@tornado.web.authenticated
	def post(self, job_uuid, upload_id):
		type = self.get_argument("type")
		assert type in ("package", "log")

		# Fetch job we are working on and check if it is actually ours.
		job = self.backend.jobs.get_by_uuid(job_uuid)
		if not job:
			raise tornado.web.HTTPError(404, "Invalid job id.")

		if not job.builder == self.builder:
			raise tornado.web.HTTPError(403, "Altering another builder's job.")

		# Fetch uploaded file object and check we uploaded it ourself.
		upload = self.backend.uploads.get_by_uuid(upload_id)
		if not upload:
			raise tornado.web.HTTPError(404, "Invalid upload id.")

		if not upload.builder == self.builder:
			raise tornado.web.HTTPError(403, "Using an other host's file.")

		# Remove all files that have to be deleted, first.
		self.backend.cleanup_files()

		try:
			job.add_file(upload.path)

		finally:
			# Finally, remove the uploaded file.
			upload.remove()

		self.finish("OK")
