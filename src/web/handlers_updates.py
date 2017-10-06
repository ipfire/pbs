#!/usr/bin/python

import tornado.web

from handlers_base import BaseHandler

class UpdatesHandler(BaseHandler):
	def get(self):
		self.render("updates-index.html")
