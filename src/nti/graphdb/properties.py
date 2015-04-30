#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time

import zope.intid

from zope import component
from zope import interface

from nti.assessment.interfaces import IQuestion
from nti.assessment.interfaces import IQAssignment
from nti.assessment.interfaces import IQuestionSet

from nti.chatserver.interfaces import IMeeting
from nti.chatserver.interfaces import IMessageInfo

from nti.contentlibrary.interfaces import IContentUnit

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import IEntity
from nti.dataserver.interfaces import ICreated
from nti.dataserver.interfaces import ICommunity
from nti.dataserver.interfaces import ITitledContent
from nti.dataserver.interfaces import IModeledContent
from nti.dataserver.interfaces import IDynamicSharingTargetFriendsList

from nti.dataserver.contenttypes.forums.interfaces import IBoard
from nti.dataserver.contenttypes.forums.interfaces import IForum
from nti.dataserver.contenttypes.forums.interfaces import ITopic
from nti.dataserver.contenttypes.forums.interfaces import IHeadlinePost

from nti.dataserver.users.interfaces import IFriendlyNamed

from nti.externalization.externalization import to_external_ntiid_oid

from .common import get_creator

from .interfaces import IPropertyAdapter

def get_ntiid(obj):
	result = getattr(obj, 'NTIID', None) or getattr(obj, 'ntiid', None)
	return result

def add_oid(obj, ext):
	ext['oid'] = to_external_ntiid_oid(obj)
	return ext

def add_type(obj, ext):
	name = getattr(obj, '__external_class_name__', None)
	ext['type'] = unicode(name or obj.__class__.__name__)
	return ext

def add_intid(obj, ext):
	intids = component.getUtility(zope.intid.IIntIds)
	uid = intids.queryId(obj)
	if uid is not None:
		ext['intid'] = uid
	return ext

@interface.implementer(IPropertyAdapter)
@component.adapter(interface.Interface)
def _GenericPropertyAdpater(obj):
	result = {'createdTime':time.time()}
	result['lastModified'] = getattr(obj, 'lastModified', 0)
	add_intid(obj, result)
	return result

@component.adapter(IEntity)
@interface.implementer(IPropertyAdapter)
def _EntityPropertyAdpater(entity):
	result = {"username": entity.username, 
			  "creator" : entity.username,
			  'createdTime': entity.createdTime}
	## check alias and realname
	names = IFriendlyNamed(entity, None)
	alias = getattr(names, 'alias', None)
	name = getattr(names, 'realname', None)
	for key, value in (('alias', alias), ('name', name)):
		if value:
			result[key] = unicode(value)
	add_oid(entity, result)
	add_intid(entity, result)
	return result

@component.adapter(ICommunity)
@interface.implementer(IPropertyAdapter)
def _CommunityPropertyAdpater(community):
	result = _EntityPropertyAdpater(community)
	result['type'] = u'Community'
	return result

@component.adapter(IUser)
@interface.implementer(IPropertyAdapter)
def _UserPropertyAdpater(user):
	result = _EntityPropertyAdpater(user)
	result['type'] = u'User'
	return result

@interface.implementer(IPropertyAdapter)
@component.adapter(IDynamicSharingTargetFriendsList)
def _DFLPropertyAdpater(dfl):
	result = _EntityPropertyAdpater(dfl)
	result['type'] = u'DFL'
	return result

@component.adapter(ICreated)
@interface.implementer(IPropertyAdapter)
def _CreatedPropertyAdpater(created):
	result = {'lastModified': getattr(created, 'lastModified', 0) }
	result['createdTime'] = getattr(created, 'createdTime', None) or time.time()
	add_oid(created, result)
	add_type(created, result)
	add_intid(created, result)
	creator = getattr(created, 'creator', None)
	creator = getattr(creator, 'username', creator)
	if creator:
		result['creator'] = creator
	return result

@component.adapter(IModeledContent)
@interface.implementer(IPropertyAdapter)
def _ModeledContentPropertyAdpater(modeled):
	result = _CreatedPropertyAdpater(modeled)
	containerId = getattr(modeled, 'containerId', None)
	if containerId:
		result['containerId'] = containerId
	return result

