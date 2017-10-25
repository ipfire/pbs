#!/usr/bin/python

import logging

from . import arches
from . import base
from . import builds
from . import packages
from . import sources

from .repository import Repository, RepositoryAux

from .decorators import *

class Distributions(base.Object):
	def _get_distribution(self, query, *args):
		res = self.db.get(query, *args)

		if res:
			return Distribution(self.backend, res.id, data=res)

	def _get_distributions(self, query, *args):
		res = self.db.query(query, *args)

		for row in res:
			yield Distribution(self.backend, row.id, data=row)

	def __iter__(self):
		distros = self._get_distributions("SELECT * FROM distributions \
			WHERE deleted IS FALSE ORDER BY name")

		return iter(distros)

	def get_by_id(self, distro_id):
		return self._get_distribution("SELECT * FROM distributions \
			WHERE id = %s", distro_id)

	def get_by_name(self, sname):
		return self._get_distribution("SELECT * FROM distributions \
			WHERE sname = %s AND deleted IS FALSE", sname)

	def get_by_ident(self, ident):
		return self.get_by_name(ident)

	def get_default(self):
		# XXX a bit ugly
		return self.get_by_ident("ipfire3")


class Distribution(base.DataObject):
	table = "distributions"

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.name)

	def __iter__(self):
		return iter(self.repositories)

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
		res = self.db.query("SELECT arch FROM distributions_arches \
			WHERE distro_id = %s ORDER BY arch", self.id)

		return sorted((row.arch for row in res), key=arches.priority)

	def set_arches(self, arches):
		self.db.execute("DELETE FROM distro_arches WHERE distro_id = %s", self.id)

		for arch in arches:
			self.db.execute("INSERT INTO distro_arches(distro_id, arch) \
				VALUES(%s, %s)", self.id, arch)

		self.arches = sorted(arches)

	arches = lazy_property(get_arches, set_arches)

	@property
	def vendor(self):
		return self.data.vendor

	def get_contact(self):
		return self.data.contact

	def set_contact(self, contact):
		self._set_attribute("contact", contact)

	contact = property(get_contact, set_contact)

	def get_tag(self):
		return self.data.tag

	def set_tag(self, tag):
		self._set_attribute("tag", tag)

	tag = property(get_tag, set_tag)

	@property
	def description(self):
		return self.data.description or ""

	@lazy_property
	def repositories(self):
		_repositories = self.backend.repos._get_repositories("SELECT * FROM repositories \
			WHERE distro_id = %s", self.id)

		# Cache
		repositories = []
		for repo in _repositories:
			repo.distro = self
			repositories.append(repo)

		return sorted(repositories)

	@lazy_property
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
		repo = self.backend.repos._get_repository("SELECT * FROM repositories \
			WHERE distro_id = %s AND name = %s", self.id, name)

		# Cache
		repo.distro = self

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

	@lazy_property
	def sources(self):
		_sources = []

		for source in self.db.query("SELECT id FROM sources WHERE distro_id = %s", self.id):
			source = sources.Source(self.pakfire, source.id)
			_sources.append(source)

		return sorted(_sources)

	def get_source(self, identifier):
		for source in self.sources:
			if not source.identifier == identifier:
				continue

			return source
