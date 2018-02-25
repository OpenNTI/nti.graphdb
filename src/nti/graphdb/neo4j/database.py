#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six
import numbers

from zope import interface

from neo4j.v1 import GraphDatabase

from nti.graphdb.common import get_node_pk, NodePK

from nti.graphdb.interfaces import IGraphDB
# from nti.graphdb.interfaces import IGraphNode
from nti.graphdb.interfaces import ILabelAdapter
from nti.graphdb.interfaces import IPropertyAdapter
# from nti.graphdb.interfaces import IGraphRelationship

# from nti.graphdb.neo4j.interfaces import INeo4jNode
# from nti.graphdb.neo4j.interfaces import IGraphNodeNeo4j
# from nti.graphdb.neo4j.interfaces import INeo4jRelationship
#
from nti.graphdb.neo4j.node import Neo4jNode

# from nti.graphdb.neo4j.relationship import Neo4jRelationship

from nti.externalization.representation import WithRepr

from nti.schema.eqhash import EqHash

_marker = object()

logger = __import__('logging').getLogger(__name__)


# def _is_404(ex):
#     response = getattr(ex, 'response', None)
#     return getattr(response, 'status_code', None) == 404
#
def merge_node_query(label, key, value):
    result = "MERGE (n:%s { %s:'%s' }" % (label, key, value)
    return result


def process_properties(properties):
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
    result = ["MATCH (n:%s { %s:'%s' })" % (label, key, value)]
    result.append(" SET n += {")
    props = process_properties(properties)
    result.append(','.join(props))
    result.append('} RETURN n')
    return ''.join(result)


def create_node_query(label, properties):
    result = ["CREATE (n:%s)" % label]
    props = process_properties(properties)
    if props:
        result.append(" { ")
        result.append(','.join(props))
        result.append(" }")
    result.append(" RETURN n")
    return ''.join(result)


def match_node_query(label, key, value):
    result = "MATCH (n:%s { %s:'%s' }) RETURN n" % (label, key, value)
    return result
#
# def _create_unique_rel_query(start_id, end_id, rel_type, bidirectional=False):
#     direction = '-' if bidirectional else '->'
#     result = """
#     MATCH (a)
#     WHERE id(a)=%s
#     MATCH (b)
#     WHERE id(b)=%s
#     CREATE UNIQUE (a)-[r:%s]%s(b)
#     RETURN r""" % (start_id, end_id, rel_type, direction)
#     return result.strip()
#
# def _merge_rel_query(start_id, end_id, rel_type, bidirectional=False):
#     direction = '-' if bidirectional else '->'
#     result = """
#     MATCH (a)
#     WHERE id(a)=%s
#     MATCH (b)
#     WHERE id(b)=%s
#     MERGE r=(a)-[:%s]%s(b)
#     RETURN r""" % (start_id, end_id, rel_type, direction)
#     return result.strip()
#
# def _match_rel_query(key, value, rel_type=None, start_id=None, end_id=None, bidirectional=False):
#     direction = '-' if bidirectional else '->'
#     if start_id is not None:
#         result = "MATCH (a) WHERE id(a)=%s " % start_id
#     if end_id is not None:
#         result = "MATCH (b) WHERE id(b)=%s " % end_id
#     if rel_type:
#         result = "MATCH p=(a)-[:%s {%s:%s}]%s(b) RETURN p" % (rel_type, key, value, direction)
#     else:
#         result = "MATCH p=(a)-[ {%s:%s}]%s(b) RETURN p" % (key, value, direction)
#     return result
#
# def _isolate(self, node):
#     remote_node = remote(node) or node
#     query = "START a=node(%s) MATCH (a)-[r]-(b) DELETE r" % remote_node._id
#     self.append(CypherJob(query))
# WriteBatch.isolate = _isolate


