#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six
import time

from zope import component
from zope import interface

from zope.intid.interfaces import IIntIds

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

from nti.dataserver.contenttypes.forums.interfaces import IBoard
from nti.dataserver.contenttypes.forums.interfaces import IForum
from nti.dataserver.contenttypes.forums.interfaces import ITopic
from nti.dataserver.contenttypes.forums.interfaces import IHeadlinePost

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import IEntity
from nti.dataserver.interfaces import ICreated
from nti.dataserver.interfaces import ICommunity
from nti.dataserver.interfaces import ITitledContent
from nti.dataserver.interfaces import IModeledContent
from nti.dataserver.interfaces import IUseNTIIDAsExternalUsername
from nti.dataserver.interfaces import IDynamicSharingTargetFriendsList

from nti.dataserver.users.interfaces import IFriendlyNamed

from nti.graphdb import OID
from nti.graphdb import TYPE
from nti.graphdb import INTID
from nti.graphdb import NTIID
from nti.graphdb import TITLE
from nti.graphdb import CREATOR
from nti.graphdb import USERNAME
from nti.graphdb import CONTAINER_ID
from nti.graphdb import CREATED_TIME
from nti.graphdb import LAST_MODIFIED

from nti.graphdb.common import get_oid
from nti.graphdb.common import get_ntiid
from nti.graphdb.common import get_creator
from nti.graphdb.common import get_createdTime
from nti.graphdb.common import get_lastModified
from nti.graphdb.common import get_principal_id

from nti.graphdb.interfaces import ICommentOn
from nti.graphdb.interfaces import IContainer
from nti.graphdb.interfaces import IPropertyAdapter

from nti.schema.interfaces import find_most_derived_interface

logger = __import__('logging').getLogger(__name__)


def add_oid(obj, ext):
    oid = get_oid(obj)
    if oid is not None:
        ext[OID] = get_oid(obj)
    return ext


def add_type(obj, ext):
    name = getattr(obj, '__external_class_name__', None)
    ext[TYPE] = six.text_type(name or obj.__class__.__name__)
    return ext


def add_intid(obj, ext):
    intids = component.getUtility(IIntIds)
    uid = intids.queryId(obj)
    if uid is not None:
        ext[INTID] = uid
    return ext


@interface.implementer(IPropertyAdapter)
@component.adapter(interface.Interface)
def _GenericPropertyAdpater(obj):
    result = {
        CREATED_TIME: get_createdTime(obj),
        LAST_MODIFIED: get_lastModified(obj)
    }
    add_intid(obj, result)
    return result


@component.adapter(IEntity)
@interface.implementer(IPropertyAdapter)
def _EntityPropertyAdpater(entity):
    result = {
        USERNAME: entity.username,
        CREATOR: entity.username,
        CREATED_TIME: get_createdTime(entity)
    }
    # check alias and realname
    names = IFriendlyNamed(entity, None)
    alias = getattr(names, 'alias', None)
    name = getattr(names, 'realname', None)
    for key, value in (('alias', alias), ('name', name)):
        if value:
            result[key] = six.text_type(value)
    add_oid(entity, result)
    add_intid(entity, result)
    # check for external username
    if IUseNTIIDAsExternalUsername.providedBy(entity):
        result['name'] = result[USERNAME]
        result[USERNAME] = get_ntiid(entity) or get_oid(entity)
    return result


@component.adapter(ICommunity)
@interface.implementer(IPropertyAdapter)
def _CommunityPropertyAdpater(community):
    result = _EntityPropertyAdpater(community)
    result[TYPE] = 'Community'
    return result


@component.adapter(IUser)
@interface.implementer(IPropertyAdapter)
def _UserPropertyAdpater(user):
    result = _EntityPropertyAdpater(user)
    result[TYPE] = 'User'
    return result


@interface.implementer(IPropertyAdapter)
@component.adapter(IDynamicSharingTargetFriendsList)
def _DFLPropertyAdpater(dfl):
    result = _EntityPropertyAdpater(dfl)
    result[CREATOR] = get_creator(dfl)
    result[TYPE] = 'DFL'
    return result


