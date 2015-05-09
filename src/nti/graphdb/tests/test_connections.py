#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_in
from hamcrest import has_length
from hamcrest import assert_that

import unittest

from nti.dataserver.users import User
from nti.dataserver.users import FriendsList

from nti.graphdb.relationships import FriendOf
from nti.graphdb.neo4j.database import Neo4jDB
from nti.graphdb.connections import zodb_friends
from nti.graphdb.connections import graph_friends
from nti.graphdb.connections import _Relationship
from nti.graphdb.connections import update_friendships

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.graphdb.tests import DEFAULT_URI
from nti.graphdb.tests import cannot_connect
from nti.graphdb.tests import random_username
from nti.graphdb.tests import GraphDBTestCase

@unittest.skipIf(cannot_connect(DEFAULT_URI), "Neo4j not available")
class TestFriendships(GraphDBTestCase):

	def setUp(self):
		super(TestFriendships, self).setUp()
		self.db = Neo4jDB(DEFAULT_URI)

	def _create_user(self, username='nt@nti.com', password='temp001'):
		usr = User.create_user(self.ds, username=username, password=password)
		return usr

	def _create_random_user(self):
		username = random_username()
		user = self._create_user(username)
		return user

	def _create_friendslist(self, owner, name="mycontacts", *friends):
		result = FriendsList(username=name)
		result.creator = owner
		for friend in friends:
			result.addFriend(friend)
		owner.addContainedObject(result)
		return result

	@WithMockDSTrans
	def test_entity_friends(self):
		owner = self._create_random_user()
		user1 = self._create_random_user()
		user2 = self._create_random_user()
		user3 = self._create_random_user()

		self._create_friendslist(owner, "mycontacts1", user1, user2)
		self._create_friendslist(owner, "mycontacts2", user3)

		result = zodb_friends(owner)
		assert_that(result, has_length(3))
		for friend in (user1, user2, user3):
			key = _Relationship(owner, friend)
			assert_that(key, is_in(result))

		result = zodb_friends(user3)
		assert_that(result, has_length(0))

	@WithMockDSTrans
	def test_graph_friends(self):
		user1 = self._create_random_user()
		user2 = self._create_random_user()
		user3 = self._create_random_user()
		self._create_friendslist(user1, "mycontacts1", user2, user3)

		# create in grapth
		self.db.create_relationship(user1, user2, FriendOf())
		self.db.create_relationship(user1, user3, FriendOf())

		result = graph_friends(self.db, user1)
		assert_that(result, has_length(2))

		user4 = self._create_random_user()
		self._create_friendslist(user1, "mycontacts2", user4)

		result = update_friendships(self.db, user1)
		assert_that(result, has_length(1))
