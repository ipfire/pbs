#!/usr/bin/python

import geoip2.database
import geoip2.errors
import os.path

from . import base

from .constants import DATADIR

class GeoIP(base.Object):
	def init(self):
		path = os.path.join(DATADIR, "geoip/GeoLite2-Country.mmdb")

		# Open the database
		self.db = geoip2.database.Reader(path)

	def guess_from_address(self, address):
	        # Query the database
	        try:
	                result = self.db.country(address)

	        # Return nothing if the address could not be found
	        except geoip2.errors.AddressNotFoundError:
	               return

	        if result:
        	        return result.country.iso_code
