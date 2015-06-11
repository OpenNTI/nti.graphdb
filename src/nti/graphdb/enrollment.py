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
#from .relationships import Unenroll

from .interfaces import IPropertyAdapter
from .interfaces import IObjectProcessor

from . import OID
from . import create_job
from . import get_graph_db
from . import get_job_queue

def _process_add_enrollment_event(db, oid):
	record = find_object_with_ntiid(oid)
	if record is not None:
		return None

	user = User.get_user(get_principal_id(record) or u'')
	entry = ICourseCatalogEntry(record.CourseInstance, None)
	if entry is not None and user is not None:
		db.get_or_create_node(user)
		db.get_or_create_node(entry)
		
		# create relationship
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
	job = create_job(_process_add_enrollment_event, 
					 db=db,
					 oid=oid)
	queue.put(job)

@component.adapter(ICourseInstanceEnrollmentRecord, IObjectAddedEvent)
def _enrollement_added(record, event):
	db = get_graph_db()
	if db is not None:
		_process_user_enrollment(db, record)

@component.adapter(ICourseInstanceEnrollmentRecord, IObjectModifiedEvent)
def _enrollment_modified(topic, event):
	db = get_graph_db()
	if db is not None:
		pass #_process_topic_event(db, topic, MODIFY_EVENT)

@component.adapter(ICourseInstanceEnrollmentRecord, IIntIdRemovedEvent)
def _enrollment_removed(topic, event):
	db = get_graph_db()
	if db is not None:
		#_process_topic_event(db, topic, MODIFY_EVENT)
		pass

component.moduleProvides(IObjectProcessor)

def init(db, obj):
	result = True
	if ICourseInstanceEnrollmentRecord.providedBy(obj):
		_process_user_enrollment(db, obj)
	else:
		result = False
	return result
