#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
graphdb adapters

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time

from zope import component
from zope import interface

from nti.assessment import interfaces as asm_interfaces

from nti.dataserver import interfaces as nti_interfaces
from nti.dataserver.users import interfaces as user_interfaces
from nti.dataserver.contenttypes.forums import interfaces as frm_interfaces

from nti.externalization import externalization

from nti.utils.maps import CaseInsensitiveDict

from . import interfaces as graph_interfaces

def get_ntiid(obj):
	return getattr(obj, 'NTIID', getattr(obj, 'ntiid'))

@interface.implementer(graph_interfaces.IPropertyAdapter)
@component.adapter(interface.Interface)
def _GenericPropertyAdpater(obj):
	return CaseInsensitiveDict()

@interface.implementer(graph_interfaces.IPropertyAdapter)
@component.adapter(nti_interfaces.IEntity)
def _EntityPropertyAdpater(entity):
	result = CaseInsensitiveDict({"username":entity.username})
	names = user_interfaces.IFriendlyNamed(entity, None)
	alias = getattr(names, 'alias', None)
	name = getattr(names, 'realname', None)
	for key, value in (('alias', alias), ('name', name)):
		if value:
			result[key] = unicode(value)
	result['oid'] = externalization.to_external_ntiid_oid(entity)
	return result

@component.adapter(nti_interfaces.ICommunity)
def _CommunityPropertyAdpater(community):
	result = _EntityPropertyAdpater(community)
	result['type'] = u'Community'
	return result

@component.adapter(nti_interfaces.IUser)
def _UserPropertyAdpater(user):
	result = _EntityPropertyAdpater(user)
	result['type'] = u'User'
	return result

@component.adapter(nti_interfaces.IDynamicSharingTargetFriendsList)
def _DFLPropertyAdpater(dfl):
	result = _EntityPropertyAdpater(dfl)
	result['type'] = u'DFL'
	return result

@interface.implementer(graph_interfaces.IPropertyAdapter)
@component.adapter(nti_interfaces.IModeledContent)
def _ModeledContentPropertyAdpater(modeled):
	result = CaseInsensitiveDict({'type':modeled.__class__.__name__})
	result['creator'] = modeled.creator.username
	result['created'] = modeled.createdTime
	result['oid'] = externalization.to_external_ntiid_oid(modeled)
	return result

@component.adapter(nti_interfaces.INote)
def _NotePropertyAdpater(note):
	result = _ModeledContentPropertyAdpater(note)
	result['title'] = unicode(note.title)
	return result

_HighlightPropertyAdpater = _ModeledContentPropertyAdpater
_RedactionPropertyAdpater = _ModeledContentPropertyAdpater

@interface.implementer(graph_interfaces.IPropertyAdapter)
@component.adapter(frm_interfaces.ITopic)
def _TopicPropertyAdpater(topic):
	result = CaseInsensitiveDict({'type':'Topic'})
	result['author'] = topic.creator.username
	result['title'] = unicode(topic.title)
	result['ntiid'] = topic.NTIID
	result['oid'] = externalization.to_external_ntiid_oid(topic)
	return result

@interface.implementer(graph_interfaces.IPropertyAdapter)
def _CommentPropertyAdpater(post):  # IPersonalBlogComment, IGeneralForumComment
	result = CaseInsensitiveDict({'type':'Comment'})
	result['author'] = post.creator.username
	result['oid'] = externalization.to_external_ntiid_oid(post)
	return result

@interface.implementer(graph_interfaces.IPropertyAdapter)
def _CommentRelationshipPropertyAdpater(_from, _post, _rel):  # IPersonalBlogComment, IGeneralForumComment
	result = CaseInsensitiveDict({'created': _post.createdTime})
	result['oid'] = externalization.to_external_ntiid_oid(_post)
	result['topic'] = _post.__parent__.NTIID
	return result

