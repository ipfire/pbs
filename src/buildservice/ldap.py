#!/usr/bin/python

from __future__ import absolute_import

import ldap
import logging

log = logging.getLogger("ldap")
log.propagate = 1

from . import base
from .decorators import *

class LDAP(base.Object):
	@lazy_property
	def ldap(self):
		ldap_uri = self.settings.get("ldap_uri")

		log.debug("Connecting to %s..." % ldap_uri)

		# Establish LDAP connection
		return ldap.initialize(ldap_uri)

	def search(self, query, attrlist=None, limit=0):
		log.debug("Performing LDAP query: %s" % query)

		search_base = self.settings.get("ldap_search_base")

		results = self.ldap.search_ext_s(search_base, ldap.SCOPE_SUBTREE,
			query, attrlist=attrlist, sizelimit=limit)
	
		return results

	def auth(self, username, password):
		log.debug("Checking credentials for %s" % username)

		dn = self.get_dn_by_uid(username)
		if not dn:
			log.debug("Could not resolve username %s to dn" % username)
			return False

		return self.bind(dn, password)

	def bind(self, dn, password):
		try:
			self.ldap.simple_bind_s(dn, password)
		except ldap.INVALID_CREDENTIALS:
			log.debug("Account credentials for %s are invalid" % dn)
			return False

		log.debug("Successfully authenticated %s" % dn)

		return True 

	def get_dn_by_uid(self, uid):
		dn, attrs = self.get_user(uid, attrlist=["uid"])

		if not dn:
			return

		log.debug("DN for uid %s is: %s" % (uid, dn))
		return dn

	def get_user(self, uid, **kwargs):
		result = self.search("(&(objectClass=posixAccount)(uid=%s))" % uid, limit=1, **kwargs)
		for dn, attrs in result:
			return (dn, attrs)

		return (None, None)