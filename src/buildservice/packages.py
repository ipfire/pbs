#!/usr/bin/python

import datetime
import logging
import os
import shutil

import pakfire
import pakfire.packages as packages

from . import base
from . import database
from . import misc

log = logging.getLogger("packages")
log.propagate = 1

from .constants import *
from .decorators import *

class Packages(base.Object):
	def _get_package(self, query, *args):
		res = self.db.get(query, *args)

		if res:
			return Package(self.backend, res.id, data=res)

	def _get_packages(self, query, *args):
		res = self.db.query(query, *args)

		for row in res:
			yield Package(self.backend, row.id, data=row)

	def get_by_id(self, pkg_id):
		return self._get_package("SELECT * FROM packages \
			WHERE id = %s", pkg_id)

	def get_list(self):
		"""
			Returns a list with all package names and the summary line
			that have at one time been part of the distribution
		"""
		res = self.db.query("SELECT DISTINCT packages.name AS name, packages.summary AS summary FROM builds \
			LEFT JOIN packages ON builds.pkg_id = packages.id \
			WHERE builds.type = %s AND builds.state != %s", "release", "obsolete")

		return res

	def get_all_names(self, user=None, states=None):
		query = "SELECT DISTINCT packages.name AS name, summary FROM packages \
			JOIN builds ON builds.pkg_id = packages.id \
			WHERE packages.type = 'source'"

		conditions = []
		args = []

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

		return Package(self.backend, pkg.id, pkg)

	def create(self, path):
		# Just check if the file really exist
		assert os.path.exists(path)

		_pkg = packages.open(pakfire.PakfireServer(), None, path)

		hash_sha512 = misc.calc_hash(path, "sha512")
		assert hash_sha512

		query = [
			("name",        _pkg.name),
			("epoch",       _pkg.epoch),
			("version",     _pkg.version),
			("release",     _pkg.release),
			("type",        _pkg.type),
			("arch",        _pkg.arch),

			("groups",      " ".join(_pkg.groups)),
			("maintainer",  _pkg.maintainer),
			("license",     _pkg.license),
			("url",         _pkg.url),
			("summary",     _pkg.summary),
			("description", _pkg.description),
			("size",        _pkg.inst_size),
			("uuid",        _pkg.uuid),

			# Build information.
			("build_id",    _pkg.build_id),
			("build_host",  _pkg.build_host),
			("build_time",  datetime.datetime.utcfromtimestamp(_pkg.build_time)),

			# File "metadata".
			("path",        path),
			("filesize",    os.path.getsize(path)),
			("hash_sha512", hash_sha512),
		]

		if _pkg.type == "source":
			query.append(("supported_arches", _pkg.supported_arches))

		keys = []
		vals = []
		for key, val in query:
			keys.append(key)
			vals.append(val)

		_query = "INSERT INTO packages(%s)" % ", ".join(keys)
		_query += " VALUES(%s) RETURNING *" % ", ".join("%s" for v in vals)

		# Create package entry in the database.
		pkg = self._get_package(_query, *vals)

		# Dependency information.
		for d in _pkg.prerequires:
			pkg.add_dependency("prerequires", d)

		for d in _pkg.requires:
			pkg.add_dependency("requires", d)

		for d in _pkg.provides:
			pkg.add_dependency("provides", d)

		for d in _pkg.conflicts:
			pkg.add_dependency("conflicts", d)

		for d in _pkg.obsoletes:
			pkg.add_dependency("obsoletes", d)

		# Add all files to filelists table
		for f in _pkg.filelist:
			pkg.add_file(f.name, f.size, f.hash1, f.type, f.config, f.mode,
				f.user, f.group, f.mtime, f.capabilities)

		# Return the newly created object
		return pkg

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
			pkg = Package(self.backend, row.id, row)
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
			pkg = Package(self.backend, result.pkg_id)
			files.append((pkg, result))

		return files

	def autocomplete(self, query, limit=8):
		res = self.db.query("SELECT DISTINCT name FROM packages \
			WHERE packages.name LIKE %s AND packages.type = %s \
			ORDER BY packages.name LIMIT %s", "%%%s%%" % query, "source", limit)

		return [row.name for row in res]


