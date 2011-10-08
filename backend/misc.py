#!/usr/bin/python

from __future__ import division

import hashlib
import tarfile

def friendly_size(s):
	units = ("B", "K", "M", "G", "T")

	i = 0
	while s >= 1024 and i < len(units):
		s /= 1024
		i += 1

	return "%.1f %s" % (s, units[i])

def calc_hash1(filename):
	f = open(filename)

	h = hashlib.sha1()
	while True:
		buf = f.read(1024)
		if not buf:
			break

		h.update(buf)

	f.close()

	return h.hexdigest()


def guess_filetype(filename):
	# XXX very cheap check. Need to do better here.
	if tarfile.is_tarfile(filename):
		return "pkg"

	elif filename.endswith(".log"):
		return "log"

	return "unknown"
