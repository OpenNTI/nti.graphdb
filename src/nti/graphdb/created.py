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

from zope.lifecycleevent.interfaces import IObjectCreatedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent

from nti.chatserver.interfaces import IMessageInfo
from nti.chatserver.interfaces import IMessageInfoPostedToRoomEvent

from nti.dataserver.interfaces import ICreated

from nti.ntiids.ntiids import find_object_with_ntiid

from .common import get_oid
from .common import get_entity
from .common import get_creator
from .common import get_node_pk

from .relationships import Created

from .interfaces import IObjectProcessor
from .interfaces import IPropertyAdapter

from . import create_job
from . import get_graph_db
from . import get_job_queue

def _add_created_relationship(db, creator, oid):
	creator = get_entity(creator)
	obj = find_object_with_ntiid(oid)
	if obj is not None and creator is not None:
		result = db.create_relationship(creator, obj, Created())
		if result is not None:
			logger.debug("creator relationship %s retreived/created", result)
			return True
	return False

def _process_created_event(db, created):
	creator = get_creator(created)
	if creator is not None:
		oid = get_oid(created)
		queue = get_job_queue()
		job = create_job(_add_created_relationship, db=db, oid=oid,
						 creator=creator.username)
		queue.put(job)

@component.adapter(ICreated, IObjectCreatedEvent)
def _object_created(created, event):
	db = get_graph_db()
	if db is not None:
		_process_created_event(db, created)

@component.adapter(IMessageInfoPostedToRoomEvent)
def _message_posted_to_room(event):
	db = get_graph_db()
	if db is not None:
		_process_created_event(db, event.object)

def _update_created(db, oid):
	created = find_object_with_ntiid(oid)
	pk = get_node_pk(created) if created is not None else None
	if pk is not None:
		node = db.get_indexed_node(pk.label, pk.key, pk.value)
		if node is not None:
			properties = IPropertyAdapter(created)
			db.update_node(node, properties)
			logger.debug("Properties updated for node %s", node)
			return properties

def _process_created_modified(db, created):
	oid = get_oid(created)
	queue = get_job_queue()
	job = create_job(_update_created, db=db, oid=oid)
	queue.put(job)

@component.adapter(ICreated, IObjectModifiedEvent)
def _object_modified(created, event):
	db = get_graph_db()
	if db is not None:
		_process_created_modified(db, created)

def _remove_created(db, label, key, value):
	node = db.get_indexed_node(label, key, value)
	if node is not None:
		db.delete_node(node)
		logger.debug("Node %s deleted", node)
		return True
	return False

def _process_created_removed(db, created):
	pk = get_node_pk(created) if created is not None else None
	if pk is not None:
		queue = get_job_queue()
		job = create_job(_remove_created, db=db,
						 label=pk.label,
						 key=pk.key,
						 value=pk.value)
		queue.put(job)

@component.adapter(ICreated, IIntIdRemovedEvent)
def _object_removed(created, event):
	db = get_graph_db()
	if db is not None:
		_process_created_removed(db, created)

component.moduleProvides(IObjectProcessor)

def init(db, obj):
	result = False
	if ICreated.providedBy(obj) or IMessageInfo.providedBy(obj):
		_process_created_event(db, obj)
		result = True
	return result
