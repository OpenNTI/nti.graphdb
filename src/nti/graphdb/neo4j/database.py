#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six
import sys
import numbers
from collections import Mapping
from collections import Sequence

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

# pylint: disable=no-name-in-module,import-error
from neo4j.exceptions import CypherError

from neo4j.v1 import GraphDatabase

from nti.graphdb.common import NodePrimaryKey
from nti.graphdb.common import get_node_primary_key

from nti.graphdb.interfaces import IGraphDB
from nti.graphdb.interfaces import ILabelAdapter
from nti.graphdb.interfaces import IPropertyAdapter
from nti.graphdb.interfaces import IUniqueAttributeAdapter

from nti.graphdb.neo4j.interfaces import INeo4jNode
from nti.graphdb.neo4j.interfaces import IGraphNodeNeo4j
from nti.graphdb.neo4j.interfaces import INeo4jRelationship
from nti.graphdb.neo4j.interfaces import IGraphRelationshipNeo4j

from nti.graphdb.neo4j.node import Neo4jNode

from nti.graphdb.neo4j.relationship import Neo4jRelationship

from nti.externalization.representation import WithRepr

from nti.schema.eqhash import EqHash

logger = __import__('logging').getLogger(__name__)


def is_node_404(e):
    """
    Check if the exception is for an entitiy not found error
    """
    code = getattr(e, 'code', None) or ''
    return "EntityNotFound" in code


def merge_node_query(label, key, value):
    """
    Returns a merge query for the specififed label, key and value
    """
    result = "MERGE (n:%s { %s:'%s' }) RETURN n" % (label, key, value)
    return result


def process_properties(properties):
    """
    Returns an array with entries of key,value pairs
    for node properties
    """
    props = []
    for key, value in properties.items():
        if isinstance(value, six.string_types):
            props.append("%s:'%s'" % (key, value))
        elif isinstance(value, bool):
            props.append("%s:%s" % (key, str(value).upper()))
        elif isinstance(value, numbers.Number):
            props.append("%s:%s" % (key, value))
        else:
            props.append("%s:'%s'" % (key, value))
    return props


def set_node_properties_query(label, key, value, properties):
    """
    Returns a query that sets the specified properties for a node
    with the specified label, key, value
    """
    result = ["MATCH (n:%s { %s:'%s' })" % (label, key, value)]
    result.append(" SET n += {")
    props = process_properties(properties)
    result.append(' , '.join(props))
    result.append('} RETURN n')
    return ''.join(result)


def set_node_properties_with_id_query(nid, properties):
    """
    Returns a query that sets the specified properties for a node
    with the specified node id
    """
    result = ["START n=NODE(%s) MATCH (n)" % nid]
    result.append(" SET n += {")
    props = process_properties(properties)
    result.append(' , '.join(props))
    result.append('} RETURN n')
    return ''.join(result)


def create_node_query(label, properties):
    """
    Returns a a query to create a node with the specified label and
    properties
    """
    result = ["CREATE (n:%s" % label]
    props = process_properties(properties)
    if props:
        result.append(" { ")
        result.append(' , '.join(props))
        result.append(" }")
    result.append(") RETURN n")
    return ''.join(result)


def match_node_query(label, key, value):
    """
    Returns a query that matches a node with the specified label, key and value
    """
    result = "MATCH (n:%s { %s:'%s' }) RETURN n" % (label, key, value)
    return result


def match_node_by_id_query(nid):
    """
    Returns a query that matches a node with the specified id
    """
    return "START n=NODE(%s) MATCH (n) RETURN n" % nid


def isolate_node(nid):
    """
    Returns a query that deletes all relationships of a node
    """
    return "START a=node(%s) MATCH (a)-[r]-(b) DELETE r" % nid


def delete_node(nid):
    """
    Returns a query that deletes a node with the specified id
    """
    return "START n=node(%s) MATCH (n) DELETE n" % nid


