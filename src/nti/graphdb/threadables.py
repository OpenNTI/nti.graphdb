#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component

from zope.intid.interfaces import IIntIdRemovedEvent

from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent

from nti.dataserver.interfaces import IThreadable
from nti.dataserver.interfaces import IDeletedObjectPlaceholder

from nti.graphdb import create_job
from nti.graphdb import get_graph_db
from nti.graphdb import get_job_queue

from nti.graphdb.common import get_oid
from nti.graphdb.common import get_creator
from nti.graphdb.common import get_node_primary_key

from nti.graphdb.interfaces import IObjectProcessor
from nti.graphdb.interfaces import IPropertyAdapter

from nti.graphdb.relationships import Reply
from nti.graphdb.relationships import IsReplyOf

from nti.ntiids.ntiids import find_object_with_ntiid

logger = __import__('logging').getLogger(__name__)


def remove_node(db, label, key, value):
    result = False
    node = db.get_indexed_node(label, key, value)
    if node is not None:
        db.delete_node(node)
        logger.debug("Node %s deleted", node)
        result = True
    return result


def remove_reply_relationship(db, key, value):
    rel_type = str(Reply())
    for rel in db.get_indexed_relationships(key, value):
        if str(rel.type) == rel_type:
            db.delete_relationship(rel)
            logger.debug("ReplyTo relationship %s deleted", rel)


def remove_threadable(db, label, key, value):
    remove_reply_relationship(db, key, value)
    remove_node(db, label, key, value)


def proces_threadable_removed(db, threadable):
    pk = get_node_primary_key(threadable) if threadable is not None else None
    if pk is not None:
        queue = get_job_queue()
        job = create_job(remove_threadable, db=db,
                         label=pk.label,
                         key=pk.key,
                         value=pk.value)
        queue.put(job)


@component.adapter(IThreadable, IIntIdRemovedEvent)
def _threadable_removed(threadable, unused_event):
    db = get_graph_db()
    if db is not None:
        proces_threadable_removed(db, threadable)


def delete_inReplyTo_relationship(db, oid):
    threadable = find_object_with_ntiid(oid)
    for rel in db.match(threadable, type_=IsReplyOf()) or ():
        db.delete_relationship(rel)


def add_inReplyTo_relationship(db, oid):
    result = False
    threadable = find_object_with_ntiid(oid)
    in_replyTo = threadable.inReplyTo if threadable is not None else None
    if in_replyTo is not None and not db.match(threadable, in_replyTo, IsReplyOf()):
        # create parent/child relationship
        rel = db.create_relationship(threadable, in_replyTo, IsReplyOf())
        logger.debug("IsReplyOf Relationship %s created", rel)
        # create author reply relationship
        from_author = get_creator(threadable)
        to_author = get_creator(in_replyTo)
        if to_author is not None and from_author is not None:
            # create a relationship between author and
            # the author being replied to
            properties = component.getMultiAdapter((from_author, threadable, Reply()),
                                                   IPropertyAdapter)
            rel = db.create_relationship(from_author, to_author, Reply(),
                                         properties=properties)
            logger.debug("ReplyTo relationship %s retreived/created", rel)
            result = True
    return result


def process_threadable_inReplyTo(db, threadable):
    oid = get_oid(threadable)
    queue = get_job_queue()
    job = create_job(add_inReplyTo_relationship, db=db, oid=oid)
    queue.put(job)


@component.adapter(IThreadable, IObjectAddedEvent)
def _threadable_added(threadable, unused_event):
    db = get_graph_db()
    if db is not None and threadable.inReplyTo:
        process_threadable_inReplyTo(db, threadable)


def modify_threadable(db, oid):
    threadable = find_object_with_ntiid(oid)
    if threadable is not None:
        pk = get_node_primary_key(threadable)
        if pk is not None:
            remove_reply_relationship(db, pk.key, pk.value)
        delete_inReplyTo_relationship(db, oid)
        add_inReplyTo_relationship(db, oid)


def proces_threadable_modified(db, threadable):
    oid = get_oid(threadable)
    if oid is not None:
        queue = get_job_queue()
        job = create_job(modify_threadable, db=db, oid=oid)
        queue.put(job)


@component.adapter(IThreadable, IObjectModifiedEvent)
def _threadable_modified(thread, unused_event):
    db = get_graph_db()
    if db is not None:
        if IDeletedObjectPlaceholder.providedBy(thread):
            proces_threadable_removed(db, thread)
        else:
            proces_threadable_modified(db, thread)


component.moduleProvides(IObjectProcessor)


def init(db, obj):  # pragma: no cover
    result = False
    if IThreadable.providedBy(obj) and obj.inReplyTo:
        process_threadable_inReplyTo(db, obj)
        result = True
    return result
