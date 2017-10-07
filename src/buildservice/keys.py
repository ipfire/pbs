#!/usr/bin/python

import datetime
import gpgme
import io
import os
import shutil
import tempfile

from . import base

from .decorators import *

def read_key(data):
	data = str(data)
	data = io.BytesIO(data)

	tmpdir = tempfile.mkdtemp()
	os.environ["GNUPGHOME"] = tmpdir

	try:
		ctx = gpgme.Context()
		res = ctx.import_(data)

		assert len(res.imports) == 1
		(fpr, trash_a, trash_b) = res.imports[0]

		key = ctx.get_key(fpr)
		assert key

		return fpr, key

	finally:
		shutil.rmtree(tmpdir)
		del os.environ["GNUPGHOME"]


class Keys(base.Object):
	def create(self, data):
		fingerprint, key = read_key(data)

		# Search for duplicates and just update them.
		k = pakfire.keys.get_by_fpr(fingerprint)
		if k:
			k.update(data)
			return k

		# Insert new into the database.
		res = self.db.get("INSERT INTO keys(fingerprint, uids, data) \
			VALUES(%s, %s, %s) RETURNING *", fingerprint, ", ".join([u.uid for u in key.uids]), data)

		key = Key(self.backend, res.id, data=res)
		key.update(data)

		return key

	def get_all(self):
		query = self.db.query("SELECT id FROM keys ORDER BY uids")

		keys = []
		for key in query:
			key = Key(self.pakfire, key.id)
			keys.append(key)

		return keys

	def get_by_id(self, id):
		key = self.db.get("SELECT id FROM keys WHERE id = %s", id)
		if not key:
			return

		return Key(self.pakfire, key.id)

	def get_by_fpr(self, fpr):
		fpr = "%%%s" % fpr

		key = self.db.get("SELECT id FROM keys WHERE fingerprint LIKE %s", fpr)
		if not key:
			return

		return Key(self.pakfire, key.id)


class Key(base.DataObject):
	table = "keys"

	def update(self, data):
		fingerprint, key = read_key(data)

		# First, delete all subkeys.
		self.db.execute("DELETE FROM keys_subkeys WHERE key_id = %s", self.id)

		for subkey in key.subkeys:
			time_created = datetime.datetime.fromtimestamp(subkey.timestamp)
			if subkey.expires:
				time_expires = datetime.datetime.fromtimestamp(subkey.expires)
			else:
				time_expires = None # Key does never expire.

			algo = None
			if subkey.pubkey_algo == gpgme.PK_RSA:
				algo = "RSA/%s" % subkey.length

			self.db.execute("INSERT INTO keys_subkeys(key_id, fingerprint, \
				time_created, time_expires, algo) VALUES(%s, %s, %s, %s, %s)",
				self.id, subkey.keyid, time_created, time_expires, algo)

		self.db.execute("UPDATE keys SET fingerprint = %s, uids = %s, data = %s WHERE id = %s",
			fingerprint, ", ".join([u.uid for u in key.uids]), data, self.id)

	def can_be_deleted(self):
		ret = self.db.query("SELECT id FROM repositories WHERE key_id = %s", self.id)

		if ret:
			return False

		return True

	def delete(self):
		assert self.can_be_deleted()

		self.db.execute("DELETE FROM keys_subkeys WHERE key_id = %s", self.id)
		self.db.execute("DELETE FROM keys WHERE id = %s", self.id)

	@property
	def fingerprint(self):
		return self.data.fingerprint[-16:]

	@property
	def uids(self):
		return self.data.uids.split(", ")

	@property
	def key(self):
		return self.data.data

	@lazy_property
	def subkeys(self):
		res = self.db.query("SELECT * FROM keys_subkeys WHERE key_id = %s ORDER BY time_created", self.id)

		subkeys = []
		for row in res:
			subkey = Subkey(self.backend, row.id, data=row)
			subkeys.append(subkey)

		return sorted(subkeys)


class Subkey(base.DataObject):
	table = "keys_subkeys"

	def __lt__(self, other):
		if isinstance(other, self.__class__):
			return self.time_created < other.time_created

	@property
	def fingerprint(self):
		return self.data.fingerprint

	@property
	def time_created(self):
		return self.data.time_created

	@property
	def time_expires(self):
		return self.data.time_expires

	@property
	def expired(self):
		return self.time_expires <= datetime.datetime.utcnow()

	@property
	def algo(self):
		return self.data.algo
