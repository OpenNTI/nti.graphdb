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
from .interfaces import IAuthor
from .interfaces import IFollow
from .interfaces import IShared
from .interfaces import ICreated
from .interfaces import IFlagged
from .interfaces import IFriendOf
from .interfaces import IMemberOf
from .interfaces import IIsSharedTo

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

@interface.implementer(IIsSharedTo)
class IsSharedTo(_Singleton):

	def __str__(self):
		return "IS_SHARED_TO"
	__repr__ = __str__

# @interface.implementer(graph_interfaces.IParentOf)
# class ParentOf(_Singleton):
# 
# 	def __str__(self):
# 		return "IS_PARENT_OF"
# 	__repr__ = __str__
# 
# @interface.implementer(graph_interfaces.ICommentOn)
# class CommentOn(_Singleton):
# 
# 	def __str__(self):
# 		return "HAS_COMMENTED_ON"
# 	__repr__ = __str__
# 
# @interface.implementer(graph_interfaces.ITakeAssessment)
# class TakeAssessment(_Singleton):
# 
# 	def __str__(self):
# 		return "HAS_TAKEN"
# 	__repr__ = __str__
# 
# @interface.implementer(graph_interfaces.IReply)
# class Reply(_Singleton):
# 
# 	def __str__(self):
# 		return "HAS_REPLIED_TO"
# 	__repr__ = __str__
# 
# @interface.implementer(graph_interfaces.IIsReplyOf)
# class IsReplyOf(_Singleton):
# 
# 	def __str__(self):
# 		return "IS_REPLY_OF"
# 	__repr__ = __str__
#
# @interface.implementer(graph_interfaces.IFeedback)
# class Feedback(_Singleton):
# 
# 	def __str__(self):
# 		return "HAS_FEEDBACKED"
# 	__repr__ = __str__
# 
# @interface.implementer(graph_interfaces.IAssignmentFeedback)
# class AssigmentFeedback(_Singleton):
# 
# 	def __str__(self):
# 		return "ASM_FEEDBACKED"
# 	__repr__ = __str__
# 
# @interface.implementer(graph_interfaces.ISearch)
# class Search(_Singleton):
# 
# 	def __str__(self):
# 		return "HAS_SEARCHED"
# 	__repr__ = __str__
# 
# @interface.implementer(graph_interfaces.ITaggedTo)
# class TaggedTo(_Singleton):
# 
# 	def __str__(self):
# 		return "IS_TAGGED_TO"
# 	__repr__ = __str__
# 
# @interface.implementer(graph_interfaces.IContained)
# class Contained(_Singleton):
# 
# 	def __str__(self):
# 		return "IS_CONTAINED"
# 	__repr__ = __str__
# 
# @interface.implementer(graph_interfaces.IView)
# class View(_Singleton):
# 
# 	def __str__(self):
# 		return "HAS_VIEWED"
# 	__repr__ = __str__
# 
# @interface.implementer(graph_interfaces.ISubmit)
# class Submit(_Singleton):
# 
# 	def __str__(self):
# 		return "HAS_SUBMITTED"
# 	__repr__ = __str__
# 
# @interface.implementer(graph_interfaces.IBelong)
# class Belong(_Singleton):
# 
# 	def __str__(self):
# 		return "BELONG_TO"
# 	__repr__ = __str__
