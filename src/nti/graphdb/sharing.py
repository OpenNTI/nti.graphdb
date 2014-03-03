#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six

from zope import component
from zope import interface
from zope.lifecycleevent import interfaces as lce_interfaces

from nti.dataserver.users import User
from nti.dataserver import interfaces as nti_interfaces
from nti.dataserver.contenttypes.forums import interfaces as forum_interfaces

from nti.externalization import externalization

from nti.ntiids import ntiids

from . import create_job
from . import get_graph_db
from . import get_job_queue
from . import relationships
from . import interfaces as graph_interfaces

def get_entity(entity):
	if isinstance(entity, six.string_types):
		entity = User.get_entity(entity)
	return entity

def get_underlying(oid):
	obj = ntiids.find_object_with_ntiid(oid)
	if forum_interfaces.IHeadlinePost.providedBy(obj):
		obj = obj.__parent__
	return obj

def _delete_isSharedTo_rels(db, oid, sharedWith=()):
	obj = get_underlying(oid)
	if obj and sharedWith:
		rel_type = relationships.IsSharedTo()
		for entity in sharedWith:
			entity = get_entity(entity)
			if entity is None:
				continue
			adapted = component.getMultiAdapter((obj, entity, rel_type),
												graph_interfaces.IUniqueAttributeAdapter)
			db.delete_indexed_relationship(adapted.key, adapted.value)

def _create_isSharedTo_rels(db, oid, sharedWith=()):
	result = []
	obj = get_underlying(oid)
	if obj and sharedWith:
		rel_type = relationships.IsSharedTo()
		for entity in sharedWith:
			entity = get_entity(entity)
			if entity is not None:
				result.append(db.create_relationship(obj, entity, rel_type))
	return result

def _create_shared_rel(db, oid):
	obj = get_underlying(oid)
	if obj is not None:
		creator = get_entity(obj.creator)
		rel = db.create_relationship(creator, obj, relationships.Shared())
		return (obj, rel)
	return (None, None)

def _process_shareable(db, obj, sharedWith=()):
	sharedWith = sharedWith or getattr(obj, 'sharedWith', ())
	if sharedWith:
		queue = get_job_queue()
		oid = externalization.to_external_ntiid_oid(obj)
		sharedWith = [getattr(x, 'username', x) for x in sharedWith]
		job = create_job(_create_isSharedTo_rels, db=db, oid=oid, sharedWith=sharedWith)
		queue.put(job)
		job = create_job(_create_shared_rel, db=db, oid=oid)
		queue.put(job)

@component.adapter(nti_interfaces.IReadableShared, lce_interfaces.IObjectAddedEvent)
def _shareable_added(obj, event):
	db = get_graph_db()
	if db is not None:
		_process_shareable(db, obj)

def _process_delete_rels(db, obj, oldSharingTargets=()):
	oldSharingTargets = [getattr(x, 'username', x) for x in oldSharingTargets]
	if oldSharingTargets:
		queue = get_job_queue()
		oid = externalization.to_external_ntiid_oid(obj)
		job = create_job(_delete_isSharedTo_rels, db=db, oid=oid,
						 sharedWith=oldSharingTargets)
		queue.put(job)

def _process_modified_event(db, obj, oldSharingTargets=()):
	sharingTargets = getattr(obj, 'sharingTargets', ())
	_process_delete_rels(db, obj, oldSharingTargets)  # delete old
	_process_shareable(db, obj, sharingTargets)  # create new

@component.adapter(nti_interfaces.IContained, nti_interfaces.IObjectSharingModifiedEvent)
def _shareable_modified(obj, event):
	db = get_graph_db()
	if db is not None:
		_process_modified_event(db, obj, event.oldSharingTargets)

interface.moduleProvides(graph_interfaces.IObjectProcessor)

def init(db, obj):
	result = False
	if nti_interfaces.IShareableModeledContent.providedBy(obj):
		_process_shareable(db, obj)
		result = True
	return result
