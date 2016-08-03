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

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import IFriendsList
from nti.dataserver.interfaces import IStopFollowingEvent
from nti.dataserver.interfaces import IEntityFollowingEvent
from nti.dataserver.interfaces import IStopDynamicMembershipEvent
from nti.dataserver.interfaces import IStartDynamicMembershipEvent
from nti.dataserver.interfaces import IDynamicSharingTargetFriendsList

from nti.graphdb import create_job
from nti.graphdb import get_graph_db
from nti.graphdb import get_job_queue

from nti.graphdb.common import get_oid
from nti.graphdb.common import get_entity
from nti.graphdb.common import get_node_pk

from nti.graphdb.interfaces import IObjectProcessor

from nti.graphdb.relationships import Follow
from nti.graphdb.relationships import FriendOf
from nti.graphdb.relationships import MemberOf

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.schema.eqhash import EqHash

@EqHash('_from', '_to')
class _Relationship(object):

	def __init__(self, _from, _to, **kwargs):
		self._to = _to
		self._from = _from
		self.__dict__.update(kwargs)

def _get_graph_connections(db, entity, rel_type, loose=True):
	result = set()
	rels = db.match(start=entity, rel_type=rel_type, loose=loose)
	for rel in rels:
		end = db.get_node(rel.end)
		username = end.properties.get('username') if end is not None else None
		friend = get_entity(username) if username else None
		if friend is not None:
			result.add(_Relationship(entity, friend, rel=rel))
	return result

def _update_connections(db, entity,
						current_graph_relations,
						stored_db_relations,
					 	rel_type):
	# computer db/graph relationships
	entity = get_entity(entity)
	to_add = stored_db_relations - current_graph_relations
	to_remove = current_graph_relations - stored_db_relations

	# remove old relationships
	if to_remove:
		db.delete_relationships(*[x.rel for x in to_remove])
		logger.debug("%s connection relationship(s) deleted", len(to_remove))

	# create nodes
	to_create = set()
	for fship in to_add:
		to_create.add(fship._to)
		to_create.add(fship._from)
	if to_create:
		to_create = list(to_create)
		db.create_nodes(*to_create)

	# add new relationships
	result = []
	for fship in to_add:
		_to = fship._to
		_from = fship._from
		rel = db.create_relationship(_from, _to, rel_type)
		logger.debug("Connection relationship %s created", rel)
		result.append(rel)
	return result

# friendship

def graph_friends(db, entity):
	result = _get_graph_connections(db, entity, rel_type=FriendOf())
	return result

def zodb_friends(entity):
	result = set()
	friendlists = getattr(entity, 'friendsLists', {}).values()
	for fnd_list in friendlists:
		for friend in fnd_list:
			result.add(_Relationship(entity, friend))
	return result

def update_friendships(db, entity):
	entity = get_entity(entity)
	if entity is not None:
		stored_db_relations = zodb_friends(entity)
		graph_relations = graph_friends(db, entity)
		result = _update_connections(db, entity,
	 								 graph_relations,
	 								 stored_db_relations,
	 								 FriendOf())
		return result
	return ()

def _process_friendslist_event(db, obj):
	if IDynamicSharingTargetFriendsList.providedBy(obj):
		return  # pragma no cover

	username = getattr(obj.creator, 'username', obj.creator)
	queue = get_job_queue()
	job = create_job(update_friendships, db=db, entity=username)
	queue.put(job)

@component.adapter(IFriendsList, IObjectAddedEvent)
def _friendslist_added(obj, event):
	db = get_graph_db()
	if db is not None:
		_process_friendslist_event(db, obj)

@component.adapter(IFriendsList, IObjectModifiedEvent)
def _friendslist_modified(obj, event):
	db = get_graph_db()
	if db is not None:
		_process_friendslist_event(db, obj)

@component.adapter(IFriendsList, IIntIdRemovedEvent)
def _friendslist_deleted(obj, event):
	db = get_graph_db()
	if db is not None:
		_process_friendslist_event(db, obj)

# membership

def graph_memberships(db, entity):
	result = _get_graph_connections(db, entity, rel_type=MemberOf())
	return result

def zodb_memberships(entity):
	result = set()
	everyone = get_entity('Everyone')
	memberships = getattr(entity, 'dynamic_memberships', None)
	for x in memberships or ():
		if x != everyone:
			result.add(_Relationship(entity, x))
	return result

def update_memberships(db, entity):
	entity = get_entity(entity)
	if entity is not None:
		zodb_relations = zodb_memberships(entity)
		graph_relations = graph_memberships(db, entity)
		result = _update_connections(db, entity,
									 graph_relations,
									 zodb_relations,
									 MemberOf())
		return result
	return ()

