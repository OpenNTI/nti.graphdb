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
from zope.lifecycleevent.interfaces import IObjectModifiedEvent

from nti.dataserver.interfaces import IUserTaggedContent
from nti.dataserver.contenttypes.forums.interfaces import IHeadlinePost

from nti.ntiids.ntiids import TYPE_NAMED_ENTITY
from nti.ntiids.ntiids import is_ntiid_of_types
from nti.ntiids.ntiids import find_object_with_ntiid

from .common import get_oid
from .common import get_entity
from .common import get_node_pk

from .relationships import TaggedTo

from .interfaces import IObjectProcessor

from . import create_job
from . import get_graph_db
from . import get_job_queue

_ENTITY_TYPES = {TYPE_NAMED_ENTITY, TYPE_NAMED_ENTITY.lower()}

def _underlying(oid):
	obj = find_object_with_ntiid(oid)
	if IHeadlinePost.providedBy(obj):
		obj = obj.__parent__
	return obj

def _create_is_tagged_to_rels(db, oid, entities=()):
	result = []
	obj = _underlying(oid)
	if obj is not None:
		rel_type = TaggedTo()
		for entity in entities or ():
			entity = get_entity(entity)
			if entity is not None and not db.match(obj, entity, rel_type):
				rel = db.create_relationship(obj, entity, rel_type)
				logger.debug("isTaggedTo relationship %s created", rel)
				result.append(rel)
	return result

def _get_username_tags(obj, tags=()):
	username_tags = set()
	tags = tags or getattr(obj, 'tags', ())
	for raw_tag in tags or ():
		if is_ntiid_of_types(raw_tag, _ENTITY_TYPES):
			entity = find_object_with_ntiid(raw_tag)
			if entity is not None:
				username_tags.add(entity.username)
	return username_tags

def _process_added_event(db, obj, tags=()):
	username_tags = _get_username_tags(obj, tags)
	if username_tags:
		queue = get_job_queue()
		oid = get_oid(obj)
		job = create_job(_create_is_tagged_to_rels, db=db, oid=oid,
						 entities=list(username_tags))
		queue.put(job)

@component.adapter(IUserTaggedContent, IObjectAddedEvent)
def _user_tagged_content_added(obj, event):
	db = get_graph_db()
	if db is not None:
		_process_added_event(db, obj)

def _delete_is_tagged_to_rels(db, oid):
	obj = _underlying(oid)
	if obj is not None:
		rels = db.match(start=obj, rel_type=TaggedTo(), loose=True)
		if rels:
			db.delete_relationships(*rels)
			logger.debug("%s isTaggedTo relationship(s) deleted", len(rels))
			return True
	return False

def _process_modify_rels(db, oid):
	# delete existing
	_delete_is_tagged_to_rels(db=db, oid=oid)
	# recreate
	obj = _underlying(oid)
	username_tags = _get_username_tags(obj) if obj is not None else None
	if username_tags:
		_create_is_tagged_to_rels(db=db, oid=oid,
								  entities=list(username_tags))

def _process_modified_event(db, obj):
	queue = get_job_queue()
	oid = get_oid(obj)
	job = create_job(_process_modify_rels, db=db, oid=oid)
	queue.put(job)

@component.adapter(IUserTaggedContent, IObjectModifiedEvent)
def _user_tagged_content_modified(obj, event):
	db = get_graph_db()
	if db is not None:
		_process_modified_event(db, obj)

def _remove_node(db, label, key, value):
	node = db.get_indexed_node(label, key, value)
	if node is not None:
		db.delete_node(node)
		logger.debug("node %s deleted", node)
		return True
	return False

def _process_removed_event(db, obj):
	pk = get_node_pk(obj)
	if pk is not None:
		queue = get_job_queue()
		job = create_job(_remove_node,
						 db=db, label=pk.label,
						 key=pk.key, value=pk.value)
		queue.put(job)

@component.adapter(IUserTaggedContent, IIntIdRemovedEvent)
def _user_tagged_content_removed(obj, event):
	db = get_graph_db()
	if db is not None:
		_process_removed_event(db, obj)

component.moduleProvides(IObjectProcessor)

def init(db, obj):
	result = False
	if IUserTaggedContent.providedBy(obj):
		_process_added_event(db, obj)
		result = True
	return result