@interface.implementer(graph_interfaces.IPropertyAdapter)
@component.adapter(asm_interfaces.IQuestionSet)
def _QuestionSetPropertyAdpater(obj):
	result = CaseInsensitiveDict({'type':'QuestionSet'})
	result['ntiid'] = result['oid'] = get_ntiid(obj)
	return result
	
@interface.implementer(graph_interfaces.IPropertyAdapter)
@component.adapter(asm_interfaces.IQuestion)
def _QuestionPropertyAdpater(obj):
	result = CaseInsensitiveDict({'type':'Question'})
	result['ntiid'] = result['oid'] = get_ntiid(obj)
	return result

@interface.implementer(graph_interfaces.IPropertyAdapter)
@component.adapter(asm_interfaces.IQAssignment)
def _AssignmentPropertyAdpater(obj):
	result = CaseInsensitiveDict({'type':'Assignment'})
	result['ntiid'] = result['oid'] = get_ntiid(obj)
	return result

def _question_stats(question):
	total = incorrect = correct = partial = 0
	for part in question.parts:
		total += 1
		if part.assessedValue <= 0.01:
			incorrect += 1
		elif part.assessedValue >= 0.99:
			correct += 1
		else:
			partial += 1
	return (total == correct, total == incorrect, partial > 0)

@interface.implementer(graph_interfaces.IPropertyAdapter)
@component.adapter(nti_interfaces.IUser, asm_interfaces.IQAssessedQuestion,
				   graph_interfaces.ITakeAssessment)
def _AssessedQuestionRelationshipPropertyAdpater(_from, _question, _rel):
	result = CaseInsensitiveDict({'taker' : _from.username})
	result['created'] = _question.createdTime
	result['oid'] = externalization.to_external_ntiid_oid(_question)
	is_correct, is_incorrect, partial = _question_stats(_question)
	result['correct'] = is_correct
	result['incorrect'] = is_incorrect
	result['partial'] = partial
	return result

@interface.implementer(graph_interfaces.IPropertyAdapter)
@component.adapter(nti_interfaces.IUser, asm_interfaces.IQAssessedQuestionSet,
				  graph_interfaces.ITakeAssessment)
def _AssessedQuestionSetRelationshipPropertyAdpater(_from, _qset, _rel):
	result = CaseInsensitiveDict({'taker' : _from.username})
	result['created'] = _qset.createdTime
	result['oid'] = externalization.to_external_ntiid_oid(_qset)
	correct = incorrect = 0
	questions = _qset.questions
	for question in questions:
		is_correct, is_incorrect, _ = _question_stats(question)
		if is_correct:
			correct += 1
		elif is_incorrect:
			incorrect += 1
	result['correct'] = correct
	result['incorrect'] = incorrect
	return result

@interface.implementer(graph_interfaces.IPropertyAdapter)
@component.adapter(nti_interfaces.IUser, asm_interfaces.IQAssignment,
				   graph_interfaces.ITakeAssessment)
def _AssignmentRelationshipPropertyAdpater(_from, _asm, _rel):
	result = CaseInsensitiveDict({'taker' : _from.username})
	result['created'] = _asm.createdTime
	return result

@interface.implementer(graph_interfaces.IPropertyAdapter)
def _CreatedTimePropertyAdpater(_from, _to, _rel):
	result = CaseInsensitiveDict({'created':time.time()})
	return result

@interface.implementer(graph_interfaces.IPropertyAdapter)
def _RepliedRelationshipPropertyAdpater(entity, obj, rel_type):
	result = _CreatedTimePropertyAdpater(entity, obj, rel_type)
	result['oid'] = externalization.to_external_ntiid_oid(obj)
	return result

_LikeRelationshipPropertyAdpater = _CreatedTimePropertyAdpater
_RateRelationshipPropertyAdpater = _CreatedTimePropertyAdpater
_FollowRelationshipPropertyAdpater = _CreatedTimePropertyAdpater
_FlaggedRelationshipPropertyAdpater = _CreatedTimePropertyAdpater
_AuthorshipRelationshipPropertyAdpater = _CreatedTimePropertyAdpater