@component.adapter(ITitledContent)
@interface.implementer(IPropertyAdapter)
def _TitledContentPropertyAdpater(content):
	result = _ModeledContentPropertyAdpater(content)
	result['title'] = unicode(content.title) or u''
	return result

_NotePropertyAdpater = _TitledContentPropertyAdpater
_HighlightPropertyAdpater = _ModeledContentPropertyAdpater
_RedactionPropertyAdpater = _ModeledContentPropertyAdpater

@interface.implementer(IPropertyAdapter)
@component.adapter(IBoard)
def _BoardPropertyAdpater(board):
	result = {'type':'Board'}
	result['title'] = unicode(board.title)
	result['createdTime'] = board.createdTime
	result['lastModified'] = getattr(board, 'lastModified', 0)
	add_oid(board, result)
	add_intid(board, result)
	return result

@interface.implementer(IPropertyAdapter)
@component.adapter(IForum)
def _ForumPropertyAdpater(forum):
	result = {'type':'Forum'}
	result['title'] = unicode(forum.title)
	result['createdTime'] = forum.createdTime
	result['lastModified'] = getattr(forum, 'lastModified', 0)
	add_oid(forum, result)
	add_intid(forum, result)
	return result

@interface.implementer(IPropertyAdapter)
@component.adapter(ITopic)
def _TopicPropertyAdpater(topic):
	result = {'type':'Topic'}
	creator = get_creator(topic)
	if creator is not None:
		result['creator'] = creator.username
	result['title'] = unicode(topic.title)
	result['ntiid'] = topic.NTIID
	result['createdTime'] = topic.createdTime
	result['lastModified'] = getattr(topic, 'lastModified', 0)
	result['forum'] = to_external_ntiid_oid(topic.__parent__)
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
	result = {'type':'Meeting'}
	creator = get_creator(meeting)
	if creator is not None:
		result['creator'] = creator.username
	result['roomId'] = meeting.RoomId
	result['moderated'] = meeting.Moderated
	result['createdTime'] = meeting.CreatedTime
	result['lastModified'] = getattr(meeting, 'lastModified', 0)
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
def _CommentPropertyAdpater(post):  # IPersonalBlogComment, IGeneralForumComment
	result = {'type':'Comment'}
	creator = get_creator(post)
	if creator is not None:
		result['creator'] = creator.username
	result['topic'] = post.__parent__.NTIID
	result['createdTime'] = post.createdTime
	result['lastModified'] = getattr(post, 'lastModified', 0)
	add_oid(post, result)
	add_intid(post, result)
	return result

@component.adapter(IContentUnit)
@interface.implementer(IPropertyAdapter)
def _ContentUnitPropertyAdpater(unit):
	result = {'type':'ContentUnit'}
	result['title'] = unit.title
	result['createdTime'] = time.time()
	result['lastModified'] = time.time()
	result['oid'] = result['ntiid'] = unit.ntiid
	add_intid(unit, result)
	return result

@component.adapter(IQuestionSet)
@interface.implementer(IPropertyAdapter)
def _QuestionSetPropertyAdpater(obj):
	result = {'type':'QuestionSet'}
	result['createdTime'] = time.time()
	result['lastModified'] = time.time()
	result['ntiid'] = result['oid'] = get_ntiid(obj)
	add_intid(obj, result)
	return result
	
@component.adapter(IQuestion)
@interface.implementer(IPropertyAdapter)
def _QuestionPropertyAdpater(obj):
	result = {'type':'Question'}
	result['createdTime'] = time.time()
	result['lastModified'] = time.time()
	result['ntiid'] = result['oid'] = get_ntiid(obj)
	add_intid(obj, result)
	return result

@component.adapter(IQAssignment)
@interface.implementer(IPropertyAdapter)
def _AssignmentPropertyAdpater(obj):
	result = {'type':'Assignment'}
	result['ntiid'] = result['oid'] = get_ntiid(obj)
	result['createdTime'] = time.time()
	result['lastModified'] = time.time()
	return result