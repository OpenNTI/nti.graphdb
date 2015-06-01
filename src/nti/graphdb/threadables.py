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

from nti.dataserver.interfaces import IThreadable
from nti.dataserver.interfaces import IDeletedObjectPlaceholder

from nti.ntiids.ntiids import find_object_with_ntiid

from .common import get_oid
from .common import get_creator
from .common import get_node_pk

from . import create_job
from . import get_graph_db
from . import get_job_queue

from .relationships import Reply
from .relationships import IsReplyOf

from .interfaces import IObjectProcessor
from .interfaces import IPropertyAdapter

def _remove_node(db, label, key, value):
	node = db.get_indexed_node(label, key, value)
	if node is not None:
		db.delete_node(node)
		logger.debug("Node %s deleted", node)
		return True
	return False

def _remove_threadable(db, label, key, value):
	rel_type = str(Reply())
	for rel in db.get_indexed_relationships(key, value):
		if str(rel.type) == rel_type:
			db.delete_relationship(rel)
			logger.debug("ReplyTo relationship %s deleted", rel)
	_remove_node(db, label, key, value)

def _proces_threadable_removed(db, threadable):
	pk = get_node_pk(threadable) if threadable is not None else None
	if pk is not None:
		queue = get_job_queue()
		job = create_job(_remove_threadable, db=db,
						 label=pk.label,
						 key=pk.key,
						 value=pk.value)
		queue.put(job)

@component.adapter(IThreadable, IIntIdRemovedEvent)
def _threadable_removed(threadable, event):
	db = get_graph_db()
	if db is not None:
		_proces_threadable_removed(db, threadable)

@component.adapter(IThreadable, IObjectModifiedEvent)
def _threadable_modified(thread, event):
	db = get_graph_db()
	if db is not None and IDeletedObjectPlaceholder.providedBy(thread):
		_proces_threadable_removed(db, thread)

def _add_in_reply_to_relationship(db, oid):
	threadable = find_object_with_ntiid(oid)
	in_replyTo = threadable.inReplyTo if threadable is not None else None
	if in_replyTo is not None and not db.match(threadable, in_replyTo, IsReplyOf()):
		# create parent/child relationship
		rel = db.create_relationship(threadable, in_replyTo, IsReplyOf())
		logger.debug("IsReplyOf Relationship %s created", rel)

		t_author = get_creator(threadable)
		i_author = get_creator(in_replyTo)
		if not i_author or not t_author:
			return
		# from IPython.core.debugger import Tracer; Tracer()()
		# create a relationship between author and the author being replied to
		properties = component.getMultiAdapter((t_author, threadable, Reply()),
												IPropertyAdapter)

		rel = db.create_relationship(t_author, i_author, Reply(),
									properties=properties)
		logger.debug("ReplyTo relationship %s retreived/created", rel)
		
		pk = get_node_pk(threadable)
		if pk is not None:
			db.index_relationship(rel, pk.key, pk.value)

		return True
	return False

def _process_threadable_in_reply_to(db, threadable):
	oid = get_oid(threadable)
	queue = get_job_queue()
	job = create_job(_add_in_reply_to_relationship, db=db, oid=oid)
	queue.put(job)

@component.adapter(IThreadable, IObjectAddedEvent)
def _threadable_added(threadable, event):
	db = get_graph_db()
	if db is not None and threadable.in_reply_to:
		_process_threadable_in_reply_to(db, threadable)

component.moduleProvides(IObjectProcessor)

def init(db, obj):
	result = False
	if IThreadable.providedBy(obj) and obj.in_reply_to:
		_process_threadable_in_reply_to(db, obj)
		result = True
	return result
