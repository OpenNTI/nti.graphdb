#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
Gradebook event subscribers

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import gevent
import functools
import transaction

from zope import component
from zope.lifecycleevent import interfaces as lce_interfaces

from nti.app.assessment import interfaces as appa_interfaces

from nti.app.products.courseware import interfaces as cw_interfaces

from nti.assessment import interfaces as assessment_interfaces

from nti.dataserver import users
from nti.dataserver import interfaces as nti_interfaces

from nti.externalization import externalization

from nti.ntiids import ntiids

from . import get_graph_db
from . import relationships
from . import interfaces as graph_interfaces

# question/questionset

def add_question_relationship(db, assessed, taker=None):
	taker = taker or assessed.creator
	result = db.create_relationship(taker, assessed, relationships.TakeAssessment())
	logger.debug("take-assessment relationship %s created" % result)
	return result

def add_question_node(db, assessed):
	obj = assessed if not isinstance(assessed, six.string_types) \
				   else ntiids.find_object_with_ntiid(assessed)
	if obj is not None:
		node = db.get_or_create_node(assessed)
		logger.debug("node %s retreived/created" % node)
		return obj, node
	return (None, None)
add_questionset_node = add_question_node

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

def _process_assessed_questionset(db, oid):
	qaset, _ = add_questionset_node(db, oid)
	if qaset is not None:
		# create relationship taker->question-set
		add_question_relationship(db, qaset)
		for question in qaset.questions:
			# create relationship question --> questionset
			create_question_membership(db, question, qaset)
			# create relationship taker->question
			add_question_node(db, question)
			add_question_relationship(db, question, qaset.creator)

def _process_assessed_question(db, oid):
	question, _ = add_question_node(db, oid)
	if question is not None:
		add_question_relationship(db, question)

def _queue_question_event(db, assessed):

	oid = externalization.to_external_ntiid_oid(assessed)
	is_questionset = assessment_interfaces.IQAssessedQuestionSet.providedBy(assessed)

	def _process_event():
		transaction_runner = \
				component.getUtility(nti_interfaces.IDataserverTransactionRunner)

		func = _process_assessed_questionset if is_questionset \
											 else _process_assessed_question
		func = functools.partial(func, db=db, oid=oid)
		transaction_runner(func)

	transaction.get().addAfterCommitHook(
					lambda success: success and gevent.spawn(_process_event))

@component.adapter(assessment_interfaces.IQAssessedQuestionSet,
				   lce_interfaces.IObjectAddedEvent)
def _questionset_assessed(question_set, event):
	db = get_graph_db()
	if db is not None:
		_queue_question_event(db, question_set)

@component.adapter(assessment_interfaces.IQAssessedQuestion,
				   lce_interfaces.IObjectAddedEvent)
def _question_assessed(question, event):
	db = get_graph_db()
	if db is not None:
		_queue_question_event(db, question)

# assignments

def add_assignment_node(db, assignmentId):
	node = None
	a = component.queryUtility(assessment_interfaces.IQAssignment, assignmentId)
	if a is not None:
		adapted = graph_interfaces.IUniqueAttributeAdapter(a)
		key, value = adapted.key, adapted.value
		node = db.get_indexed_node(key, value)
		if node is None:
			node = db.create_node(a)
	return (a, node)

def add_assignment_taken_relationship(db, username, assignmentId):
	a, _ = add_assignment_node(db, assignmentId)
	user = users.User.get_user(username)
	if a is not None and user is not None:
		rel = db.create_relationship(user, a, relationships.TakeAssessment())
		return rel
	return None

def process_assignment_taken(db, item):
	assignmentId = item.__name__  # by definition
	username = nti_interfaces.IUser(item).username
	def _process_event():
		transaction_runner = \
				component.getUtility(nti_interfaces.IDataserverTransactionRunner)

		func = functools.partial(add_assignment_taken_relationship, db=db,
								 username=username,
								 assignmentId=assignmentId)
		transaction_runner(func)

	transaction.get().addAfterCommitHook(
				lambda success: success and gevent.spawn(_process_event))

@component.adapter(appa_interfaces.IUsersCourseAssignmentHistoryItem,
				   lce_interfaces.IObjectAddedEvent)
def _assignment_history_item_added(item, event):
	db = get_graph_db()
	if db is not None:
		process_assignment_taken(db, item)

# utils

from zope.generations.utility import findObjectsMatching

def get_course_enrollments(user):
	container = []
	for catalog in component.subscribers((user,), cw_interfaces.IPrincipalEnrollmentCatalog):
		queried = catalog.iter_enrollments()
		container.extend(queried)
	container[:] = [cw_interfaces.ICourseInstanceEnrollment(x) for x in container]
	return container

def init_asssignments(db, user):
	enrollments = get_course_enrollments(user)
	for enrollment in enrollments:
		course = enrollment.CourseInstance
		history = component.getMultiAdapter((course, user),
											appa_interfaces.IUsersCourseAssignmentHistory)
		for assignmentId, _ in history.items():
			add_assignment_taken_relationship(db, user.username, assignmentId)

def init_questions(db, user):

	condition = lambda x : 	assessment_interfaces.IQAssessedQuestion.providedBy(x) or \
							assessment_interfaces.IQAssessedQuestionSet.providedBy(x)

	for assessed in findObjectsMatching(user, condition):
		oid = externalization.to_external_ntiid_oid(assessed)
		is_questionset = assessment_interfaces.IQAssessedQuestionSet.providedBy(assessed)
		func = _process_assessed_questionset if is_questionset \
											 else _process_assessed_question
		func(db, oid)

def init(db, user):
	if nti_interfaces.IUser.providedBy(user):
		init_questions(db, user)
		init_asssignments(db, user)
