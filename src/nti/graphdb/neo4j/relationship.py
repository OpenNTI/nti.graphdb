#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import createDirectFieldProperties

from .node import Neo4jNode
from .. import interfaces as graph_interfaces

@interface.implementer(graph_interfaces.IGraphRelationship)
class Neo4jRelationship(SchemaConfigured):
	createDirectFieldProperties(graph_interfaces.IGraphRelationship)

	_neo = None

	def __str__(self):
		return self.id

	def __repr__(self):
		return "%s(%s,%s)" % (self.__class__.__name__, self.id, self.properties)

	def __eq__(self, other):
		try:
			return self is other or (self.id == other.id)
		except AttributeError:
			return NotImplemented

	def __hash__(self):
		xhash = 47
		xhash ^= hash(self.id)
		return xhash

	@classmethod
	def create(cls, rel):
		if isinstance(rel, Neo4jRelationship):
			result = rel
		elif graph_interfaces.IGraphRelationship.providedBy(rel):
			result = Neo4jRelationship(id=rel.id, uri=rel.uri, type=rel.type,
									   start=rel.start, end=rel.end,
									   properties=dict(rel.properties))
		elif rel is not None:
			result = Neo4jRelationship(id=unicode(rel._id),
									   uri=unicode(rel.__uri__),
									   type=rel.type,
									   start=Neo4jNode.create(rel.start_node),
									   end=Neo4jNode.create(rel.end_node),
									   properties=dict(rel._properties))
			result._neo = rel
		else:
			result = None
		return result
