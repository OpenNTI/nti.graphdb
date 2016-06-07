#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from py2neo.types import remote

from nti.common.property import alias
from nti.common.representation import WithRepr

from nti.graphdb.interfaces import IGraphNode

from nti.graphdb.neo4j.interfaces import INeo4jNode
from nti.graphdb.neo4j.interfaces import IGraphNodeNeo4j

from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import EqHash

@WithRepr
@EqHash('id')
@interface.implementer(IGraphNodeNeo4j)
class Neo4jNode(SchemaConfigured):
	createDirectFieldProperties(IGraphNodeNeo4j)

	_v_neo = None

	neo = alias('_v_neo')

	@classmethod
	def create(cls, node):
		if IGraphNodeNeo4j.providedBy(node):
			result = node
		elif IGraphNode.providedBy(node):
			result = Neo4jNode(id=node.id, uri=node.uri,
							   label=node.label,
							   properties=dict(node.properties))
		elif INeo4jNode.providedBy(node):
			remote_node = remote(node) or node
			labels = list(node.labels or ())
			result = Neo4jNode(id=unicode(remote_node._id),
							   uri=unicode(remote_node.uri.string),
							   label=labels[0] if labels else None)
			result.label = labels[0] if labels else None
			result.properties = dict(node) # node.properties is deprecated
			result.neo = node
		else:
			result = None
		return result
