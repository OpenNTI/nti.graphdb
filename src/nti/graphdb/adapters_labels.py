#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.chatserver.interfaces import IMeeting
from nti.chatserver.interfaces import IMessageInfo

from nti.contentlibrary.interfaces import IContentUnit

from nti.dataserver.interfaces import INote
from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import IEntity
from nti.dataserver.interfaces import IModeledContent
from nti.dataserver.interfaces import IDynamicSharingTargetFriendsList

from nti.dataserver.contenttypes.forums.interfaces import IBoard
from nti.dataserver.contenttypes.forums.interfaces import ITopic
from nti.dataserver.contenttypes.forums.interfaces import IForum
from nti.dataserver.contenttypes.forums.interfaces import IHeadlinePost

from .interfaces import ILabelAdapter

@interface.implementer(ILabelAdapter)
@component.adapter(interface.Interface)
def _GenericLabelAdpater(obj):
	return obj.__class__.__name__.title()

@component.adapter(IEntity)
@interface.implementer(ILabelAdapter)
def _EntityLabelAdpater(entity):
	return entity.__class__.__name__.title()

@component.adapter(IUser)
@interface.implementer(ILabelAdapter)
def _UserLabelAdpater(entity):
	return u'User'

@interface.implementer(ILabelAdapter)
@component.adapter(IDynamicSharingTargetFriendsList)
def _DFLLabelAdpater(context):
	return 'DFL'

@component.adapter(IModeledContent)
@interface.implementer(ILabelAdapter)
def _ModeledContentLabelAdpater(context):
	return context.__class__.__name__.title()

@component.adapter(INote)
def _NoteLabelAdpater(context):
	return u'Note'

@interface.implementer(ILabelAdapter)
def _CommentLabelAdpater(context):
	return u'Comment'

@interface.implementer(ILabelAdapter)
@component.adapter(IForum)
def _ForumLabelAdpater(context):
	return u"Forum"

@interface.implementer(ILabelAdapter)
@component.adapter(ITopic)
def _TopicLabelAdpater(context):
	return u'Topic'
	
@interface.implementer(ILabelAdapter)
@component.adapter(IBoard)
def _BoardLabelAdpater(context):
	return u"Board"

@component.adapter(IHeadlinePost)
@interface.implementer(ILabelAdapter)
def _HeadlinePostLabelAdpater(post):
	return ILabelAdapter(post.__parent__)

@interface.implementer(ILabelAdapter)
@component.adapter(IContentUnit)
def _ContentUnitLabelAdpater(context):
	return u"ContentUnit"

@component.adapter(IMeeting)
@interface.implementer(ILabelAdapter)
def _MeetingLabelAdpater(meeting):
	return u'Meeting'

@interface.implementer(ILabelAdapter)
@component.adapter(IMessageInfo)
def _MessageInfoLabelAdpater(message):
	return u'Message'

# @interface.implementer(ILabelAdapter)
# @component.adapter(asm_interfaces.IQuestionSet)
# def _QuestionSetLabelAdpater(obj):
# 	result = ('questionset',)
# 	return result
# 
# @interface.implementer(ILabelAdapter)
# @component.adapter(asm_interfaces.IQuestion)
# def _QuestionLabelAdpater(question):
# 	result = ('question',)
# 	return result
# 
# @interface.implementer(ILabelAdapter)
# @component.adapter(asm_interfaces.IQAssignment)
# def _AssignmentLabelAdpater(question):
# 	result = ('assignment',)
# 	return result
# 
# @interface.implementer(ILabelAdapter)
# @component.adapter(app_asm_interfaces.IUsersCourseAssignmentHistoryItemFeedback)
# def _AssignmentFeedbackLabelAdpater(modeled):
# 	return ("assignmentFeedback",)
# 
# @interface.implementer(ILabelAdapter)
# @component.adapter(asm_interfaces.IQAssessedPart)
# def _QAssessedPartLabelAdpater(obj):
# 	return ("assessedPart",)
# 
# @interface.implementer(ILabelAdapter)
# @component.adapter(asm_interfaces.IQAssessedQuestion)
# def _QAssessedQuestionLabelAdpater(obj):
# 	return ("assessedQuestion",)
# 
# @interface.implementer(ILabelAdapter)
# @component.adapter(asm_interfaces.IQAssessedQuestionSet)
# def _QAssessedQuestionSetLabelAdpater(obj):
# 	return ("assessedQuestionSet",)
# 
# 
# @interface.implementer(ILabelAdapter)
# @component.adapter(search_interfaces.ISearchQuery)
# def _SearchQueryLabelAdpater(query):
# 	result = ('searchquery',)
# 	return result
# 
# @interface.implementer(ILabelAdapter)
# @component.adapter(IContainer)
# def _ContainerLabelAdpater(container):
# 	result = ('container',)
# 	return result
# 
# @interface.implementer(ILabelAdapter)
# @component.adapter(store_interfaces.IPurchaseAttempt)
# def _PurchaseAttemptLabelAdpater(pa):
# 	result = ("purchase",)
# 	if store_interfaces.IEnrollmentAttempt.providedBy(pa):
# 		result = ("enrollment",)
# 	elif store_interfaces.IInvitationPurchaseAttempt.providedBy(pa):
# 		result = ("purchaseInvitation",)
# 	elif store_interfaces.IRedeemedPurchaseAttempt.providedBy(pa):
# 		result = ("purchaseRedeemed",)
# 	return result
