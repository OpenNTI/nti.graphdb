#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import contains
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property
does_not = is_not

import unittest

from nti.dataserver.users import User

#from nti.graphdb import relationships
from nti.graphdb.neo4j import database

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.graphdb.tests import random_username
from nti.graphdb.tests import GraphDBTestCase

from nti.graphdb.neo4j.tests import cannot_connect

DEFAULT_URI = 'http://localhost:7474/db/data'

@unittest.skipIf(cannot_connect(DEFAULT_URI), "Neo4j not available")
class TestNeo4jDB(GraphDBTestCase):

	def setUp(self):
		super(GraphDBTestCase, self).setUp()
		self.db = database.Neo4jDB(DEFAULT_URI)

	def _create_user(self, username='nt@nti.com', password='temp001', **kwargs):
		user = User.create_user(self.ds, username=username, password=password, **kwargs)
		return user

	@WithMockDSTrans
	def test_node_funcs(self):
		username = random_username()
		user = self._create_user(username)
		node = self.db.create_node(user)
		assert_that(node, has_property('id', is_not(none())))
		assert_that(node, has_property('uri', is_not(none())))
		assert_that(node, has_property('properties',
									   has_entry('username', username)))

		res = self.db.get_node(node.id)
		assert_that(res, is_not(none()))

		res = self.db.get_node(user)
		assert_that(res, is_not(none()))

		username = random_username()
		user2 = self._create_user(username)
		res = self.db.get_node(user2)
		assert_that(res, is_(none()))
		
		res = self.db.create_nodes(user2)
		assert_that(res, is_not(none()))
		assert_that(res, has_length(1))

		res = self.db.get_nodes(user, user2)
		assert_that(res, is_not(none()))
		assert_that(res, has_length(2))
		assert_that(res, does_not(contains(None)))
		
		node = self.db.get_indexed_node("User", 'username', username)
		assert_that(node, is_not(none()))
		
		props = dict(node.properties)
		props['language'] = 'latin'
		res = self.db.update_node(node, properties=props)
		assert_that(res, is_(True))
		
		node = self.db.get_node(node)
		assert_that(node, has_property('properties',
 									   has_entry('language', 'latin')))

		res = self.db.delete_node(user)
		assert_that(res, is_(True))

		node = self.db.get_node(user)
		assert_that(node, is_(none()))

		res = self.db.delete_nodes(user2)
		assert_that(res, is_(1))

	@WithMockDSTrans
	def test_relationship_funcs(self):
		user1 = self._random_username()
		user1 = self._create_user(user1)
		self.db.create_node(user1)
		
		user2 = self._random_username()
		user2 = self._create_user(user2)
		self.db.create_node(user2)

		self.db.create_relationship(user1, user2, "friend")

# 		assert_that(rel, is_not(none()))
# 		assert_that(rel, has_property('id', is_not(none())))
# 		assert_that(rel, has_property('uri', is_not(none())))
# 		assert_that(rel, has_property('end', is_not(none())))
# 		assert_that(rel, has_property('start', is_not(none())))
# 		assert_that(rel, has_property('type', is_not(none())))
# 
# 		res = self.db.get_relationship(rel.id)
# 		assert_that(res, is_not(none()))
# 		assert_that(rel, has_property('id', is_not(none())))
# 		assert_that(rel, has_property('uri', is_not(none())))
# 		assert_that(rel, has_property('end', is_not(none())))
# 		assert_that(rel, has_property('start', is_not(none())))
# 
# 		res = self.db.get_relationship(rel)
# 		assert_that(res, is_not(none()))
# 
# 		res = self.db.match(start=user1, end=user2, rel_type=relationships.FriendOf())
# 		assert_that(res, has_length(1))
# 
# 		rel_type = str(relationships.FriendOf())
# 		res = self.db.match(start=node1, end=node2, rel_type=rel_type)
# 		assert_that(res, has_length(1))
# 
# 		res = self.db.match(start=user1, end=user2, rel_type="unknown")
# 		assert_that(res, has_length(0))
# 
# 		self.db.delete_relationships(rel)
# 		res = self.db.get_relationship(rel)
# 		assert_that(res, is_(none()))
# 
# 	@WithMockDSTrans
# 	def test_create_nodes(self):
# 		users = []
# 		for _ in range(4):
# 			user = self._random_username()
# 			users.append(self._create_user(user))
# 
# 		nodes = self.db.create_nodes(*users)
# 		assert_that(nodes, has_length(len(users)))
# 
# 		deleted = self.db.delete_nodes(*users)
# 		assert_that(deleted, is_(len(users)))
