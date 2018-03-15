#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from contentratings.category import BASE_KEY

from contentratings.interfaces import IObjectRatedEvent

from contentratings.storage import UserRatingStorage

from zope import component

from zope.annotation.interfaces import IAnnotations

from nti.dataserver.interfaces import IRatable
from nti.dataserver.interfaces import ILikeable

from nti.dataserver.rating import IObjectUnratedEvent

from nti.graphdb import create_job
from nti.graphdb import get_graph_db
from nti.graphdb import get_job_queue

from nti.graphdb.common import get_oid
from nti.graphdb.common import get_entity
from nti.graphdb.common import get_current_principal_id

from nti.graphdb.interfaces import IObjectProcessor

from nti.graphdb.relationships import Like
from nti.graphdb.relationships import Rate

from nti.ntiids.ntiids import find_object_with_ntiid

#: Like category name
LIKE_CAT_NAME = 'likes'

#: Rating category name
RATING_CAT_NAME = 'rating'

logger = __import__('logging').getLogger(__name__)


def get_relationship(db, username, oid, rel_type):
    result = None
    author = get_entity(username)
    obj = find_object_with_ntiid(oid)
    if obj is not None and author is not None:
        result = db.match(author, obj, rel_type)
    return result


def add_relationship(db, username, oid, rel_type, properties=None):
    result = None
    author = get_entity(username)
    obj = find_object_with_ntiid(oid)
    if obj is not None and author is not None:
        result = db.create_relationship(author, obj, rel_type, 
										properties=properties)
        logger.debug("%s relationship %s created", rel_type, result)
    return result


def remove_relationship(db, username, oid, rel_type):
    result = False
    rels = get_relationship(db, username, oid, rel_type)
    if rels:
        db.delete_relationships(*rels)
        logger.debug("%s relationship deleted", rel_type)
        result = True
    return result


# like


def add_like_relationship(db, username, oid):
    if not get_relationship(db, username, oid, Like()):
        result = add_relationship(db, username, oid, Like())
    return result


def remove_like_relationship(db, username, oid):
    result = remove_relationship(db, username, oid, Like())
    return result


def process_like_event(db, username, oid, is_like=True):
    queue = get_job_queue()
    if is_like:
        job = create_job(add_like_relationship, db=db,
                         username=username, oid=oid)
    else:
        job = create_job(remove_like_relationship, db=db,
                         username=username, oid=oid)
    queue.put(job)


# rate


def remove_rate_relationship(db, username, oid):
    result = remove_relationship(db, username, oid, Rate())
    return result


def add_rate_relationship(db, username, oid, rating, check_existing=False):
    if not check_existing or not get_relationship(db, username, oid, Rate()):
        rating = rating if rating is not None else 0
        # remove previous if present
        remove_rate_relationship(db, username, oid)
        # add relationship
        result = add_relationship(db, username, oid, Rate(),
                                  properties={"rating": rating})
        return result


def process_rate_event(db, username, oid, rating=None, is_rate=True):
    queue = get_job_queue()
    if is_rate:
        job = create_job(add_rate_relationship, db=db, username=username,
                         oid=oid, rating=rating)
    else:
        job = create_job(remove_rate_relationship, db=db,
                         username=username, oid=oid)
    queue.put(job)


@component.adapter(IObjectRatedEvent)
def _object_rated(event):
    db = get_graph_db()
    modeled = event.object
    username = get_current_principal_id()
    if username and db is not None:
        oid = get_oid(modeled)
        is_rated = not IObjectUnratedEvent.providedBy(event)
        if event.category == LIKE_CAT_NAME:
            process_like_event(db, username, oid, is_rated)
        elif event.category == RATING_CAT_NAME:
            rating = event.rating
            rating = getattr(rating, '_rating', rating)
            process_rate_event(db, username, oid, rating, is_rated)

       
# utils


def get_ratings(context, category):
    # Get the key from the storage, or use a default
    key = getattr(UserRatingStorage, 'annotation_key', BASE_KEY)
    # Append the category name to the dotted annotation key name
    key = str(key + '.' + category)  # # see ds rating.lookup_rating_for_read
    storage = IAnnotations(context, {}).get(key)
    if storage is not None:
        return storage.all_user_ratings()
    return ()


def record_likeable(db, obj):
    result = 0
    queue = get_job_queue()
    oid = get_oid(obj)
    for rating in get_ratings(obj, LIKE_CAT_NAME):
        username = rating.userid or u''
        if get_entity(username) is not None:
            job = create_job(add_like_relationship, db=db,
                             username=username, oid=oid)
            queue.put(job)
            result += 1
    return result


def record_ratings(db, obj):
    result = 0
    queue = get_job_queue()
    oid = get_oid(obj)
    for rating in get_ratings(obj, RATING_CAT_NAME):
        username = rating.userid or u''
        if get_entity(username) is not None:
            job = create_job(add_rate_relationship, db=db, username=username,
                             oid=oid, rating=rating, check_existing=True)
            queue.put(job)
            result += 1
    return result


component.moduleProvides(IObjectProcessor)


def init(db, obj):
    result = 0
    if ILikeable.providedBy(obj):
        result = record_likeable(db, obj)
    if IRatable.providedBy(obj):
        result = record_ratings(db, obj)
    return result > 0
