#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
graphdb adapters

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

import time
from datetime import datetime

from zope import component
from zope import interface

from nti.assessment import interfaces as asm_interfaces

from nti.dataserver import interfaces as nti_interfaces
from nti.dataserver.users import interfaces as user_interfaces
from nti.dataserver.contenttypes.forums import interfaces as frm_interfaces

from nti.externalization import externalization

from . import interfaces as graph_interfaces

def _to_isoformat(t):
	d = datetime.fromtimestamp(t)
	return unicode(d.isoformat())

#### labels

@interface.implementer(graph_interfaces.ILabelAdapter)
@component.adapter(interface.Interface)
class GenericLabelAdpater(object):

	def __init__(self, obj):
		self.obj = obj

	def labels(self):
		return set()

@interface.implementer(graph_interfaces.ILabelAdapter)
@component.adapter(nti_interfaces.IEntity)
class EntityLabelAdpater(object):

	def __init__(self, entity):
		self.entity = entity

	def labels(self):
		return {self.entity.__class__.__name__}

@interface.implementer(graph_interfaces.ILabelAdapter)
@component.adapter(nti_interfaces.IDynamicSharingTargetFriendsList)
class DFLLabelAdpater(object):

	def __init__(self, dfl):
		self.dfl = dfl

	def labels(self):
		return {'DFL'}

@interface.implementer(graph_interfaces.ILabelAdapter)
@component.adapter(nti_interfaces.IModeledContent)
class ModeledContentLabelAdpater(object):

	def __init__(self, modeled):
		self.modeled = modeled

	def labels(self):
		return {self.modeled.__class__.__name__}

@component.adapter(nti_interfaces.INote)
class NoteLabelAdpater(ModeledContentLabelAdpater):

	def labels(self):
		result = super(NoteLabelAdpater, self).labels()
		result.update(getattr(self.modeled, 'AutoTags', ()))
		return result

@interface.implementer(graph_interfaces.ILabelAdapter)
class CommentLabelAdpater(object):

	def __init__(self, post):
		self.post = post

	def labels(self):
		result = {'Comment'}
		return result

@interface.implementer(graph_interfaces.ILabelAdapter)
@component.adapter(frm_interfaces.ITopic)
class TopicLabelAdpater(object):

	def __init__(self, topic):
		self.topic = topic

	def labels(self):
		result = {'Topic'}
		result.update(self.topic.tags or ())
		headline = getattr(self.topic, 'headline', None)
		if headline is not None:
			result.update(getattr(headline, 'tags', ()))
		return result
	
@interface.implementer(graph_interfaces.ILabelAdapter)
@component.adapter(asm_interfaces.IQAssessedQuestionSet)
class QuestionSetLabelAdpater(object):

	def __init__(self, qset):
		self.qset = qset

	def labels(self):
		result = {'QuestionSet'}
		return result

@interface.implementer(graph_interfaces.ILabelAdapter)
@component.adapter(asm_interfaces.IQAssessedQuestion)
class QuestionLabelAdpater(object):

	def __init__(self, question):
		self.question = question

	def labels(self):
		result = {'Question'}
		return result

#### properties

@interface.implementer(graph_interfaces.IPropertyAdapter)
@component.adapter(interface.Interface)
class GenericPropertyAdpater(object):

	def __init__(self, obj):
		self.obj = obj

	def properties(self):
		return {}

@interface.implementer(graph_interfaces.IPropertyAdapter)
@component.adapter(nti_interfaces.IEntity)
class EntityPropertyAdpater(object):

	def __init__(self, entity):
		self.entity = entity

	def properties(self):
		result = {"username":self.entity.username}
		names = user_interfaces.IFriendlyNamed(self.entity, None)
		alias = getattr(names, 'alias', None)
		name = getattr(names, 'realname', None)
		for key, value in (('alias', alias), ('name', name)):
			if value:
				result[key] = unicode(value)
		result['OID'] = externalization.to_external_ntiid_oid(self.entity)
		return result

@component.adapter(nti_interfaces.ICommunity)
class CommunityPropertyAdpater(EntityPropertyAdpater):

	def properties(self):
		result = super(CommunityPropertyAdpater, self).properties()
		result['type'] = u'Community'
		return result

@component.adapter(nti_interfaces.IUser)
class UserPropertyAdpater(EntityPropertyAdpater):

	def properties(self):
		result = super(UserPropertyAdpater, self).properties()
		result['type'] = u'User'
		return result

@component.adapter(nti_interfaces.IDynamicSharingTargetFriendsList)
class DFLPropertyAdpater(EntityPropertyAdpater):

	def properties(self):
		result = super(DFLPropertyAdpater, self).properties()
		result['type'] = u'DFL'
		return result

