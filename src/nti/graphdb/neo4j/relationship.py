#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from nti.graphdb.neo4j.interfaces import INeo4jRelationship
from nti.graphdb.neo4j.interfaces import IGraphRelationshipNeo4j

from nti.graphdb.neo4j.node import Neo4jNode

from nti.externalization.representation import WithRepr

from nti.property.property import alias

from nti.schema.eqhash import EqHash

from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import createDirectFieldProperties

logger = __import__('logging').getLogger(__name__)


@WithRepr
@EqHash('id')
@interface.implementer(IGraphRelationshipNeo4j)
class Neo4jRelationship(SchemaConfigured):
    createDirectFieldProperties(IGraphRelationshipNeo4j)

    _v_neo = None

    neo = alias('_v_neo')

    @classmethod
    def create(cls, rel):
        result = None
        if IGraphRelationshipNeo4j.providedBy(rel):
            result = rel
        elif INeo4jRelationship.providedBy(rel):
            result = Neo4jRelationship(id=rel.id,
                                       type=rel.type,
                                       end=Neo4jNode.create(rel.end),
                                       start=Neo4jNode.create(rel.start),
                                       properties=dict(rel.properties or {}))
            result.neo = rel if INeo4jRelationship.providedBy(rel) else None
        return result