@WithRepr
@EqHash('url')
@interface.implementer(IGraphDB)
class Neo4jDB(object):

    _v_graph = None

    def __init__(self, url=None, username=None, password=None):
        self.url = url
        self.username = username
        self.password = password

    @property
    def graph(self):
        if self._v_graph is None:
            if self.username and self.password:
                self._v_graph = GraphDatabase.driver(
                    self.url,
                    auth=(self.username, self.password)
                )
            else:
                self._v_graph = GraphDatabase.driver(self.url)
        return self._v_graph
    db = graph

    def _reinit(self):
        self._v_graph = None

    def session(self):
        return self.db.session()

    def _create_unique_node(self, label, key, value, properties=None):
        # prepare query
        properties = dict(properties or {})
        query = merge_node_query(label, key, value)
        with self.session() as s:
            result = s.run(query)
            if properties:
                query = set_node_properties_query(label, key, value, properties)
                result = s.run(query)
        return result

    def _create_node(self, obj, label=None, key=None, value=None, properties=None):
        # get object properties
        properties = dict(properties or {})
        properties.update(IPropertyAdapter(obj))
        # get object labels
        label = label or ILabelAdapter(obj)
        assert label, "must provide an object label"
        # get primary key
        if key and value:
            pk = NodePK(label, key, value)
        else:
            pk = get_node_pk(obj)
        if pk is not None:
            result = self._create_unique_node(pk.label, pk.key, pk.value, properties)
        else:
            query = create_node_query(label, **properties)
            with self.session() as s:
                result = s.run(query)
        return result

    def create_node(self, obj, label=None, key=None, value=None, properties=None, raw=False):
        result = self._create_node(obj, label, key, value, properties)
        result = Neo4jNode.create(result) if not raw else result
        return result
