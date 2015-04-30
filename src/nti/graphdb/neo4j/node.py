#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.common.property import alias
from nti.common.representation import WithRepr

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import createDirectFieldProperties

from ..interfaces import IGraphNode

@WithRepr
@EqHash('id')
@interface.implementer(IGraphNode)
class Neo4jNode(SchemaConfigured):
	createDirectFieldProperties(IGraphNode)

	_v_neo = None
	neo = alias('_v_neo')
	
	@classmethod
	def create(cls, node):
		if isinstance(node, Neo4jNode):
			result = node
		elif IGraphNode.providedBy(node):
			result = Neo4jNode(id=node.id, uri=node.uri,
							   label=node.label,
							   properties=dict(node.properties))
		elif node is not None:
			labels = list(node.labels or ())
			result = Neo4jNode(id=unicode(node._id), 
                               uri=unicode(node.uri.string),
                               label = labels[0] if labels else None)
			result.label = labels[0] if labels else None
			result.properties = dict(node.properties)
			result.neo = node
		else:
			result = None
		return result
