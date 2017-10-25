#!/usr/bin/python

from __future__ import division

import hashlib
import os
import re
import tarfile

from tornado.escape import xhtml_escape

from .constants import *

def format_size(s):
	units = ("B", "k", "M", "G", "T")

	i = 0
	while s >= 1024 and i < len(units):
		s /= 1024
		i += 1

	return "%d%s" % (round(s), units[i])

def friendly_time(t):
	if not t:
		return "--:--"

	t = int(t)
	ret = []

	if t >= 604800:
		ret.append("%s w" % (t // 604800))
		t %= 604800

	if t >= 86400:
		ret.append("%s d" % (t // 38400))
		t %= 86400

	if t >= 3600:
		ret.append("%s h" % (t // 3600))
		t %= 3600

	if t >= 60:
		ret.append("%s m" % (t // 60))
		t %= 60

	if t:
		ret.append("%s s" % t)

	return " ".join(ret)

def format_email(email):
	m = re.match(r"(.*) <(.*)>", email)
	if m:
		fmt = {
			"name" : xhtml_escape(m.group(1)),
			"mail" : xhtml_escape(m.group(2)),
		}
	else:
		fmt = {
			"name" : xhtml_escape(email),
			"mail" : xhtml_escape(email),
		}

	return """<a class="email" href="mailto:%(mail)s">%(name)s</a>""" % fmt

def format_filemode(filetype, filemode):
	if filetype == 2:
		prefix = "l"
	elif filetype == 5:
		prefix = "d"
	else:
		prefix = "-"

	return prefix + tarfile.filemode(filemode)[1:]

def calc_hash(filename, algo="sha512"):
	assert algo in hashlib.algorithms

	f = open(filename, "rb")
	h = hashlib.new(algo)

	while True:
		buf = f.read(BUFFER_SIZE)
		if not buf:
			break

		h.update(buf)

	f.close()

	return h.hexdigest()
