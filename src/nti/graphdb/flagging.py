#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
graphdb flagging

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import gevent
import functools
import transaction

from zope import component

from pyramid.security import authenticated_userid
from pyramid.threadlocal import get_current_request

from nti.dataserver import users
from nti.dataserver import interfaces as nti_interfaces

from nti.externalization import externalization

from nti.ntiids import ntiids

from . import get_graph_db
from . import relationships

def get_current_user():
	request = get_current_request()
	username = authenticated_userid(request) if request else None
	return username

def add_flagged_relationship(db, username, oid):
	result = None
	author = users.User.get_user(username)
	obj = ntiids.find_object_with_ntiid(oid)
	if obj is not None and author is not None:
		rel_type = relationships.Flagged()
		result = db.create_relationship(author, obj, rel_type)
		logger.debug("%s relationship %s created", rel_type, result)
	return result

def remove_flagged_relationship(db, username, oid):
	result = False
	author = users.User.get_user(username)
	obj = ntiids.find_object_with_ntiid(oid)
	if obj is not None and author is not None:
		rel_type = relationships.Flagged()
		match = db.match(author, obj, rel_type)
		if match and db.delete_relationships(match[0]):
			logger.debug("%s relationship %s deleted", rel_type, match[0])
			result = True
	return result

def _process_flagging_event(flaggable, is_flagged=True):
	db = get_graph_db()
	username = get_current_user()
	if not username or db is None:
		return
	oid = externalization.to_external_ntiid_oid(flaggable)

	def _process_event():
		transaction_runner = \
				component.getUtility(nti_interfaces.IDataserverTransactionRunner)
		if is_flagged:
			func = functools.partial(add_flagged_relationship, db=db, username=username,
									 oid=oid)
		else:
			func = functools.partial(remove_flagged_relationship, db=db,
									 username=username, oid=oid)
		transaction_runner(func)

	transaction.get().addAfterCommitHook(
					lambda success: success and gevent.spawn(_process_event))

@component.adapter(nti_interfaces.IFlaggable, nti_interfaces.IObjectFlaggedEvent)
def _object_flagged(flaggable, event):
	_process_flagging_event(flaggable)

@component.adapter(nti_interfaces.IFlaggable, nti_interfaces.ObjectUnflaggedEvent)
def _object_unflagged(flaggable, event):
	_process_flagging_event(flaggable, False)

# utils

def init(db, entity):
	pass