def create_relationship_query(start, end, type_, bidirectional=False, unique=False):
    # prepare params
    end = getattr(end, 'id', end)
    start = getattr(start, 'id', start)
    unique = 'UNIQUE' if unique else ''
    direction = '-' if bidirectional else '->'
    # write query
    result = """
    MATCH (a)
    WHERE id(a)=%s
    MATCH (b)
    WHERE id(b)=%s
    CREATE %s (a)-[r:%s]%s(b)
    RETURN r""" % (start, end, unique, type_, direction)
    return ' '.join(result.split())


def create_unique_relationship_query(start, end, type_, bidirectional):
    return create_relationship_query(start, end, type_, bidirectional, True)


def match_relationship_by_id_query(rid):
    """
    Returns a query that matches a relationship with the specified id
    """
    rid = getattr(rid, 'id', rid)
    return "MATCH (a)-[r]-(b) WHERE ID(r) = %s RETURN r" % rid


def set_relationship_properties_with_id_query(rid, properties):
    """
    Returns a query that sets the specified properties for a relationship
    for the specified node ids
    """
    # prepare params
    rid = getattr(rid, 'id', rid)
    props = process_properties(properties)
    # write query
    result = ["MATCH (a)-[r]-(b) WHERE ID(r) = %s" % rid]
    result.append(" SET r += {")
    result.append(' , '.join(props))
    result.append('} RETURN r')
    return ''.join(result)


def match_relationship_query(start=None, end=None, type_=None, bidirectional=False):
    result = ''
    end = getattr(end, 'id', end)
    start = getattr(start, 'id', start)
    direction = '-' if bidirectional else '->'
    if start is not None:
        result = "MATCH (a) WHERE id(a)=%s " % start
    if end is not None:
        result += "MATCH (b) WHERE id(b)=%s " % end
    if type_:
        result += "MATCH p=(a)-[:%s]%s(b) RETURN rels(p)" % (type_, direction)
    else:
        result += "MATCH p=(a)-[r]%s(b) RETURN rels(p)" % direction
    return result


def delete_relationship_query(rid):
    rid = getattr(rid, 'id', rid)
    result = "MATCH (a)-[r]-(b) WHERE ID(r) = %s DELETE r" % rid
    return result


def delist(x):
    result = []
    for a in x:
        if isinstance(a, Sequence):
            result.extend(delist(a))
        else:
            result.append(a)
    return result


def fix_query_value(value):
    if isinstance(value, six.string_types):
        value = value if value.endswith("'") else "%s'" % value
        value = value if value.startswith("'") else "'%s" % value
    return value


def find_relationship_query(key, value, start=None, end=None, type_=None, bidirectional=False):
    result = ''
    end = getattr(end, 'id', end)
    start = getattr(start, 'id', start)
    direction = '-' if bidirectional else '->'
    if start is not None:
        result = "MATCH (a) WHERE id(a)=%s " % start
    if end is not None:
        result += "MATCH (b) WHERE id(b)=%s " % end
    if type_:
        result += "MATCH p=(a)-[:%s {%s:%s}]%s(b) RETURN rels(p)" % (type_, key, value,
                                                                     direction)
    else:
        result += "MATCH p=(a)-[ {%s:%s}]%s(b) RETURN rels(p)" % (key, value,
                                                                  direction)
    return result


