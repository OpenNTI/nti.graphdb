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

from nti.dataserver.interfaces import IEntity
from nti.dataserver.interfaces import IFriendsList
from nti.dataserver.interfaces import IDynamicSharingTargetFriendsList

from nti.graphdb import create_job
from nti.graphdb import get_graph_db
from nti.graphdb import get_job_queue

from nti.graphdb.common import get_oid

from nti.graphdb.interfaces import ILabelAdapter
from nti.graphdb.interfaces import IObjectProcessor
from nti.graphdb.interfaces import IUniqueAttributeAdapter

from nti.ntiids.ntiids import find_object_with_ntiid

logger = __import__('logging').getLogger(__name__)


def is_regular_DFL(obj):
    return IFriendsList.providedBy(obj) \
       and not IDynamicSharingTargetFriendsList.providedBy(obj)


def remove_entity(db, label, key, value):
    node = db.get_indexed_node(label, key, value)
    if node is not None:
        db.delete_node(node)
        logger.debug("Node %s deleted", node)
        return True
    return False


def add_entity(db, oid):
    entity = find_object_with_ntiid(oid)
    if entity is not None:
        node = db.get_or_create_node(entity)
        logger.debug("Entity node %s created/retrieved", node)
        return entity, node
    return None, None


def process_entity_removed(db, entity):
    label = ILabelAdapter(entity)
    adapted = IUniqueAttributeAdapter(entity)
    queue = get_job_queue()
    job = create_job(remove_entity,
                     db=db,
                     label=label,
                     key=adapted.key,
                     value=adapted.value)
    queue.put(job)


def process_entity_added(db, entity):
    oid = get_oid(entity)
    queue = get_job_queue()
    job = create_job(add_entity, db=db, oid=oid)
    queue.put(job)


@component.adapter(IEntity, IObjectAddedEvent)
def _entity_added(entity, unused_event):
    db = get_graph_db()
    queue = get_job_queue()
    if      db is not None \
        and queue is not None \
        and not is_regular_DFL(entity):  # check queue b/c of Everyone comm
        process_entity_added(db, entity)


@component.adapter(IEntity, IIntIdRemovedEvent)
def _entity_removed(entity, unused_event):
    db = get_graph_db()
    if db is not None and not is_regular_DFL(entity):
        process_entity_removed(db, entity)


component.moduleProvides(IObjectProcessor)


def init(db, obj):  # pragma: no cover
    result = False
    if IEntity.providedBy(obj) and not is_regular_DFL(obj):
        process_entity_added(db, obj)
        result = True
    return result
