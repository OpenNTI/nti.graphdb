#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope.lifecycleevent import interfaces as lce_interfaces

from nti.dataserver.users import Entity
from nti.dataserver import interfaces as nti_interfaces

from nti.ntiids import ntiids

from .common import get_creator
from .common import to_external_ntiid_oid

from . import create_job
from . import get_graph_db
from . import get_job_queue
from . import relationships
from . import interfaces as graph_interfaces

def _add_created_relationship(db, oid, creator):
	obj = ntiids.find_object_with_ntiid(oid)
	creator = Entity.get_entity(creator)
	if obj is not None and creator is not None:
		result = db.create_relationship(creator, obj, relationships.Created())
		if result is not None:
			logger.debug("creator relationship %s retreived/created" % result)
			return True
	return False

def _process_created_event(db, created):
	creator = get_creator(created)
	if creator:
		oid = to_external_ntiid_oid(created)
		queue = get_job_queue()
		job = create_job(_add_created_relationship, db=db, oid=oid,
						 creator=creator.username)
		queue.put(job)

@component.adapter(nti_interfaces.ICreated, lce_interfaces.IObjectCreatedEvent)
def _object_created(created, event):
	db = get_graph_db()
	if db is not None:
		_process_created_event(db, created)

def _remove_node(db, key, value):
	node = db.get_indexed_node(key, value)
	if node is not None:
		db.delete_node(node)
		logger.debug("Node %s,%s deleted" % (key, value))
		return True
	return False

def _process_created_removed(db, contained):
	adapted = graph_interfaces.IUniqueAttributeAdapter(contained)
	queue = get_job_queue()
	job = create_job(_remove_node, db=db, key=adapted.key, value=adapted.value)
	queue.put(job)

@component.adapter(nti_interfaces.ICreated, lce_interfaces.IObjectRemovedEvent)
def _object_removed(contained, event):
	db = get_graph_db()
	if db is not None:
		_process_created_removed(db, contained)

component.moduleProvides(graph_interfaces.IObjectProcessor)

def init(db, obj):
	result = False
	if nti_interfaces.ICreated.providedBy(obj):
		_process_created_event(db, obj)
		result = True
	return result