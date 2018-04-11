#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from nti.graphdb.interfaces import ILike
from nti.graphdb.interfaces import IRate
from nti.graphdb.interfaces import IReply
from nti.graphdb.interfaces import IAuthor
from nti.graphdb.interfaces import IBelong
from nti.graphdb.interfaces import IBought
from nti.graphdb.interfaces import IFollow
from nti.graphdb.interfaces import IShared
from nti.graphdb.interfaces import IViewed
from nti.graphdb.interfaces import ICreated
from nti.graphdb.interfaces import IFlagged
from nti.graphdb.interfaces import IFeedback
from nti.graphdb.interfaces import IFriendOf
from nti.graphdb.interfaces import IMemberOf
from nti.graphdb.interfaces import IParentOf
from nti.graphdb.interfaces import ITaggedTo
from nti.graphdb.interfaces import ICommentOn
from nti.graphdb.interfaces import IContained
from nti.graphdb.interfaces import IIsReplyOf
from nti.graphdb.interfaces import IIsSharedWith
from nti.graphdb.interfaces import ITakenInquiry
from nti.graphdb.interfaces import ITakenAssessment
from nti.graphdb.interfaces import IAssignmentFeedback

logger = __import__('logging').getLogger(__name__)


class Singleton(object):

    instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls.instances:
            cls.instances[cls] = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls.instances[cls]


@interface.implementer(IFriendOf)
class FriendOf(Singleton):

    def __str__(self):
        return "IS_FRIEND_OF"
    __repr__ = __str__


@interface.implementer(IMemberOf)
class MemberOf(Singleton):

    def __str__(self):
        return "IS_MEMBER_OF"
    __repr__ = __str__


@interface.implementer(IFollow)
class Follow(Singleton):

    def __str__(self):
        return "FOLLOWS"
    __repr__ = __str__


@interface.implementer(IFlagged)
class Flagged(Singleton):

    def __str__(self):
        return "HAS_FLAGGED"
    __repr__ = __str__


@interface.implementer(ICreated)
class Created(Singleton):

    def __str__(self):
        return "HAS_CREATED"
    __repr__ = __str__


@interface.implementer(ILike)
class Like(Singleton):

    def __str__(self):
        return "LIKES"
    __repr__ = __str__


@interface.implementer(IRate)
class Rate(Singleton):

    def __str__(self):
        return "HAS_RATED"
    __repr__ = __str__


@interface.implementer(IAuthor)
class Author(Singleton):

    def __str__(self):
        return "HAS_AUTHORED"
    __repr__ = __str__


@interface.implementer(IShared)
class Shared(Singleton):

    def __str__(self):
        return "HAS_SHARED"
    __repr__ = __str__


@interface.implementer(IIsSharedWith)
class IsSharedWith(Singleton):

    def __str__(self):
        return "IS_SHARED_WITH"
    __repr__ = __str__


@interface.implementer(ICommentOn)
class CommentOn(Singleton):

    def __str__(self):
        return "HAS_COMMENTED_ON"
    __repr__ = __str__


@interface.implementer(ITaggedTo)
class TaggedTo(Singleton):
    def __str__(self):
        return "IS_TAGGED_TO"
    __repr__ = __str__


@interface.implementer(IViewed)
class Viewed(Singleton):

    def __str__(self):
        return "HAS_VIEWED"
    __repr__ = __str__


@interface.implementer(ITakenAssessment)
class TakenAssessment(Singleton):

    def __str__(self):
        return "HAS_TAKEN_ASSESMENT"
    __repr__ = __str__


@interface.implementer(ITakenInquiry)
class TakenInquiry(Singleton):

    def __str__(self):
        return "HAS_TAKEN_INQUIRY"
    __repr__ = __str__


@interface.implementer(IContained)
class Contained(Singleton):

    def __str__(self):
        return "IS_CONTAINED"
    __repr__ = __str__


@interface.implementer(IFeedback)
class Feedback(Singleton):

    def __str__(self):
        return "HAS_FEEDBACKED"
    __repr__ = __str__


@interface.implementer(IAssignmentFeedback)
class AssigmentFeedback(Singleton):

    def __str__(self):
        return "ASM_FEEDBACKED"
    __repr__ = __str__


@interface.implementer(IParentOf)
class ParentOf(Singleton):

    def __str__(self):
        return "IS_PARENT_OF"
    __repr__ = __str__


@interface.implementer(IIsReplyOf)
class IsReplyOf(Singleton):

    def __str__(self):
        return "IS_REPLY_OF"
    __repr__ = __str__


@interface.implementer(IReply)
class Reply(Singleton):

    def __str__(self):
        return "HAS_REPLIED_TO"
    __repr__ = __str__


@interface.implementer(IBelong)
class Belong(Singleton):

    def __str__(self):
        return "BELONG_TO"
    __repr__ = __str__


@interface.implementer(IBought)
class Bought(Singleton):

    def __str__(self):
        return "HAS_BOUGHT"
    __repr__ = __str__
