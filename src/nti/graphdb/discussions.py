#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from six import string_types

from zope import component

from zope.intid.interfaces import IIntIdRemovedEvent

from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent

from nti.dataserver.interfaces import IDeletedObjectPlaceholder

from nti.dataserver.contenttypes.forums.interfaces import IForum
from nti.dataserver.contenttypes.forums.interfaces import ITopic
from nti.dataserver.contenttypes.forums.interfaces import ICommentPost

from nti.graphdb import create_job
from nti.graphdb import get_graph_db
from nti.graphdb import get_job_queue

from nti.graphdb.common import get_oid
from nti.graphdb.common import get_creator
from nti.graphdb.common import get_node_primary_key

from nti.graphdb.interfaces import ADD_EVENT
from nti.graphdb.interfaces import MODIFY_EVENT
from nti.graphdb.interfaces import REMOVE_EVENT

from nti.graphdb.interfaces import IPropertyAdapter
from nti.graphdb.interfaces import IObjectProcessor

from nti.graphdb.relationships import Author
from nti.graphdb.relationships import MemberOf
from nti.graphdb.relationships import CommentOn

from nti.ntiids.ntiids import find_object_with_ntiid

logger = __import__('logging').getLogger(__name__)

# utils


def add_node(db, oid, label, key, value):
    created = False
    obj = find_object_with_ntiid(oid)
    node = db.get_indexed_node(label, key, value)
    if obj is not None and node is None:
        node = db.create_node(obj)
        created = True
        logger.debug("Node %s created", node)
    return node, obj, created


def update_node(db, node, obj):
    properties = IPropertyAdapter(obj)
    db.update_node(node, properties)
    logger.debug("Properties updated for node %s", node)
    return node, obj


def delete_node(db, label, key, value):
    node = db.get_indexed_node(label, key, value)
    if node is not None:
        db.delete_node(node)
        logger.debug("Node %s deleted", node)
        return True
    return False


def delete_nodes(db, pks=()):
    nodes = db.get_indexed_nodes(*pks)
    result = db.delete_nodes(*nodes)
    logger.debug("%s node(s) deleted", result)


# forums


def add_forum_node(db, oid, label, key, value):
    node, forum, _ = add_node(db, oid, label, key, value)
    return node, forum


def update_forum_node(db, oid, label, key, value):
    node, forum = add_forum_node(db, oid, label, key, value)
    if forum is not None:
        update_node(db, node, forum)
    return node, forum


# topics


def add_topic_node(db, oid, label, key, value):
    node, topic, created = add_node(db, oid, label, key, value)
    if created is not None:
        creator = get_creator(topic)
        rel = db.create_relationship(creator, topic, Author())
        logger.debug("Authorship relationship %s created", rel)
    return node, topic


def update_topic_node(db, oid, label, key, value):
    node, topic = add_topic_node(db, oid, label, key, value)
    if topic is not None:
        update_node(db, node, topic)
    return node, topic


def add_membership_relationship(db, child, parent):
    child = find_object_with_ntiid(child) if isinstance(child, string_types) else child
    parent = find_object_with_ntiid(parent) if isinstance(parent, string_types) else parent
    if child is not None and parent is not None:
        result = db.create_relationship(child, parent, MemberOf())
        logger.debug("Membership relationship %s created", result)
        return result


def process_add_topic_event(db, oid, label, key, value, parent):
    # create topic node
    add_topic_node(db=db, oid=oid,
                    label=label,
                    key=key,
                    value=value)
    # membership
    add_membership_relationship(db=db,
                                 child=oid,
                                 parent=parent)


def process_topic_event(db, topic, event):
    oid = get_oid(topic)
    pk = get_node_primary_key(topic)
    queue = get_job_queue()
    if pk is not None:
        if event == ADD_EVENT:
            parent = get_oid(topic.__parent__)
            job = create_job(process_add_topic_event,
                             db=db,
                             oid=oid,
                             label=pk.label,
                             key=pk.key,
                             value=pk.value,
                             parent=parent)
            queue.put(job)
        else:
            job = create_job(update_topic_node, db=db,
                             oid=oid,
                             label=pk.label,
                             key=pk.key,
                             value=pk.value)
            queue.put(job)


@component.adapter(ITopic, IObjectAddedEvent)
def _topic_added(topic, unused_event):
    db = get_graph_db()
    if db is not None:
        process_topic_event(db, topic, ADD_EVENT)


@component.adapter(ITopic, IObjectModifiedEvent)
def _topic_modified(topic, unused_event):
    db = get_graph_db()
    if db is not None:
        process_topic_event(db, topic, MODIFY_EVENT)


def process_discussion_remove_events(db, primary_keys=()):
    if primary_keys:
        queue = get_job_queue()
        job = create_job(delete_nodes, db=db, pks=primary_keys)
        queue.put(job)


