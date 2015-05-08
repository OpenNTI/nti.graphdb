#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import numbers
import urlparse
#import collections

from zope import component
from zope import interface

from py2neo.neo4j import Node
from py2neo.neo4j import Graph
from py2neo.neo4j import ReadBatch
from py2neo.neo4j import CypherJob
from py2neo.neo4j import WriteBatch
from py2neo.neo4j import authenticate
from py2neo.neo4j import Relationship

from py2neo import node as node4j
from py2neo.error import GraphError

from nti.common.representation import WithRepr

from nti.schema.schema import EqHash

from .node import Neo4jNode
from .relationship import Neo4jRelationship

from ..interfaces import IGraphDB
from ..interfaces import IGraphNode
from ..interfaces import ILabelAdapter
from ..interfaces import IPropertyAdapter
from ..interfaces import IGraphRelationship
from ..interfaces import IUniqueAttributeAdapter

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

	def __init__(self, url, username=None, password=None):
		self.url = url
		self.username = username
		self.password = password

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
					 props=True):
		
		## Get object properties
		properties = dict(properties or {})
		properties.update(IPropertyAdapter(obj))
		
		## Get object labels
		label = label or ILabelAdapter(obj)
		assert label
	
		unique = IUniqueAttributeAdapter(obj, None)
		key = key or (unique.key if unique is not None else None)
		value = value or (unique.value if unique is not None else None)
		
		if key and value is not None:
			result = self.db.merge_one(label, key, value)
			result.properties.update(properties)
			result.push()
			if props:
				self.db.pull(result)
			
		else:
			node = Node(label, **properties)
			result = self.db.create(node)[0]
		return result

	def create_node(self, obj, label=None, properties=None, key=None,
					value=None, raw=False, props=True):
		result = self._create_node(	obj, label=label, properties=properties, 
									key=key, value=value, props=props)
		result = Neo4jNode.create(result) if not raw else result
		return result

	def create_nodes(self, *objs):
		wb = WriteBatch(self.db)
		for o in objs:
			label = ILabelAdapter(o)
			properties = IPropertyAdapter(o)
			adapted = IUniqueAttributeAdapter(o, None)
			if adapted is not None and adapted.key and adapted.value:
				query = _merge_node_query(label, adapted.key, adapted.value)
				wb.append(CypherJob(query))
				if properties:
					query = _set_properties_query(label, adapted.key, adapted.value)
					wb.append(CypherJob(query, parameters={"props":properties}))
			else:
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
				adapted = IUniqueAttributeAdapter(obj, None)
				if adapted is not None:
					label = ILabelAdapter(obj)
					result = self.db.find_one(label, adapted.key, adapted.value)
			if result is not None and props:
				result.pull()
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
			label = ILabelAdapter(o)
			adapted = IUniqueAttributeAdapter(o)
			query = _match_node_query(label, adapted.key, adapted.value)
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

	def update_node(self, obj, labels=_marker, properties=_marker):
		node = self._get_node(obj, props=False)
		if node is not None:
			if properties != _marker:
				node.set_properties(properties)
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
		
		## get all the nodes at once
		rb = ReadBatch(self.db)
		for o in objs:
			label = ILabelAdapter(o)
			adapted = IUniqueAttributeAdapter(o)
			query = _match_node_query(label, adapted.key, adapted.value)
			rb.append(CypherJob(query))

		for node in rb.submit():
			if node is not None:
				nodes.append(node)

		## process all deletions at once
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
		## neo4j nodes
		n4j_end = self.get_or_create_node(end, raw=True, props=False)
		n4j_start = self.get_or_create_node(start, raw=True, props=False)
		
		## properties
		properties = dict(properties or {})
		properties.update(self._rel_properties(start, end, rel_type))
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

	def _match(self, start_node=None, end_node=None, rel_type=None,
				  bidirectional=False, limit=None):
		n4j_end = self._get_node(end_node) if end_node is not None else None
		n4j_start = self._get_node(start_node) if start_node is not None else None
		n4j_type = str(rel_type) if rel_type is not None else None
		result = self.db.match(n4j_start, n4j_type, n4j_end, bidirectional, limit)
		return result

	def match(self, start=None, end=None, rel_type=None, bidirectional=False,
			  limit=None, raw=False):
		result = self._match(start, end, rel_type, bidirectional, limit)
		result = [Neo4jRelationship.create(x) for x in result or ()] \
				 if not raw else result
		return result or ()

