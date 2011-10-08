#!/usr/bin/python

import os
import shutil
import time
import urlparse
import uuid

import base
import build

from constants import *

class Packages(base.Object):
	def get_by_id(self, id):
		return Package(self.pakfire, id)

	def get_all_names(self):
		names = self.db.query("SELECT DISTINCT name FROM packages ORDER BY name")

		return [n.name for n in names]

	def get_by_name(self, name):
		pkgs = self.db.query("SELECT id FROM packages WHERE name = %s ORDER BY id ASC", name)

		return [Package(self.pakfire, pkg.id) for pkg in pkgs]

	find_by_name = get_by_name

	def search(self, query):
		# Search for an exact match
		pkgs = self.db.query("SELECT DISTINCT name, summary FROM packages"
			" WHERE name = %s LIMIT 1", query)

		if not pkgs:
			query = "%%%s%%" % query
			pkgs = self.db.query("SELECT DISTINCT name, summary FROM packages"
			" WHERE name LIKE %s OR summary LIKE %s OR description LIKE %s"
			" ORDER BY name", query, query, query)

		return pkgs

	def get_by_tuple(self, name, epoch, version, release):
		pkg = self.db.get("""SELECT id FROM packages WHERE name = %s AND
			epoch = %s AND version = %s AND `release` = %s LIMIT 1""",
			name, epoch, version, release)

		if pkg:
			return Package(self.pakfire, pkg.id)

	def get_with_file_by_uuid(self, uuid):
		file = self.db.get("SELECT id, type, pkg_id FROM package_files WHERE uuid = %s LIMIT 1", uuid)

		if not file:
			return None, None

		pkg = Package(self.pakfire, file.pkg_id)

		if file.type == SourcePackageFile.type:
			file = SourcePackageFile(self.pakfire, file.id)

		elif file.type == BinaryPackageFile.type:
			file = BinaryPackageFile(self.pakfire, file.id)

		return pkg, file

	def get_comments(self, limit=50):
		comments = self.db.query("""SELECT * FROM package_comments
			ORDER BY time DESC LIMIT %s""", limit)

		return comments