#
#     def create_nodes(self, *objs):
#         wb = WriteBatch(self.graph)
#         for o in objs:
#             pk = get_node_pk(o)
#             properties = IPropertyAdapter(o)
#             if pk is not None:
#                 query = _merge_node_query(pk.label, pk.key, pk.value)
#                 wb.append(CypherJob(query))
#                 if properties:
#                     query = _set_properties_query(pk.label, pk.key, pk.value)
#                     wb.append(CypherJob(query, parameters={"props":properties}))
#             else:
#                 label = ILabelAdapter(o)
#                 abstract = Node(label, **properties)
#                 wb.create(abstract)
#         result = []
#         for n in wb.run():
#             if n is not None and isinstance(n, Node):
#                 result.append(Neo4jNode.create(n))
#         return result
#
#     def _get_node(self, obj, props=True):
#         result = None
#         __traceback_info__ = obj, props
#         try:
#             if isinstance(obj, Node):
#                 result = obj
#             elif isinstance(obj, (six.string_types, numbers.Number)):
#                 result = self.graph.node(str(obj))
#             elif isinstance(obj, Neo4jNode) and obj.neo is not None:
#                 result = obj.neo
#             elif IGraphNode.providedBy(obj):
#                 result = self.graph.node(obj.id)
#             elif obj is not None:
#                 pk = get_node_pk(obj)
#                 if pk is not None:
#                     result = self.graph.find_one(pk.label, pk.key, pk.value)
#                     props = False  # no need to refresh
#             if result is not None and props:
#                 self.graph.pull(result)
#         except GraphError as e:
#             if not _is_404(e):
#                 raise e
#             result = None
#         return result
#
#     def get_node(self, obj, raw=False, props=True):
#         result = self._get_node(obj, props=props)
#         result = Neo4jNode.create(result) if result is not None and not raw else result
#         return result
#
#     node = get_node
#
#     def get_or_create_node(self, obj, raw=False, props=True):
#         result =     self.get_node(obj, raw=raw, props=props) \
#                  or    self.create_node(obj, raw=raw, props=props)
#         return result
#
#     def _run_read_batch(self, rb):
#         modified = False
#         if not hasattr(rb.graph, 'batch'):
#             modified = True
#             rb.graph.batch = rb.runner
#         try:
#             return rb.run()
#         finally:
#             if modified:
#                 del rb.graph.batch
#
#     def get_nodes(self, *objs):
#         nodes = []
#         rb = ReadBatch(self.graph)
#         for o in objs:
#             pk = get_node_pk(o)
#             query = _match_node_query(pk.label, pk.key, pk.value)
#             rb.append(CypherJob(query))
#
#         for result in self._run_read_batch(rb):
#             if result is not None:
#                 nodes.append(Neo4jNode.create(result))
#             else:
#                 nodes.append(None)
#         return nodes
#
#     def get_indexed_node(self, label, key, value, raw=False, props=True):
#         __traceback_info__ = label, key, value
#         result = self.graph.find_one(label, key, value)
#         if props and result is not None:
#             self.graph.pull(result)
#         result = Neo4jNode.create(result) if result is not None and not raw else result
#         return result
#
#     def get_indexed_nodes(self, *tuples):
#         rb = ReadBatch(self.graph)
#         for label, key, value in tuples:
#             query = _match_node_query(label, key, value)
#             rb.append(CypherJob(query))
#
#         nodes = []
#         for node in self._run_read_batch(rb):
#             if node is not None:
#                 nodes.append(node)
#         return nodes
#
#     def update_node(self, obj, properties=_marker):
#         node = self._get_node(obj, props=False)
#         if node is not None and properties != _marker:
#             node.update(properties)
#             self.graph.push(node)
#             return True
#         return False
#
#     def _delete_node(self, obj):
#         node = self._get_node(obj, props=False)
#         if node is not None:
#             wb = WriteBatch(self.graph)
#             wb.isolate(node)
#             wb.delete(node)
#             responses = wb.run()
#             return responses[1] is None
#         return False
#
#     def delete_node(self, obj):
#         result = self._delete_node(obj)
#         return result
#
#     def delete_nodes(self, *objs):
#         nodes = []
#         # get all the nodes at once
#         rb = ReadBatch(self.graph)
#         for o in objs:
#             pk = get_node_pk(o)
#             query = _match_node_query(pk.label, pk.key, pk.value)
#             rb.append(CypherJob(query))
#
#         for node in self._run_read_batch(rb):
#             if node is not None:
#                 nodes.append(node)
#
#         # process all deletions at once
#         wb = WriteBatch(self.graph)
#         for node in nodes:
#             wb.isolate(node)
#             wb.delete(node)
#
#         result = 0
#         responses = wb.run()
#         for idx in range(1, len(responses), 2):
#             if responses[idx] is None:
#                 result += 1
#         return result
#
#     # relationships
#
#     @classmethod
#     def _rel_properties(cls, start, end, rel_type):
#         result = component.queryMultiAdapter((start, end, rel_type), IPropertyAdapter)
#         return result or {}
#
#     def _create_unique_relationship(self, start, end, rel_type, properties=None,
#                                     bidirectional=False):
#         # prepare query
#         end = remote(end) or end
#         start = remote(start) or start
#         query = _create_unique_rel_query(start._id, end._id, rel_type, bidirectional)
#         # run cyper query
#         wb = WriteBatch(self.graph)
#         wb.append(CypherJob(query))
#         relationship = wb.run()[0]
#         relationship = relationship if isinstance(relationship, Relationship) else None
#         # update properties
#         if relationship is not None and properties:
#             relationship.update(properties)
#             self.graph.push(relationship)
#         return relationship
#
#     def _create_relationship(self, start, end, rel_type, properties=None, unique=True):
#         # get or create nodes
#         n4j_end = self.get_or_create_node(end, raw=True, props=False)
#         n4j_start = self.get_or_create_node(start, raw=True, props=False)
#         # capture properties
#         props = dict(self._rel_properties(start, end, rel_type))
#         props.update(properties or {})
#         properties = props
#         # create
#         if unique:
#             result = self._create_unique_relationship(n4j_start,
#                                                       n4j_end,
#                                                       str(rel_type),
#                                                       properties)
#         else:
#             result = Relationship(n4j_start, str(rel_type), n4j_end, **properties)
#             self.graph.create(result)
#         return result
#
#     def create_relationship(self, start, end, rel_type, properties=None,
#                             unique=True, raw=False):
#         result = self._create_relationship(start, end, rel_type, properties, unique=unique)
#         result = Neo4jRelationship.create(result) if not raw else result
#         return result
#
#     def _get_relationship(self, obj, props=True):
#         result = None
#         try:
#             if isinstance(obj, Relationship):
#                 result = obj
#             elif isinstance(obj, (six.string_types, numbers.Number)):
#                 result = self.graph.relationship(str(obj))
#             elif isinstance(obj, Neo4jRelationship) and obj.neo is not None:
#                 result = obj.neo
#             elif IGraphRelationship.providedBy(obj):
#                 result = self.graph.relationship(obj.id)
#             if result is not None and props:
#                 self.graph.pull(result)
#         except GraphError as e:
#             if not _is_404(e):
#                 raise e
#             result = None
#         return result
#
#     def get_relationship(self, obj, raw=False):
#         result = self._get_relationship(obj)
#         result = Neo4jRelationship.create(result) if result is not None and not raw else result
#         return result
#
#     relationship = get_relationship
#
#     def _match(self, start_node=None, end_node=None, rel_type=None,
#                bidirectional=False, limit=None, loose=False):
#         n4j_type = str(rel_type) if rel_type is not None else None
#         n4j_end = self._get_node(end_node, False) if end_node is not None else None
#         n4j_start = self._get_node(start_node, False) if start_node is not None else None
#         if not loose and (n4j_type is None or n4j_start is None or n4j_end is None):
#             result = ()
#         else:
#             result = self.graph.match(n4j_start, n4j_type, n4j_end, bidirectional, limit)
#         return result
#
#     def match(self, start=None, end=None, rel_type=None, bidirectional=False,
#               limit=None, raw=False, loose=False):
#         result = self._match(start_node=start,
#                              end_node=end,
#                              rel_type=rel_type,
#                              bidirectional=bidirectional,
#                              limit=limit,
#                              loose=loose)
#         result = [Neo4jRelationship.create(x) for x in result or ()] if not raw else result
#         return result or ()
#
#     def create_relationships(self, *rels):
#         wb = WriteBatch(self.graph)
#         for rel in rels:
#             assert isinstance(rel, (tuple, list)) and len(rel) >= 3, 'Invalid tuple'
#
#             # get relationship type
#             rel_type = rel[1]
#             assert rel_type, 'Invalid relationship type'
#
#             # get nodes
#             end = rel[2]  # end node
#             start = rel[0]  # start node
#             for n in (start, end):
#                 assert INeo4jNode.providedBy(n) or IGraphNodeNeo4j.providedBy(n)
#
#             end = end if INeo4jNode.providedBy(end) else end.neo
#             start = start if INeo4jNode.providedBy(start) else start.neo
#
#             # get properties
#             properties = {} if len(rel) < 4 or rel[3] is None  else rel[3]
#             assert isinstance(properties, Mapping)
#
#             # get unique
#             unique = False if len(rel) < 5 or rel[4] is None else rel[4]
#             if not unique:
#                 rel = Relationship(start, str(rel_type), end, **properties)
#                 wb.create(rel)
#             else:
#                 end = remote(end) or end
#                 start = remote(start) or start
#                 query = _merge_rel_query(start._id, end._id, rel_type)
#                 wb.append(CypherJob(query))  # Parameter maps cannot be used in MERGE patterns
#
#         result = wb.run()
#         return result
#
#     def delete_relationships(self, *objs):
#         # collect node4j rels
#         rels = [self._get_relationship(x, False) for x in objs]
#         # prepare and execute
#         wb = WriteBatch(self.graph)
#         for rel in rels:
#             if rel is not None:
#                 wb.delete(rel)
#         deleted = wb.run()
#         result = bool(deleted)
#         return result
#
#     delete_relationship = delete_relationships
#
#     def update_relationship(self, obj, properties=_marker):
#         rel = self._get_relationship(obj)
#         if rel is not None and properties != _marker:
#             rel.update(properties)
#             self.graph.push(rel)
#             return True
#         return False
#
#     def _find_relationships(self, key, value, rel_type=None, start=None, end=None,
#                             bidirectional=False):
#         # get nodes
#         n4j_type = str(rel_type) if rel_type is not None else None
#         n4j_end = self._get_node(end, False) if end is not None else None
#         n4j_start = self._get_node(start, False) if start is not None else None
#
#         if isinstance(value, six.string_types):
#             value = value if value.endswith("'") else "%s'" % value
#             value = value if value.startswith("'") else "'%s" % value
#
#         # get remote node ids
#         n4j_end = remote(n4j_end) if n4j_end is not None else n4j_end
#         n4j_start = remote(n4j_start) if n4j_start is not None else n4j_start
#         n4j_end = getattr(n4j_end, '_id', None)
#         n4j_start = getattr(n4j_start, '_id', None)
#
#         # construct query
#         result = []
#         query = _match_rel_query(key, value,
#                                  rel_type=n4j_type,
#                                  start_id=n4j_start,
#                                  end_id=n4j_end,
#                                  bidirectional=bidirectional)
#         records = self.graph.evaluate(query)
#         for record in records or ():
#             if INeo4jRelationship.providedBy(record):
#                 result.append(record)
#         return result
#
#     def find_relationships(self, key, value, rel_type=None, start=None, end=None,
#                            bidirectional=False, raw=False):
#         result = self._find_relationships(key, value, rel_type=rel_type, start=start,
#                                           end=start, bidirectional=bidirectional)
#         result = [Neo4jRelationship.create(x) for x in result] if not raw else result
#         return result
#
#     # index
#
#     def _get_or_create_index(self, name="PKIndex", content_type=Relationship):
#         return self.index_manager.get_or_create_index(Relationship, name)
#
#     def _index_entity(self, key, value, entity, content_type=Relationship):
#         if entity is not None:
#             index = self._get_or_create_index(content_type=content_type)
#             index.add(key, value, entity)
#             return True
#         return False
#
#     def index_relationship(self, rel, key, value):
#         rel = self._get_relationship(rel, False)
#         result = self._index_entity(key, value, rel)
#         return result
#
#     def get_indexed_relationships(self, key, value, raw=False):
#         index = self._get_or_create_index()
#         result = index.get(key, value)
#         result = [Neo4jRelationship.create(x) for x in result or ()] if not raw else result
#         return result
#
#     def unindex_relationship(self, key, value, rel=None):
#         rel = self._get_relationship(rel, False) if rel is not None else None
#         index = self._get_or_create_index()
#         result = index.remove(key, value, rel)
#         return result
