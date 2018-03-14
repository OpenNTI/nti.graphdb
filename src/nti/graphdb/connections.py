#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component

from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectRemovedEvent
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

from nti.graphdb.interfaces import IObjectProcessor

from nti.graphdb.relationships import Follow
from nti.graphdb.relationships import FriendOf
from nti.graphdb.relationships import MemberOf

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.schema.eqhash import EqHash

logger = __import__('logging').getLogger(__name__)


@EqHash('from_', 'to_')
class Relationship(object):

    def __init__(self, from_, to_, **kwargs):
        self.to_ = to_
        self.from_ = from_
        self.__dict__.update(kwargs)


def get_graph_connections(db, entity, type_):
    result = set()
    rels = db.match(start=entity, type_=type_)
    for rel in rels:
        end = db.get_node(rel.end)
        username = end.properties.get('username') if end is not None else None
        friend = get_entity(username) if username else None
        if friend is not None:
            result.add(Relationship(entity, friend, rel=rel))
    return result


def update_connections(db, entity,
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
        to_create.add(fship.to_)
        to_create.add(fship.from_)
    if to_create:
        to_create = list(to_create)
        db.create_nodes(*to_create)

    # add new relationships
    result = []
    for fship in to_add:
        rel = db.create_relationship(fship.from_, fship.to_, rel_type)
        logger.debug("Connection relationship %s created", rel)
        result.append(rel)
    return result


# friendship


def graph_friends(db, entity):
    result = get_graph_connections(db, entity, FriendOf())
    return result


def zodb_friends(entity):
    result = set()
    friendlists = getattr(entity, 'friendsLists', {}).values()
    for friendlist in friendlists:
        for friend in friendlist:
            result.add(Relationship(entity, friend))
    return result


def update_friendships(db, entity):
    entity = get_entity(entity)
    if entity is not None:
        stored_db_relations = zodb_friends(entity)
        graph_relations = graph_friends(db, entity)
        result = update_connections(db, entity,
                                    graph_relations,
                                    stored_db_relations,
                                    FriendOf())
        return result


def process_friendslist_event(db, obj):
    if not IDynamicSharingTargetFriendsList.providedBy(obj):
        username = getattr(obj.creator, 'username', obj.creator)
        queue = get_job_queue()
        job = create_job(update_friendships, db=db, entity=username)
        queue.put(job)


@component.adapter(IFriendsList, IObjectAddedEvent)
def _friendslist_added(obj, unused_event):
    db = get_graph_db()
    if db is not None:
        process_friendslist_event(db, obj)


@component.adapter(IFriendsList, IObjectModifiedEvent)
def _friendslist_modified(obj, unused_event):
    db = get_graph_db()
    if db is not None:
        process_friendslist_event(db, obj)


@component.adapter(IFriendsList, IObjectRemovedEvent)
def _friendslist_deleted(obj, unused_event):
    db = get_graph_db()
    if db is not None:
        process_friendslist_event(db, obj)


# membership


def graph_memberships(db, entity):
    result = get_graph_connections(db, entity, MemberOf())
    return result


def zodb_memberships(entity):
    result = set()
    everyone = get_entity('Everyone')
    memberships = getattr(entity, 'dynamic_memberships', None)
    for x in memberships or ():
        if x != everyone:
            result.add(Relationship(entity, x))
    return result


def update_memberships(db, entity):
    entity = get_entity(entity)
    if entity is not None:
        zodb_relations = zodb_memberships(entity)
        graph_relations = graph_memberships(db, entity)
        result = update_connections(db, entity,
                                    graph_relations,
                                    zodb_relations,
                                    MemberOf())
        return result


def process_start_membership(db, source, target):
    source = get_entity(source)
    target = find_object_with_ntiid(target)
    if source is not None and target is not None:
        result = db.create_relationship(source, target, MemberOf())
        logger.debug("Entity membership relationship %s created", result)
        return result


def process_stop_membership(db, source, target):
    source = get_entity(source)
    target = find_object_with_ntiid(target)
    if source is not None and target is not None:
        rels = db.match(start=source, end=target, type_=MemberOf())
        if rels:
            db.delete_relationships(*rels)
            logger.debug("%s entity membership relationship(s) removed",
                         len(rels))
            return True


def process_membership_event(db, event):
    queue = get_job_queue()
    everyone = get_entity('Everyone')
    source, target = event.object, event.target
    if target != everyone:
        source = source.username
        target = get_oid(target)
        start_membership = IStartDynamicMembershipEvent.providedBy(event)
        if start_membership:
            job = create_job(process_start_membership, db=db,
                             source=source, target=target)
        else:
            job = create_job(process_stop_membership, db=db,
                             source=source, target=target)
        queue.put(job)


@component.adapter(IStartDynamicMembershipEvent)
def _start_dynamic_membership_event(event):
    db = get_graph_db()
    if db is not None:
        process_membership_event(db, event)


@component.adapter(IStopDynamicMembershipEvent)
def _stop_dynamic_membership_event(event):
    db = get_graph_db()
    if db is not None:
        process_membership_event(db, event)


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
        rels = db.match(source, followed, Follow())
        if rels:
            db.delete_relationships(*rels)
            logger.debug("%s follow relationship(s) removed", len(rels))
            return True


def process_follow_event(db, event):
    source = getattr(event.object, 'username', event.object)
    stop_following = IStopFollowingEvent.providedBy(event)
    if stop_following:
        followed = event.not_following
    else:
        followed = event.now_following
    followed = getattr(followed, 'username', followed)

    queue = get_job_queue()
    if stop_following:
        job = create_job(process_unfollow, db=db,
                         source=source, followed=followed)
    else:
        job = create_job(process_follow, db=db,
                         source=source, followed=followed)
    queue.put(job)


@component.adapter(IEntityFollowingEvent)
def _start_following_event(event):
    db = get_graph_db()
    if db is not None:
        process_follow_event(db, event)


@component.adapter(IStopFollowingEvent)
def _stop_following_event(event):
    db = get_graph_db()
    if db is not None:
        process_follow_event(db, event)


def graph_following(db, entity):
    result = get_graph_connections(db, entity, type_=Follow())
    return result


def zodb_following(entity):
    result = set()
    entities_followed = getattr(entity, 'entities_followed', ())
    for followed in entities_followed:
        result.add(Relationship(entity, followed))
    return result


def update_following(db, entity):
    zodb_relations = zodb_following(entity)
    graph_relations = graph_following(db, entity)
    result = update_connections(db, entity,
                                graph_relations,
                                zodb_relations,
                                Follow())
    return result


# utils


def process_following(db, user):
    source = user.username
    queue = get_job_queue()
    job = create_job(update_following, db=db, entity=source)
    queue.put(job)


def process_memberships(db, user):
    source = user.username
    queue = get_job_queue()
    job = create_job(update_memberships, db=db, entity=source)
    queue.put(job)


def process_friendships(db, user):
    queue = get_job_queue()
    job = create_job(update_friendships, db=db, entity=user)
    queue.put(job)


component.moduleProvides(IObjectProcessor)


def init(db, obj):
    result = False
    if IUser.providedBy(obj):
        process_following(db, obj)
        process_memberships(db, obj)
        process_friendships(db, obj)
        result = True
    return result
