#!/usr/bin/python

import logging
import memcache

from . import base

class Client(memcache.Client):
	def debuglog(self, str):
		logging.debug("MemCached: %s" % str)


class Cache(base.Object):
	key_prefix = "pbs_"

	def __init__(self, pakfire):
		base.Object.__init__(self, pakfire)

		logging.info("Initializing memcache...")

		# Fetching servers from the database configuration.
		servers = self.settings.get("memcache_servers", "")
		self.servers = servers.split()

		logging.info("  Using servers: %s" % ", ".join(self.servers))

		self._memcache = Client(self.servers, debug=1)

	def get(self, key):
		logging.debug("Querying memcache for: %s" % key)

		key = "".join((self.key_prefix, key))

		return self._memcache.get(key)

	def set(self, key, val, time=60, min_compress_len=0):
		key = "".join((self.key_prefix, key))

		return self._memcache.set(key, val, time=time,
			min_compress_len=min_compress_len)

	def delete(self, key, time=0):
		key = "".join((self.key_prefix, key))

		return self._memcache.delete(key, time=time)
