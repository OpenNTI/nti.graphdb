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
from zope.lifecycleevent import interfaces as lce_interfaces

from nti.dataserver import interfaces as nti_interfaces

from nti.externalization import externalization

from nti.ntiids import ntiids

from . import relationships
from . import get_possible_site_names
from . import interfaces as graph_interfaces

def to_external_ntiid_oid(obj):
	return  externalization.to_external_ntiid_oid(obj)

def remove_modeled(db, key, value):
	node = db.get_indexed_node(key, value)
	if node is not None:
		db.delete_node(node)
		logger.debug("Node %s,%s deleted" % (key, value))
		return True
	return False

def remove_note(db, key, value, inReplyTo_key=None, inReplyTo_value=None):
	if inReplyTo_key and inReplyTo_value:
		db.delete_indexed_relationship(inReplyTo_key, inReplyTo_value)
	remove_modeled(db, key, value)

def _get_inReplyTo_PK(obj):
	key, value = (None, None)
	if obj is not None:
		author = obj.creator
		rel_type = relationships.Reply()
		adapted = component.queryMultiAdapter((author, obj, rel_type), graph_interfaces.IUniqueAttributeAdapter)
		key = adapted.key if adapted is not None else None
		value = adapted.value if adapted is not None else None
	return key, value

def _proces_note_removed(note, event):
	site = get_possible_site_names()[0]
	irt_key, irt_value = _get_inReplyTo_PK(note)
	adapted = graph_interfaces.IUniqueAttributeAdapter(note)
	db = component.getUtility(graph_interfaces.IGraphDB, name=site)
	func = functools.partial(remove_note, db=db, key=adapted.key, value=adapted.value,
							 inReplyTo_key=irt_key, inReplyTo_value=irt_value)
	transaction.get().addAfterCommitHook(lambda success: success and gevent.spawn(func))

def _do_add_inReplyTo_relationship(db, note):
	in_replyTo = note.inReplyTo if note is not None else None
	if in_replyTo and note:
		author = note.creator
		rel_type = relationships.Reply()
		# get the key/value to id the inreplyTo relationship
		key, value = _get_inReplyTo_PK(note)
		# create a relationship between author and the node being replied to
		adapted = component.getMultiAdapter((author, note, rel_type), graph_interfaces.IPropertyAdapter)
		result = db.create_relationship(author, in_replyTo, rel_type, properties=adapted.properties(), key=key, value=value)
		return result
	return None

def add_inReplyTo_relationship(db, oid):
	note = ntiids.find_object_with_ntiid(oid)
	result = _do_add_inReplyTo_relationship(db, note)
	if result is not None:
		logger.debug("replyTo relationship %s retrived/created" % result)

def _process_note_inReplyTo(note):
	site = get_possible_site_names()[0]
	oid = to_external_ntiid_oid(note)
	def _process_event():
		transaction_runner = component.getUtility(nti_interfaces.IDataserverTransactionRunner)
		db = component.getUtility(graph_interfaces.IGraphDB, name=site)
		func = functools.partial(add_inReplyTo_relationship, db=db, oid=oid)
		transaction_runner(func)
	transaction.get().addAfterCommitHook(lambda success: success and gevent.spawn(_process_event))

@component.adapter(nti_interfaces.INote, lce_interfaces.IObjectAddedEvent)
def _note_added(note, event):
	if note.inReplyTo:
		_process_note_inReplyTo(note)

@component.adapter(nti_interfaces.INote, lce_interfaces.IObjectRemovedEvent)
def _note_removed(note, event):
	_proces_note_removed(note, event)

# utils

from zope.generations.utility import findObjectsProviding

def build_graph_user(db, user):
	for note in findObjectsProviding(user, nti_interfaces.INote):
		_do_add_inReplyTo_relationship(db, note)
