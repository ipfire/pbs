#!/usr/bin/python

import logging
import tornado.database

Row = tornado.database.Row

class Connection(tornado.database.Connection):
	def __init__(self, *args, **kwargs):
		logging.debug("Creating new database connection: %s" % args[1])

		tornado.database.Connection.__init__(self, *args, **kwargs)

	def _execute(self, cursor, query, parameters):
		msg = "Executing query: %s" % (query % parameters)
		logging.debug(" ".join(msg.split()))

		return tornado.database.Connection._execute(self, cursor, query, parameters)