@interface.implementer(graph_interfaces.IPropertyAdapter)
@component.adapter(nti_interfaces.IModeledContent)
class ModeledContentPropertyAdpater(object):

	def __init__(self, modeled):
		self.modeled = modeled

	def properties(self):
		result = {'type':self.modeled.__class__.__name__}
		result['creator'] = self.modeled.creator.username
		result['createdTime'] = _to_isoformat(self.modeled.createdTime)
		result['OID'] = externalization.to_external_ntiid_oid(self.modeled)
		return result

@component.adapter(nti_interfaces.INote)
class NotePropertyAdpater(ModeledContentPropertyAdpater):

	def properties(self):
		result = super(NotePropertyAdpater, self).properties()
		result['title'] = unicode(self.modeled.title)
		return result

@interface.implementer(graph_interfaces.IPropertyAdapter)
@component.adapter(frm_interfaces.ITopic)
class TopicPropertyAdpater(object):

	def __init__(self, topic):
		self.topic = topic

	def properties(self):
		result = {'type':'Topic'}
		result['author'] = self.topic.creator.username
		result['title'] = unicode(self.topic.title)
		result['NTIID'] = self.topic.NTIID
		result['OID'] = externalization.to_external_ntiid_oid(self.topic)
		return result

@interface.implementer(graph_interfaces.IPropertyAdapter)
class CommentPropertyAdpater(object):

	def __init__(self, post):
		self.post = post

	def properties(self):
		result = {'type':'Comment'}
		result['author'] = self.post.creator.username
		result['OID'] = externalization.to_external_ntiid_oid(self.post)
		return result

@interface.implementer(graph_interfaces.IPropertyAdapter)
class CommentRelationshipPropertyAdpater(object):

	def __init__(self, _from, _post, _rel):
		self._rel = _rel
		self._from = _from
		self._post = _post

	def properties(self):
		result={'createdTime': _to_isoformat(self._post.createdTime)}
		result['OID'] = externalization.to_external_ntiid_oid(self._post)
		result['topicNTIID'] = self._post.__parent__.NTIID
		return result

@interface.implementer(graph_interfaces.IPropertyAdapter)
@component.adapter(asm_interfaces.IQAssessedQuestionSet)
class QuestionSetPropertyAdpater(object):

	def __init__(self, obj):
		self.obj = obj

	def properties(self):
		result = {'type':'QuestionSet'}
		result['ID'] = self.obj.questionSetId
		return result
	
@interface.implementer(graph_interfaces.IPropertyAdapter)
@component.adapter(asm_interfaces.IQAssessedQuestion)
class QuestionPropertyAdpater(object):

	def __init__(self, obj):
		self.obj = obj

	def properties(self):
		result = {'type':'Question'}
		result['ID'] = self.obj.questionId
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

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
class CreatedTimePropertyAdpater(object):

	def __init__(self, _from, _to, _rel):
		self._to = _to
		self._rel = _rel
		self._from = _from

	def properties(self):
		result = {'createdTime':_to_isoformat(time.time())}
		return result

@interface.implementer(graph_interfaces.IPropertyAdapter)
@component.adapter(nti_interfaces.IUser, asm_interfaces.IQAssessedQuestion, graph_interfaces.ITakeAssessment)
class AssessedQuestionRelationshipPropertyAdpater(object):

	def __init__(self, _from, _question, _rel):
		self._rel = _rel
		self._from = _from
		self._question = _question

	def properties(self):
		result = {'taker' : self._from.username}
		result['createdTime'] = _to_isoformat(self._question.createdTime)
		result['OID'] = externalization.to_external_ntiid_oid(self._question)
		is_correct, is_incorrect, partial = _question_stats(self._question)
		result['correct'] = is_correct
		result['incorrect'] = is_incorrect
		result['partial'] = partial
		return result

@interface.implementer(graph_interfaces.IPropertyAdapter)
@component.adapter(nti_interfaces.IUser, asm_interfaces.IQAssessedQuestionSet, graph_interfaces.ITakeAssessment)
class AssessedQuestionSetRelationshipPropertyAdpater(object):

	def __init__(self, _from, _qset, _rel):
		self._rel = _rel
		self._from = _from
		self._qset = _qset

	def properties(self):
		result = {'taker' : self._from.username}
		result['createdTime'] = _to_isoformat(self._qset.createdTime)
		result['OID'] = externalization.to_external_ntiid_oid(self._qset)
		correct = incorrect = 0
		questions = self._qset.questions
		for question in questions:
			is_correct, is_incorrect, _ = _question_stats(question)
			if is_correct:
				correct += 1
			elif is_incorrect:
				incorrect +=1 
		result['correct'] = correct
		result['incorrect'] = incorrect
		return result

