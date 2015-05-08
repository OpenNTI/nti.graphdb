#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from ..interfaces import IGraphNode
from ..interfaces import IGraphRelationship

class INeo4jNode(interface.Interface):
	pass

class INeo4jRelationship(interface.Interface):
	pass

class IGraphNodeNeo4j(IGraphNode):
	pass

class IGraphRelationshipNeo4j(IGraphRelationship):
	pass