@WithRepr
@EqHash('url')
@interface.implementer(IGraphDB)
class Neo4jDB(object):

    def __init__(self, url=None, username=None, password=None):
        self.url = url
        self.username = username
        self.password = password

    @Lazy
    def graph(self):
        if self.username and self.password:
            result = GraphDatabase.driver(
                self.url,
                auth=(self.username, self.password)
            )
        else:
            result = GraphDatabase.driver(self.url)
        return result
    db = graph

    def session(self):
        # pylint: disable=no-member
        return self.db.session()

    def single_value(self, result):
        result = result.single() if result is not None else None
        return result.value() if result is not None else None

    # nodes

    def do_create_unique_node_session(self, session, label, key, value, properties=None):
        properties = {} if properties is None else properties
        query = merge_node_query(label, key, value)
        result = session.run(query)
        if properties:
            query = set_node_properties_query(label, key, value, properties)
            result = session.run(query)
        return self.single_value(result)

    def do_create_node_session(self, session, label, properties=None):
        properties = {} if properties is None else properties
        query = create_node_query(label, properties)
        result = session.run(query)
        return self.single_value(result)

    def get_node_primary_key(self, obj, label=None, key=None, value=None):
        # get object labels
        label = label or ILabelAdapter(obj, None)
        assert label, "must provide an object label"
        # get primary key
        if key and value:
            result = NodePrimaryKey(label, key, value)
        else:
            result = get_node_primary_key(obj)
        return result

    def do_create_node(self, obj, label=None, key=None, value=None, properties=None):
        # get object properties
        merged_props = IPropertyAdapter(obj, None) or {}
        merged_props.update(properties or {})
        properties = merged_props
        # get object labels
        pk = self.get_node_primary_key(obj, label, key, value)
        # create node
        with self.session() as session:
            if pk is not None:
                result = self.do_create_unique_node_session(session, pk.label,
                                                            pk.key, pk.value,
                                                            properties)
            else:
                result = self.do_create_node_session(session, label,
                                                     properties)
        return result

    def create_node(self, obj, label=None, key=None, value=None, properties=None, raw=False):
        node = self.do_create_node(obj, label, key, value, properties)
        node = Neo4jNode.create(node) if not raw else node
        return node

    def create_nodes(self, *objects):
        result = []
        with self.session() as session:
            for obj in objects:
                # must get a label
                label = ILabelAdapter(obj)
                # try to get primary key
                pk = get_node_primary_key(obj)
                # optional properties
                properties = IPropertyAdapter(obj, None)
                if pk is not None:
                    node = self.do_create_unique_node_session(session, pk.label,
                                                              pk.key, pk.value,
                                                              properties)
                else:
                    node = self.do_create_node_session(session, label,
                                                       properties)
                result.append(Neo4jNode.create(node))
        return result

    def do_get_node_session(self, session, obj):
        result = None
        try:
            if INeo4jNode.providedBy(obj):
                result = obj
            elif IGraphNodeNeo4j.providedBy(obj):
                result = obj.neo
                if result is None:
                    query = match_node_by_id_query(obj.id)
                    result = obj.neo = self.single_value(session.run(query))
            elif obj is not None:
                if isinstance(obj, (six.string_types, numbers.Number)):
                    query = match_node_by_id_query(obj)
                    result = session.run(query)
                else:
                    pk = get_node_primary_key(obj)
                    if pk is not None:
                        query = match_node_query(pk.label, pk.key, pk.value)
                        result = session.run(query)
                # return a single node
                result = self.single_value(result)
        except CypherError as e:
            if not is_node_404(e):  # pragma: no cover
                raise e
            result = None
        return result

    def do_get_node(self, obj):
        with self.session() as session:
            result = self.do_get_node_session(session, obj)
        return result

    def get_node(self, obj):
        node = self.do_get_node(obj)
        node = Neo4jNode.create(node)
        return node
    node = get_node

    def do_get_or_create_node_session(self, session, obj):
        result = self.do_get_node_session(session, obj) \
              or self.do_create_node_session(session,
                                             ILabelAdapter(obj),
                                             IPropertyAdapter(obj, None))
        return result

    def get_or_create_node(self, obj):
        return self.get_node(obj) or self.create_node(obj)

    def get_nodes(self, *objects):
        result = []
        with self.session() as session:
            for obj in objects:
                node = self.do_get_node_session(session, obj)
                result.append(node)
        return result

    def do_get_index_node_session(self, session, label, key, value):
        query = match_node_query(label, key, value)
        result = session.run(query)
        return self.single_value(result)

    def get_indexed_node(self, label, key, value):
        with self.session() as session:
            result = self.do_get_index_node_session(session, label, key, value)
            result = Neo4jNode.create(result)
            return result

    def get_indexed_nodes(self, *tuples):
        result = []
        with self.session() as session:
            for label, key, value in tuples:
                node = self.do_get_index_node_session(session, label,
                                                      key, value)
                node = Neo4jNode.create(node) if node is not None else None
                result.append(node)
        return result

    def update_node(self, obj, properties=None):
        with self.session() as session:
            node = self.do_get_node_session(session, obj)
            if node is not None:
                new_props = IPropertyAdapter(obj, None) or {}
                new_props.update(properties or {})  # set and overwrite
                query = set_node_properties_with_id_query(node.id, properties)
                session.run(query)
                return True
        return False

    def do_delete_node_session(self, session, obj):
        node = self.do_get_node_session(session, obj)
        if node is not None:
            query = isolate_node(node.id)
            session.run(query)
            query = delete_node(node.id)
            session.run(query)
            return True
        return False

    def delete_node(self, obj):
        with self.session() as session:
            return self.do_delete_node_session(session, obj)

    def delete_nodes(self, *objects):
        result = 0
        with self.session() as session:
            for obj in objects:
                if self.do_delete_node_session(session, obj):
                    result += 1
        return result

    # relationships

    @classmethod
    def relationship_properties(cls, start, end, rel_type):
        result = component.queryMultiAdapter((start, end, rel_type),
                                             IPropertyAdapter)
        return dict(result or {})

    def do_create_unique_relationship_session(self, session, start, end, type_,
                                              properties=None, bidirectional=False):
        # prepare query
        query = create_unique_relationship_query(start, end,
                                                 type_, bidirectional)
        result = self.single_value(session.run(query))
        if result is not None and properties:
            query = set_relationship_properties_with_id_query(
                result, properties
            )
            result = self.single_value(session.run(query))
        return result

    def do_create_relationship_session(self, session, start, end, type_,
                                       properties=None, bidirectional=False):
        # prepare query
        query = create_relationship_query(start, end, type_, bidirectional)
        result = self.single_value(session.run(query))
        if result is not None and properties:
            query = set_relationship_properties_with_id_query(
                result, properties
            )
            result = self.single_value(session.run(query))
        return result

    def do_create_relationship(self, start, end, type_, properties=None,
                               unique=True, bidirectional=False):
        # get or create nodes
        with self.session() as session:
            end = self.do_get_or_create_node_session(session, end)
            start = self.do_get_or_create_node_session(session, start)
            # capture properties
            merged_props = self.relationship_properties(start, end, type_)
            merged_props.update(properties or {})
            # create
            if unique:
                result = self.do_create_unique_relationship_session(session, start, end, str(type_),
                                                                    merged_props, bidirectional)
            else:
                result = self.do_create_relationship_session(session, start, end, str(type_),
                                                             merged_props, bidirectional)
            return result

    def create_relationship(self, start, end, type_, properties=None,
                            unique=True, bidirectional=False):
        result = self.do_create_relationship(start, end, type_, properties,
                                             unique, bidirectional)
        result = Neo4jRelationship.create(result)
        return result

    def create_relationships(self, *relationships):
        assert all(isinstance(r, Sequence) and len(r) >= 3
                   for r in relationships)
        result = []
        with self.session() as session:
            for data in relationships:
                # get relationship type
                start, type_, end = data[:3]
                assert type_, 'Invalid relationship type'
                # get end nodes
                end = self.do_get_node_session(session, end)
                assert end is not None, "Cannot find end node"
                # get start node
                start = self.do_get_node_session(session, start)
                assert start is not None, "Cannot find start node"
                # get properties
                properties = {} if len(data) < 4 or not data[3] else data[3]
                assert isinstance(properties, Mapping), "Invalid properties"
                # get unique flag
                unique = False if len(data) < 5 or data[4] is None else data[4]
                # create
                if unique:
                    created = self.do_create_unique_relationship_session(session, start, end,
                                                                         type_, properties)
                else:
                    created = self.do_create_relationship_session(session, start, end,
                                                                  type_, properties)
                # store
                result.append(Neo4jRelationship.create(created))
        return result

    def do_get_relationship_session(self, session, obj):
        result = None
        try:
            if INeo4jRelationship.providedBy(obj):
                result = obj
            elif IGraphRelationshipNeo4j.providedBy(obj):
                result = obj.neo
                if result is None:
                    query = match_relationship_by_id_query(obj.id)
                    result = obj.neo = self.single_value(session.run(query))
            elif obj is not None:
                query = match_relationship_by_id_query(obj)
                result = self.single_value(session.run(query))
        except CypherError as e:
            if not is_node_404(e):  # pragma: no cover
                raise e
            result = None
        return result

    def do_get_relationship(self, obj):
        with self.session() as session:
            result = self.do_get_relationship_session(session, obj)
        return result

    def get_relationship(self, obj):
        result = self.do_get_relationship(obj)
        result = Neo4jRelationship.create(result)
        return result
    relationship = get_relationship

    def do_match_session(self, session, start, end=None, type_=None,
                         bidirectional=False, limit=None):
        result = ()
        limit = limit or sys.maxint
        type_ = str(type_) if type_ else None
        end = self.do_get_node_session(session, end)
        start = self.do_get_node_session(session, start)
        if start is not None:
            query = match_relationship_query(start, end, type_, bidirectional)
            values = session.run(query).values()
            # delist relationships for paths of length 1
            result = delist(values)
        return result or ()

    def match(self, start, end=None, type_=None, bidirectional=False, limit=None):
        with self.session() as session:
            result = self.do_match_session(session,
                                           start, end, type_,
                                           bidirectional, limit)
            result = list({Neo4jRelationship.create(x) for x in result})
            return result or ()

    def do_delete_relationships_session(self, session, *objects):
        for obj in objects:
            query = delete_relationship_query(obj)
            session.run(query)

    def delete_relationships(self, *objects):
        with self.session() as session:
            self.do_delete_relationships_session(session, *objects)
    delete_relationship = delete_relationships

    def do_update_relationship_session(self, session, obj, properties):
        obj = self.do_get_relationship_session(session, obj)
        if obj is not None:
            query = set_relationship_properties_with_id_query(obj, properties)
            return self.single_value(session.run(query))

    def update_relationship(self, obj, properties):
        with self.session() as session:
            result = self.do_update_relationship_session(
                session, obj, properties
            )
            return Neo4jRelationship.create(result)

    def do_find_relationships_session(self, session, key, value, type_=None,
                                      start=None, end=None, bidirectional=False):
        # gather data
        value = fix_query_value(value)
        type_ = str(type_) if type_ else None
        end = self.do_get_node_session(session, end)
        start = self.do_get_node_session(session, start)
        # construct query
        query = find_relationship_query(key, value,
                                        start, end, type_, bidirectional)
        values = session.run(query).values()
        # delist relationships for paths of length 1
        result = delist(values)
        return result

    def find_relationships(self, key, value, type_=None, start=None, end=None,
                           bidirectional=False):
        with self.session() as session:
            result = self.do_find_relationships_session(session, key, value,
                                                        type_, start, end,
                                                        bidirectional)
            result = list({Neo4jRelationship.create(x) for x in result})
            return result or ()

    def get_indexed_relationships(self, key, value):
        return self.find_relationships(key, value)

    # index
    
    def create_index(self, obj=None, label=None, key=None):
        label = label or ILabelAdapter(obj)
        assert label, "must provided a node label"
        
        key = key or IUniqueAttributeAdapter(obj).key
        assert key, "must provided a node key"
        
        with self.session() as session:
            query = "CREATE INDEX ON :%s(%s)" % (label, key)
            session.run(query)
            
    def drop_index(self, obj=None, label=None, key=None):
        label = label or ILabelAdapter(obj)
        assert label, "must provided a node label"
        
        key = key or IUniqueAttributeAdapter(obj).key
        assert key, "must provided a node key"
        
        with self.session() as session:
            query = "DROP INDEX ON :%s(%s)" % (label, key)
            session.run(query)
