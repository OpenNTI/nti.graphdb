#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six

from zope import component
from zope import interface
from zope.lifecycleevent import interfaces as lce_interfaces

from pyramid.traversal import find_interface
from pyramid.threadlocal import get_current_request

from nti.app.assessment import interfaces as appa_interfaces

from nti.app.products.courseware import interfaces as cw_interfaces

from nti.app.products.gradebook import interfaces as gb_interfaces

from nti.assessment import interfaces as assessment_interfaces

from nti.contenttypes.courses.interfaces import ICourseInstance

from nti.dataserver import users
from nti.dataserver import interfaces as nti_interfaces

from nti.externalization import externalization

from nti.ntiids import ntiids

from . import create_job
from . import get_graph_db
from . import get_job_queue
from . import relationships
from . import interfaces as graph_interfaces

# question/question_set

def _get_creator_in_lineage(obj):
	result = None
	while result is None and obj is not None:
		result = getattr(obj, 'creator', None)
		obj = getattr(obj, '__parent__', None)
		if nti_interfaces.IUser.providedBy(obj) and result is None:
			result = obj
	return result

def _get_underlying(obj):
	if 	assessment_interfaces.IQuestion.providedBy(obj) or \
		assessment_interfaces.IQuestionSet.providedBy(obj) or \
		assessment_interfaces.IQAssignment.providedBy(obj) :
		result = obj
	elif assessment_interfaces.IQAssessedQuestion.providedBy(obj):
		result = component.getUtility(assessment_interfaces.IQuestion,
									  name=obj.questionId)
	elif assessment_interfaces.IQAssessedQuestionSet.providedBy(obj):
		result = component.getUtility(assessment_interfaces.IQuestionSet,
									  name=obj.questionSetId)
	else:
		result = None # Throw Exception?
	return result

def _add_assessed_relationship(db, assessed, taker=None):
	taker = taker or _get_creator_in_lineage(assessed)
	rel_type = relationships.TakeAssessment()
	properties = component.getMultiAdapter(
								(taker, assessed, rel_type),
								graph_interfaces.IPropertyAdapter)
	
	unique = component.getMultiAdapter(
								(taker, assessed, rel_type),
								graph_interfaces.IUniqueAttributeAdapter)
		
	underlying = _get_underlying(assessed)
	result = db.create_relationship(taker, underlying, rel_type,
									properties=properties,
									key=unique.key, value=unique.value)
	logger.debug("taker-question[set] relationship %s created" % result)
	return result

def _add_question_node(db, obj):
	obj = obj if not isinstance(obj, six.string_types) \
				  	 else ntiids.find_object_with_ntiid(obj)
	if obj is not None:
		underlying = _get_underlying(obj)
		node = db.get_or_create_node(underlying)
		return obj, node
	return (None, None)
_add_questionset_node = _add_question_node

def _create_slave_master_membership(db, slave, master, rel_type=None):
	rel_type = rel_type or relationships.MemberOf()
	adapter = component.getMultiAdapter(
							(slave, master, rel_type),
							graph_interfaces.IUniqueAttributeAdapter)
	if db.get_indexed_relationship(adapter.key, adapter.value) is None:
		db.create_relationship(slave, master, rel_type)
		return True
	return False

def _create_question_membership(db, question, question_set):
	question = _get_underlying(question)
	question_set = _get_underlying(question_set)
	if question is not None and question_set is not None:
		return _create_slave_master_membership(db, question, question_set)

def _create_question_set_membership(db, question_set):
	for question in question_set.questions:
		_create_slave_master_membership(db, question, question_set)

def _process_assessed_question_set(db, oid):
	qaset, _ = _add_questionset_node(db, oid)
	if qaset is not None:
		# create relationship taker->question-set
		_add_assessed_relationship(db, qaset)
		for question in qaset.questions:
			# create relationship question --> question_set
			_add_question_node(db, question)
			_create_question_membership(db, question, qaset)

def _process_assessed_question(db, oid):
	question, _ = _add_question_node(db, oid)
	if question is not None:
		_add_assessed_relationship(db, question)

def _queue_question_event(db, assessed):
	oid = externalization.to_external_ntiid_oid(assessed)
	is_question_set = assessment_interfaces.IQAssessedQuestionSet.providedBy(assessed)
	queue = get_job_queue()
	if is_question_set:
		job = create_job(_process_assessed_question_set, db=db, oid=oid)
	else:
		job = create_job(_process_assessed_question, db=db, oid=oid)
	queue.put(job)

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
	assignment = component.queryUtility(assessment_interfaces.IQAssignment, assignmentId)
	if assignment is not None:
		adapted = graph_interfaces.IUniqueAttributeAdapter(assignment)
		key, value = adapted.key, adapted.value
		node = db.get_indexed_node(key, value)
		if node is None:
			node = db.create_node(assignment)
			for part in assignment.parts:
				question_set = part.question_set
				_create_slave_master_membership(db, question_set, assignment)
				_create_question_set_membership(db, part.question_set)
	return (assignment, node)

def add_assignment_taken_relationship(db, username, assignmentId):
	assignment, _ = add_assignment_node(db, assignmentId)
	user = users.User.get_user(username)
	if assignment is not None and user is not None:
		rel = db.create_relationship(user, assignment, relationships.TakeAssessment())
		return rel
	return None

def process_assignment_taken(db, item):
	assignmentId = item.__name__  # by definition
	username = nti_interfaces.IUser(item).username
	queue = get_job_queue()
	job = create_job(add_assignment_taken_relationship, db=db,
					 username=username,
					 assignmentId=assignmentId)
	queue.put(job)

