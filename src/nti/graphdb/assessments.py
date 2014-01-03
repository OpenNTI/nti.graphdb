#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
Gradebook event subscribers

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

from nti.app.assessment import interfaces as appa_interfaces

from nti.app.products.courseware import interfaces as cw_interfaces

from nti.assessment import interfaces as assessment_interfaces

from nti.dataserver import users
from nti.dataserver import interfaces as nti_interfaces

from . import get_graph_db
from . import relationships
from . import interfaces as graph_interfaces

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

def get_course_enrollments(user):
	container = []
	for catalog in component.subscribers((user,), cw_interfaces.IPrincipalEnrollmentCatalog):
		queried = catalog.iter_enrollments()
		container.extend(queried)
	container[:] = [cw_interfaces.ICourseInstanceEnrollment(x) for x in container]
	return container

def init(db, user):
	if not nti_interfaces.IUser.providedBy(user):
		return
	enrollments = get_course_enrollments(user)
	for enrollment in enrollments:
		course = enrollment.CourseInstance
		history = component.getMultiAdapter((course, user),
											appa_interfaces.IUsersCourseAssignmentHistory)
		for assignmentId, _ in history.items():
			add_assignment_taken_relationship(db, user.username, assignmentId)
