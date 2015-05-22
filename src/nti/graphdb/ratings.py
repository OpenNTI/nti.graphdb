#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from zope.annotation.interfaces import IAnnotations

from contentratings.category import BASE_KEY
from contentratings.storage import UserRatingStorage
from contentratings.interfaces import IObjectRatedEvent

from nti.dataserver.interfaces import IRatable
from nti.dataserver.interfaces import ILikeable
from nti.dataserver.rating import IObjectUnratedEvent

from nti.ntiids.ntiids import find_object_with_ntiid

from .common import get_oid
from .common import get_entity
from .common import get_current_principal

from .relationships import Like
from .relationships import Rate

from . import create_job
from . import get_graph_db
from . import get_job_queue
from . import interfaces as graph_interfaces

LIKE_CAT_NAME = 'likes'
RATING_CAT_NAME = 'rating'

def _get_relationship(db, username, oid, rel_type):
	result = None
	author = get_entity(username)
	obj = find_object_with_ntiid(oid)
	if obj is not None and author is not None:
		result = db.match(author, obj, rel_type)
	return result

def _add_relationship(db, username, oid, rel_type, properties=None):
	result = None
	author = get_entity(username)
	obj = find_object_with_ntiid(oid)
	if obj is not None and author is not None:
		result = db.create_relationship(author, obj, rel_type, properties=properties)
		logger.debug("%s relationship %s created", rel_type, result)
	return result

def _remove_relationship(db, username, oid, rel_type):
	rels = _get_relationship(db, username, oid, rel_type)
	if rels:
		db.delete_relationships(*rels)
		logger.debug("%s relationship deleted", rel_type)
		return True
	return False

# like

def _add_like_relationship(db, username, oid):
	if not _get_relationship(db, username, oid, Like()):
		result = _add_relationship(db, username, oid, Like())
	return result

def _remove_like_relationship(db, username, oid):
	result = _remove_relationship(db, username, oid, Like())
	return result

def _process_like_event(db, username, oid, is_like=True):
	queue = get_job_queue()
	if is_like:
		job = create_job(_add_like_relationship, db=db, username=username, oid=oid)
	else:
		job = create_job(_remove_like_relationship, db=db, username=username, oid=oid)
	queue.put(job)

# rate

def _remove_rate_relationship(db, username, oid):
	result = _remove_relationship(db, username, oid, Rate())
	return result

def _add_rate_relationship(db, username, oid, rating, check_existing=False):
	if check_existing and _get_relationship(db, username, oid, Rate()):
		return
	rating = rating if rating is not None else 0
	# remove previous if present
	_remove_rate_relationship(db, username, oid)
	# add relationship
	result = _add_relationship(db, username, oid, Rate(),
							   properties={"rating":int(rating)})
	return result

def _process_rate_event(db, username, oid, rating=None, is_rate=True):
	queue = get_job_queue()
	if is_rate:
		job = create_job(_add_rate_relationship, db=db, username=username,
						 oid=oid, rating=rating)
	else:
		job = create_job(_remove_rate_relationship, db=db, username=username, oid=oid)
	queue.put(job)

@component.adapter(IObjectRatedEvent)
def _object_rated(event):
	db = get_graph_db()
	modeled = event.object
	username = get_current_principal()
	if username and db is not None:
		oid = get_oid(modeled)
		if event.category == LIKE_CAT_NAME:
			is_like = bool(event.rating != 0)
			_process_like_event(db, username, oid, is_like)
		elif event.category == RATING_CAT_NAME:
			rating = getattr(event, 'rating', None)
			is_rate = not IObjectUnratedEvent.providedBy(event)
			_process_rate_event(db, username, oid, rating, is_rate)

# utils

def _get_ratings(context, category):
	# Get the key from the storage, or use a default
	key = getattr(UserRatingStorage, 'annotation_key', BASE_KEY)
	# Append the category name to the dotted annotation key name
	key = str(key + '.' + category)  # # see ds rating.lookup_rating_for_read
	storage = IAnnotations(context, {}).get(key)
	if storage is not None:
		return storage.all_user_ratings()
	return ()

def _record_likeable(db, obj):
	result = 0
	queue = get_job_queue()
	oid = get_oid(obj)
	for rating in _get_ratings(obj, LIKE_CAT_NAME):
		username = rating.userid or u''
		if get_entity(username) is not None:
			job = create_job(_add_like_relationship, db=db, username=username, oid=oid)
			queue.put(job)
			result += 1
	return result

def _record_ratings(db, obj):
	result = 0
	queue = get_job_queue()
	oid = get_oid(obj)
	for rating in _get_ratings(obj, RATING_CAT_NAME):
		username = rating.userid or u''
		if get_entity(username) is not None:
			job = create_job(_add_rate_relationship, db=db, username=username,
							 oid=oid, rating=rating, check_existing=True)
			queue.put(job)
			result += 1
	return result

component.moduleProvides(graph_interfaces.IObjectProcessor)

def init(db, obj):
	result = 0
	if ILikeable.providedBy(obj):
		result = _record_likeable(db, obj)
	if IRatable.providedBy(obj):
		result = _record_ratings(db, obj)
	return result > 0
