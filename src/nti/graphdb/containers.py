#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time

from zope import component
from zope import interface

from zope.intid.interfaces import IIntIdRemovedEvent

from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent

from nti.common.property import alias
from nti.common.representation import WithRepr

from nti.dataserver.interfaces import IContained

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.schema.schema import EqHash

from .common import get_oid
from .common import get_node_pk

from .interfaces import IContainer
from .interfaces import IObjectProcessor
from .interfaces import IPropertyAdapter

from .relationships import Contained

from . import create_job
from . import get_graph_db
from . import get_job_queue

@WithRepr
@EqHash('id')
@interface.implementer(IContainer)
class Container(object):

	containerId = alias('id')

	def __init__(self, containerId):
		self.id = containerId

@component.adapter(basestring)
@interface.implementer(IContainer)
def _default_container_adapter(containerId):
	return Container(containerId)

def _get_containerId(obj):
	containerId = getattr(obj, 'containerId', None)
	if not containerId:
		parent = getattr(obj, '__parent__', None)
		if parent is not None:
			containerId = get_oid(parent)
	return containerId

def _get_container(container=None, containerId=None):
	if container is None:
		container = find_object_with_ntiid(containerId or u'')
		container = IContainer(containerId, None) if container is None else container
	return container

def _update_container(db, container=None, containerId=None):
	container = _get_container(container, containerId)
	pk = get_node_pk(container) if container is not None else None
	if container is not None and pk is not None:
		node = db.get_indexed_node(pk.label, pk.key, pk.value)
		if node is not None:
			properties = getattr(node, 'properties', None) or {}
			properties = IPropertyAdapter(container)
			if 'createdTime' is not properties:
				properties['createdTime'] = time.time()
			db.update_node(node, properties=properties)
			logger.debug("Properties updated for node %s", node)
			return True
	return False

def _add_contained_membership(db, oid, containerId):
	obj = find_object_with_ntiid(oid)
	container = find_object_with_ntiid(containerId)
	pk = get_node_pk(obj) if obj is not None else None
	if obj is not None and pk is not None:
		container = _get_container(container, containerId)
		if 	container is not None and container is not obj and \
			not db.match(obj, container, Contained()):
			result = db.create_relationship(obj, container, Contained())
			logger.debug("Containment relationship %s created", result)
			_update_container(db, container=container)
			return True
	return False

def _process_contained_added(db, contained):
	containerId = _get_containerId(contained)
	if containerId:
		oid = get_oid(contained)
		queue = get_job_queue()
		job = create_job(_add_contained_membership, db=db, oid=oid,
						 containerId=containerId)
		queue.put(job)

@component.adapter(IContained, IObjectAddedEvent)
def _contained_added(contained, event):
	db = get_graph_db()
	if db is not None:
		_process_contained_added(db, contained)

def _process_contained_modified(db, contained):
	containerId = _get_containerId(contained)
	if containerId:
		queue = get_job_queue()
		job = create_job(_update_container, db=db, containerId=containerId)
		queue.put(job)

@component.adapter(IContained, IObjectModifiedEvent)
def _contained_modified(contained, event):
	db = get_graph_db()
	if db is not None:
		_process_contained_modified(db, contained)

def _remove_node(db, label, key, value):
	node = db.get_indexed_node(label, key, value)
	if node is not None:
		db.delete_node(node)
		logger.debug("node %s deleted", node)
		return True
	return False

def _process_contained_removed(db, contained):
	pk = get_node_pk(contained)
	if pk is not None:
		queue = get_job_queue()
		job = create_job(_remove_node, db=db, label=pk.label, key=pk.key, value=pk.value)
		queue.put(job)
		# update parent container
		_process_contained_modified(db, contained)

@component.adapter(IContained, IIntIdRemovedEvent)
def _contained_removed(contained, event):
	db = get_graph_db()
	if db is not None:
		_process_contained_removed(db, contained)

component.moduleProvides(IObjectProcessor)

def init(db, obj):
	result = False
	if IContained.providedBy(obj):
		_process_contained_added(db, obj)
		result = True
	return result