def remove_topic(db, topic):
    primary_keys = [get_node_primary_key(topic)]
    for comment in topic.values():  # remove comments
        primary_keys.append(get_node_primary_key(comment))
    process_discussion_remove_events(db, primary_keys)


@component.adapter(ITopic, IIntIdRemovedEvent)
def _topic_removed(topic, unused_event):
    db = get_graph_db()
    if db is not None:
        remove_topic(db, topic)


# comments


def get_comment_relationship(db, comment):
    pk = get_node_primary_key(comment)  # see user, comment, CommentOn adapter
    topic = comment.__parent__
    author = get_creator(comment)
    rels = db.match(author, topic, CommentOn())
    for rel in rels or ():
        props = getattr(rel, 'properties', None) or {}
        if props.get(pk.key) == pk.value:
            return rel
    return None


def comment_properties(comment):
    creator = get_creator(comment)
    result = component.queryMultiAdapter(
        (creator, comment, CommentOn()), IPropertyAdapter)
    return result


def add_comment_relationship(db, oid):
    result = None
    comment = find_object_with_ntiid(oid)
    if comment is not None:
        # Comments are special case. we build a relationship between the
        # commenting user and the topic. We identify the relationship with
        # the primary key of the comment
        # Note we don't create a comment node.
        topic = comment.__parent__
        author = get_creator(comment)
        properties = comment_properties(comment)
        result = db.create_relationship(author, topic, CommentOn(),
                                        properties=properties,
                                        unique=False)
        logger.debug("CommentOn relationship %s created", result)
    return result


def delete_comment(db, oid, label, key, value):
    comment = find_object_with_ntiid(oid)
    if comment is not None:
        node = db.get_indexed_node(label, key, value)  # check for comment node
        if node is not None:
            db.delete_node(node)
            logger.debug("Comment node %s deleted", node)

        rel = get_comment_relationship(db, comment)
        if rel is not None:
            db.delete_relationship(rel)
            logger.debug("Comment-on relationship %s deleted", rel)
            return True
        return False


def process_add_comment_event(db, oid, parent):
    # add user->topic relationship
    add_comment_relationship(db=db, oid=oid)
    # create comment->topic relationship
    add_membership_relationship(db=db, child=oid, parent=parent)


def process_comment_event(db, comment, event):
    queue = get_job_queue()
    oid = get_oid(comment)
    if event == ADD_EVENT:
        parent = get_oid(comment.__parent__)
        job = create_job(process_add_comment_event,
                         db=db, oid=oid, parent=parent)
        queue.put(job)
    else:
        pk = get_node_primary_key(comment)
        job = create_job(delete_comment, db=db, oid=oid,
                         label=pk.label,
                         key=pk.key, value=pk.value)
        queue.put(job)


@component.adapter(ICommentPost, IObjectAddedEvent)
def _comment_added(comment, unused_event):
    db = get_graph_db()
    if db is not None:
        process_comment_event(db, comment, ADD_EVENT)


@component.adapter(ICommentPost, IObjectModifiedEvent)
def _comment_modified(comment, unused_event):
    db = get_graph_db()
    if db is not None and IDeletedObjectPlaceholder.providedBy(comment):
        process_comment_event(db, comment, REMOVE_EVENT)


# forums


def process_forum_event(db, forum, event):
    oid = get_oid(forum)
    pk = get_node_primary_key(forum)
    queue = get_job_queue()
    func = add_forum_node if event == ADD_EVENT else update_forum_node
    job = create_job(func, db=db, oid=oid, label=pk.label,
                     key=pk.key, value=pk.value)
    queue.put(job)


@component.adapter(IForum, IObjectAddedEvent)
def _forum_added(forum, unused_event):
    db = get_graph_db()
    if db is not None:
        process_forum_event(db, forum, ADD_EVENT)


@component.adapter(IForum, IObjectModifiedEvent)
def _forum_modified(forum, unused_event):
    db = get_graph_db()
    if db is not None:
        process_forum_event(db, forum, MODIFY_EVENT)


@component.adapter(IForum, IIntIdRemovedEvent)
def _forum_removed(forum, unused_event):
    db = get_graph_db()
    if db is not None:
        # remove topics
        for topic in forum.values():
            remove_topic(db, topic)
        # remove forum node
        process_discussion_remove_events(db, [get_node_primary_key(forum)])


component.moduleProvides(IObjectProcessor)


def init(db, obj):
    result = True
    if IForum.providedBy(obj):
        process_forum_event(db, obj, ADD_EVENT)
    elif ITopic.providedBy(obj):
        process_topic_event(db, obj, ADD_EVENT)
    elif ICommentPost.providedBy(obj):
        process_comment_event(db, obj, ADD_EVENT)
    else:
        result = False
    return result
