#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that

import fudge
import unittest

from nti.dataserver.users import User

from nti.dataserver.contenttypes import Note

from nti.graphdb.relationships import Reply
from nti.graphdb.relationships import IsReplyOf

from nti.graphdb.neo4j.database import Neo4jDB

from nti.graphdb.common import get_oid
from nti.graphdb.common import get_node_pk
from nti.graphdb.threadables import _remove_threadable
from nti.graphdb.threadables import _add_in_reply_to_relationship

from nti.ntiids.ntiids import make_ntiid

import nti.dataserver.tests.mock_dataserver as mock_dataserver
from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.graphdb.tests import DEFAULT_URI
from nti.graphdb.tests import cannot_connect
from nti.graphdb.tests import random_username
from nti.graphdb.tests import GraphDBTestCase

@unittest.skipIf(cannot_connect(DEFAULT_URI), "Neo4j not available")
class TestThreadables(GraphDBTestCase):

	def setUp(self):
		super(TestThreadables, self).setUp()
		self.db = Neo4jDB(DEFAULT_URI)

	def _create_user(self, username='nt@nti.com', password='temp001'):
		usr = User.create_user(self.ds, username=username, password=password)
		return usr

	def _create_random_user(self):
		username = random_username()
		user = self._create_user(username)
		return user

	def _create_note(self, msg, creator, containerId=None, inReplyTo=None):
		note = Note()
		note.body = [unicode(msg)]
		note.creator = creator
		note.containerId = containerId or make_ntiid(nttype='bleach', specific='manga')
		note.inReplyTo = inReplyTo
		return note

	@fudge.patch('nti.graphdb.sharing.get_graph_db')
	@WithMockDSTrans
	def test_threadables(self, mock_ggdb):
		mock_ggdb.is_callable().with_args().returns(None)

		user_1 = self._create_random_user()
		parent_note = self._create_note('parent note', user_1)
		mock_dataserver.current_transaction.add(parent_note)
		parent_note = user_1.addContainedObject(parent_note)

		user_2 = self._create_random_user()
		child_note = self._create_note('parent note', user_2, inReplyTo=parent_note)
		mock_dataserver.current_transaction.add(parent_note)
		child_note = user_2.addContainedObject(child_note)
		
		oid = get_oid(child_note)
		m = _add_in_reply_to_relationship(self.db, oid)
		assert_that(m, is_(True))
		
		m = self.db.match(child_note, parent_note, IsReplyOf())
		assert_that(m, has_length(1))
		
		m = self.db.match(user_2, user_1, rel_type=Reply())
		assert_that(m, has_length(1))
		
		pk = get_node_pk(child_note)
		m = self.db.get_indexed_relationships(pk.key, pk.value)
		assert_that(m, has_length(1))

		_remove_threadable(self.db, pk.label, pk.key, pk.value)
		
		m = self.db.get_indexed_relationships(pk.key, pk.value)
		assert_that(m, has_length(0))
		
		m = self.db.match(user_2, user_1, rel_type=Reply())
		assert_that(m, has_length(0))

		m = self.db.match(child_note, parent_note, IsReplyOf())
		assert_that(m, has_length(0))
