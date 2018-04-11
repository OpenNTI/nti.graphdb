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

    def get_indexed_node(label, key, value):
        """
        Return a graph node for the specified values

        :param str label: Node label
        :param str key: Node [primary] key name
        :param str value: Node [primary] key value
        """

    def get_indexed_nodes(*tuples):
        """
        Return the nodes for the specified data 3-value tuples
        """

    def update_node(obj, properties=None):
        """
        Update the node for specified object
        """

    def delete_node(obj):
        """
        Delete the node for specified object
        """

    def delete_nodes(*objs):
        """
        Delete the nodes for specified objects
        """

    def create_relationship(start, end, type_, properties=None,
                            unique=True, bidirectional=False):
        """
        Create a node relationship
        
        :param start: Starting object
        :param end: Ending object
        :param type_: Relationship type
        :param dict properties: Optional relationship properties
        :param bool unique: Create a unique relationship
        :param bool bidirectional: Create a bidirectional relationship
        """

    def get_relationship(obj):
        """
        Return a relationship for the specified object
        """

    def match(start, end=None, type_=None, bidirectional=False, limit=None):
        """
        Return all relationships from the specified start node to the
        end node based on the specified type
        
        :param start: Starting object
        :param end: (Optional) Ending object
        :param type_: (Optional) Relationship type
        :param bool bidirectional: (Optional) bidirectional relationship flag
        :param bool limit: (Optional) number of relationships to return
        """

    def delete_relationships(*rels):
        """
        Delete the specified relationships

        :param rels: relationships to deleted
        """

    def update_relationship(obj, properties):
        """
        Update the specified relationship

        :param obj: relationships to update
        :param properties: Relationship properties
        """

    def find_relationships(key, value, type_=None, start=None, end=None,
                           bidirectional=False):
        """
        Find relationships for the specified key and value property
        
        :param key: Property key
        :param value: Property value
        :param type_: (Optional) Relationship type
        :param start: (Optional) Starting object
        :param end: (Optional) Ending object
        :param bool bidirectional: (Optional) bidirectional relationship flag
        """

    def get_indexed_relationships(key, value):
        """
        Return the relationships for the specified key and value property
        
        :param key: Property key
        :param value: Property value
        """


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


class IBought(IRelationshipType):
    pass
