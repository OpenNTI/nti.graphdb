#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface
from zope import component
from zope.intid import interfaces as intid_interfaces
from zope.lifecycleevent import interfaces as lce_interfaces

from nti.dataserver import interfaces as nti_interfaces

from nti.ntiids import ntiids

from .common import to_external_ntiid_oid

from . import create_job
from . import get_graph_db
from . import get_job_queue
from . import relationships
from . import interfaces as graph_interfaces

@interface.implementer(graph_interfaces.IContainer)
class Container(object):
	
	__slots__ = ('id',)

	def __init__(self, containerId):
		self.id = containerId

	@property
	def containerId(self):
		return self.id

	def __eq__(self, other):
		try:
			return self is other or self.id == other.id
		except AttributeError:
			return NotImplemented

	def __hash__(self):
		xhash = 47
		xhash ^= hash(self.id)
		return xhash

	def __str__(self):
		return self.id

@interface.implementer(graph_interfaces.IContainer)
@component.adapter(basestring)
def _default_container_adapter(containerId):
	return Container(containerId)

def _add_contained_membership(db, oid, containerId):
	obj = ntiids.find_object_with_ntiid(oid)
	container = ntiids.find_object_with_ntiid(containerId)
	if obj is not None:
		container = container or graph_interfaces.IContainer(containerId)
		result = db.create_relationship(obj, container, relationships.Contained())
		if result is not None:
			logger.debug("containment relationship %s retreived/created", result)
			return True
	return False

def _process_contained_added(db, contained):
	containerId = getattr(contained, 'containerId', None)
	if containerId:
		oid = to_external_ntiid_oid(contained)
		queue = get_job_queue()
		job = create_job(_add_contained_membership, db=db, oid=oid,
						 containerId=containerId)
		queue.put(job)

@component.adapter(nti_interfaces.IContained, lce_interfaces.IObjectAddedEvent)
def _contained_added(contained, event):
	db = get_graph_db()
	if db is not None:
		_process_contained_added(db, contained)

def _remove_node(db, key, value):
	node = db.get_indexed_node(key, value)
	if node is not None:
		db.delete_node(node)
		logger.debug("node %s deleted", node)
		return True
	return False

def _process_contained_removed(db, contained):
	adapted = graph_interfaces.IUniqueAttributeAdapter(contained)
	queue = get_job_queue()
	job = create_job(_remove_node, db=db, key=adapted.key, value=adapted.value)
	queue.put(job)

@component.adapter(nti_interfaces.IContained, intid_interfaces.IIntIdRemovedEvent)
def _contained_removed(contained, event):
	db = get_graph_db()
	if db is not None:
		_process_contained_removed(db, contained)

component.moduleProvides(graph_interfaces.IObjectProcessor)

def init(db, obj):
	result = False
	if nti_interfaces.IContained.providedBy(obj):
		_process_contained_added(db, obj)
		result = True
	return result
