#!/usr/bin/python

import logging

import arches
import base
import builds
import packages
import sources
import updates

from repository import Repository, RepositoryAux

class Distributions(base.Object):
	def get_all(self):
		distros = self.db.query("SELECT id FROM distributions ORDER BY name")

		return [Distribution(self.pakfire, d.id) for d in distros]

	def get_by_id(self, id):
		distro = self.db.get("SELECT id FROM distributions WHERE id = %s LIMIT 1", id)

		if distro:
			return Distribution(self.pakfire, distro.id)

	def get_by_name(self, name):
		distro = self.db.get("SELECT id FROM distributions WHERE sname = %s LIMIT 1", name)

		if distro:
			return Distribution(self.pakfire, distro.id)

	def get_by_ident(self, ident):
		return self.get_by_name(ident)

	def get_default(self):
		# XXX a bit ugly
		return self.get_by_ident("ipfire3")


class Distribution(base.Object):
	def __init__(self, pakfire, id):
		base.Object.__init__(self, pakfire)
		self.id = id

		self._data = None
		self._arches = None
		self._sources = None

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.name)

	@property
	def data(self):
		if self._data is None:
			self._data = self.db.get("SELECT * FROM distributions WHERE id = %s", self.id)

		return self._data

	def set(self, key, value):
		self.db.execute("UPDATE distributions SET %s = %%s WHERE id = %%s" % key,
			value, self.id)

		if self._data:
			self._data[key] = value

	@property
	def info(self):
		return {
			"name"        : self.name,
			"sname"       : self.sname,
			"slogan"      : self.slogan,
			"vendor"      : self.vendor,
			"contact"     : self.contact,
			"description" : self.description,
		}

	def get_config(self):
		try:
			name, release = self.name.split()
		except:
			name = self.name
			release = "N/A"

		lines = [
			"[distro]",
			"name = %s" % name,
			"release = %s" % release,
			"slogan = %s" % self.slogan,
			"",
			"vendor = %s" % self.vendor,
			"contact = %s" % self.contact,
		]

		return "\n".join(lines)

	@property
	def name(self):
		return self.data.name

	@property
	def sname(self):
		return self.data.sname

	@property
	def identifier(self):
		return self.sname

	@property
	def slogan(self):
		return self.data.slogan

	def get_arches(self):
		if self._arches is None:
			_arches = self.db.query("SELECT arch_id AS id FROM distro_arches \
				WHERE distro_id = %s", self.id)

			self._arches = []
			for arch in _arches:
				arch = arches.Arch(self.pakfire, arch.id)
				self._arches.append(arch)

			# Sort architectures by their priority.
			self._arches.sort()

		return self._arches

	def set_arches(self, _arches):
		self.db.execute("DELETE FROM distro_arches WHERE distro_id = %s", self.id)

		for arch in _arches:
			self.db.execute("INSERT INTO distro_arches(distro_id, arch_id) \
				VALUES(%s, %s)", self.id, arch.id)

		self._arches = _arches

	arches = property(get_arches, set_arches)

	@property
	def vendor(self):
		return self.data.vendor

	def get_contact(self):
		return self.data.contact

	def set_contact(self, contact):
		self.db.execute("UPDATE distributions SET contact = %s WHERE id = %s",
			contact, self.id)

		if self._data:
			self._data["contact"] = contact

	contact = property(get_contact, set_contact)

	def get_tag(self):
		return self.data.tag

	def set_tag(self, tag):
		self.db.execute("UPDATE distributions SET tag = %s WHERE id = %s",
			tag, self.id)

		if self._data:
			self._data["tag"] = tag

	tag = property(get_tag, set_tag)

	@property
	def description(self):
		return self.data.description or ""

	@property
	def repositories(self):
		_repos = self.db.query("SELECT id FROM repositories WHERE distro_id = %s", self.id)

		repos = []
		for repo in _repos:
			repo = Repository(self.pakfire, repo.id)
			repo._distro = self

			repos.append(repo)

		return sorted(repos)

	@property
	def repositories_aux(self):
		_repos = self.db.query("SELECT id FROM repositories_aux \
			WHERE status = 'enabled' AND distro_id = %s", self.id)

		repos = []
		for repo in _repos:
			repo = RepositoryAux(self.pakfire, repo.id)
			repo._distro = self

			repos.append(repo)

		return sorted(repos)

	def get_repo(self, name):
		repo = self.db.get("SELECT id FROM repositories WHERE distro_id = %s AND name = %s",
			self.id, name)

		if not repo:
			return

		repo = Repository(self.pakfire, repo.id)
		repo._distro = self

		return repo

	def get_build_repos(self):
		repos = []
		
		for repo in self.repositories:
			if repo.enabled_for_builds:
				repos.append(repo)

		# Add all aux. repositories.
		repos += self.repositories_aux

		return repos

	@property
	def first_repo(self):
		repos = self.repositories

		if repos:
			return self.repositories[-1]

	@property
	def comprehensive_repositories(self):
		return [r for r in self.repositories if r.comprehensive]

	def add_repository(self, name, description):
		return Repository.new(self.pakfire, self, name, description)

	@property
	def log(self):
		return [] # TODO

	def has_package(self, name, epoch, version, release):
		#pkg = self.db.get("SELECT packages.id AS id FROM packages \
		#	JOIN builds ON packages.id = builds.pkg_id \
		#	JOIN sources_commits ON packages.commit_id = sources_commits.id \
		#	JOIN sources ON sources_commits.source_id = sources.id \
		#	WHERE builds.type = 'release' AND sources.distro_id = %s \
		#	AND packages.name = %s AND packages.epoch = %s \
		#	AND packages.version = %s AND packages.release = %s LIMIT 1",
		#	self.id, name, epoch, version, release)

		pkg = self.db.get("SELECT p.id AS id FROM packages p \
			JOIN builds b ON p.id = b.pkg_id \
			WHERE b.type = 'release' AND b.distro_id = %s AND \
			p.name = %s AND p.epoch = %s AND p.version = %s AND p.release = %s \
			LIMIT 1", self.id, name, epoch, version, release)

		if not pkg:
			logging.debug("Package %s-%s:%s-%s does not exist, yet." % \
				(name, epoch, version, release))
			return

		logging.debug("Package %s-%s:%s-%s does already exist." % \
			(name, epoch, version, release))

		return packages.Package(self.pakfire, pkg.id)

	def delete_package(self, name):
		pass # XXX figure out what to do at this place

	@property
	def sources(self):
		if self._sources is None:
			self._sources = []

			for source in self.db.query("SELECT id FROM sources WHERE distro_id = %s", self.id):
				source = sources.Source(self.pakfire, source.id)
				self._sources.append(source)

			self._sources.sort()

		return self._sources

	def get_source(self, ident):
		for source in self.sources:
			if not source.identifier == ident:
				continue

			return source
