#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import createDirectFieldProperties

from .. import interfaces as graph_interfaces

@interface.implementer(graph_interfaces.IGraphNode)
class Neo4jNode(SchemaConfigured):
    createDirectFieldProperties(graph_interfaces.IGraphNode)

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
    def create(cls, node):
        if isinstance(node, Neo4jNode):
            result = node
        elif graph_interfaces.IGraphNode.providedBy(node):
            result = Neo4jNode(id=node.id, uri=node.uri,
                               labels=tuple(node.labels),
                               properties=dict(node.properties))
        elif node is not None:
            result = Neo4jNode(id=unicode(node._id), uri=unicode(node.__uri__))
            result.labels = tuple(getattr(node, '_labels', ()))
            result.properties = dict(node._properties)
            result._neo = node
        else:
            result = None
        return result
