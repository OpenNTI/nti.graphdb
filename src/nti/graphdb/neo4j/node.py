#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from nti.graphdb.interfaces import IGraphNode

from nti.graphdb.neo4j.interfaces import INeo4jNode
from nti.graphdb.neo4j.interfaces import IGraphNodeNeo4j

from nti.externalization.representation import WithRepr

from nti.property.property import alias

from nti.schema.eqhash import EqHash

from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import createDirectFieldProperties

logger = __import__('logging').getLogger(__name__)


@WithRepr
@EqHash('id')
@interface.implementer(IGraphNodeNeo4j)
class Neo4jNode(SchemaConfigured):
    createDirectFieldProperties(IGraphNodeNeo4j)

    _v_neo = None

    neo = alias('_v_neo')

    @classmethod
    def create(cls, node):
        result = None
        if IGraphNodeNeo4j.providedBy(node):
            result = node
        elif IGraphNode.providedBy(node):
            result = Neo4jNode(id=node.id,
                               label=node.label,
                               properties=dict(node.properties or {}))
        elif INeo4jNode.providedBy(node):
            labels = list(node.labels or ())
            result = Neo4jNode(id=node.id)
            # pylint: disable=attribute-defined-outside-init
            result.label = labels[0] if labels else None
            result.properties = dict(node.properties or {})
            result.neo = node
        return result
