#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import logging
import argparse

from zope import component

from nti.async.utils.processor import Processor

from nti.graphdb import QUEUE_NAME
from nti.graphdb import interfaces as graph_interfaces

class Constructor(Processor):

	def create_arg_parser(self):
		arg_parser = argparse.ArgumentParser(description="Graph processor")
		arg_parser.add_argument('-v', '--verbose', help="Be verbose",
								action='store_true', dest='verbose')
		return arg_parser

	def tone_down_logging(self):
		try:
			package = 'py2neo.packages.httpstream.http'
			__import__(package)
			py2neo_logger = logging.getLogger(package)
			py2neo_logger.setLevel(logging.ERROR)
		except ImportError:
			logger.error("Could not setup logging level for py2neo")

	def set_log_formatter(self, args):
		super(Constructor, self).set_log_formatter(args)
		if args.verbose:
			for _, module in component.getUtilitiesFor(graph_interfaces.IObjectProcessor):
				module.logger.setLevel(logging.DEBUG)
		self.tone_down_logging()

	def process_args(self, args):
		setattr(args, 'library', True)  # load library
		setattr(args, 'name', QUEUE_NAME)  # set queue name
		super(Constructor, self).process_args(args)
	
def main():
	return Constructor()()

if __name__ == '__main__':
	main()