class Package(base.Object):
	"""
		This class represents a package (like source package) that is passed to
		the buildsystem.

		New objects of this are created by the new() method.
	"""

	def __init__(self, pakfire, id):
		base.Object.__init__(self, pakfire)
		self.id = id

		self._data = self.db.get("SELECT * FROM packages WHERE id = %s", self.id)

	def __cmp__(self, other):
		# Order alphabetically.
		return cmp(self.friendly_name, other.friendly_name)

	@classmethod
	def new(cls, pakfire, file, build):
		# Check if the package does already exist in the database.
		pkg = pakfire.packages.get_by_tuple(file.name, file.epoch, file.version,
			file.release)

		if pkg:
			return pkg

		id = pakfire.db.execute("INSERT INTO packages(name, epoch, version,"
		 	" `release`, groups, maintainer, license, url, summary, description,"
		 	" supported_arches, source_build) VALUES(%s, %s, %s, %s, %s, %s, %s, %s,"
		 	" %s, %s, %s, %s)", file.name, file.epoch, file.version, file.release,
		 	" ".join(file.groups), file.maintainer, file.license, file.url,
		 	file.summary, file.description, file.supported_arches, build.id)

		pkg = cls(pakfire, id)
		pkg.add_file(file, build)

		# Create all needed build jobs.
		pkg.create_builds()

		return pkg

	@property
	def name(self):
		return self._data.get("name")

	@property
	def epoch(self):
		return self._data.get("epoch")

	@property
	def version(self):
		return self._data.get("version")

	@property
	def release(self):
		return self._data.get("release")

	@property
	def friendly_name(self):
		return "%s-%s" % (self.name, self.friendly_version)

	@property
	def friendly_version(self):
		s = "%s-%s" % (self.version, self.release)

		if self.epoch:
			s = "%d:%s" % (self.epoch, s)

		return s

	@property
	def distro(self):
		return self.source.distro

	def get_state(self):
		return self._data.get("state")

	def set_state(self, state):
		self.db.execute("UPDATE packages SET state = %s WHERE id = %s", state, self.id)
		self._data["state"] = state

		if state == "finished":
			# Add package to all comprehensive repositories.
			for repo in self.distro.comprehensive_repositories:
				self.add_to_repository(repo)

	state = property(get_state, set_state)

	@property
	def summary(self):
		return self._data.get("summary")

	@property
	def description(self):
		return self._data.get("description")

	@property
	def groups(self):
		return self._data.get("groups")

	@property
	def url(self):
		return self._data.get("url")

	@property
	def maintainer(self):
		return self._data.get("maintainer")

	@property
	def license(self):
		return self._data.get("license")

	@property
	def source(self):
		return self.source_build.source

	def get_files(self, type=None):
		files = []

		query = "SELECT id, type FROM package_files WHERE pkg_id = %s"
		if type:
			query += " AND type = '%s'" % type

		for p in self.db.query(query, self.id):
			for p_class in (SourcePackageFile, BinaryPackageFile, LogFile):
				if p.type == p_class.type:
					p = p_class(self.pakfire, p.id)
					break
			else:
				continue

			files.append(p)

		return files

	@property
	def packagefiles(self):
		return [f for f in self.get_files() if isinstance(f, PackageFile)]

	@property
	def logfiles(self):
		return [f for f in self.get_files() if isinstance(f, LogFile)]

	@property
	def sourcefile(self):
		sourcefiles = [f for f in self.get_files() if isinstance(f, SourcePackageFile)]

		assert len(sourcefiles) <= 1

		if sourcefiles:
			return sourcefiles[0]

	@property
	def log(self):
		return self.db.query("SELECT * FROM log WHERE pkg_id = %s AND"
			" build_id IS NULL ORDER BY time DESC", self.id)

	def add_file(self, pkg, build):
		path = os.path.join(
			self.name,
			"%s-%s-%s" % (self.epoch, self.version, self.release),
			build.arch,
			os.path.basename(pkg.filename))
		abspath = os.path.join(self.source.targetpath, path)

		if os.path.exists(abspath):
			# Check if file is already in the database and return the id.
			file = self.db.get("SELECT id FROM package_files WHERE path = %s LIMIT 1", path)
			if file:
				return file.id

			os.unlink(abspath)

		# Save the data to a file.
		dirname = os.path.dirname(abspath)
		if not os.path.exists(dirname):
			os.makedirs(dirname)

		# Copy file to target directory.
		shutil.copy(pkg.filename, abspath)

		id = self.db.execute("INSERT INTO package_files(path, pkg_id, source_id,"
			" type, arch, summary, description, requires, provides, obsoletes,"
			" conflicts, url, license, maintainer, size, hash1, build_host,"
			" build_id, build_time, uuid) VALUES(%s, %s, %s, %s, %s, %s, %s, %s,"
			" %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
			path, self.id, build.source.id, pkg.type, pkg.arch, pkg.summary,
			pkg.description, " ".join(pkg.requires), " ".join(pkg.provides),
			" ".join(pkg.obsoletes), " ".join(pkg.conflicts), pkg.url, pkg.license,
			pkg.maintainer, pkg.size, pkg.hash1, pkg.build_host, pkg.build_id,
			pkg.build_time, pkg.uuid)

		# Add package filelist
		self.db.executemany("INSERT INTO filelists(pkgfile_id, name, size, hash1)"
			" VALUES(%s, %s, %s, %s)", [(id, f, 0, "0"*40) for f in pkg.filelist])

		return id

	def add_log(self, filename, build):
		path = os.path.join(
			self.name,
			"%s-%s-%s" % (self.epoch, self.version, self.release),
			"logs/build.%s.%s.log" % (build.arch, build.retries))
		abspath = os.path.join(self.source.targetpath, path)

		# Save the data to a file.
		dirname = os.path.dirname(abspath)
		if not os.path.exists(dirname):
			os.makedirs(dirname)

		# Move file to target directory.
		shutil.copy(filename, abspath)

		self.db.execute("INSERT INTO package_files(path, source_id, pkg_id,"
			" type, arch, build_id) VALUES(%s, %s, %s, %s, %s, %s)", path,
			self.source.id, self.id, "log", build.arch, build.uuid)

	@property
	def supported_arches(self):
		supported = self._data.get("supported_arches") or ""
		supported = supported.split()

		arches = []

		if "all" in supported:
			# Inherit all supported architectures from the distribution.
			arches += self.distro.arches
			supported.remove("all")

		excludes = [a[1:] for a in supported if a.startswith("-")]

		if excludes:
			_arches = []

			for arch in arches:
				if arch in excludes:
					continue

				_arches.append(arch)

			arches = _arches

		includes = [a[1:] for a in supported if not a.startswith("-")]

		# Add explicitely included architectures.
		arches += includes

		return arches

	def create_builds(self):
		builds = []

		for arch in self.supported_arches:
			b = build.BinaryBuild.new(self.pakfire, self, arch)

			builds.append(b)

		return builds

	@property
	def builds(self):
		if not hasattr(self, "_builds"):
			self._builds = self.pakfire.builds.get_by_pkgid(self.id)

			if self.source_build:
				self._builds.append(self.source_build)

		return self._builds

	@property
	def source_build(self):
		return self.pakfire.builds.get_by_id(self._data.source_build)

	def update(self):
		if not self.state == "finished":
			# Check if all builds are finished and set package state to finished, too.
			for build in self.builds:
				if not build.finished:
					return

			self.state = "finished"

	@property
	def repositories(self):
		repos = self.db.query("SELECT repo_id FROM repository_packages WHERE pkg_id = %s", self.id)

		return [self.pakfire.repos.get_by_id(r.id) for r in repos]

	def add_to_repository(self, repo):
		#repo.add_package(self)
		repo.register_action("add", self.id)

	@property
	def comments(self):
		comments = self.db.query("""SELECT * FROM package_comments
			WHERE pkg_id = %s ORDER BY time DESC""", self.id)

		return comments

	def comment(self, user_id, text, vote):
		id = self.db.execute("""INSERT INTO package_comments(pkg_id, user_id,
			text, vote) VALUES(%s, %s, %s, %s)""", self.id, user_id, text, vote)

		vote2credit = { "up" : 1, "down" : -1, "none" : 0, }
		try:
			self.credits = self.credits + vote2credit[vote]

		except KeyError:
			pass

		return id

	def get_credits(self):
		return self._data.credits

	def set_credits(self, credits):
		self.db.execute("UPDATE packages SET credits = %s WHERE id = %s",
			credits, self.id)
		self._data["credits"] = credits

	credits = property(get_credits, set_credits)

	def get_actions(self):
		return self.pakfire.repos.get_actions_by_pkgid(self.id)


