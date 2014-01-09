#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
graphdb property adapters

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.assessment import interfaces as asm_interfaces

from nti.dataserver import interfaces as nti_interfaces
from nti.dataserver.contenttypes.forums import interfaces as frm_interfaces

from nti.externalization import externalization

from . import interfaces as graph_interfaces

def get_ntiid(obj):
	return getattr(obj, 'NTIID', getattr(obj, 'ntiid'))

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
@component.adapter(interface.Interface)
class _GenericUniqueAttributeAdpater(object):

	key = value = None

	def __init__(self, obj):
		pass

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
class _OIDUniqueAttributeAdpater(object):

	key = "oid"

	def __init__(self, obj):
		self.obj = obj

	@property
	def value(self):
		result = externalization.to_external_ntiid_oid(self.obj)
		return result

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
class _EndRelationshipUniqueAttributeAdpater(_OIDUniqueAttributeAdpater):

	def __init__(self, _from, _to, _rel):
		# a relationship is identified by the end object oid
		super(_EndRelationshipUniqueAttributeAdpater, self).__init__(_to)

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
@component.adapter(nti_interfaces.IEntity)
class _EntityUniqueAttributeAdpater(object):

	key = "username"

	def __init__(self, obj):
		self.obj = obj

	@property
	def value(self):
		return self.obj.username

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
@component.adapter(nti_interfaces.IModeledContent)
class _ModeledContentUniqueAttributeAdpater(_OIDUniqueAttributeAdpater):
	pass

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
@component.adapter(frm_interfaces.ITopic)
class _TopicUniqueAttributeAdpater(object):

	key = "oid"

	def __init__(self, obj):
		self.obj = obj

	@property
	def value(self):
		return self.obj.NTIID

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
class _CommentUniqueAttributeAdpater(_OIDUniqueAttributeAdpater):
	pass

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
class _CommentRelationshipUniqueAttributeAdpater(object):

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

_FollowUniqueAttributeAdpater = _RelationshipUniqueAttributeAdpater
_FriendshipUniqueAttributeAdpater = _RelationshipUniqueAttributeAdpater
_TargetMembershipUniqueAttributeAdpater = _RelationshipUniqueAttributeAdpater

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
@component.adapter(asm_interfaces.IQuestionSet)
class _QuestionSetUniqueAttributeAdpater(object):

	key = "oid"

	def __init__(self, obj):
		self.obj = obj

	@property
	def value(self):
		return get_ntiid(self.obj)

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
@component.adapter(asm_interfaces.IQuestion)
class _QuestionUniqueAttributeAdpater(object):

	key = "oid"

	def __init__(self, obj):
		self.obj = obj

	@property
	def value(self):
		return get_ntiid(self.obj)

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
@component.adapter(asm_interfaces.IQAssignment)
class _AssignmentUniqueAttributeAdpater(object):

	key = "oid"

	def __init__(self, obj):
		self.obj = obj

	@property
	def value(self):
		result = get_ntiid(self.obj)
		return result

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
@component.adapter(asm_interfaces.IQuestion,
				   asm_interfaces.IQuestionSet,
				   graph_interfaces.IMemberOf)
class _QuestionMembershipUniqueAttributeAdpater(object):

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

@component.adapter(nti_interfaces.IEntity,
				   nti_interfaces.ILikeable,
				   graph_interfaces.ILike)
class _LikeUniqueAttributeAdpater(_UserObjectUniqueAttributeAdpater):
	pass

@component.adapter(nti_interfaces.IEntity,
				   nti_interfaces.IRatable,
				   graph_interfaces.IRate)
class _RateUniqueAttributeAdpater(_UserObjectUniqueAttributeAdpater):
	pass

@component.adapter(nti_interfaces.IEntity,
				   nti_interfaces.IFlaggable,
				   graph_interfaces.IFlagged)
class _FlaggUniqueAttributeAdpater(_UserObjectUniqueAttributeAdpater):
	pass

@component.adapter(nti_interfaces.IEntity,
				   nti_interfaces.IThreadable,
				   graph_interfaces.IReply)
class _InReplyToUniqueAttributeAdpater(_UserObjectUniqueAttributeAdpater):
	pass

_AuthorshipUniqueAttributeAdpater = _UserObjectUniqueAttributeAdpater

_AssessedRelationshipUniqueAttributeAdpater = _UserObjectUniqueAttributeAdpater

@interface.implementer(graph_interfaces.IUniqueAttributeAdapter)
@component.adapter(nti_interfaces.IUser,
				   asm_interfaces.IQAssignment,
				   graph_interfaces.ITakeAssessment)
class _AssignmentTakenUniqueAttributeAdpater(object):

	def __init__(self, _from, _to, _rel):
		self._to = _to
		self._rel = _rel
		self._from = _from

	@property
	def key(self):
		return self._from.username

	@property
	def value(self):
		ntiid = get_ntiid(self._to)
		result = '%s,%s' % (self._rel, ntiid)
		return result
