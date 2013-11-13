#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
graphdb assessment

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import gevent
import functools
import transaction

from zope import component
from zope.lifecycleevent import interfaces as lce_interfaces

from nti.assessment import interfaces as asm_interfaces

from nti.dataserver import users
from nti.dataserver import interfaces as nti_interfaces

from nti.externalization import externalization

from nti.ntiids import ntiids

from . import get_graph_db
from . import relationships
from . import interfaces as graph_interfaces

def _do_add_assessment_relationship(db, assessed, taker=None):
	taker = taker or assessed.creator
	result = db.create_relationship(taker, assessed, relationships.TakeAssessment())
	logger.debug("take-assessment relationship %s created" % result)
	return result

def add_assessment_relationship(db, oid):
	qaset = ntiids.find_object_with_ntiid(oid)
	return _do_add_assessment_relationship(db, qaset) if qaset is not None else None

def _do_add_assessment_node(db, assessed):
	result = db.get_or_create_node(assessed)
	logger.debug("node %s retreived/created" % result)
	return result

def add_assessment_node(db, oid):
	obj = ntiids.find_object_with_ntiid(oid)
	if obj is not None:
		node = _do_add_assessment_node(db, obj)
		return obj, node
	return (None, None)

def create_question_membership(db, question, questionset):
	rel_type = relationships.MemberOf()
	adapter = component.getMultiAdapter(
							(question, questionset, rel_type),
							graph_interfaces.IUniqueAttributeAdapter)
	if db.get_indexed_relationship(adapter.key, adapter.value) is None:
		db.create_relationship(question, questionset, rel_type)
		logger.debug("question-questionset membership relationship created")
		return True
	return False

def process_assessed_question_set(db, oid):
	qaset, _ = add_assessment_node(db, oid)
	if qaset is not None:
		# create relationship taker->question-set
		_do_add_assessment_relationship(db, qaset)
		for question in qaset.questions:
			# create relationship question --> questionset
			create_question_membership(db, question, qaset)
			# create relationship taker->question
			_do_add_assessment_node(db, question)
			_do_add_assessment_relationship(db, question, qaset.creator)

def process_assessed_question(db, oid):
	question, _ = add_assessment_node(db, oid)
	if question is not None:
		_do_add_assessment_relationship(db, question)
		
def _queue_question_event(db, oid, event, is_questionset=True):

	def _process_event():
		transaction_runner = \
				component.getUtility(nti_interfaces.IDataserverTransactionRunner)
		if event == graph_interfaces.ADD_EVENT:
			func = process_assessed_question_set if is_questionset \
												 else process_assessed_question
			func = functools.partial(func, db=db, oid=oid)
			transaction_runner(func)

	transaction.get().addAfterCommitHook(
					lambda success: success and gevent.spawn(_process_event))

@component.adapter(asm_interfaces.IQAssessedQuestionSet,
				   lce_interfaces.IObjectAddedEvent)
def _questionset_assessed(question_set, event):
	db = get_graph_db()
	if db is not None:
		oid = externalization.to_external_ntiid_oid(question_set)
		_queue_question_event(db, oid, graph_interfaces.ADD_EVENT)

@component.adapter(asm_interfaces.IQAssessedQuestion, lce_interfaces.IObjectAddedEvent)
def _question_assessed(question, event):
	db = get_graph_db()
	if db is not None:
		oid = externalization.to_external_ntiid_oid(question)
		_queue_question_event(db, oid, graph_interfaces.ADD_EVENT, False)

# utils

def install(db, usernames=()):

	from zope.generations.utility import findObjectsMatching
	
	if not usernames:
		dataserver = component.getUtility(nti_interfaces.IDataserver)
		_users = nti_interfaces.IShardLayout(dataserver).users_folder
		usernames = _users.iterkeys()

	condition = lambda x : 	asm_interfaces.IQAssessedQuestion.providedBy(x) or \
							asm_interfaces.IQAssessedQuestionSet.providedBy(x)


	def _build_assessed_graph_object(db, obj):
		oid = externalization.to_external_ntiid_oid(obj)
		is_questionset = asm_interfaces.IQAssessedQuestionSet.providedBy(obj)
		func = process_assessed_question_set if is_questionset else process_assessed_question
		func(db, oid)
	
	for username in usernames:
		user = users.Entity.get_entity(username)
		if not nti_interfaces.IUser.providedBy(user):
			continue
				
		for assessed in findObjectsMatching(user, condition):
			_build_assessed_graph_object(db, assessed)

