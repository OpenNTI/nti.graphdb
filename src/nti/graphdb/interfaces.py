#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import interface

from dolmen.builtins import IDict
from dolmen.builtins import IString

from nti.dataserver_core.interfaces import IExternalService

from nti.schema.field import Bool
from nti.schema.field import Dict
from nti.schema.field import List
from nti.schema.field import Number
from nti.schema.field import Object
from nti.schema.field import Variant
from nti.schema.field import ValidTextLine

NEO4J = u"neo4j"
DATABASE_TYPES = (NEO4J,)

ADD_EVENT = 0
MODIFY_EVENT = 1
REMOVE_EVENT = 2

class IGraphDBQueueFactory(interface.Interface):
	"""
	A factory for graphdb processing queues.
	"""

class IGraphDB(IExternalService):

	def create_node(obj, label=None, properties=None, key=None, value=None):
		pass

	def create_nodes(*objs):
		pass

	def get_node(obj):
		pass

	def get_or_create_node(obj):
		pass

	def get_nodes(*objs):
		pass

	def get_indexed_node(label, key, value):
		pass

	def get_indexed_nodes(tuples):
		pass

	def get_node_properties(obj):
		pass

	def update_node(obj, properties=None):
		pass

	def delete_node(obj):
		pass

	def delete_nodes(*objs):
		pass

	def create_relationship(start, end, rel_type, properties=None, key=None, value=None):
		pass

	def get_relationship(obj):
		pass

	def match(start=None, end=None, rel_type=None, bidirectional=False,
			  limit=None, loose=False):
		pass

	def delete_relationships(*rels):
		pass

	def update_relationship(obj, properties=None):
		pass

	def find_relationships(key, value, rel_type=None, start=None, end=None,
						   bidirectional=False):
		"""
		Find relationships for the specified key and value property
		"""

	def index_relationship(rel, key, value):
		pass

	def get_indexed_relationships(key, value):
		pass

	def unindex_relationship(key, value, rel=None):
		pass

class INode(interface.Interface):
	"""
	Marker interface for a node
	"""

class IGraphNode(INode):
	id = ValidTextLine(title="node id")
	label = ValidTextLine(title="label", required=False)
	uri = ValidTextLine(title="uri identifier", required=False)
	properties = Dict(ValidTextLine(title="The key"),
					  Variant((Number(title="Number value"),
							   Bool(title='Boolean value'),
							   ValidTextLine(title='String value')), title="The value"),
							  required=False,
							  min_length=0)

class IObjectProcessor(interface.Interface):

	def init(db, obj):
		"""
		build relationships for the specified object
		"""

class IRelationshipType(interface.Interface):
	"""
	Marker interface for a relationship type
	"""

	def __str__():
		pass

class IRelationship(interface.Interface):
	"""
	Marker interface for a relationship
	"""

class IGraphRelationship(IRelationship):

	id = ValidTextLine(title="relationship id")

	uri = ValidTextLine(title="uri identifier", required=False)

	type = Variant((Object(IRelationshipType, description="A :class:`.Interface`"),
					ValidTextLine(title='relationship type')),
					title="The relationship type")

	start = Object(INode, title="The start node", required=False)

	end = Object(INode, title="The end node", required=False)

	properties = Dict(ValidTextLine(title="key"),
					  Variant((ValidTextLine(title="value string"),
							   Number(title="value number"),
							   Bool(title="value bool"),
							   List(title="value list"))),
					  required=False)

class IPropertyAdapter(IDict):
	"""
	marker interface for object properties
	"""

class ILabelAdapter(IString):
	"""
	marker interface for an object label
	"""

class IUniqueAttributeAdapter(interface.Interface):
	"""
	Interface to specify the attribute name/value that uniquely identifies an object
	"""
	key = interface.Attribute("Attribute key")
	value = interface.Attribute("Attribute value")

class IFriendOf(IRelationshipType):
	pass

class IMemberOf(IRelationshipType):
	pass

class IFollow(IRelationshipType):
	pass

class IFlagged(IRelationshipType):
	pass

class ICreated(IRelationshipType):
	pass

class ILike(IRelationshipType):
	pass

class IRate(IRelationshipType):
	pass

class IAuthor(IRelationshipType):
	pass

class IShared(IRelationshipType):
	pass

class IIsSharedWith(IRelationshipType):
	pass

class ICommentOn(IRelationshipType):
	pass

class ITaggedTo(IRelationshipType):
	pass

class IView(IRelationshipType):
	pass

class ITakeAssessment(IRelationshipType):
	pass

class IContainer(interface.Interface):
	pass

class IContained(IRelationshipType):
	pass

class IFeedback(IRelationshipType):
	pass

class IAssignmentFeedback(IRelationshipType):
	pass

class IIsReplyOf(IRelationshipType):
	pass

class IReply(IRelationshipType):
	pass

class IParentOf(IRelationshipType):
	pass

class IBelong(IRelationshipType):
	pass

class IEnroll(IRelationshipType):
	pass

class IUnenroll(IRelationshipType):
	pass
