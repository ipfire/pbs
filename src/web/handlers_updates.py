#!/usr/bin/python

import tornado.web

from . import base

class UpdatesHandler(base.BaseHandler):
	def get(self):
		self.render("updates-index.html")
