#!/usr/bin/python

import tornado.web

from . import base

class Error404Handler(base.BaseHandler):
	def prepare(self):
		raise tornado.web.HTTPError(404)
