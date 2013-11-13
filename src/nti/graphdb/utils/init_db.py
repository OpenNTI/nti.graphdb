#!/usr/bin/env python
"""
nti.graphdb initialization

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import sys
import argparse

from zope import component

from nti.dataserver.utils import run_with_dataserver

from nti.graphdb import modeled
from nti.graphdb import ratings
from nti.graphdb import assessments
from nti.graphdb import connections
from nti.graphdb import interfaces as graph_interfaces

def init_db(name=None):
	name = name or u''
	db = component.getUtility(graph_interfaces.IGraphDB, name=name)
	modeled.install(db)
	ratings.install(db)
	connections.install(db)
	assessments.install(db)

def main():
	arg_parser = argparse.ArgumentParser(description="Initialize a graphdb")
	arg_parser.add_argument('env_dir', help="Dataserver environment root directory")
	arg_parser.add_argument('-n', '--name', dest='name', help="database name.")
	args = arg_parser.parse_args()

	name = args.name
	env_dir = args.env_dir

	conf_packages = ('nti.graphdb',)
	run_with_dataserver(environment_dir=env_dir,
						xmlconfig_packages=conf_packages,
						function=lambda: init_db(name))
	sys.exit( 0 )

if __name__ == '__main__':
	main()
