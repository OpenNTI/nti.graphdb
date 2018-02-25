#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from nti.assessment.interfaces import IQPoll
from nti.assessment.interfaces import IQSurvey
from nti.assessment.interfaces import IQuestion
from nti.assessment.interfaces import IQAssignment
from nti.assessment.interfaces import IQuestionSet

from nti.chatserver.interfaces import IMeeting
from nti.chatserver.interfaces import IMessageInfo

from nti.contentlibrary.interfaces import IContentUnit
from nti.contentlibrary.interfaces import IContentPackage

from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseOutlineNode
from nti.contenttypes.courses.interfaces import ICourseCatalogEntry
from nti.contenttypes.courses.interfaces import ICourseOutlineContentNode
from nti.contenttypes.courses.interfaces import ICourseOutlineCalendarNode
from nti.contenttypes.courses.interfaces import ICourseInstanceEnrollmentRecord

from nti.contenttypes.presentation.interfaces import IPresentationAsset

from nti.dataserver.interfaces import INote
from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import IEntity
from nti.dataserver.interfaces import IModeledContent
from nti.dataserver.interfaces import IDynamicSharingTargetFriendsList

from nti.dataserver.contenttypes.forums.interfaces import IBoard
from nti.dataserver.contenttypes.forums.interfaces import ITopic
from nti.dataserver.contenttypes.forums.interfaces import IForum
from nti.dataserver.contenttypes.forums.interfaces import IHeadlinePost

from nti.graphdb.interfaces import IContainer
from nti.graphdb.interfaces import ILabelAdapter

from nti.schema.interfaces import find_most_derived_interface

logger = __import__('logging').getLogger(__name__)


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
def _UserLabelAdpater(unused_entity):
    return u'User'


@interface.implementer(ILabelAdapter)
@component.adapter(IDynamicSharingTargetFriendsList)
def _DFLLabelAdpater(unused_context):
    return u'DFL'


@component.adapter(IModeledContent)
@interface.implementer(ILabelAdapter)
def _ModeledContentLabelAdpater(context):
    return context.__class__.__name__.title()


@component.adapter(INote)
def _NoteLabelAdpater(unused_context):
    return u'Note'


@interface.implementer(ILabelAdapter)
def _CommentLabelAdpater(unused_context):
    return u'Comment'


@component.adapter(IForum)
@interface.implementer(ILabelAdapter)
def _ForumLabelAdpater(unused_context):
    return u"Forum"


@component.adapter(ITopic)
@interface.implementer(ILabelAdapter)
def _TopicLabelAdpater(unused_context):
    return u'Topic'


@component.adapter(IBoard)
@interface.implementer(ILabelAdapter)
def _BoardLabelAdpater(unused_context):
    return u"Board"


@component.adapter(IHeadlinePost)
@interface.implementer(ILabelAdapter)
def _HeadlinePostLabelAdpater(post):
    return ILabelAdapter(post.__parent__)


@component.adapter(IContentPackage)
@interface.implementer(ILabelAdapter)
def _ContentPackageLabelAdpater(unused_context):
    return u"ContentPackage"


@component.adapter(IContentUnit)
@interface.implementer(ILabelAdapter)
def _ContentUnitLabelAdpater(unused_context):
    return u"ContentUnit"


@component.adapter(IMeeting)
@interface.implementer(ILabelAdapter)
def _MeetingLabelAdpater(unused_meeting):
    return u'Meeting'


@component.adapter(IMessageInfo)
@interface.implementer(ILabelAdapter)
def _MessageInfoLabelAdpater(unused_message):
    return u'Message'


@component.adapter(IQuestion)
@interface.implementer(ILabelAdapter)
def _QuestionLabelAdpater(unused_obj):
    return u"Question"


@component.adapter(IQuestionSet)
@interface.implementer(ILabelAdapter)
def _QuestionSetLabelAdpater(unused_obj):
    return u'QuestionSet'


@component.adapter(IQAssignment)
@interface.implementer(ILabelAdapter)
def _AssignmentLabelAdpater(unused_obj):
    return u'Assignment'


@component.adapter(IQSurvey)
@interface.implementer(ILabelAdapter)
def _SurveyLabelAdpater(unused_obj):
    return u'Survey'


@component.adapter(IQPoll)
@interface.implementer(ILabelAdapter)
def _PollLabelAdpater(unused_obj):
    return u'Poll'


@component.adapter(ICourseInstance)
@interface.implementer(ILabelAdapter)
def _CourseInstanceLabelAdpater(unused_obj):
    return u'CourseInstance'


@interface.implementer(ILabelAdapter)
@component.adapter(ICourseCatalogEntry)
def _CourseCatalogEntryLabelAdpater(unused_obj):
    return u'CatalogEntry'


@interface.implementer(ILabelAdapter)
@component.adapter(ICourseOutlineNode)
def _CourseOutlineNodeLabelAdpater(unused_node):
    return u'CourseOutlineNode'


@interface.implementer(ILabelAdapter)
@component.adapter(ICourseOutlineContentNode)
def _CourseOutlineContentNodeLabelAdpater(unused_node):
    return u'CourseOutlineContentNode'


@interface.implementer(ILabelAdapter)
@component.adapter(ICourseOutlineCalendarNode)
def _CourseOutlineCalendarNodeLabelAdpater(unused_node):
    return u'CourseOutlineCalendarNode'


@interface.implementer(ILabelAdapter)
@component.adapter(ICourseInstanceEnrollmentRecord)
def _EnrollmentRecordLabelAdpater(unused_obj):
    return u'EnrollmentRecord'


@component.adapter(IContainer)
@interface.implementer(ILabelAdapter)
def _ContainerLabelAdpater(unused_container):
    return u'Container'


@interface.implementer(ILabelAdapter)
@component.adapter(IPresentationAsset)
def _PresentationAssetLabelAdpater(asset):
    iface = find_most_derived_interface(asset, IPresentationAsset,
                                        possibilities=interface.providedBy(asset))
    result = iface.__name__[1:]
    return result
