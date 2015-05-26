#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that

import uuid
import unittest

from nti.dataserver.users import User

from nti.dataserver.contenttypes import Note

from nti.graphdb.relationships import Contained

from nti.graphdb.neo4j.database import Neo4jDB

from nti.graphdb.common import get_oid
from nti.graphdb.interfaces import IContainer
from nti.graphdb.containers import _update_container
from nti.graphdb.containers import _add_contained_membership

import nti.dataserver.tests.mock_dataserver as mock_dataserver
from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.graphdb.tests import DEFAULT_URI
from nti.graphdb.tests import cannot_connect
from nti.graphdb.tests import random_username
from nti.graphdb.tests import GraphDBTestCase

@unittest.skipIf(cannot_connect(DEFAULT_URI), "Neo4j not available")
class TestContainers(GraphDBTestCase):

	def setUp(self):
		super(TestContainers, self).setUp()
		self.db = Neo4jDB(DEFAULT_URI)

	def _create_user(self, username='nt@nti.com', password='temp001'):
		usr = User.create_user(self.ds, username=username, password=password)
		return usr

	def _create_random_user(self):
		username = random_username()
		user = self._create_user(username)
		return user

	def _create_note(self, msg, creator, containerId=None):
		note = Note()
		note.body = [unicode(msg)]
		note.creator = creator
		note.containerId = containerId or str(uuid.uuid4())
		return note

	@WithMockDSTrans
	def test_containers(self):
		user_1 = self._create_random_user()
		note = self._create_note('sample note', user_1)
		mock_dataserver.current_transaction.add(note)
		note = user_1.addContainedObject(note)
		containerId = note.containerId
		
		oid = get_oid(note)
		m = _add_contained_membership(self.db, oid, containerId)
		assert_that(m, is_(True))

		m = _update_container(self.db, containerId=containerId)
		assert_that(m, is_(True))

		container = IContainer(containerId)
		rels = self.db.match(note, container, Contained())
		assert_that(rels, has_length(1))
