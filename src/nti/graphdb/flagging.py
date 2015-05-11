#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from nti.dataserver.interfaces import IFlaggable
from nti.dataserver.interfaces import IGlobalFlagStorage
from nti.dataserver.interfaces import IObjectFlaggedEvent
from nti.dataserver.interfaces import IObjectUnflaggedEvent

from nti.ntiids.ntiids import find_object_with_ntiid

from .common import get_oid
from .common import get_entity
from .common import get_current_principal

from .relationships import Flagged

from .interfaces import IObjectProcessor

from . import create_job
from . import get_graph_db
from . import get_job_queue

def add_flagged_relationship(db, username, oid):
	result = None
	author = get_entity(username)
	obj = find_object_with_ntiid(oid)
	if obj is not None and author is not None:
		result = db.create_relationship(author, obj, Flagged())
		logger.debug("Flagged relationship %s created", result)
	return result

def remove_flagged_relationship(db, username, oid):
	result = False
	author = get_entity(username)
	obj = find_object_with_ntiid(oid)
	if obj is not None and author is not None:
		rels = db.match(author, obj, Flagged())
		if rels:
			db.delete_relationships(*rels)
			logger.debug("Flagged relationship %s deleted", rels)
			result = True
	return result

def _process_flagging_event(db, flaggable, username=None, is_flagged=True):
	username = username or get_current_principal()
	if username:
		oid = get_oid(flaggable)
		queue = get_job_queue()
		if is_flagged:
			job = create_job(add_flagged_relationship, db=db, username=username,
							 oid=oid)
		else:
			job = create_job(remove_flagged_relationship, db=db, username=username,
							 oid=oid)
		queue.put(job)

@component.adapter(IFlaggable, IObjectFlaggedEvent)
def _object_flagged(flaggable, event):
	db = get_graph_db()
	if db is not None:
		_process_flagging_event(db, flaggable)

@component.adapter(IFlaggable, IObjectUnflaggedEvent)
def _object_unflagged(flaggable, event):
	db = get_graph_db()
	if db is not None:
		_process_flagging_event(db, flaggable, is_flagged=False)

component.moduleProvides(IObjectProcessor)

def init(db, obj):
	result = False
	if IFlaggable.providedBy(obj):
		store = IGlobalFlagStorage(obj)
		if store.is_flagged(obj):
			creator = getattr(obj, 'creator', None)
			## asume all sharedWith users have flagged object
			flaggers = list(getattr(obj, 'sharedWith', None) or ())
			if not flaggers and creator:
				flaggers.append(creator)
			flaggers = { getattr(x, 'username', x) for x in flaggers }
			for flagger in flaggers:
				_process_flagging_event(db, obj, flagger)
			result = len(flaggers) > 0
	return result
