#!/usr/bin/python

import datetime
import gpgme
import io
import os
import shutil
import tempfile

from . import base

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
	def create(self, *args, **kwargs):
		return Key.create(self.pakfire, *args, **kwargs)

	def get_all(self):
		query = self.db.query("SELECT id FROM `keys` ORDER BY uids")

		keys = []
		for key in query:
			key = Key(self.pakfire, key.id)
			keys.append(key)

		return keys

	def get_by_id(self, id):
		key = self.db.get("SELECT id FROM `keys` WHERE id = %s", id)
		if not key:
			return

		return Key(self.pakfire, key.id)

	def get_by_fpr(self, fpr):
		fpr = "%%%s" % fpr

		key = self.db.get("SELECT id FROM `keys` WHERE fingerprint LIKE %s", fpr)
		if not key:
			return

		return Key(self.pakfire, key.id)


class Key(base.Object):
	def __init__(self, pakfire, id):
		base.Object.__init__(self, pakfire)

		self.id = id

		# Cache.
		self._data = None
		self._subkeys = None

	@property
	def keys(self):
		return self.pakfire.keys

	@classmethod
	def create(cls, pakfire, data):
		fingerprint, key = read_key(data)

		# Search for duplicates and just update them.
		k = pakfire.keys.get_by_fpr(fingerprint)
		if k:
			k.update(data)
			return k

		# Insert new into the database.
		key_id = pakfire.db.execute("INSERT INTO `keys`(fingerprint, uids, data) \
			VALUES(%s, %s, %s)", fingerprint, ", ".join([u.uid for u in key.uids]), data)

		key = cls(pakfire, key_id)
		key.update(data)

		return key

	@property
	def data(self):
		if self._data is None:
			self._data = self.db.get("SELECT * FROM `keys` WHERE id = %s", self.id)
			assert self._data

		return self._data

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

		self.db.execute("UPDATE `keys` SET fingerprint = %s, uids = %s, data = %s WHERE id = %s",
			fingerprint, ", ".join([u.uid for u in key.uids]), data, self.id)

	def can_be_deleted(self):
		ret = self.db.query("SELECT id FROM repositories WHERE key_id = %s", self.id)

		if ret:
			return False

		return True

	def delete(self):
		assert self.can_be_deleted()

		self.db.execute("DELETE FROM `keys_subkeys` WHERE key_id = %s", self.id)
		self.db.execute("DELETE FROM `keys` WHERE id = %s", self.id)

	@property
	def fingerprint(self):
		return self.data.fingerprint[-16:]

	@property
	def uids(self):
		return self.data.uids.split(", ")

	@property
	def key(self):
		return self.data.data

	@property
	def subkeys(self):
		if self._subkeys is None:
			self._subkeys = []

			query = self.db.query("SELECT * FROM keys_subkeys WHERE key_id = %s ORDER BY time_created", self.id)

			for subkey in query:
				subkey = Subkey(self.pakfire, subkey.id)
				self._subkeys.append(subkey)

		return self._subkeys


class Subkey(base.Object):
	def __init__(self, pakfire, id):
		base.Object.__init__(self, pakfire)

		self.id = id

		# Cache.
		self._data = None

	@property
	def data(self):
		if self._data is None:
			self._data = self.db.get("SELECT *, time_expires - NOW() AS expired \
				FROM keys_subkeys WHERE id = %s", self.id)
			assert self._data

		return self._data

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
		return self.data.expired <= 0

	@property
	def algo(self):
		return self.data.algo
