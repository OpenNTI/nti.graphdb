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

from nti.dataserver.contenttypes.forums.interfaces import IHeadlinePost

from nti.dataserver.interfaces import IUserTaggedContent

from nti.graphdb import create_job
from nti.graphdb import get_graph_db
from nti.graphdb import get_job_queue

from nti.graphdb.common import get_oid
from nti.graphdb.common import get_entity
from nti.graphdb.common import get_node_primary_key

from nti.graphdb.interfaces import IObjectProcessor

from nti.graphdb.relationships import TaggedTo

from nti.ntiids.ntiids import TYPE_NAMED_ENTITY
from nti.ntiids.ntiids import is_ntiid_of_types
from nti.ntiids.ntiids import find_object_with_ntiid

ENTITY_TYPES = {
    TYPE_NAMED_ENTITY, TYPE_NAMED_ENTITY.lower()
}

logger = __import__('logging').getLogger(__name__)


def get_underlying(oid):
    obj = find_object_with_ntiid(oid)
    if IHeadlinePost.providedBy(obj):
        obj = obj.__parent__
    return obj


def create_isTaggedTo_rels(db, oid, entities=()):
    result = []
    obj = get_underlying(oid)
    if obj is not None:
        for entity in entities or ():
            entity = get_entity(entity)
            if entity is not None and not db.match(obj, entity, TaggedTo()):
                rel = db.create_relationship(obj, entity, TaggedTo())
                logger.debug("isTaggedTo relationship %s created", rel)
                result.append(rel)
    return result


def get_username_tags(obj, tags=()):
    username_tags = set()
    tags = tags or getattr(obj, 'tags', ())
    for raw_tag in tags or ():
        if is_ntiid_of_types(raw_tag, ENTITY_TYPES):
            entity = find_object_with_ntiid(raw_tag)
            if entity is not None:
                username_tags.add(entity.username)
    return username_tags


def process_added_event(db, obj, tags=()):
    username_tags = get_username_tags(obj, tags)
    if username_tags:
        queue = get_job_queue()
        oid = get_oid(obj)
        job = create_job(create_isTaggedTo_rels, db=db, oid=oid,
                         entities=list(username_tags))
        queue.put(job)


@component.adapter(IUserTaggedContent, IObjectAddedEvent)
def _user_tagged_content_added(obj, unused_event):
    db = get_graph_db()
    if db is not None:
        process_added_event(db, obj)


def delete_isTaggedTo_rels(db, oid):
    result = False
    obj = get_underlying(oid)
    if obj is not None:
        rels = db.match(obj, type_=TaggedTo())
        if rels:
            db.delete_relationships(*rels)
            logger.debug("%s isTaggedTo relationship(s) deleted", len(rels))
            result = True
    return result


def process_modify_rels(db, oid):
    # delete existing
    delete_isTaggedTo_rels(db=db, oid=oid)
    # recreate
    obj = get_underlying(oid)
    username_tags = get_username_tags(obj) if obj is not None else None
    if username_tags:
        create_isTaggedTo_rels(db=db, oid=oid,
                               entities=list(username_tags))


def process_modified_event(db, obj):
    queue = get_job_queue()
    oid = get_oid(obj)
    job = create_job(process_modify_rels, db=db, oid=oid)
    queue.put(job)


@component.adapter(IUserTaggedContent, IObjectModifiedEvent)
def _user_tagged_content_modified(obj, unused_event):
    db = get_graph_db()
    if db is not None:
        process_modified_event(db, obj)


def remove_node(db, label, key, value):
    result = False
    node = db.get_indexed_node(label, key, value)
    if node is not None:
        db.delete_node(node)
        logger.debug("node %s deleted", node)
        result = True
    return result


def process_removed_event(db, obj):
    pk = get_node_primary_key(obj)
    if pk is not None:
        queue = get_job_queue()
        job = create_job(remove_node,
                         db=db, label=pk.label,
                         key=pk.key, value=pk.value)
        queue.put(job)


@component.adapter(IUserTaggedContent, IIntIdRemovedEvent)
def _user_tagged_content_removed(obj, unused_event):
    db = get_graph_db()
    if db is not None:
        process_removed_event(db, obj)


component.moduleProvides(IObjectProcessor)


def init(db, obj):  # pragma: no cover
    result = False
    if IUserTaggedContent.providedBy(obj):
        process_added_event(db, obj)
        result = True
    return result
