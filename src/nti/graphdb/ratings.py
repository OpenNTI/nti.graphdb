#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
graphdb ratings

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import gevent
import functools
import transaction
import collections

from zope import component

from pyramid.security import authenticated_userid
from pyramid.threadlocal import get_current_request

from contentratings.interfaces import IObjectRatedEvent

from nti.dataserver import users
from nti.dataserver import interfaces as nti_interfaces
from nti.dataserver.contenttypes.forums import interfaces as frm_interfaces

from nti.externalization import externalization

from nti.ntiids import ntiids

from . import get_graph_db
from . import relationships
from . import interfaces as graph_interfaces

LIKE_CAT_NAME = 'likes'

def add_like_relationship(db, username, oid):
	result = None
	author = users.User.get_user(username)
	modeled = ntiids.find_object_with_ntiid(oid)
	if modeled is not None and author is not None:
		result = db.create_relationship(author, modeled, relationships.Like())
		logger.debug("like relationship %s created" % result)
	return result

def remove_like_relationship(db, username, oid):
	result = False
	author = users.User.get_user(username)
	modeled = ntiids.find_object_with_ntiid(oid)
	if modeled is not None and author is not None:
		match = db.match(author, modeled, relationships.Like())
		if match and db.delete_relationships(match[0]):
			logger.debug("like relationship %s deleted" % match[0])
			result = True
	return result

def _process_like_event(username, oid, like=True):
	db = get_graph_db()
	def _process_event():
		transaction_runner = \
			component.getUtility(nti_interfaces.IDataserverTransactionRunner)
		if like:
			func = functools.partial(add_like_relationship, db=db, username=username,
									 oid=oid)
		else:
			func = functools.partial(remove_like_relationship, db=db, username=username,
									 oid=oid)
		transaction_runner(func)
	transaction.get().addAfterCommitHook(
					lambda success: success and gevent.spawn(_process_event))

@component.adapter(nti_interfaces.IModeledContent, IObjectRatedEvent)
def _object_rated(modeled, event):
	request = get_current_request()
	username = authenticated_userid(request) if request else None
	if username and event.category == LIKE_CAT_NAME:
		like = event.rating != 0
		oid = externalization.to_external_ntiid_oid(modeled)
		_process_like_event(username, oid, like)

@component.adapter(frm_interfaces.ITopic, IObjectRatedEvent)
def _topic_rated(topic, event):
	_object_rated(topic, event)

# utils

def install(db):

	from zope.annotation import interfaces as an_interfaces
	from zope.generations.utility import findObjectsProviding

	from contentratings.category import BASE_KEY
	from contentratings.storage import UserRatingStorage

	rels = collections.defaultdict(list)

	dataserver = component.getUtility(nti_interfaces.IDataserver)
	_users = nti_interfaces.IShardLayout(dataserver).users_folder
	rel_type = relationships.Like()

	def _lookup_like_rating_for_read(context, cat_name=LIKE_CAT_NAME):
		key = getattr(UserRatingStorage, 'annotation_key', BASE_KEY)
		key = str(key + '.' + cat_name)
		annotations = an_interfaces.IAnnotations(context, {})
		storage = annotations.get(key)
		return storage

	def _record_likeable(rels, obj):
		storage = _lookup_like_rating_for_read(obj) if obj is not None else None
		if storage is not None:
			oid = externalization.to_external_ntiid_oid(obj)
			for rating in storage.all_user_ratings():
				if rating.userid and rating.userid in _users:
					rels[rating.userid].append(oid)

	for entity in _users.itervalues():
		if nti_interfaces.IUser.providedBy(entity):

			# get all likeable objects
			for likeable in findObjectsProviding(entity, nti_interfaces.ILikeable):
				_record_likeable(rels, likeable)

			# check blogs
			blog = frm_interfaces.IPersonalBlog(entity)
			for topic in blog.values():
				_record_likeable(topic, blog)
				for comment in topic.values():
					_record_likeable(comment, blog)

		elif nti_interfaces.ICommunity.providedBy(entity):
			pass

	result = 0
	for username,likes in rels.items():
		# create nodes
		user = users.User.get_user(username)
		objs = [user]
		objs.extend(likes)
		nodes = db.create_nodes(*objs)
		assert len(nodes) == len(objs)

		# create relationships
		rels = []
		for i, n in enumerate(nodes[1:]):
			likeable = objs[i + 1]
			properties = component.getMultiAdapter((user, likeable, rel_type),
													graph_interfaces.IPropertyAdapter)
			adapted = component.getMultiAdapter((user, likeable, rel_type),
											 	 graph_interfaces.IUniqueAttributeAdapter)
			rels.append((nodes[0], rel_type, n, properties, adapted.key, adapted.value))

		# create relationships in batch
		rels = db.create_relationships(*rels)
		result += len(rels)

	return result
