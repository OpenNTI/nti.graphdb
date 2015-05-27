#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import none
from hamcrest import is_not
from hamcrest import has_length
from hamcrest import assert_that

import unittest

from nti.dataserver.users import User

from nti.dataserver.contenttypes import Note

from nti.graphdb.relationships import Flagged
from nti.graphdb.neo4j.database import Neo4jDB

from nti.graphdb.common import get_oid
from nti.graphdb.flagging import _add_flagged_relationship
from nti.graphdb.flagging import _remove_flagged_relationship

from nti.ntiids.ntiids import make_ntiid

import nti.dataserver.tests.mock_dataserver as mock_dataserver
from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.graphdb.tests import DEFAULT_URI
from nti.graphdb.tests import cannot_connect
from nti.graphdb.tests import random_username
from nti.graphdb.tests import GraphDBTestCase

@unittest.skipIf(cannot_connect(DEFAULT_URI), "Neo4j not available")
class TestFlagging(GraphDBTestCase):

	def setUp(self):
		super(TestFlagging, self).setUp()
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
		note.containerId = containerId or make_ntiid(nttype='bleach', specific='manga')
		return note

	@WithMockDSTrans
	def test_flagging(self):
		user = self._create_random_user()
		note = self._create_note('sample note', user)
		mock_dataserver.current_transaction.add(note)
		note = user.addContainedObject(note)
		
		oid = get_oid(note)
		m = _add_flagged_relationship(self.db, user.username, oid)
		assert_that(m, is_not(none()))

		rels = self.db.match(user, note, Flagged())
		assert_that(rels, has_length(1))
		
		_remove_flagged_relationship(self.db, user.username, oid)
		
		rels = self.db.match(user, note, Flagged())
		assert_that(rels, has_length(0))