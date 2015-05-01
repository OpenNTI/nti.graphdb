#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from zope.intid.interfaces import IIntIdRemovedEvent

from zope.lifecycleevent.interfaces import IObjectAddedEvent

from nti.dataserver.interfaces import IEntity
from nti.dataserver.interfaces import IFriendsList

from nti.ntiids.ntiids import find_object_with_ntiid

from .common import to_external_oid

from .interfaces import ILabelAdapter
from .interfaces import IObjectProcessor
from .interfaces import IUniqueAttributeAdapter

from . import create_job
from . import get_graph_db
from . import get_job_queue

def _remove_entity(db, label, key, value):
	node = db.get_indexed_node(label, key, value)
	if node is not None:
		db.delete_node(node)
		logger.debug("node %s deleted", node)
		return True
	return False

def _add_entity(db, oid):
	entity = find_object_with_ntiid(oid)
	if entity is not None:
		node = db.get_or_create_node(entity)
		logger.debug("entity node %s created/retrieved", node)
		return entity, node
	return None, None

def _process_entity_removed(db, entity):
	label = ILabelAdapter(entity)
	adapted = IUniqueAttributeAdapter(entity)
	queue = get_job_queue()
	job = create_job(_remove_entity,
					 db=db,
					 label=label,
					 key=adapted.key,
					 value=adapted.value)
	queue.put(job)

def _process_entity_added(db, entity):
	oid = to_external_oid(entity)
	queue = get_job_queue()
	job = create_job(_add_entity, db=db, oid=oid)
	queue.put(job)

@component.adapter(IEntity, IObjectAddedEvent)
def _entity_added(entity, event):
	db = get_graph_db()
	queue = get_job_queue()
	if 	db is not None and queue is not None:  # check queue b/c of Everyone comm
		_process_entity_added(db, entity)

@component.adapter(IEntity, IIntIdRemovedEvent)
def _entity_removed(entity, event):
	db = get_graph_db()
	if db is not None:
		_process_entity_removed(db, entity)

component.moduleProvides(IObjectProcessor)

def init(db, obj):
	result = False
	if IEntity.providedBy(obj) and not IFriendsList.providedBy(obj):
		_process_entity_added(db, obj)
		result = True
	return result