@component.adapter(ICreated)
@interface.implementer(IPropertyAdapter)
def _CreatedPropertyAdpater(created):
    result = {CREATED_TIME: get_createdTime(created),
              LAST_MODIFIED: get_lastModified(created)}
    add_oid(created, result)
    add_type(created, result)
    add_intid(created, result)
    creator = getattr(created, CREATOR, None)
    creator = getattr(creator, USERNAME, creator)
    if creator:
        result[CREATOR] = creator
    return result


@component.adapter(IModeledContent)
@interface.implementer(IPropertyAdapter)
def _ModeledContentPropertyAdpater(modeled):
    result = _CreatedPropertyAdpater(modeled)
    containerId = getattr(modeled, CONTAINER_ID, None)
    if containerId:
        result[CONTAINER_ID] = containerId
    return result


ModeledContentPropertyAdpater = _ModeledContentPropertyAdpater


@component.adapter(ITitledContent)
@interface.implementer(IPropertyAdapter)
def _TitledContentPropertyAdpater(content):
    result = _ModeledContentPropertyAdpater(content)
    result[TITLE] = six.text_type(content.title) or u''
    return result


_NotePropertyAdpater = _TitledContentPropertyAdpater
_HighlightPropertyAdpater = _ModeledContentPropertyAdpater
_RedactionPropertyAdpater = _ModeledContentPropertyAdpater


@interface.implementer(IPropertyAdapter)
@component.adapter(IBoard)
def _BoardPropertyAdpater(board):
    result = {TYPE: 'Board'}
    result[TITLE] = six.text_type(board.title)
    result[CREATED_TIME] = get_createdTime(board)
    result[LAST_MODIFIED] = get_lastModified(board)
    add_oid(board, result)
    add_intid(board, result)
    return result


@interface.implementer(IPropertyAdapter)
@component.adapter(IForum)
def _ForumPropertyAdpater(forum):
    result = {TYPE: 'Forum'}
    result[TITLE] = six.text_type(forum.title)
    result[CREATED_TIME] = get_createdTime(forum)
    result[LAST_MODIFIED] = get_lastModified(forum)
    add_oid(forum, result)
    add_intid(forum, result)
    return result


@interface.implementer(IPropertyAdapter)
@component.adapter(ITopic)
def _TopicPropertyAdpater(topic):
    result = {TYPE: 'Topic'}
    creator = get_creator(topic)
    if creator is not None:
        result[CREATOR] = creator.username
    result[NTIID] = topic.NTIID
    result[TITLE] = six.text_type(topic.title)
    result[CREATED_TIME] = get_createdTime(topic)
    result[LAST_MODIFIED] = get_lastModified(topic)
    result['forum'] = get_oid(topic.__parent__)
    add_oid(topic, result)
    add_intid(topic, result)
    return result


@interface.implementer(IPropertyAdapter)
@component.adapter(IHeadlinePost)
def _HeadlinePostPropertyAdpater(post):
    return IPropertyAdapter(post.__parent__)


@component.adapter(IMeeting)
@interface.implementer(IPropertyAdapter)
def _MeetingPropertyAdpater(meeting):
    result = {TYPE: 'Meeting'}
    creator = get_creator(meeting)
    if creator is not None:
        result[CREATOR] = creator.username
    result['roomId'] = meeting.RoomId
    result['moderated'] = meeting.Moderated
    result[CREATED_TIME] = get_createdTime(meeting)
    result[LAST_MODIFIED] = get_lastModified(meeting)
    add_oid(meeting, result)
    add_intid(meeting, result)
    return result


@component.adapter(IMessageInfo)
@interface.implementer(IPropertyAdapter)
def _MessageInfoPropertyAdpater(message):
    result = _ModeledContentPropertyAdpater(message)
    result['channel'] = message.channel
    result['status'] = message.Status
    return result


