#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=inherit-non-class,expression-not-assigned

from zope import interface

from nti.base.interfaces import IDict
from nti.base.interfaces import IString

from nti.coremetadata.interfaces import IExternalService

from nti.schema.field import Bool
from nti.schema.field import Dict
from nti.schema.field import List
from nti.schema.field import Number
from nti.schema.field import Object
from nti.schema.field import Variant
from nti.schema.field import DecodingValidTextLine as ValidTextLine

#: Add event code
ADD_EVENT = 0

#: Modify event code
MODIFY_EVENT = 1

#: Remove event code
REMOVE_EVENT = 2


class IGraphDBQueueFactory(interface.Interface):
    """
    A factory for graphdb processing queues.
    """


class IGraphDB(IExternalService):

    def create_node(obj, label=None, key=None, value=None, properties=None):
        """
        Create a graph node for the specified object
        
        :param object obj: Object to create the node for
        :param str label: Optional object label
        :param str key: Optional object [primary] key name
        :param str value: Optional object [primary] key value
        :param dict properties: Optional node properties
        """
        pass

    def create_nodes(*objs):
        """
        Create nodes for the specified objects
        """
        pass
 
    def get_node(obj):
        """
        Return the graph node for the specified object
        """

    def get_or_create_node(obj):
        """
        Get or create a node for the specified object
        """
 
    def get_nodes(*objs):
        """
        Return the nodes for the specified objects
        """

# 
#     def get_indexed_node(label, key, value):
#         pass
# 
#     def get_indexed_nodes(tuples):
#         pass
# 
#     def get_node_properties(obj):
#         pass
# 
#     def update_node(obj, properties=None):
#         pass
# 
#     def delete_node(obj):
#         pass
# 
#     def delete_nodes(*objs):
#         pass
# 
#     def create_relationship(start, end, rel_type, properties=None, key=None, value=None):
#         pass
# 
#     def get_relationship(obj):
#         pass
# 
#     def match(start=None, end=None, rel_type=None, bidirectional=False,
#               limit=None, loose=False):
#         pass
# 
#     def delete_relationships(*rels):
#         pass
# 
#     def update_relationship(obj, properties=None):
#         pass
# 
#     def find_relationships(key, value, rel_type=None, start=None, end=None,
#                            bidirectional=False):
#         """
#         Find relationships for the specified key and value property
#         """
# 
#     def index_relationship(rel, key, value):
#         pass
# 
#     def get_indexed_relationships(key, value):
#         pass
# 
#     def unindex_relationship(key, value, rel=None):
#         pass


class INode(interface.Interface):
    """
    Marker interface for a node
    """


class IGraphNode(INode):
    id = ValidTextLine(title=u"node id")

    label = ValidTextLine(title=u"label", required=False)

    properties = Dict(ValidTextLine(title=u"The key"),
                      Variant((Number(title=u"The Number"),
                               Bool(title=u'The Boolean'),
                               ValidTextLine(title=u'The String value')), 
                               title=u"The value"),
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

    id = ValidTextLine(title=u"relationship id")

    type = Variant((Object(IRelationshipType),
                    ValidTextLine(title=u'relationship type')),
                   title=u"The relationship type")

    start = Object(INode, title=u"The start node", required=False)

    end = Object(INode, title=u"The end node", required=False)

    properties = Dict(ValidTextLine(title=u"The key"),
                      Variant((ValidTextLine(title=u"The string"),
                               Number(title=u"The number"),
                               Bool(title=u"The bool"),
                               List(title=u"The list"))),
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


class IContainer(interface.Interface):
    pass


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


class IViewed(IRelationshipType):
    pass


class ITakenAssessment(IRelationshipType):
    pass


class ITakenInquiry(IRelationshipType):
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


class IBought(IRelationshipType):
    pass
