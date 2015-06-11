#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from .interfaces import ILike
from .interfaces import IRate
from .interfaces import IView
from .interfaces import IReply
from .interfaces import IAuthor
from .interfaces import IBelong
from .interfaces import IEnroll
from .interfaces import IFollow
from .interfaces import IShared
from .interfaces import ICreated
from .interfaces import IFlagged
from .interfaces import IFeedback
from .interfaces import IFriendOf
from .interfaces import IMemberOf
from .interfaces import IParentOf
from .interfaces import ITaggedTo
from .interfaces import IUnenroll
from .interfaces import ICommentOn
from .interfaces import IContained
from .interfaces import IIsReplyOf
from .interfaces import IIsSharedWith
from .interfaces import ITakeAssessment
from .interfaces import IAssignmentFeedback

class _Singleton(object):
	_instances = {}
	def __new__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(_Singleton, cls).__new__(cls, *args, **kwargs)
		return cls._instances[cls]

@interface.implementer(IFriendOf)
class FriendOf(_Singleton):

	def __str__(self):
		return "IS_FRIEND_OF"
	__repr__ = __str__

@interface.implementer(IMemberOf)
class MemberOf(_Singleton):

	def __str__(self):
		return "IS_MEMBER_OF"
	__repr__ = __str__

@interface.implementer(IFollow)
class Follow(_Singleton):

	def __str__(self):
		return "FOLLOWS"
	__repr__ = __str__

@interface.implementer(IFlagged)
class Flagged(_Singleton):

	def __str__(self):
		return "HAS_FLAGGED"
	__repr__ = __str__

@interface.implementer(ICreated)
class Created(_Singleton):

	def __str__(self):
		return "HAS_CREATED"
	__repr__ = __str__

@interface.implementer(ILike)
class Like(_Singleton):

	def __str__(self):
		return "LIKES"
	__repr__ = __str__

@interface.implementer(IRate)
class Rate(_Singleton):

	def __str__(self):
		return "HAS_RATED"
	__repr__ = __str__

@interface.implementer(IAuthor)
class Author(_Singleton):

	def __str__(self):
		return "HAS_AUTHORED"
	__repr__ = __str__

@interface.implementer(IShared)
class Shared(_Singleton):

	def __str__(self):
		return "HAS_SHARED"
	__repr__ = __str__

@interface.implementer(IIsSharedWith)
class IsSharedWith(_Singleton):

	def __str__(self):
		return "IS_SHARED_WITH"
	__repr__ = __str__

@interface.implementer(ICommentOn)
class CommentOn(_Singleton):

	def __str__(self):
		return "HAS_COMMENTED_ON"
	__repr__ = __str__

@interface.implementer(ITaggedTo)
class TaggedTo(_Singleton):
	def __str__(self):
		return "IS_TAGGED_TO"
	__repr__ = __str__

@interface.implementer(IView)
class View(_Singleton):

	def __str__(self):
		return "HAS_VIEWED"
	__repr__ = __str__

@interface.implementer(ITakeAssessment)
class TakeAssessment(_Singleton):

	def __str__(self):
		return "HAS_TAKEN"
	__repr__ = __str__

@interface.implementer(IContained)
class Contained(_Singleton):

	def __str__(self):
		return "IS_CONTAINED"
	__repr__ = __str__

@interface.implementer(IFeedback)
class Feedback(_Singleton):

	def __str__(self):
		return "HAS_FEEDBACKED"
	__repr__ = __str__

@interface.implementer(IAssignmentFeedback)
class AssigmentFeedback(_Singleton):

	def __str__(self):
		return "ASM_FEEDBACKED"
	__repr__ = __str__

@interface.implementer(IParentOf)
class ParentOf(_Singleton):

	def __str__(self):
		return "IS_PARENT_OF"
	__repr__ = __str__

@interface.implementer(IIsReplyOf)
class IsReplyOf(_Singleton):

	def __str__(self):
		return "IS_REPLY_OF"
	__repr__ = __str__

@interface.implementer(IReply)
class Reply(_Singleton):

	def __str__(self):
		return "HAS_REPLIED_TO"
	__repr__ = __str__

@interface.implementer(IEnroll)
class Enroll(_Singleton):

	def __str__(self):
		return "HAS_ENROLLED"
	__repr__ = __str__
	
@interface.implementer(IUnenroll)
class Unenroll(_Singleton):

	def __str__(self):
		return "HAS_UNENROLLED"
	__repr__ = __str__
	
@interface.implementer(IBelong)
class Belong(_Singleton):

	def __str__(self):
		return "BELONG_TO"
	__repr__ = __str__
