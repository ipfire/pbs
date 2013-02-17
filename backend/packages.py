#!/usr/bin/python

import datetime
import logging
import os
import shutil

import pakfire
import pakfire.packages as packages

import arches
import base
import builds
import database
import misc
import sources

from constants import *

class Packages(base.Object):
	def get_all_names(self, public=None, user=None, states=None):
		query = "SELECT DISTINCT name, summary FROM packages \
			JOIN builds ON builds.pkg_id = packages.id \
			WHERE packages.type = 'source'"

		conditions = []
		args = []

		if public in (True, False):
			if public is True:
				public = "Y"
			elif public is False:
				public = "N"

			conditions.append("builds.public = %s")
			args.append(public)

		if user and not user.is_admin():
			conditions.append("builds.owner_id = %s")
			args.append(user.id)

		if states:
			for state in states:
				conditions.append("builds.state = %s")
				args.append(state)

		if conditions:
			query += " AND (%s)" % " OR ".join(conditions)
		
		query += " ORDER BY packages.name"

		return [(n.name, n.summary) for n in self.db.query(query, *args)]

	def get_by_uuid(self, uuid):
		pkg = self.db.get("SELECT * FROM packages WHERE uuid = %s LIMIT 1", uuid)
		if not pkg:
			return

		return Package(self.pakfire, pkg.id, pkg)

	def search(self, pattern, limit=None):
		"""
			Searches for packages that do match the query.

			This function does not work for UUIDs or filenames.
		"""
		query = "SELECT * FROM packages \
			WHERE type = %s AND ( \
				name LIKE %s OR \
				summary LIKE %s OR \
				description LIKE %s \
			) \
			GROUP BY name"

		pattern = "%%%s%%" % pattern
		args = ("source", pattern, pattern, pattern)

		res = self.db.query(query, *args)

		pkgs = []
		for row in res:
			pkg = Package(self.pakfire, row.id, row)
			pkgs.append(pkg)

			if limit and len(pkgs) >= limit:
				break

		return pkgs

	def search_by_filename(self, filename, limit=None):
		query = "SELECT filelists.* FROM filelists \
			JOIN packages ON filelists.pkg_id = packages.id \
			WHERE filelists.name = %s ORDER BY packages.build_time DESC"
		args = [filename,]

		if limit:
			query += " LIMIT %s"
			args.append(limit)

		files = []
		for result in self.db.query(query, *args):
			pkg = Package(self.pakfire, result.pkg_id)
			files.append((pkg, result))

		return files

	def autocomplete(self, query, limit=8):
		res = self.db.query("SELECT DISTINCT name FROM packages \
			WHERE packages.name LIKE %s AND packages.type = %s \
			ORDER BY packages.name LIMIT %s", "%%%s%%" % query, "source", limit)

		return [row.name for row in res]

	def get_avg_build_times(self, name):
		query = "SELECT jobs.arch_id AS arch_id, \
				AVG(UNIX_TIMESTAMP(jobs.time_finished) - UNIX_TIMESTAMP(jobs.time_started)) AS build_time \
			FROM jobs \
				JOIN builds ON jobs.build_id = builds.id \
				JOIN packages ON builds.pkg_id = packages.id \
			WHERE packages.name = %s \
				AND jobs.state = 'finished' \
				AND jobs.type = 'build' \
				AND NOT jobs.time_started IS NULL \
				AND NOT jobs.time_finished IS NULL \
			GROUP BY jobs.arch_id"

		ret = []
		for row in self.db.query(query, name):
			arch = arches.Arch(self.pakfire, row.arch_id)
			ret.append((arch, row.build_time))

		# Sorts the list by the priority of the arches.
		ret.sort()

		return ret


