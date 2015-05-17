#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from zope.lifecycleevent.interfaces import IObjectAddedEvent

from nti.dataserver.interfaces import IContained
from nti.dataserver.interfaces import IReadableShared
from nti.dataserver.interfaces import IShareableModeledContent
from nti.dataserver.interfaces import IObjectSharingModifiedEvent
from nti.dataserver.contenttypes.forums.interfaces import IHeadlinePost

from nti.ntiids.ntiids import find_object_with_ntiid

from .common import get_oid
from .common import get_entity
from .common import get_creator

from .relationships import Shared
from .relationships import IsSharedWith

from .interfaces import IObjectProcessor

from . import create_job
from . import get_graph_db
from . import get_job_queue

def _underlying(oid):
	obj = find_object_with_ntiid(oid)
	if IHeadlinePost.providedBy(obj):
		obj = obj.__parent__
	return obj

def _delete_is_shared_with_rels(db, oid, sharedWith=()):
	result = 0
	obj = _underlying(oid)
	if obj and sharedWith:
		for entity in sharedWith:
			entity = get_entity(entity)
			if entity is None:
				continue
			rels = db.match(obj, entity, IsSharedWith())
			if rels:
				db.delete_relationships(*rels)
				logger.debug("%s IsSharedWith relationshi(s) deleted", len(rels))
				result += 1
	return result

def _create_is_shared_with_rels(db, oid, sharedWith=()):
	result = []
	obj = _underlying(oid)
	if obj and sharedWith:
		for entity in sharedWith:
			entity = get_entity(entity)
			if entity is not None:
				rel = db.create_relationship(obj, entity, IsSharedWith())
				logger.debug("IsSharedWith relationship %s created", rel)
				result.append(rel)
	return result

def _create_shared_rel(db, oid, entity=None):
	obj = _underlying(oid)
	if obj is not None:
		creator = entity or get_creator(obj)
		creator = get_entity(creator)
		rel = db.create_relationship(creator, obj, Shared())
		logger.debug("Shared relationship %s created", rel)
		return rel
	return None

def _get_sharedWith(obj, sharedWith=()):
	result = sharedWith or getattr(obj, 'sharedWith', ())
	return result

def _process_shareable(db, obj, sharedWith=()):
	sharedWith = _get_sharedWith(obj, sharedWith)
	if sharedWith:
		oid = get_oid(obj)
		queue = get_job_queue()
		sharedWith = [getattr(x, 'username', x) for x in sharedWith]
		job = create_job(_create_is_shared_with_rels, db=db,
						 oid=oid, sharedWith=sharedWith)
		queue.put(job)
		job = create_job(_create_shared_rel, db=db, oid=oid)
		queue.put(job)

@component.adapter(IReadableShared, IObjectAddedEvent)
def _shareable_added(obj, event):
	db = get_graph_db()
	if db is not None:
		_process_shareable(db, obj)

def _process_delete_rels(db, obj, oldSharingTargets=()):
	oldSharingTargets = [getattr(x, 'username', x) for x in oldSharingTargets]
	if oldSharingTargets:
		queue = get_job_queue()
		oid = get_oid(obj)
		job = create_job(_delete_is_shared_with_rels, db=db, oid=oid,
						 sharedWith=oldSharingTargets)
		queue.put(job)

def _process_modified_event(db, obj, oldSharingTargets=()):
	sharingTargets = getattr(obj, 'sharingTargets', ())
	_process_delete_rels(db, obj, oldSharingTargets)  # delete old
	_process_shareable(db, obj, sharingTargets)  # create new

@component.adapter(IContained, IObjectSharingModifiedEvent)
def _shareable_modified(obj, event):
	db = get_graph_db()
	if db is not None:
		_process_modified_event(db, obj, event.oldSharingTargets)

component.moduleProvides(IObjectProcessor)

def init(db, obj):
	result = False
	if IShareableModeledContent.providedBy(obj):
		_process_shareable(db, obj)
		result = True
	return result