class File(base.Object):
	type = None

	def __init__(self, pakfire, id):
		base.Object.__init__(self, pakfire)
		self.id = id

		self._data = \
			self.db.get("SELECT * FROM package_files WHERE id = %s", self.id)


	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.name)

	def __cmp__(self, other):
		return cmp(self.name, other.name)

	@property
	def name(self):
		return os.path.basename(self.path)

	@property
	def path(self):
		path = self._data.get("path")

		if path.startswith("/"):
			path = path[1:]

		return path

	@property
	def abspath(self):
		return os.path.join(self.source.targetpath, self.path)

	@property
	def download(self):
		path = self.abspath.split("/")

		while path:
			if path[0] == "packages":
				break
			path = path[1:]

		return "%s/%s" % (self.pakfire.settings.get("baseurl"), "/".join(path))

	@property
	def source(self):
		return self.pakfire.sources.get_by_id(self._data.source_id)


class PackageFile(File):
	@property
	def filelist(self):
		return self.db.query("SELECT name, size, hash1 FROM filelists"
			" WHERE pkgfile_id = %s", self.id)

	@property
	def hash1(self):
		return self._data.get("hash1")

	@property
	def uuid(self):
		return self._data.get("uuid")

	@property
	def summary(self):
		return self._data.get("summary")

	@property
	def description(self):
		return self._data.get("description")

	@property
	def license(self):
		return self._data.get("license")

	@property
	def size(self):
		return self._data.get("size")

	@property
	def url(self):
		return self._data.get("url")

	@property
	def maintainer(self):
		return self._data.get("maintainer")

	@property
	def build_id(self):
		return self._data.get("build_id")

	@property
	def build_host(self):
		return self._data.get("build_host")

	@property
	def build_time(self):
		return self._data.get("build_time")

	@property
	def build_date(self):
		return time.strftime("%a, %d %b %Y %H:%M:%S +0000",
			time.gmtime(self.build_time))

	@property
	def provides(self):
		return self._data.get("provides").split()

	@property
	def requires(self):
		requires = self._data.get("requires").split()

		return sorted(requires)

	@property
	def obsoletes(self):
		obsoletes = self._data.get("obsoletes").split()

		return sorted(obsoletes)

	@property
	def conflicts(self):
		conflicts = self._data.get("conflicts").split()

		return sorted(conflicts)


class BinaryPackageFile(PackageFile):
	type = "binary"


class SourcePackageFile(PackageFile):
	type = "source"


class LogFile(File):
	type = "log"

