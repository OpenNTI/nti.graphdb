#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
graphdb label adapters

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.assessment import interfaces as asm_interfaces

from nti.contentsearch import discriminators

from nti.dataserver import interfaces as nti_interfaces
from nti.dataserver.contenttypes.forums import interfaces as frm_interfaces

from . import interfaces as graph_interfaces

#### labels

@interface.implementer(graph_interfaces.ILabelAdapter)
@component.adapter(interface.Interface)
def _GenericLabelAdpater(obj):
	return ()

@interface.implementer(graph_interfaces.ILabelAdapter)
@component.adapter(nti_interfaces.IEntity)
def _EntityLabelAdpater(entity):
	return (entity.__class__.__name__.lower(),)

@interface.implementer(graph_interfaces.ILabelAdapter)
@component.adapter(nti_interfaces.IUser)
def _UserLabelAdpater(entity):
	return ('user',)

@interface.implementer(graph_interfaces.ILabelAdapter)
@component.adapter(nti_interfaces.IDynamicSharingTargetFriendsList)
def _DFLLabelAdpater(obj):
	return ('dfl',)

@interface.implementer(graph_interfaces.ILabelAdapter)
@component.adapter(nti_interfaces.IModeledContent)
def _ModeledContentLabelAdpater(modeled):
	return (modeled.__class__.__name__.lower(),)

@component.adapter(nti_interfaces.INote)
def _NoteLabelAdpater(note):
	tags = discriminators.get_tags(note, ())
	return ('note',) + tuple([r.lower() for r in tags])

@interface.implementer(graph_interfaces.ILabelAdapter)
def _CommentLabelAdpater(obj):
	result = ('comment',)
	return result

@interface.implementer(graph_interfaces.ILabelAdapter)
@component.adapter(frm_interfaces.IForum)
def _ForumLabelAdpater(modeled):
	return ("forum",)

@interface.implementer(graph_interfaces.ILabelAdapter)
@component.adapter(frm_interfaces.ITopic)
def _TopicLabelAdpater(topic):
	tags = set(discriminators.get_tags(topic, ()))
	headline = getattr(topic, 'headline', None)
	if headline is not None:
		tags.update(discriminators.get_tags(headline, ()))
	return ('topic',) + tuple([r.lower() for r in tags])
	
@interface.implementer(graph_interfaces.ILabelAdapter)
@component.adapter(asm_interfaces.IQuestionSet)
def _QuestionSetLabelAdpater(obj):
	result = ('questionset',)
	return result

@interface.implementer(graph_interfaces.ILabelAdapter)
@component.adapter(asm_interfaces.IQuestion)
def _QuestionLabelAdpater(question):
	result = ('question',)
	return result

@interface.implementer(graph_interfaces.ILabelAdapter)
@component.adapter(asm_interfaces.IQAssignment)
def _AssignmentLabelAdpater(question):
	result = ('assignment',)
	return result
