#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from nti.graphdb.interfaces import INode
from nti.graphdb.interfaces import IGraphNode
from nti.graphdb.interfaces import IRelationship
from nti.graphdb.interfaces import IGraphRelationship

class INeo4jNode(INode):
	pass

class INeo4jRelationship(IRelationship):
	pass

class IGraphNodeNeo4j(IGraphNode):
	pass

class IGraphRelationshipNeo4j(IGraphRelationship):
	pass
