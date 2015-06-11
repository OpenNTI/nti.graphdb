#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from zope.intid.interfaces import IIntIdRemovedEvent

from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent

from nti.contenttypes.courses.interfaces import ICourseCatalogEntry
from nti.contenttypes.courses.interfaces import ICourseInstanceEnrollmentRecord

from nti.dataserver.users import User

from nti.ntiids.ntiids import find_object_with_ntiid

from .common import get_oid
from .common import get_principal_id

from .relationships import Enroll
from .relationships import Unenroll

from .interfaces import IPropertyAdapter
from .interfaces import IObjectProcessor

from . import OID
from . import create_job
from . import get_graph_db
from . import get_job_queue

def _get_user(record):
	pid = get_principal_id(record)
	result = User.get_user(pid or u'')
	return result

def _get_entry(record):
	entry = ICourseCatalogEntry(record.CourseInstance, None)
	return entry

def _process_enrollment_event(db, oid):
	record = find_object_with_ntiid(oid)
	if record is None:
		return None

	user = _get_user(record)
	entry = _get_entry(record)
	if entry is not None and user is not None:
		properies = IPropertyAdapter(record)
		rel = db.create_relationship(user, entry, Enroll(), properies=properies)
		logger.debug("Enrollment relationship %s created", rel)
		# index to find later
		db.index_relationship(rel, OID, oid)
		return rel
	return None

def _process_user_enrollment(db, record):
	oid = get_oid(record)
	queue = get_job_queue()
	job = create_job(_process_enrollment_event, 
					 db=db,
					 oid=oid)
	queue.put(job)

@component.adapter(ICourseInstanceEnrollmentRecord, IObjectAddedEvent)
def _enrollement_added(record, event):
	db = get_graph_db()
	if db is not None:
		_process_user_enrollment(db, record)

def _process_enrollment_modified_event(db, oid):
	record = find_object_with_ntiid(oid)
	if record is None:
		return None
	
	found_rel = None
	rel_type = str(Enroll())
	rels = db.get_indexed_relationships(OID, oid)
	for rel in rels:
		if str(rel.type) == rel_type:
			found_rel = rel
			break

	if found_rel is None:
		properies = IPropertyAdapter(record)
		db.update_relationship(rel, properies)
		logger.debug("Enrollment relationship %s updated", found_rel)
	else:
		found_rel = _process_enrollment_event(db, oid)
	return found_rel

def _process_enrollment_modified(db, record):
	oid = get_oid(record)
	queue = get_job_queue()
	job = create_job(_process_enrollment_modified_event, 
					 db=db,
					 oid=oid)
	queue.put(job)
	
@component.adapter(ICourseInstanceEnrollmentRecord, IObjectModifiedEvent)
def _enrollment_modified(record, event):
	db = get_graph_db()
	if db is not None:
		_process_enrollment_modified(db, record)

def _process_unenrollment_event(db, username, entry):
	user = User.get_user(username)
	entry = find_object_with_ntiid(entry)
	if user is None or entry is None:
		return None
		
	rel = db.create_relationship(user, entry, Unenroll())
	logger.debug("Enrollment relationship %s created", rel)		
	return rel

def _process_user_unenrollment(db, record):
	username = get_principal_id(record)
	entry = ICourseCatalogEntry(record.CourseInstance, None)
	entry = entry.ntiid if entry is not None else None
	if username and entry:
		queue = get_job_queue()
		job = create_job(_process_unenrollment_event, 
						 db=db,
						 entry=entry,
						 username=username)
		queue.put(job)

@component.adapter(ICourseInstanceEnrollmentRecord, IIntIdRemovedEvent)
def _enrollment_removed(record, event):
	db = get_graph_db()
	if db is not None:
		_process_user_unenrollment(db, record)

component.moduleProvides(IObjectProcessor)

def init(db, obj):
	result = True
	if ICourseInstanceEnrollmentRecord.providedBy(obj):
		_process_user_enrollment(db, obj)
	else:
		result = False
	return result