@component.adapter(appa_interfaces.IUsersCourseAssignmentHistoryItem,
				   lce_interfaces.IObjectAddedEvent)
def _assignment_history_item_added(item, event):
	db = get_graph_db()
	if db is not None:
		process_assignment_taken(db, item)

def set_grade_to_assignment(db, username, assignmentId, value):
	rel = add_assignment_taken_relationship(db, username, assignmentId)
	if rel is not None and value:
		props = dict(rel.properties)
		props['grade'] = unicode(str(value))
		db.update_relationship(rel, props)

def process_grade_modified(db, grade):
	assignmentId = grade.AssignmentId
	if assignmentId:
		queue = get_job_queue()
		job = create_job(set_grade_to_assignment, db=db,
						 username=grade.Username,
						 assignmentId=grade.AssignmentId,
						 value=grade.value)
		queue.put(job)

@component.adapter(gb_interfaces.IGrade,
				   lce_interfaces.IObjectModifiedEvent)
def _grade_modified(grade, event):
	db = get_graph_db()
	if db is not None:
		process_grade_modified(db, grade)

@component.adapter(gb_interfaces.IGrade,
				   lce_interfaces.IObjectAddedEvent)
def _grade_added(grade, event):
	_grade_modified(grade, event)

# feedback

def get_current_user():
	request = get_current_request()
	username = request.authenticated_userid if request is not None else None
	return username

def _pick_instructor(course):
	instructors = course.instructors if course is not None else None
	for instructor in instructors or ():
		entity = instructor if nti_interfaces.IEntity.providedBy(instructor) \
							else users.User.get_entity(str(instructor))
		if entity is not None:
			return entity
	return None
			
def set_asm_feedback(db, oid, username=None):
	feedback = ntiids.find_object_with_ntiid(oid)
	user = users.User.get_entity(username) if username else None
	if feedback is not None:
		creator = feedback.creator
		if user is None or user == creator:
			direction = 1  # feedback from student to professor
			item = find_interface(feedback,
								  appa_interfaces.IUsersCourseAssignmentHistoryItem)
			course = ICourseInstance(item, None)
			instructor = _pick_instructor(course)  # pick first found
			if user is None:
				direction = 2  # feedback from professor to student
		else:
			direction = 2
			instructor = user  # feedback from professor to student

		if not instructor:
			return

		rel_type = relationships.AssigmentFeedback()
		properties = graph_interfaces.IPropertyAdapter(feedback)
		unique = graph_interfaces.IUniqueAttributeAdapter(feedback)

		if direction == 1:
			rel = db.create_relationship(creator, instructor, rel_type,
										 properties=properties,
										 key=unique.key, value=unique.value)
		else:
			rel = db.create_relationship(instructor, creator, rel_type,
										 properties=properties,
										 key=unique.key, value=unique.value)
		return rel

def _process_feedback_added(db, feedback, user=None):
	username = getattr(user, 'username', user)
	oid = externalization.to_external_ntiid_oid(feedback)
	queue = get_job_queue()
	job = create_job(set_asm_feedback, db=db,
					 oid=oid, username=username)
	queue.put(job)

@component.adapter(appa_interfaces.IUsersCourseAssignmentHistoryItemFeedback,
				   lce_interfaces.IObjectAddedEvent)
def _feedback_added(feedback, event):
	db = get_graph_db()
	if db is not None:
		_process_feedback_added(db, feedback, get_current_user())

def del_asm_feedback(db, key, value):
	if db.delete_indexed_relationship(key, value):
		logger.debug("Assignment feedback relationship %s deleted" % value)
		return True
	return False

def _process_feedback_removed(db, feedback):
	unique = graph_interfaces.IUniqueAttributeAdapter(feedback)
	queue = get_job_queue()
	job = create_job(del_asm_feedback, db=db, key=unique.key, value=unique.value)
	queue.put(job)

@component.adapter(appa_interfaces.IUsersCourseAssignmentHistoryItemFeedback,
				   lce_interfaces.IObjectRemovedEvent)
def _feedback_removed(feedback, event):
	db = get_graph_db()
	if db is not None:
		_process_feedback_removed(db, feedback)

# utils

def get_course_enrollments(user):
	container = []
	subs = component.subscribers((user,), cw_interfaces.IPrincipalEnrollmentCatalog)
	for catalog in subs:
		queried = catalog.iter_enrollments()
		container.extend(queried)
	container[:] = [cw_interfaces.ICourseInstanceEnrollment(x) for x in container]
	return container

def init_asssignments(db, user):
	enrollments = get_course_enrollments(user)
	for enrollment in enrollments:
		course = enrollment.CourseInstance
		history = component.getMultiAdapter(
									(course, user),
									appa_interfaces.IUsersCourseAssignmentHistory)
		for _, item in history.items():
			grade = gb_interfaces.IGrade(item, None)
			if grade is not None and grade.value is not None:
				process_grade_modified(db, grade)
			else:
				process_assignment_taken(db, item)

interface.moduleProvides(graph_interfaces.IObjectProcessor)

def init(db, obj):
	result = True
	if 	assessment_interfaces.IQAssessedQuestionSet.providedBy(obj) or \
		assessment_interfaces.IQAssessedQuestionSet.providedBy(obj):
		_queue_question_event(db, obj)
	elif nti_interfaces.IUser.providedBy(obj):
		init_asssignments(db, obj)
	elif appa_interfaces.IUsersCourseAssignmentHistoryItemFeedback.providedBy(obj):
		_process_feedback_added(db, obj)
	else:
		result = False
	return result
