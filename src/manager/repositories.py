#!/usr/bin/python

import logging
import os
import pakfire

from . import base

from ..constants import *

class RepositoriesUpdateEvent(base.Event):
	priority = 6

	@property
	def interval(self):
		return self.pakfire.settings.get_int("repository_update_interval", 600)

	def run(self):
		for distro in self.pakfire.distros.get_all():
			for repo in distro.repositories:
				# Skip repostories that do not need an update at all.
				if not repo.needs_update():
					logging.info("Repository %s - %s is already up to date." % (distro.name, repo.name))
					continue

				e = RepositoryUpdateEvent(self.pakfire, repo.id)
				self.scheduler.add_event(e)


class RepositoryUpdateEvent(base.Event):
	# This is an important task, but it may take a while to process.
	priority = 5

	def run(self, repo_id):
		# Run this in a new process.
		self.run_subprocess_background(self.update_repo, repo_id)

	@staticmethod
	def update_repo(_pakfire, repo_id):
		repo = _pakfire.repos.get_by_id(repo_id)
		assert repo

		logging.info("Going to update repository %s..." % repo.name)

		# Update the timestamp when we started at last.
		repo.updated()

		# Find out for which arches this repository is created.
		arches = repo.arches

		# Add the source repository.
		arches.append(_pakfire.arches.get_by_name("src"))

		for arch in arches:
			changed = False

			# Get all package paths that are to be included in this repository.
			paths = repo.get_paths(arch)

			repo_path = os.path.join(
				REPOS_DIR,
				repo.distro.identifier,
				repo.identifier,
				arch.name
			)

			if not os.path.exists(repo_path):
				os.makedirs(repo_path)

			source_files = []
			remove_files = []

			for filename in os.listdir(repo_path):
				path = os.path.join(repo_path, filename)

				if not os.path.isfile(path):
					continue

				remove_files.append(path)

			for path in paths:
				filename = os.path.basename(path)

				source_file = os.path.join(PACKAGES_DIR, path)
				target_file = os.path.join(repo_path, filename)

				# Do not add duplicate files twice.
				if source_file in source_files:
					continue

				source_files.append(source_file)

				try:
					remove_files.remove(target_file)
				except ValueError:
					changed = True

			if remove_files:
				changed = True

			# If nothing in the repository data has changed, there
			# is nothing to do.
			if changed:
				logging.info("The repository has updates...")
			else:
				logging.info("Nothing to update.")
				continue

			# Find the key to sign the package.
			key_id = None
			if repo.key:
				key_id = repo.key.fingerprint

			# Create package index.
			p = pakfire.PakfireServer(arch=arch.name)

			p.repo_create(repo_path, source_files,
				name="%s - %s.%s" % (repo.distro.name, repo.name, arch.name),
				key_id=key_id)

			# Remove files afterwards.
			for file in remove_files:
				file = os.path.join(repo_path, file)

				try:
					os.remove(file)
				except OSError:
					logging.warning("Could not remove %s." % file)
