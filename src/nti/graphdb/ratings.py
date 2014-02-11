#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from pyramid.security import authenticated_userid
from pyramid.threadlocal import get_current_request

from contentratings.interfaces import IObjectRatedEvent

from nti.dataserver import users
from nti.dataserver.rating import IObjectUnratedEvent
from nti.dataserver import interfaces as nti_interfaces
from nti.dataserver.contenttypes.forums import interfaces as frm_interfaces

from nti.externalization import externalization

from nti.ntiids import ntiids

from . import create_job
from . import get_graph_db
from . import get_job_queue
from . import relationships

LIKE_CAT_NAME = 'likes'
RATING_CAT_NAME = 'rating'

def get_current_user():
	request = get_current_request()
	username = authenticated_userid(request) if request else None
	return username

def _add_relationship(db, username, oid, rel_type, properties=None):
	result = None
	author = users.User.get_user(username)
	obj = ntiids.find_object_with_ntiid(oid)
	if obj is not None and author is not None:
		result = db.create_relationship(author, obj, rel_type, properties=properties)
		logger.debug("%s relationship %s created", rel_type, result)
	return result

def _remove_relationship(db, username, oid, rel_type):
	result = False
	author = users.User.get_user(username)
	obj = ntiids.find_object_with_ntiid(oid)
	if obj is not None and author is not None:
		match = db.match(author, obj, rel_type)
		if match and db.delete_relationships(match[0]):
			logger.debug("%s relationship %s deleted", rel_type, match[0])
			result = True
	return result

def add_like_relationship(db, username, oid):
	result = _add_relationship(db, username, oid, relationships.Like())
	return result

def remove_like_relationship(db, username, oid):
	result = _remove_relationship(db, username, oid, relationships.Like())
	return result

def _process_like_event(db, username, oid, like=True):
	queue = get_job_queue()
	if like:
		job = create_job(add_like_relationship, db=db, username=username, oid=oid)
	else:
		job = create_job(remove_like_relationship, db=db, username=username, oid=oid)
	queue.put(job)

def add_rate_relationship(db, username, oid, rating):
	rating = rating if rating is not None else 0
	result = _add_relationship(db, username, oid, relationships.Rate(),
							   properties={"rating":int(rating)})
	return result

def remove_rate_relationship(db, username, oid):
	result = _remove_relationship(db, username, oid, relationships.Rate())
	return result

def _process_rate_event(db, username, oid, rating=None, is_rate=True):
	queue = get_job_queue()
	if is_rate:
		job = create_job(add_rate_relationship, db=db, username=username,
						 oid=oid, rating=rating)
	else:
		job = create_job(remove_rate_relationship, db=db, username=username, oid=oid)
	queue.put(job)

@component.adapter(nti_interfaces.IModeledContent, IObjectRatedEvent)
def _object_rated(modeled, event):
	db = get_graph_db()
	username = get_current_user()
	if username and db is not None:
		oid = externalization.to_external_ntiid_oid(modeled)
		if event.category == LIKE_CAT_NAME:
			like = event.rating != 0
			_process_like_event(db, username, oid, like)
		elif event.category == RATING_CAT_NAME:
			rating = getattr(event, 'rating', None)
			is_rate = not IObjectUnratedEvent.providedBy(event)
			_process_rate_event(db, username, oid, rating, is_rate)

@component.adapter(frm_interfaces.ITopic, IObjectRatedEvent)
def _topic_rated(topic, event):
	_object_rated(topic, event)

# utils

from zope.annotation import interfaces as an_interfaces
from zope.generations.utility import findObjectsMatching

from contentratings.category import BASE_KEY
from contentratings.storage import UserRatingStorage

def _get_storage(context, cat_name):
	key = getattr(UserRatingStorage, 'annotation_key', BASE_KEY)
	key = str(key + '.' + cat_name)
	annotations = an_interfaces.IAnnotations(context, {})
	storage = annotations.get(key)
	return storage

def _record_likeable(db, obj):
	result = 0
	storage = _get_storage(obj, LIKE_CAT_NAME)
	if storage is not None:
		oid = externalization.to_external_ntiid_oid(obj)
		for rating in storage.all_user_ratings():
			username = rating.userid or u''
			if 	users.Entity.get_entity(username) is not None and \
				add_like_relationship(db, username, oid) is not None:
				result += 1
	return result

def _record_ratings(db, obj):
	result = 0
	storage = _get_storage(obj, RATING_CAT_NAME)
	if storage is not None:
		oid = externalization.to_external_ntiid_oid(obj)
		for rating in storage.all_user_ratings():
			username = rating.userid or u''
			if 	users.Entity.get_entity(username) is not None and \
				add_rate_relationship(db, username, oid, float(rating)):
				result += 1
	return result

def init(db, entity):
	def condition(x):
		return  nti_interfaces.ILikeable.providedBy(x) or \
				nti_interfaces.IModeledContent.providedBy(x)

	result = 0
	if nti_interfaces.IUser.providedBy(entity):
		for obj in findObjectsMatching(entity, condition):
			result += _record_ratings(db, obj)
			if nti_interfaces.ILikeable.providedBy(obj):
				result += _record_likeable(db, obj)

		blog = frm_interfaces.IPersonalBlog(entity)
		for topic in blog.values():
			result += _record_ratings(db, topic)
			result += _record_likeable(db, topic)
			for comment in topic.values():
				result += _record_ratings(db, comment)
				result += _record_likeable(db, comment)

	elif nti_interfaces.ICommunity.providedBy(entity):
		board = frm_interfaces.ICommunityBoard(entity)
		for forum in board.values():
			for topic in forum.values():
				result += _record_ratings(db, topic)
				result += _record_likeable(db, topic)
				for comment in topic.values():
					result += _record_ratings(db, comment)
					result += _record_likeable(db, comment)

	return result
