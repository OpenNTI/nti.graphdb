#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
graphdb modeled content related functionality

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import gevent
import functools
import transaction

from zope import component
from zope.generations.utility import findObjectsProviding
from zope.lifecycleevent import interfaces as lce_interfaces

from nti.dataserver import interfaces as nti_interfaces
from nti.dataserver.contenttypes.forums import interfaces as frm_interfaces

from nti.externalization import externalization

from nti.ntiids import ntiids

from . import get_graph_db
from . import relationships
from .utils import PrimaryKey
from . import interfaces as graph_interfaces

def to_external_ntiid_oid(obj):
	return externalization.to_external_ntiid_oid(obj)

def _get_inReplyTo_PK(obj):
	author = obj.creator
	adapted = component.getMultiAdapter((author, obj, relationships.Reply()),
										graph_interfaces.IUniqueAttributeAdapter)
	return PrimaryKey(adapted.key, adapted.value)

def remove_modeled(db, key, value):
	node = db.get_indexed_node(key, value)
	if node is not None:
		db.delete_node(node)
		logger.debug("Node %s,%s deleted" % (key, value))
		return True
	return False

def _remove_threadable(db, key, value, irt_PK=None):
	if irt_PK is not None:
		db.delete_indexed_relationship(irt_PK.key, irt_PK.value)
	remove_modeled(db, key, value)

def _proces_threadable_removed(db, threadable):
	irt_PK = _get_inReplyTo_PK(threadable)
	adapted = graph_interfaces.IUniqueAttributeAdapter(threadable)
	func = functools.partial(_remove_threadable, db=db,
							 # note node locator
							 key=adapted.key,
							 value=adapted.value,
							 # inReplyTo rel locator
							 irt_PK=irt_PK)
	transaction.get().addAfterCommitHook(
					lambda success: success and gevent.spawn(func))

@component.adapter(nti_interfaces.IThreadable, lce_interfaces.IObjectRemovedEvent)
def _threadable_removed(threadable, event):
	db = get_graph_db()
	if db is not None:
		_proces_threadable_removed(db, threadable)

def _add_inReplyTo_relationship(db, oid):
	threadable = ntiids.find_object_with_ntiid(oid)
	in_replyTo = threadable.inReplyTo if threadable is not None else None
	if in_replyTo is not None:
		author = threadable.creator
		rel_type = relationships.Reply()
		# get the key/value to id the inReplyTo relationship
		irt_PK = _get_inReplyTo_PK(threadable)
		# create a relationship between author and the threadable being replied to
		properties = component.getMultiAdapter((author, threadable, rel_type),
												graph_interfaces.IPropertyAdapter)
		result = db.create_relationship(author, in_replyTo, rel_type,
										properties=properties,
										key=irt_PK.key, value=irt_PK.value)
		if result is not None:
			logger.debug("replyTo relationship %s retrived/created" % result)
			return True
	return False

def _process_threadable_inReplyTo(db, threadable):
	oid = to_external_ntiid_oid(threadable)
	def _process_event():
		transaction_runner = \
				component.getUtility(nti_interfaces.IDataserverTransactionRunner)
		func = functools.partial(_add_inReplyTo_relationship, db=db, oid=oid)
		transaction_runner(func)

	transaction.get().addAfterCommitHook(
						lambda success: success and gevent.spawn(_process_event))

@component.adapter(nti_interfaces.IThreadable, lce_interfaces.IObjectAddedEvent)
def _threadable_added(threadable, event):
	db = get_graph_db()
	if db is not None and threadable.inReplyTo:
		_process_threadable_inReplyTo(db, threadable)

# utils

def init(db, entity):
	
	def _add_threadable_rel(obj):
		if nti_interfaces.IThreadable.providedBy(obj) and obj.inReplyTo:
			oid = to_external_ntiid_oid(obj)
			_add_inReplyTo_relationship(db, oid)
			
	if nti_interfaces.IUser.providedBy(entity):
		for obj in findObjectsProviding(entity, nti_interfaces.IThreadable):
			_add_threadable_rel(obj)

		blog = frm_interfaces.IPersonalBlog(entity)
		for topic in blog.values():
			for comment in topic.values():
				_add_threadable_rel(comment)

	elif nti_interfaces.ICommunity.providedBy(entity):
		board = frm_interfaces.ICommunityBoard(entity)
		for forum in board.values():
			for topic in forum.values():
				for comment in topic.values():
					_add_threadable_rel(comment)