class Package(base.DataObject):
	table = "packages"

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.friendly_name)

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.id == other.id

	def __lt__(self, other):
		if isinstance(other, self.__class__):
			return pakfire.util.version_compare(self.backend, self.friendly_name, other.friendly_name) < 0

	def delete(self):
		self.backend.delete_file(os.path.join(PACKAGES_DIR, self.path))

		# Delete all files from the filelist.
		self.db.execute("DELETE FROM filelists WHERE pkg_id = %s", self.id)

		# Delete the package.
		self.db.execute("DELETE FROM packages WHERE id = %s", self.id)

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
		return self.data.arch

	@property
	def type(self):
		return self.data.type

	@property
	def friendly_name(self):
		return "%s-%s.%s" % (self.name, self.friendly_version, self.arch)

	@property
	def friendly_version(self):
		s = "%s-%s" % (self.version, self.release)

		if self.epoch:
			s = "%s:%s" % (self.epoch, s)

		return s

	@property
	def groups(self):
		return self.data.groups.split()

	@lazy_property
	def maintainer(self):
		return self.backend.users.find_maintainer(self.data.maintainer) or self.data.maintainer

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

	def add_dependency(self, type, what):
		self.db.execute("INSERT INTO packages_deps(pkg_id, type, what) \
			VALUES(%s, %s, %s)", self.id, type, what)

		self.deps.append((type, what))

	def has_deps(self):
		"""
			Returns True if the package has got dependencies.

			Always filter out the uuid provides.
		"""
		return len(self.deps) > 1

	@lazy_property
	def deps(self):
		res = self.db.query("SELECT type, what FROM packages_deps \
			WHERE pkg_id = %s", self.id)

		ret = []
		for row in res:
			ret.append((row.type, row.what))

		return ret

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

	def get_commit(self):
		if self.data.commit_id:
			return self.backend.sources.get_commit_by_id(self.data.commit_id)

	def set_commit(self, commit):
		self._set_attribute("commit_id", commit.id)

	commit = lazy_property(get_commit, set_commit)

	@property
	def distro(self):
		# XXX THIS CANNOT RETURN None

		if self.commit:
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
	def filename(self):
		return os.path.basename(self.path)

	@property
	def hash_sha512(self):
		return self.data.hash_sha512

	@property
	def filesize(self):
		return self.data.filesize

	def copy(self, dst):
		if os.path.isdir(dst):
			dst = os.path.join(dst, self.filename)

		if os.path.exists(dst):
			raise IOError("Destination file exists: %s" % dst)

		src = os.path.join(PACKAGES_DIR, self.path)

		log.debug("Copying %s to %s" % (src, dst))

		shutil.copy2(src, dst)

	def move(self, target_dir):
		# Create directory if it does not exist, yet.
		if not os.path.exists(target_dir):
			os.makedirs(target_dir)

		# Make full path where to put the file.
		target = os.path.join(target_dir, os.path.basename(self.path))

		# Copy the file to the target directory (keeping metadata).
		shutil.move(self.path, target)

		# Update file path in the database.
		self._set_attribute("path", os.path.relpath(target, PACKAGES_DIR))

	@lazy_property
	def build(self):
		if self.job:
			return self.job.build

		return self.backend.builds._get_build("SELECT * FROM builds \
			WHERE pkg_id = %s" % self.id)

	@lazy_property
	def job(self):
		return self.backend.jobs._get_job("SELECT jobs.* FROM jobs \
			LEFT JOIN jobs_packages pkgs ON jobs.id = pkgs.job_id \
			WHERE pkgs.pkg_id = %s", self.id)

	@lazy_property
	def filelist(self):
		res = self.db.query("SELECT * FROM filelists \
			WHERE pkg_id = %s ORDER BY name", self.id)

		ret = []
		for row in res:
			f = File(self.backend, row)
			ret.append(f)

		return ret

	def get_file(self, filename):
		res = self.db.get("SELECT * FROM filelists \
			WHERE pkg_id = %s AND name = %s", self.id, filename)

		if res:
			return File(self.backend, res)

	def add_file(self, name, size, hash_sha512, type, config, mode, user, group, mtime, capabilities):
		# Convert mtime from seconds since epoch to datetime
		mtime = datetime.datetime.utcfromtimestamp(float(mtime))

		self.db.execute("INSERT INTO filelists(pkg_id, name, size, hash_sha512, type, config, mode, \
			\"user\", \"group\", mtime, capabilities) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
			self.id, name, size, hash_sha512, type, config, mode, user, group, mtime, capabilities)

	def open(self):
		path = os.path.join(PACKAGES_DIR, self.path)

		if os.path.exists(path):
			return pakfire.packages.open(None, None, path)

	## properties

	def update_property(self, key, value):
		if self.properties:
			self.db.execute("UPDATE packages_properties SET %s = %%s \
				WHERE name = %%s" % key, value, self.name)
		else:
			self.db.execute("INSERT INTO packages_properties(name, %s) \
				VALUES(%%s, %%s)" % key, self.name, value)

		# Update cache
		self.properties[key] = value

	@lazy_property
	def properties(self):
		res = self.db.get("SELECT * FROM packages_properties WHERE name = %s", self.name)

		ret = {}
		if res:
			for key in res:
				if key in ("id", "name"):
					continue

				ret[key] = res[key]

		return ret

	@property
	def critical_path(self):
		return self.properties.get("critical_path", False)


class File(base.Object):
	def init(self, data):
		self.data = data

	def __getattr__(self, attr):
		try:
			return self.data[attr]
		except KeyError:
			raise AttributeError(attr)

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