LikeRelationshipPropertyAdpater = CreatedTimePropertyAdpater
FollowRelationshipPropertyAdpater = CreatedTimePropertyAdpater
AuthorshipRelationshipPropertyAdpater = CreatedTimePropertyAdpater

#### unique attribute

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
@component.adapter(interface.Interface)
class GenericUniqueAttributeAdpater(object):

	key = value = None

	def __init__(self, obj):
		pass

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
class OIDUniqueAttributeAdpater(object):

	key = "OID"

	def __init__(self, obj):
		self.obj = obj

	@property
	def value(self):
		result = externalization.to_external_ntiid_oid(self.obj)
		return result

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
class EndRelationshipUniqueAttributeAdpater(OIDUniqueAttributeAdpater):

	def __init__(self, _from, _to, _rel):
		# a relationship is identified by the end object oid
		super(EndRelationshipUniqueAttributeAdpater, self).__init__(_to)

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
@component.adapter(nti_interfaces.IEntity)
class EntityUniqueAttributeAdpater(object):

	key = "username"

	def __init__(self, obj):
		self.obj = obj

	@property
	def value(self):
		return self.obj.username

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
@component.adapter(nti_interfaces.IModeledContent)
class ModeledContentUniqueAttributeAdpater(OIDUniqueAttributeAdpater):
	pass

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
@component.adapter(frm_interfaces.ITopic)
class TopicUniqueAttributeAdpater(object):

	key = "NTIID"

	def __init__(self, obj):
		self.obj = obj

	@property
	def value(self):
		return self.obj.NTIID

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
class CommentUniqueAttributeAdpater(OIDUniqueAttributeAdpater):
	pass

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
class CommentRelationshipUniqueAttributeAdpater(object):

	def __init__(self, _from, _to, _rel):
		self._to = _to
		self._rel = _rel
		self._from = _from

	@property
	def key(self):
		return self._from.username

	@property
	def value(self):
		oid = externalization.to_external_ntiid_oid(self._to)
		result = '%s,%s' % (self._rel, oid)
		return result

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
class _RelationshipUniqueAttributeAdpater(object):

	def __init__(self, _from, _to, _rel):
		self._to = _to
		self._rel = _rel
		self._from = _from

	@property
	def key(self):
		return self._from.username

	@property
	def value(self):
		result = '%s,%s' % (self._rel, self._to.username)
		return result

FollowUniqueAttributeAdpater = _RelationshipUniqueAttributeAdpater
FriendshipUniqueAttributeAdpater = _RelationshipUniqueAttributeAdpater
TargetMembershipUniqueAttributeAdpater = _RelationshipUniqueAttributeAdpater

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
@component.adapter(asm_interfaces.IQAssessedQuestionSet)
class QuestionSetUniqueAttributeAdpater(object):

	key = "ID"

	def __init__(self, obj):
		self.obj = obj

	@property
	def value(self):
		return self.obj.questionSetId

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
@component.adapter(asm_interfaces.IQAssessedQuestion)
class QuestionUniqueAttributeAdpater(object):

	key = "ID"

	def __init__(self, obj):
		self.obj = obj

	@property
	def value(self):
		return self.obj.questionId

AssessedRelationshipUniqueAttributeAdpater = EndRelationshipUniqueAttributeAdpater

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
@component.adapter(asm_interfaces.IQAssessedQuestion, asm_interfaces.IQAssessedQuestionSet, graph_interfaces.IMemberOf)
class QuestionMembershipUniqueAttributeAdpater(object):

	def __init__(self, _from, _to, _rel):
		self._to = _to
		self._rel = _rel
		self._from = _from

	@property
	def key(self):
		return self._from.questionId

	@property
	def value(self):
		result = '%s,%s' % (self._rel, self._to.questionSetId)
		return result

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
class _UserObjectUniqueAttributeAdpater(object):

	def __init__(self, _from, _to, _rel):
		self._to = _to
		self._rel = _rel
		self._from = _from

	@property
	def key(self):
		return self._from.username

	@property
	def value(self):
		oid = externalization.to_external_ntiid_oid(self._to)
		result = '%s,%s' % (self._rel, oid)
		return result

@component.adapter(nti_interfaces.IEntity, nti_interfaces.ILikeable, graph_interfaces.ILike)
class LikeUniqueAttributeAdpater(_UserObjectUniqueAttributeAdpater):
	pass

@component.adapter(nti_interfaces.IEntity, nti_interfaces.IThreadable, graph_interfaces.IReply)
class InReplyToUniqueAttributeAdpater(_UserObjectUniqueAttributeAdpater):
	pass

AuthorshipUniqueAttributeAdpater = _UserObjectUniqueAttributeAdpater