@interface.implementer(IPropertyAdapter)
# IPersonalBlogComment, IGeneralForumComment
def _CommentPropertyAdpater(post):
    result = {TYPE: 'Comment'}
    creator = get_creator(post)
    if creator is not None:
        result[CREATOR] = creator.username
    try:
        result['topic'] = post.__parent__.NTIID
    except AttributeError:  # pragma: no cover
        pass
    result[CREATED_TIME] = get_createdTime(post)
    result[LAST_MODIFIED] = get_lastModified(post)
    add_oid(post, result)
    add_intid(post, result)
    return result


@component.adapter(IContentUnit)
@interface.implementer(IPropertyAdapter)
def _ContentUnitPropertyAdpater(unit):
    result = {TYPE: 'ContentUnit'}
    result[TITLE] = unit.title
    result[CREATED_TIME] = time.time()
    result[LAST_MODIFIED] = time.time()
    result[NTIID] = result[OID] = unit.ntiid
    add_intid(unit, result)
    return result


@component.adapter(IContentPackage)
@interface.implementer(IPropertyAdapter)
def _ContentPackagePropertyAdpater(pkg):
    result = {TYPE: 'ContentPackage'}
    result[TITLE] = pkg.title
    result[CREATED_TIME] = pkg.createdTime
    result[LAST_MODIFIED] = pkg.lastModified
    result[NTIID] = result[OID] = pkg.ntiid
    add_intid(pkg, result)
    return result


@component.adapter(IQuestionSet)
@interface.implementer(IPropertyAdapter)
def _QuestionSetPropertyAdpater(obj):
    result = {TYPE: 'QuestionSet'}
    result[CREATED_TIME] = get_createdTime(obj)
    result[LAST_MODIFIED] = get_lastModified(obj)
    result[NTIID] = result[OID] = get_ntiid(obj)
    add_intid(obj, result)
    return result


@component.adapter(IQuestion)
@interface.implementer(IPropertyAdapter)
def _QuestionPropertyAdpater(obj):
    result = {TYPE: 'Question'}
    result[CREATED_TIME] = get_createdTime(obj)
    result[LAST_MODIFIED] = get_lastModified(obj)
    result[NTIID] = result[OID] = get_ntiid(obj)
    add_intid(obj, result)
    return result


@component.adapter(IQAssignment)
@interface.implementer(IPropertyAdapter)
def _AssignmentPropertyAdpater(obj):
    result = {TYPE: 'Assignment'}
    result[NTIID] = result[OID] = get_ntiid(obj)
    result[CREATED_TIME] = get_createdTime(obj)
    result[LAST_MODIFIED] = get_lastModified(obj)
    return result


@component.adapter(IQSurvey)
@interface.implementer(IPropertyAdapter)
def _SurveyPropertyAdpater(obj):
    result = {TYPE: 'Survey'}
    result[CREATED_TIME] = get_createdTime(obj)
    result[LAST_MODIFIED] = get_lastModified(obj)
    result[NTIID] = result[OID] = get_ntiid(obj)
    add_intid(obj, result)
    return result


@component.adapter(IQPoll)
@interface.implementer(IPropertyAdapter)
def _PollPropertyAdpater(obj):
    result = {TYPE: 'Poll'}
    result[CREATED_TIME] = get_createdTime(obj)
    result[LAST_MODIFIED] = get_lastModified(obj)
    result[NTIID] = result[OID] = get_ntiid(obj)
    add_intid(obj, result)
    return result


@component.adapter(ICourseInstance)
@interface.implementer(IPropertyAdapter)
def _CourseInstancePropertyAdpater(obj):
    result = {TYPE: 'CourseInstance'}
    result[NTIID] = get_ntiid(obj)
    result[CREATED_TIME] = get_createdTime(obj)
    result[LAST_MODIFIED] = get_lastModified(obj)
    add_oid(obj, result)
    add_intid(obj, result)
    return result


