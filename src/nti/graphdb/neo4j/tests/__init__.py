#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

def can_connect(uri=None):
	from py2neo import Graph
	try:
		graph = Graph(uri)
		assert graph.neo4j_version
		return True
	except Exception:
		return False

def cannot_connect(uri=None):
	return not can_connect(uri)
