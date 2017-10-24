#!/usr/bin/python

import logging
import ldap
import logging

from . import base
from .decorators import *


class LDAP(base.Object):
	@lazy_property
	def ldap(self):
		ldap_uri = self.settings.get("ldap_uri")
		return ldap.initialize(ldap_uri)
	
	def search(self, query, attrlist=None, limit=0):
		logging.debug("Performing LDAP query: %s" % query)

		search_base = self.settings.get("ldap_search_base")

		results = self.ldap.search_ext_s(search_base, ldap.SCOPE_SUBTREE,
			query, attrlist=attrlist, sizelimit=limit)
	
		return results

	def auth(self, username, password):
		logging.debug("Checking credentials for %s" % username)

		dn = self.get_dn_by_uid(username)
		if not dn:
			logging.debug("Could not resolve username %s to dn" % username)
			return False

		return self.bind(dn, password)

	def bind(self, dn, password):
		try:
			self.ldap.simple_bind_s(dn, password)
		except ldap.INVALID_CREDENTIALS:
			logging.debug("Account credentials are invalid.")
			return False

		logging.debug("Successfully authenticated.")
		return True 

	def get_dn_by_uid(self, uid):
		dn, attrs = self.get_user(uid, attrlist=["uid"])

		if not dn:
			return
		
		logging.debug("DN for uid %s is: %s" % (uid, dn))
		return dn

	def get_user(self, uid, **kwargs):
		result = self.search("(&(objectClass=posixAccount)(uid=%s))" % uid, limit=1, **kwargs)
		for dn, attrs in result:
			return (dn, attrs)

		return (None, None)