@component.adapter(ICourseCatalogEntry)
@interface.implementer(IPropertyAdapter)
def _CourseCatalogEntryPropertyAdpater(obj):
    result = {TYPE: 'CatalogEntry'}
    result[NTIID] = result['oid'] = get_ntiid(obj)
    result['provider'] = obj.ProviderUniqueID
    result[CREATED_TIME] = get_createdTime(obj)
    result[LAST_MODIFIED] = get_lastModified(obj)
    add_intid(obj, result)
    return result


@interface.implementer(IPropertyAdapter)
@component.adapter(ICourseInstanceEnrollmentRecord)
def _EnrollmentRecordPropertyAdpater(obj):
    result = {TYPE: 'EnrollmentRecord'}
    result['scope'] = obj.Scope
    result[USERNAME] = get_principal_id(obj.Principal)
    entry = ICourseCatalogEntry(obj.CourseInstance, None)
    if entry is not None:
        result['course'] = entry.ntiid
    add_oid(obj, result)
    add_intid(obj, result)
    return result


@interface.implementer(IPropertyAdapter)
@component.adapter(ICourseOutlineNode)
def _CourseOutlineNodePropertyAdpater(obj):
    result = {TYPE: 'CourseOutlineNode'}
    result[NTIID] = get_ntiid(obj)
    result[CREATED_TIME] = get_createdTime(obj)
    result[LAST_MODIFIED] = get_lastModified(obj)
    add_intid(obj, result)
    return result


@interface.implementer(IPropertyAdapter)
@component.adapter(ICourseOutlineContentNode)
def _CourseOutlineContentNodePropertyAdpater(obj):
    result = _CourseOutlineNodePropertyAdpater(obj)
    result[TYPE] = 'CourseOutlineContentNode'
    result['content_ntiid'] = obj.ContentNTIID
    return result


@interface.implementer(IPropertyAdapter)
@component.adapter(ICourseOutlineCalendarNode)
def _CourseOutlineCalendarNodePropertyAdpater(obj):
    result = _CourseOutlineContentNodePropertyAdpater(obj)
    result[TYPE] = 'CourseOutlineCalendarNode'
    return result


@interface.implementer(IPropertyAdapter)
@component.adapter(IPresentationAsset)
def _PresentationAssetPropertyAdpater(obj):
    iface = find_most_derived_interface(obj, IPresentationAsset,
                                        possibilities=interface.providedBy(obj))
    result = {TYPE: iface.__name__[1:]}
    result[NTIID] = get_ntiid(obj)
    add_oid(obj, result)
    add_intid(obj, result)
    return result


@component.adapter(IContainer)
@interface.implementer(IPropertyAdapter)
def _ContainerPropertyAdpater(container):
    result = {TYPE: 'Container'}
    result[OID] = container.id
    result[LAST_MODIFIED] = time.time()
    return result


@interface.implementer(IPropertyAdapter)
def _CurrentTimePropertyAdpater(unused_source, unused_target, unused_rel):
    result = {
        CREATED_TIME: time.time()
    }
    return result
_LikeRelationshipPropertyAdpater = _CurrentTimePropertyAdpater
_RateRelationshipPropertyAdpater = _CurrentTimePropertyAdpater


@interface.implementer(IPropertyAdapter)
def _EntityObjectRelationshipPropertyAdpater(entity, obj, unused_type):
    result = {CREATED_TIME: get_createdTime(obj, time.time())}
    result[CREATOR] = entity.username
    add_oid(obj, result)
    add_intid(obj, result)
    return result
_RepliedRelationshipPropertyAdpater = _EntityObjectRelationshipPropertyAdpater


# IPersonalBlogComment, IGeneralForumComment


@interface.implementer(IPropertyAdapter)
def _CommentRelationshipPropertyAdpater(entity, post, unused_rel):
    result = {
        OID: get_oid(post),
        CREATOR: entity.username,
        CREATED_TIME: get_createdTime(post)
    }
    return result


@interface.implementer(IPropertyAdapter)
@component.adapter(IUser, ITopic, ICommentOn)
def _TopicCommentRelationshipPropertyAdpater(unused_entity, unused_topic, unused_rel_type):
    return {}
