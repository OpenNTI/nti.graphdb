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

from nti.graphdb.interfaces import IGraphRelationship

from nti.graphdb.neo4j.interfaces import INeo4jRelationship
from nti.graphdb.neo4j.interfaces import IGraphRelationshipNeo4j

from nti.graphdb.neo4j.node import Neo4jNode

from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import EqHash

@WithRepr
@EqHash('id')
@interface.implementer(IGraphRelationshipNeo4j)
class Neo4jRelationship(SchemaConfigured):
	createDirectFieldProperties(IGraphRelationshipNeo4j)

	_v_neo = None
	neo = alias('_v_neo')

	@classmethod
	def create(cls, rel):
		if IGraphRelationshipNeo4j.providedBy(rel):
			result = rel
		elif IGraphRelationship.providedBy(rel):
			result = Neo4jRelationship(id=rel.id, uri=rel.uri, type=rel.type,
									   start=rel.start, end=rel.end,
									   properties=dict(rel.properties))
		elif INeo4jRelationship.providedBy(rel):
			result = Neo4jRelationship(id=unicode(rel._id),
									   uri=unicode(rel.uri.string),
									   type=rel.type,
									   start=Neo4jNode.create(rel.start_node),
									   end=Neo4jNode.create(rel.end_node),
									   properties=dict(rel.properties))
			result.neo = rel
		else:
			result = None
		return result
