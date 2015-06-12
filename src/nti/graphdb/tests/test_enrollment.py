#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import none
from hamcrest import is_not
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property

import uuid
import fudge
import unittest
from hashlib import md5

from nti.contenttypes.courses.courses import ContentCourseInstance
from nti.contenttypes.courses.courses import CourseAdministrativeLevel

from nti.contenttypes.courses.interfaces import ICourseCatalogEntry
from nti.contenttypes.courses.interfaces import ICourseEnrollmentManager

from nti.dataserver.users import User

from nti.graphdb.relationships import Enroll
from nti.graphdb.relationships import Unenroll
from nti.graphdb.neo4j.database import Neo4jDB

from nti.graphdb.common import get_oid
from nti.graphdb.enrollment import _process_enrollment_event
from nti.graphdb.enrollment import _process_unenrollment_event
from nti.graphdb.enrollment import _process_enrollment_modified_event

from nti.ntiids.ntiids import make_ntiid

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.graphdb.tests import DEFAULT_URI
from nti.graphdb.tests import cannot_connect
from nti.graphdb.tests import random_username
from nti.graphdb.tests import GraphDBTestCase

class MockContentPackage(object):
	ntiid = "tag:nextthought.com,2011-10:USSC-HTML-Cohen.cohen_v._california."

class MockContentPackageBundle(object):

	@property
	def ContentPackages(self):
		return (MockContentPackage(),)

@unittest.skipIf(cannot_connect(DEFAULT_URI), "Neo4j not available")
class TestEnrollment(GraphDBTestCase):

	def setUp(self):
		super(TestEnrollment, self).setUp()
		self.db = Neo4jDB(DEFAULT_URI)

	def _create_user(self, username='nt@nti.com', password='temp001'):
		usr = User.create_user(self.ds, username=username, password=password)
		return usr

	def _create_random_user(self):
		username = random_username()
		user = self._create_user(username)
		return user

	def _shared_setup(self):
		admin = CourseAdministrativeLevel()
		self.ds.root['admin'] = admin
		course_name = random_username()
		for name in (course_name,):
			course = ContentCourseInstance()
			admin[name] = course
			course.SharingScopes.initScopes()

			bundle = MockContentPackageBundle()
			# bypass field validation
			course.__dict__[str('ContentPackageBundle')] = bundle

		self.course = admin[course_name]
		return self.course

	@fudge.patch('nti.graphdb.enrollment._get_catalog_entry')
	@WithMockDSTrans
	def test_enrollment(self, mock_gce):
		principal = self._create_random_user()
		course = self._shared_setup()
		entry = ICourseCatalogEntry(course)
		ntiid = make_ntiid(provider='NTI',
						   nttype='CourseInfo',
						   specific=md5(str(uuid.uuid4())).hexdigest())
		entry.__dict__[str('_cached_ntiid')] = ntiid

		manager = ICourseEnrollmentManager(course)
		record = manager.enroll(principal, scope='Public')
		oid = get_oid(record)
		
		m = _process_enrollment_event(self.db, oid)
		assert_that(m, is_not(none()))

		rels = self.db.match(principal, entry, Enroll())
		assert_that(rels, has_length(1))

		record.Scope = 'ForCredit'
		m = _process_enrollment_modified_event(self.db, oid)
		assert_that(m, is_not(none()))
		assert_that(m, has_property('properties', has_entry('scope', 'ForCredit')))
		
		mock_gce.is_callable().with_args().returns(entry)
		_process_unenrollment_event(self.db, principal.username, ntiid)

		rels = self.db.match(principal, entry, Unenroll())
		assert_that(rels, has_length(1))