class Package(base.Object):
	def __init__(self, pakfire, id, data=None):
		base.Object.__init__(self, pakfire)

		# The ID of the package.
		self.id = id

		# Cache.
		self._data = data
		self._deps = None
		self._arch = None
		self._filelist = None
		self._job = None
		self._commit = None
		self._properties = None
		self._maintainer = None

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.friendly_name)

	def __cmp__(self, other):
		return pakfire.util.version_compare(self.pakfire,
			self.friendly_name, other.friendly_name)

	@classmethod
	def open(cls, _pakfire, path):
		# Just check if the file really does exist.
		assert os.path.exists(path)

		p = pakfire.PakfireServer()
		file = packages.open(p, None, path)

		# Get architecture from the database.
		arch = _pakfire.arches.get_by_name(file.arch)
		assert arch, "Unknown architecture: %s" % file.arch

		hash_sha512 = misc.calc_hash(path, "sha512")
		assert hash_sha512

		query = [
			("name",        file.name),
			("epoch",       file.epoch),
			("version",     file.version),
			("release",     file.release),
			("type",        file.type),
			("arch",        arch.id),

			("groups",      " ".join(file.groups)),
			("maintainer",  file.maintainer),
			("license",     file.license),
			("url",         file.url),
			("summary",     file.summary),
			("description", file.description),
			("size",        file.inst_size),
			("uuid",        file.uuid),

			# Build information.
			("build_id",    file.build_id),
			("build_host",  file.build_host),
			("build_time",  datetime.datetime.utcfromtimestamp(file.build_time)),

			# File "metadata".
			("path",        path),
			("filesize",    os.path.getsize(path)),
			("hash_sha512", hash_sha512),
		]

		if file.type == "source":
			query.append(("supported_arches", file.supported_arches))

		keys = []
		vals = []
		for key, val in query:
			keys.append("`%s`" % key)
			vals.append(val)

		_query = "INSERT INTO packages(%s)" % ", ".join(keys)
		_query += " VALUES(%s)" % ", ".join("%s" for v in vals)

		# Create package entry in the database.
		id = _pakfire.db.execute(_query, *vals)

		# Dependency information.
		deps = []
		for d in file.prerequires:
			deps.append((id, "prerequires", d))

		for d in file.requires:
			deps.append((id, "requires", d))

		for d in file.provides:
			deps.append((id, "provides", d))

		for d in file.conflicts:
			deps.append((id, "conflicts", d))

		for d in file.obsoletes:
			deps.append((id, "obsoletes", d))

		if deps:
			_pakfire.db.executemany("INSERT INTO packages_deps(pkg_id, type, what) \
				VALUES(%s, %s, %s)", deps)

		# Add all files to filelists table.
		filelist = []
		for f in file.filelist:
			if f.config:
				config = "Y"
			else:
				config = "N"

			# Convert mtime to integer.
			try:
				mtime = int(f.mtime)
			except ValueError:
				mtime = 0

			filelist.append((id, f.name, f.size, f.hash1, f.type, config, f.mode,
				f.user, f.group, datetime.datetime.utcfromtimestamp(mtime),
				f.capabilities))

		_pakfire.db.executemany("INSERT INTO filelists(pkg_id, name, size, hash_sha512, \
			type, config, mode, user, `group`, mtime, capabilities) \
			VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", filelist)

		# Return the newly created object.
		return cls(_pakfire, id)

	def delete(self):
		self.db.execute("INSERT INTO queue_delete(path) VALUES(%s)", self.path)

		# Delete all files from the filelist.
		self.db.execute("DELETE FROM filelists WHERE pkg_id = %s", self.id)

		# Delete the package.
		self.db.execute("DELETE FROM packages WHERE id = %s", self.id)

		# Remove cached data.
		self._data = {}

	@property
	def data(self):
		if self._data is None:
			self._data = \
				self.db.get("SELECT * FROM packages WHERE id = %s", self.id)
			assert self._data, "Cannot fetch package %s: %s" % (self.id, self._data)

		return self._data

	@property
	def uuid(self):
		return self.data.uuid

	@property
	def name(self):
		return self.data.name

	@property
	def epoch(self):
		return self.data.epoch

	@property
	def version(self):
		return self.data.version

	@property
	def release(self):
		return self.data.release

	@property
	def arch(self):
		if self._arch is None:
			self._arch = self.pakfire.arches.get_by_id(self.data.arch)
			assert self._arch

		return self._arch

	@property
	def type(self):
		return self.data.type

	@property
	def friendly_name(self):
		return "%s-%s.%s" % (self.name, self.friendly_version, self.arch.name)

	@property
	def friendly_version(self):
		s = "%s-%s" % (self.version, self.release)

		if self.epoch:
			s = "%d:%s" % (self.epoch, s)

		return s

	@property
	def groups(self):
		return self.data.groups.split()

	@property
	def maintainer(self):
		if self._maintainer is None:
			self._maintainer = self.data.maintainer

			# Search if there is a user account for this person.
			user = self.pakfire.users.find_maintainer(self._maintainer)
			if user:
				self._maintainer = user

		return self._maintainer

	@property
	def license(self):
		return self.data.license

	@property
	def url(self):
		return self.data.url

	@property
	def summary(self):
		return self.data.summary

	@property
	def description(self):
		return self.data.description

	@property
	def supported_arches(self):
		return self.data.supported_arches

	@property
	def size(self):
		return self.data.size

	def has_deps(self):
		"""
			Returns True if the package has got dependencies.

			Always filter out the uuid provides.
		"""
		return len(self.deps) > 1

	@property
	def deps(self):
		if self._deps is None:
			query = self.db.query("SELECT type, what FROM packages_deps WHERE pkg_id = %s", self.id)

			self._deps = []
			for row in query:
				self._deps.append((row.type, row.what))

		return self._deps

	@property
	def prerequires(self):
		return [d[1] for d in self.deps if d[0] == "prerequires"]

	@property
	def requires(self):
		return [d[1] for d in self.deps if d[0] == "requires"]

	@property
	def provides(self):
		return [d[1] for d in self.deps if d[0] == "provides" and not d[1].startswith("uuid(")]

	@property
	def conflicts(self):
		return [d[1] for d in self.deps if d[0] == "conflicts"]

	@property
	def obsoletes(self):
		return [d[1] for d in self.deps if d[0] == "obsoletes"]

	@property
	def suggests(self):
		return [d[1] for d in self.deps if d[0] == "suggests"]

	@property
	def recommends(self):
		return [d[1] for d in self.deps if d[0] == "recommends"]

	@property
	def commit_id(self):
		return self.data.commit_id

	def get_commit(self):
		if not self.commit_id:
			return

		if self._commit is None:
			self._commit = sources.Commit(self.pakfire, self.commit_id)

		return self._commit

	def set_commit(self, commit):
		self.db.execute("UPDATE packages SET commit_id = %s WHERE id = %s",
			commit.id, self.id)
		self._commit = commit

	commit = property(get_commit, set_commit)

	@property
	def distro(self):
		if not self.commit:
			return

		# XXX THIS CANNOT RETURN None

		return self.commit.distro

	@property
	def build_id(self):
		return self.data.build_id

	@property
	def build_host(self):
		return self.data.build_host

	@property
	def build_time(self):
		return self.data.build_time

	@property
	def path(self):
		return self.data.path

	@property
	def hash_sha512(self):
		return self.data.hash_sha512

	@property
	def filesize(self):
		return self.data.filesize

	def move(self, target_dir):
		# Create directory if it does not exist, yet.
		if not os.path.exists(target_dir):
			os.makedirs(target_dir)

		# Make full path where to put the file.
		target = os.path.join(target_dir, os.path.basename(self.path))

		# Copy the file to the target directory (keeping metadata).
		shutil.move(self.path, target)

		# Update file path in the database.
		self.db.execute("UPDATE packages SET path = %s WHERE id = %s",
			os.path.relpath(target, PACKAGES_DIR), self.id)
		self._data["path"] = target

	@property
	def build(self):
		if self.job:
			return self.job.build

		build = self.db.get("SELECT id FROM builds \
			WHERE type = 'release' AND pkg_id = %s", self.id)

		if build:
			return builds.Build(self.pakfire, build.id)

	@property
	def job(self):
		if self._job is None:
			job = self.db.get("SELECT job_id AS id FROM jobs_packages \
				WHERE pkg_id = %s", self.id)

			if job:
				self._job = builds.Job(self.pakfire, job.id)

		return self._job

	@property
	def filelist(self):
		if self._filelist is None:
			self._filelist = []

			for f in self.db.query("SELECT * FROM filelists WHERE pkg_id = %s ORDER BY name", self.id):
				f = File(self.pakfire, f)
				self._filelist.append(f)

		return self._filelist

	def get_file(self):
		path = os.path.join(PACKAGES_DIR, self.path)

		if os.path.exists(path):
			return pakfire.packages.open(None, None, path)

	## properties

	_default_properties = {
		"critical_path" : False,
		"priority"      : 0,
	}

	def update_property(self, key, value):
		assert self._default_properties.has_key(key), "Unknown key: %s" % key

		#print self.db.execute("UPDATE packages_properties SET 

	@property
	def properties(self):
		if self._properties is None:
			self._properties = \
				self.db.get("SELECT * FROM packages_properties WHERE name = %s", self.name)

			if not self._properties:
				self._properties = database.Row(self._default_properties)

		return self._properties

	@property
	def critical_path(self):
		return self.properties.get("critical_path", "N") == "Y"


class File(base.Object):
	def __init__(self, pakfire, data):
		base.Object.__init__(self, pakfire)

		self.data = data

	def __getattr__(self, attr):
		try:
			return self.data[attr]
		except KeyError:
			raise AttributeError, attr

	@property
	def downloadable(self):
		# All regular files are downloadable.
		return self.type == 0

	@property
	def viewable(self):
		# Empty files cannot be viewed.
		if self.size == 0:
			return False

		for ext in FILE_EXTENSIONS_VIEWABLE:
			if self.name.endswith(ext):
				return True

		return False
