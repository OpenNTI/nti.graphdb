#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import six
import numbers
import urlparse
import ConfigParser
from collections import Mapping

from py2neo.neo4j import Node
from py2neo.neo4j import Graph
from py2neo.neo4j import ReadBatch
from py2neo.neo4j import CypherJob
from py2neo.neo4j import WriteBatch
from py2neo.neo4j import authenticate
from py2neo.neo4j import Relationship

from py2neo import node as node4j
from py2neo.error import GraphError

from zope import component
from zope import interface

from nti.common.representation import WithRepr

from nti.schema.schema import EqHash

from ..common import get_node_pk

from ..interfaces import IGraphDB
from ..interfaces import IGraphNode
from ..interfaces import ILabelAdapter
from ..interfaces import IPropertyAdapter
from ..interfaces import IGraphRelationship

from .node import Neo4jNode

from .relationship import Neo4jRelationship

from .interfaces import INeo4jNode
from .interfaces import IGraphNodeNeo4j

def _is_404(ex):
	response = getattr(ex, 'response', None)
	return getattr(response, 'status_code', None) == 404

def _merge_node_query(label, key, value):
	result = "MERGE (n:%s { %s:'%s' }) RETURN n" % (label, key, value)
	return result

def _set_properties_query(label, key, value):
	result = """
	MATCH (n:%s { %s:'%s' }) SET n += { props }
	""" % (label, key, value)
	return result.strip()

def _match_node_query(label, key, value):
	result = "MATCH (n:%s { %s:'%s' }) RETURN n" % (label, key, value)
	return result.strip()

def _merge_rel_query(start_id, end_id, rel_type, bidirectional=False):
	direction = '-' if bidirectional else '->'
	result = """
	MATCH (a)
	WHERE id(a)=%s
	MATCH (b)
	WHERE id(b)=%s
	MERGE r=(a)-[:%s]%s(b)
	RETURN r""" % (start_id, end_id, rel_type, direction)
	return result.strip()

def _match_rel_query(key, value, rel_type=None, start_id=None, end_id=None,
					 bidirectional=False):
	result = ""
	direction = '-' if bidirectional else '->'
	if start_id is not None:
		result += "MATCH (a) WHERE id(a)=%s " % start_id
	if end_id is not None:
		result += "MATCH (b) WHERE id(b)=%s " % end_id
	if rel_type:
		result += "MATCH p=(a)-[:%s {%s:%s}]%s(b) RETURN p" % (rel_type, key, value, direction)
	else:
		result += "MATCH p=(a)-[ {%s:%s}]%s(b) RETURN p" % (key, value, direction)
	return result

def _isolate(self, node):
	query = "START a=node(%s) MATCH a-[r]-b DELETE r" % node._id
	self.append(CypherJob(query))
WriteBatch.isolate = _isolate

_marker = object()

