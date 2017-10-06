#!/usr/bin/python

import logging
import memcache

from . import base

from .decorators import *

log = logging.getLogger("cache")
log.propagate = 1

class Client(memcache.Client):
	def debuglog(self, str):
		log.debug(str)


class Cache(base.Object):
	key_prefix = "pbs_"

	@property
	def servers(self):
		servers = self.settings.get("memcache_servers", "")

		return servers.split()

	@lazy_property
	def _cache(self):
		logging.debug("Connecting to memcache...")

		return Client(self.servers, debug=1)

	def get(self, key):
		log.debug("Querying for: %s" % key)

		key = "".join((self.key_prefix, key))

		return self._cache.get(key)

	def set(self, key, val, time=60, min_compress_len=0):
		key = "".join((self.key_prefix, key))

		return self._cache.set(key, val, time=time,
			min_compress_len=min_compress_len)

	def delete(self, key, time=0):
		key = "".join((self.key_prefix, key))

		return self._cache.delete(key, time=time)
