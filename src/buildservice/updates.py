#!/usr/bin/python

from . import base

class Updates(base.Object):
	def __init__(self, pakfire):
		base.Object.__init__(self, pakfire)

	def get(self, type, distro=None, limit=None, offset=None):
		assert type in ("stable", "unstable", "testing")

		query = "SELECT * FROM repositories_builds \
			JOIN builds ON builds.id = repositories_builds.build_id \
			WHERE builds.type = 'release' AND \
				repositories_builds.repo_id IN \
					(SELECT id FROM repositories WHERE type = %s)"
		args = [type,]

		if distro:
			query += " AND builds.distro_id = %s"
			args.append(distro.id)

		query += " ORDER BY time_added DESC"

		if limit:
			if offset:
				query += " LIMIT %s,%s"
				args += [offset, limit]
			else:
				query += " LIMIT %s"
				args.append(limit)

		updates = []
		for row in self.db.query(query, *args):
			update = Update(self.pakfire, row)
			updates.append(update)

		return updates

	def get_latest(self, type):
		return self.get(type=type, limit=5)



class Update(base.Object):
	def __init__(self, pakfire, data):
		base.Object.__init__(self, pakfire)

		self.data = data

		self._build = None

	@property
	def build(self):
		if self._build is None:
			self._build = self.pakfire.builds.get_by_id(self.data.build_id)
			assert self._build

		return self._build

	@property
	def name(self):
		return self.build.name

	@property
	def description(self):
		return self.build.message

	@property
	def summary(self):
		line = None
		for line in self.description.splitlines():
			if not line:
				continue

			break

		if len(line) >= 60:
			line = "%s..." % line[:60]

		return line

	@property
	def severity(self):
		return self.build.severity

	@property
	def distro(self):
		return self.build.distro

	@property
	def score(self):
		return self.build.score

	@property
	def when(self):
		return self.data.time_added