def process_start_membership(db, source, target):
	source = get_entity(source)
	target = find_object_with_ntiid(target)
	if source is not None and target is not None:
		rel = db.create_relationship(source, target, MemberOf())
		logger.debug("Entity membership relationship %s created", rel)
		return rel
	return None

def process_stop_membership(db, source, target):
	source = get_entity(source)
	target = find_object_with_ntiid(target)
	if source is not None and target is not None:
		rels = db.match(start=source, end=target, rel_type=MemberOf())
		if rels:
			db.delete_relationships(*rels)
			logger.debug("%s entity membership relationship(s) removed", len(rels))
			return True
	return False

def _process_membership_event(db, event):
	everyone = get_entity('Everyone')
	source, target = event.object, event.target
	if target == everyone:
		return  # pragma no cover

	source = source.username
	target = get_oid(target)
	start_membership = IStartDynamicMembershipEvent.providedBy(event)

	queue = get_job_queue()
	if start_membership:
		job = create_job(process_start_membership, db=db, source=source, target=target)
	else:
		job = create_job(process_stop_membership, db=db, source=source, target=target)
	queue.put(job)

@component.adapter(IStartDynamicMembershipEvent)
def _start_dynamic_membership_event(event):
	db = get_graph_db()
	if db is not None:
		_process_membership_event(db, event)

@component.adapter(IStopDynamicMembershipEvent)
def _stop_dynamic_membership_event(event):
	db = get_graph_db()
	if db is not None:
		_process_membership_event(db, event)

def _do_delete_dfl(db, label, key, value):
	node = db.get_indexed_node(label, key, value)
	if node is not None:
		db.delete_node(node)
		logger.debug("Node %s deleted", node)
		return True
	return False

def _process_dfl_removal(db, obj):
	pk = get_node_pk(obj)
	if pk is not None:
		queue = get_job_queue()
		job = create_job(_do_delete_dfl, db=db,
						 label=pk.label,
						 key=pk.key,
						 value=pk.value)
		queue.put(job)

@component.adapter(IDynamicSharingTargetFriendsList, IIntIdRemovedEvent)
def _dfl_deleted(obj, event):
	db = get_graph_db()
	if db is not None:
		_process_dfl_removal(db, obj)

# follow/unfollow

def process_follow(db, source, followed):
	source = get_entity(source)
	followed = get_entity(followed)
	if source is not None and followed is not None:
		rel = db.create_relationship(source, followed, Follow())
		logger.debug("Follow relationship %s created", rel)
		return rel
	return None

def process_unfollow(db, source, followed):
	source = get_entity(source)
	followed = get_entity(followed)
	if source is not None and followed is not None:
		rels = db.match(start=source, end=followed, rel_type=Follow())
		if rels:
			db.delete_relationships(*rels)
			logger.debug("%s follow relationship(s) removed", len(rels))
			return True
	return False

def _process_follow_event(db, event):
	source = getattr(event.object, 'username', event.object)
	stop_following = IStopFollowingEvent.providedBy(event)
	followed = event.not_following if stop_following else event.now_following
	followed = getattr(followed, 'username', followed)

	queue = get_job_queue()
	if stop_following:
		job = create_job(process_unfollow, db=db, source=source, followed=followed)
	else:
		job = create_job(process_follow, db=db, source=source, followed=followed)
	queue.put(job)

@component.adapter(IEntityFollowingEvent)
def _start_following_event(event):
	db = get_graph_db()
	if db is not None:
		_process_follow_event(db, event)

@component.adapter(IStopFollowingEvent)
def _stop_following_event(event):
	db = get_graph_db()
	if db is not None:
		_process_follow_event(db, event)

def graph_following(db, entity):
	result = _get_graph_connections(db, entity, rel_type=Follow())
	return result

def zodb_following(entity):
	result = set()
	entities_followed = getattr(entity, 'entities_followed', ())
	for followed in entities_followed:
		result.add(_Relationship(entity, followed))
	return result

def update_following(db, entity):
	zodb_relations = zodb_following(entity)
	graph_relations = graph_following(db, entity)
	result = _update_connections(db, entity,
								 graph_relations,
								 zodb_relations,
								 Follow())
	return result

# utils

def _process_following(db, user):
	source = user.username
	queue = get_job_queue()
	job = create_job(update_following, db=db, entity=source)
	queue.put(job)

def _process_memberships(db, user):
	source = user.username
	queue = get_job_queue()
	job = create_job(update_memberships, db=db, entity=source)
	queue.put(job)

def _process_friendships(db, user):
	queue = get_job_queue()
	job = create_job(update_friendships, db=db, entity=user)
	queue.put(job)

component.moduleProvides(IObjectProcessor)

def init(db, obj):
	result = False
	if IUser.providedBy(obj):
		_process_following(db, obj)
		_process_memberships(db, obj)
		_process_friendships(db, obj)
		result = True
	return result