@WithRepr
@EqHash('url')
@interface.implementer(IGraphDB)
class Neo4jDB(object):

	_v_db__ = None

	def __init__(self, url=None, username=None, password=None, config=None):
		self.url = url
		self.username = username
		self.password = password
		if config:
			config_name = os.path.expandvars(config)
			parser = ConfigParser.ConfigParser()
			parser.read([config_name])
			if parser.has_option('graphdb', 'url'):
				self.url = parser.get('graphdb', 'url')
			if parser.has_option('graphdb', 'username'):
				self.username = parser.getboolean('graphdb', 'username')
			if parser.has_option('graphdb', 'password'):
				self.password = parser.getboolean('graphdb', 'password')

	@classmethod
	def authenticate(cls, url, username, password):
		o = urlparse.urlparse(url)
		authenticate(o.netloc, username, password)

	@property
	def db(self):
		if self._v_db__ is None:
			if self.username and self.password:
				self.authenticate(self.url, self.username, self.password)
			self._v_db__ = Graph(self.url)
		return self._v_db__

	def _reinit(self):
		self._v_db__ = None

	def _create_node(self, obj, key=None, value=None, label=None, properties=None,
					 props=False):

		# Get object properties
		properties = dict(properties or {})
		properties.update(IPropertyAdapter(obj))

		# Get object labels
		label = label or ILabelAdapter(obj)
		assert label, "must provide an object label"

		pk = get_node_pk(obj)
		if pk is not None:
			result = self.db.merge_one(label, pk.key, pk.value)
			result.properties.update(properties)
			result.push()
			if props:  # refresh
				self.db.pull(result)
		else:
			node = Node(label, **properties)
			result = self.db.create(node)[0]
		return result

	def create_node(self, obj, label=None, properties=None, key=None,
					value=None, raw=False, props=True):
		result = self._create_node(obj, label=label, properties=properties,
									key=key, value=value, props=props)
		result = Neo4jNode.create(result) if not raw else result
		return result

	def create_nodes(self, *objs):
		wb = WriteBatch(self.db)
		for o in objs:
			pk = get_node_pk(o)
			properties = IPropertyAdapter(o)
			if pk is not None:
				query = _merge_node_query(pk.label, pk.key, pk.value)
				wb.append(CypherJob(query))
				if properties:
					query = _set_properties_query(pk.label, pk.key, pk.value)
					wb.append(CypherJob(query, parameters={"props":properties}))
			else:
				label = ILabelAdapter(o)
				abstract = node4j(label, **properties)
				wb.create(abstract)
		result = []
		created = wb.submit()
		for n in created:
			if n is not None and isinstance(n, Node):
				result.append(Neo4jNode.create(n))
		return result

	def _get_node(self, obj, props=True):
		result = None
		__traceback_info__ = obj, props
		try:
			if isinstance(obj, Node):
				result = obj
			elif isinstance(obj, (six.string_types, numbers.Number)):
				result = self.db.node(str(obj))
			elif isinstance(obj, Neo4jNode) and obj.neo is not None:
				result = obj.neo
			elif IGraphNode.providedBy(obj):
				result = self.db.node(obj.id)
			elif obj is not None:
				pk = get_node_pk(obj)
				if pk is not None:
					result = self.db.find_one(pk.label, pk.key, pk.value)
					props = False  # # no need to refresh
			if result is not None and props:
				self.db.pull(result)
		except GraphError as e:
			if not _is_404(e):
				raise e
			result = None
		return result

	def get_node(self, obj, raw=False, props=True):
		result = self._get_node(obj, props=props)
		result = Neo4jNode.create(result) if result is not None and not raw else result
		return result

	node = get_node

	def get_or_create_node(self, obj, raw=False, props=True):
		result = self.get_node(obj, raw=raw, props=props) or \
 				 self.create_node(obj, raw=raw, props=props)
		return result

	def get_nodes(self, *objs):
		nodes = []
		rb = ReadBatch(self.db)
		for o in objs:
			pk = get_node_pk(o)
			query = _match_node_query(pk.label, pk.key, pk.value)
			rb.append(CypherJob(query))

		for result in rb.submit():
			if result is not None:
				nodes.append(Neo4jNode.create(result))
			else:
				nodes.append(None)
		return nodes

	def get_indexed_node(self, label, key, value, raw=False, props=True):
		__traceback_info__ = label, key, value
		result = self.db.find_one(label, key, value)
		if props and result is not None:
			result.pull()
		result = Neo4jNode.create(result) if result is not None and not raw else result
		return result

	def get_indexed_nodes(self, *tuples):
		rb = ReadBatch(self.db)
		for label, key, value in tuples:
			query = _match_node_query(label, key, value)
			rb.append(CypherJob(query))

		nodes = []
		for node in rb.submit():
			if node is not None:
				nodes.append(node)
		return nodes

	def update_node(self, obj, properties=_marker):
		node = self._get_node(obj, props=False)
		if node is not None and properties != _marker:
			node.properties.update(properties)
			node.push()
			return True
		return False

	def _delete_node(self, obj):
		node = self._get_node(obj, props=False)
		if node is not None:
			wb = WriteBatch(self.db)
			wb.isolate(node)
			wb.delete(node)
			responses = wb.submit()
			return responses[1] is None
		return False

	def delete_node(self, obj):
		result = self._delete_node(obj)
		return result

	def delete_nodes(self, *objs):
		nodes = []

		# get all the nodes at once
		rb = ReadBatch(self.db)
		for o in objs:
			pk = get_node_pk(o)
			query = _match_node_query(pk.label, pk.key, pk.value)
			rb.append(CypherJob(query))

		for node in rb.submit():
			if node is not None:
				nodes.append(node)

		# process all deletions at once
		wb = WriteBatch(self.db)
		for node in nodes:
			wb.isolate(node)
			wb.delete(node)

		result = 0
		responses = wb.submit()
		for idx in range(1, len(responses), 2):
			if responses[idx] is None:
				result += 1
		return result

	# relationships

	@classmethod
	def _rel_properties(cls, start, end, rel_type):
		result = component.queryMultiAdapter((start, end, rel_type), IPropertyAdapter)
		return result or {}

	def _create_relationship(self, start, end, rel_type, properties=None, unique=True):
		# neo4j nodes
		n4j_end = self.get_or_create_node(end, raw=True, props=False)
		n4j_start = self.get_or_create_node(start, raw=True, props=False)

		# properties
		props = dict(self._rel_properties(start, end, rel_type))
		props.update(properties or {})
		properties = props
		if unique:
			result = Relationship(n4j_start, str(rel_type), n4j_end, **properties)
			result = self.db.create_unique(result)[0]
		else:
			result = Relationship(n4j_start, str(rel_type), n4j_end, **properties)
			result = self.db.create(result)[0]
		return result

	def create_relationship(self, start, end, rel_type, properties=None,
							unique=True, raw=False):
		result = self._create_relationship(start, end, rel_type, properties, unique=unique)
		result = Neo4jRelationship.create(result) if not raw else result
		return result

	def _get_relationship(self, obj, props=True):
		result = None
		try:
			if isinstance(obj, Relationship):
				result = obj
			elif isinstance(obj, (six.string_types, numbers.Number)):
				result = self.db.relationship(str(obj))
			elif isinstance(obj, Neo4jRelationship) and obj.neo is not None:
				result = obj.neo
			elif IGraphRelationship.providedBy(obj):
				result = self.db.relationship(obj.id)
			if result is not None and props:
				result.pull()
		except GraphError as e:
			if not _is_404(e):
				raise e
			result = None
		return result

	def get_relationship(self, obj, raw=False):
		result = self._get_relationship(obj)
		result = Neo4jRelationship.create(result) \
				 if result is not None and not raw else result
		return result

	relationship = get_relationship

	def _match(self, start_node=None, end_node=None, rel_type=None,
				  bidirectional=False, limit=None, loose=False):
		n4j_type = str(rel_type) if rel_type is not None else None
		n4j_end = self._get_node(end_node, False) if end_node is not None else None
		n4j_start = self._get_node(start_node, False) if start_node is not None else None
		if not loose and (n4j_type is None or n4j_start is None or n4j_end is None):
			result = ()
		else:
			result = self.db.match(n4j_start, n4j_type, n4j_end, bidirectional, limit)
		return result

	def match(self, start=None, end=None, rel_type=None, bidirectional=False,
			  limit=None, raw=False, loose=False):
		result = self._match(start_node=start,
							 end_node=end,
							 rel_type=rel_type,
							 bidirectional=bidirectional,
							 limit=limit,
							 loose=loose)
		result = [Neo4jRelationship.create(x) for x in result or ()] \
				 if not raw else result
		return result or ()

	def create_relationships(self, *rels):
		wb = WriteBatch(self.db)
		for rel in rels:
			assert isinstance(rel, (tuple, list)) and len(rel) >= 3, 'invalid tuple'

			# get relationship type
			rel_type = rel[1]
			assert rel_type, 'invalid relationship type'

			# get nodes
			end = rel[2]  # end node
			start = rel[0]  # start node
			for n in (start, end):
				assert INeo4jNode.providedBy(n) or IGraphNodeNeo4j.providedBy(n)

			end = end if INeo4jNode.providedBy(end) else end.neo
			start = start if INeo4jNode.providedBy(start) else start.neo

			# get properties
			properties = {} if len(rel) < 4 or rel[3] is None  else rel[3]
			assert isinstance(properties, Mapping)

			# get unique
			unique = False if len(rel) < 5 or rel[4] is None else rel[4]
			if not unique:
				rel = Relationship(start, str(rel_type), end, **properties)
				wb.create(rel)
			else:
				query = _merge_rel_query(start._id, end._id, rel_type)
				wb.append(CypherJob(query))  # Parameter maps cannot be used in MERGE patterns

		result = wb.submit()
		return result

	def delete_relationships(self, *objs):
		# collect node4j rels
		rels = [self._get_relationship(x, False) for x in objs]

		wb = WriteBatch(self.db)
		for rel in rels:
			if rel is not None:
				wb.delete(rel)
		wb.submit()

		result = True if rels else False
		return result

	delete_relationship = delete_relationships

	def update_relationship(self, obj, properties=_marker):
		rel = self._get_relationship(obj)
		if rel is not None and properties != _marker:
			rel.properties.update(properties)
			rel.push()
			return True
		return False

	def _find_relationships(self, key, value, rel_type=None, start=None, end=None,
							bidirectional=False):
		# get nodes
		n4j_type = str(rel_type) if rel_type is not None else None
		n4j_end = self._get_node(end, False) if end is not None else None
		n4j_start = self._get_node(start, False) if start is not None else None
		
		if isinstance(value, six.string_types):
			value = value if value.endswith("'") else "%s'" % value
			value = value if value.startswith("'") else "'%s" % value

		n4j_end = getattr(n4j_end, '_id', None)
		n4j_start = getattr(n4j_start, '_id', None)
		
		# construct query
		result = []
		query = _match_rel_query(key, value, 
								 rel_type=n4j_type, 
								 start_id=n4j_start, 
								 end_id=n4j_end, 
								 bidirectional=bidirectional)
		records = self.db.cypher.execute(query)
		for record in records:
			rel = record.p.relationships[0] # p is the path returned
			result.append(rel)
		return result

	def find_relationships(self, key, value, rel_type=None, start=None, end=None,
						   bidirectional=False, raw=False):
		result = self._find_relationships(key, value, rel_type=rel_type, start=start, 
										  end=start, bidirectional=bidirectional)
		result = [Neo4jRelationship.create(x) for x in result] \
				 if not raw else result
		return result
	
	# index

	def _get_or_create_index(self, abstract=Relationship, name="PKIndex"):
		return self.db.legacy.get_or_create_index(abstract, name)

	def _index_entity(self, key, value, entity, abstract=Relationship):
		if entity is not None:
			index = self._get_or_create_index(abstract=abstract)
			index.add(key, value, entity)
			return True
		return False

	def index_relationship(self, rel, key, value):
		rel = self._get_relationship(rel, False)
		result = self._index_entity(key, value, rel)
		return result

	def get_indexed_relationships(self, key, value, raw=False):
		index = self._get_or_create_index()
		result = index.get(key, value)
		result = [Neo4jRelationship.create(x) for x in result or ()] \
				  if not raw else result
		return result

	def unindex_relationship(self, key, value, rel=None):
		rel = self._get_relationship(rel, False) if rel is not None else None
		index = self._get_or_create_index()
		result = index.remove(key, value, rel)
		return result
