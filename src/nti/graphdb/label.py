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

from nti.assessment.interfaces import IQuestion
from nti.assessment.interfaces import IQAssignment
from nti.assessment.interfaces import IQuestionSet

from nti.chatserver.interfaces import IMeeting
from nti.chatserver.interfaces import IMessageInfo

from nti.contentlibrary.interfaces import IContentUnit

from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseCatalogEntry

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

@component.adapter(IForum)
@interface.implementer(ILabelAdapter)
def _ForumLabelAdpater(context):
	return u"Forum"

@component.adapter(ITopic)
@interface.implementer(ILabelAdapter)
def _TopicLabelAdpater(context):
	return u'Topic'

@component.adapter(IBoard)
@interface.implementer(ILabelAdapter)
def _BoardLabelAdpater(context):
	return u"Board"

@component.adapter(IHeadlinePost)
@interface.implementer(ILabelAdapter)
def _HeadlinePostLabelAdpater(post):
	return ILabelAdapter(post.__parent__)

@component.adapter(IContentUnit)
@interface.implementer(ILabelAdapter)
def _ContentUnitLabelAdpater(context):
	return u"ContentUnit"

@component.adapter(IMeeting)
@interface.implementer(ILabelAdapter)
def _MeetingLabelAdpater(meeting):
	return u'Meeting'

@component.adapter(IMessageInfo)
@interface.implementer(ILabelAdapter)
def _MessageInfoLabelAdpater(message):
	return u'Message'

@component.adapter(IQuestion)
@interface.implementer(ILabelAdapter)
def _QuestionLabelAdpater(context):
	return u"Question"

@component.adapter(IQuestionSet)
@interface.implementer(ILabelAdapter)
def _QuestionSetLabelAdpater(meeting):
	return u'QuestionSet'

@component.adapter(IQAssignment)
@interface.implementer(ILabelAdapter)
def _AssignmentLabelAdpater(message):
	return u'Assignment'

@component.adapter(ICourseInstance)
@interface.implementer(ILabelAdapter)
def _CourseInstanceLabelAdpater(message):
	return u'CourseInstance'

@interface.implementer(ILabelAdapter)
@component.adapter(ICourseCatalogEntry)
def _CourseCatalogEntryLabelAdpater(message):
	return u'CatalogEntry'