# 	
# 	def _get_rel_keyvalue(self, start, end, rel_type, key=None, value=None):
# 		adapted = component.queryMultiAdapter((start, end, rel_type),
# 											  graph_interfaces.IUniqueAttributeAdapter)
# 		if adapted is not None:
# 			key = adapted.key if not key else key
# 			value = adapted.value if value is None else value
# 		return (key, value)
# 

# 
# 	def create_relationships(self, *rels):
# 		wb = neo4j.WriteBatch(self.db)
# 		for rel in rels:
# 			assert isinstance(rel, (tuple, list)) and len(rel) >= 3, 'invalid tuple'
# 
# 			# get relationship type
# 			type_ = rel[1]
# 			assert type_, 'invalid relationship type'
# 			
# 			# get nodes
# 			start = rel[0]  # start node
# 			end = rel[2] # end node
# 			for n in (start, end):
# 				assert isinstance(n, (neo4j.Node, Neo4jNode))
# 			start = start if isinstance(start, neo4j.Node) else start._neo
# 			end = end if isinstance(end, neo4j.Node) else end._neo
# 
# 			# get properties
# 			properties = {} if len(rel) < 4 or rel[3] is None  else rel[3]
# 			assert isinstance(properties, collections.Mapping)
# 
# 			# get key,value
# 			key = None if len(rel) < 5 or rel[4] is None else rel[4]
# 			value = None if len(rel) < 6 or rel[5] is None else rel[5]
# 
# 			abstract = rel4j(start, str(type_), end, **properties)
# 			if key and value:
# 				wb.get_or_create_in_index(neo4j.Relationship,
# 										  "PKIndex",
# 										   key,
# 										   value,
# 										   abstract)
# 			else:
# 				wb.create(abstract)
# 
# 		result = wb.submit()
# 		return result
# 

# 	relationship = get_relationship
# 
# 	def get_indexed_relationship(self, key, value, raw=False, props=True):
# 		result = self.db.get_indexed_relationship("PKIndex", key, value)
# 		if result is not None and props:
# 			result.get_properties()
# 		return 	Neo4jRelationship.create(result) \
# 				if result is not None and not raw else result
# 	

# 		
# 	def delete_relationships(self, *objs):
# 		# collect node4j rels
# 		rels = set([self._do_get_relationship(x, False) for x in objs])
# 		rels.discard(None)
# 
# 		wb = neo4j.WriteBatch(self.db)
# 		for rel in rels:
# 			wb.remove_from_index(neo4j.Relationship, "PKIndex", entity=rel)
# 			wb.delete(rel)
# 		wb.submit()
# 
# 		return True if rels else False
# 
# 	delete_relationship = delete_relationships
# 
# 	def delete_indexed_relationship(self, key, value):
# 		try:
# 			rel = self.db.get_indexed_relationship("PKIndex", key, value)
# 		except GraphError:
# 			rel = None
# 
# 		if rel is not None:
# 			wb = neo4j.WriteBatch(self.db)
# 			wb.remove_from_index(neo4j.Relationship, "PKIndex", entity=rel)
# 			wb.delete(rel)
# 			wb.submit()
# 		return rel
# 
# 	def update_relationship(self, obj, properties=_marker):
# 		rel = self._do_get_relationship(obj)
# 		if rel is not None and properties != _marker:
# 			rel.set_properties(properties)
# 			return True
# 		return False
