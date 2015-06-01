#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_length
from hamcrest import assert_that

import fudge
import unittest

from nti.dataserver.users import User

from nti.dataserver.contenttypes import Note

from nti.graphdb.relationships import Shared
from nti.graphdb.relationships import IsSharedWith

from nti.graphdb.neo4j.database import Neo4jDB

from nti.graphdb.common import get_oid
from nti.graphdb.threadables import _add_in_reply_to_relationship
from nti.graphdb.sharing import _create_shared_rel
from nti.graphdb.sharing import _create_is_shared_with_rels
from nti.graphdb.sharing import _delete_is_shared_with_rels

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
# 		sharedWith = _get_sharedWith(note)
# 		m = _create_is_shared_with_rels(self.db, oid, sharedWith)
# 		assert_that(m, has_length(2))
# 
# 		rels = self.db.match(note, user_2, IsSharedWith())
# 		assert_that(rels, has_length(1))
# 
# 		rels = self.db.match(note, user_3, IsSharedWith())
# 		assert_that(rels, has_length(1))
# 
# 		m = _create_shared_rel(self.db, oid)
# 		assert_that(m, is_not(none()))
# 
# 		rels = self.db.match(user_1, note, Shared())
# 		assert_that(rels, has_length(1))
# 
# 		usernames = [getattr(x, 'username', x) for x in sharedWith]
# 		m = _delete_is_shared_with_rels(self.db, oid, usernames)
# 		assert_that(m, is_(2))
