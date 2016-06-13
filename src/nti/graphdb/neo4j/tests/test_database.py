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

import uuid
import unittest

from nti.dataserver.users import User

from nti.graphdb.neo4j import database
from nti.graphdb.relationships import FriendOf

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.graphdb.tests import random_username
from nti.graphdb.tests import GraphDBTestCase

from nti.graphdb.neo4j.tests import cannot_connect

DEFAULT_URI = 'http://localhost:7474/db/data'

@unittest.skipIf(cannot_connect(DEFAULT_URI), "Neo4j not available")
class TestNeo4jDB(GraphDBTestCase):

	def setUp(self):
		super(TestNeo4jDB, self).setUp()
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

		nodes = self.db.get_indexed_nodes(("User", 'username', user.username),
										  ("User", 'username', user2.username))
		assert_that(nodes, has_length(2))

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
	def _test_relationship_funcs(self):
		user1 = random_username()
		user1 = self._create_user(user1)
		node1 = self.db.create_node(user1)

		user2 = random_username()
		user2 = self._create_user(user2)
		node2 = self.db.create_node(user2)
		# from IPython.core.debugger import Tracer; Tracer()()
		rel = self.db.create_relationship(user1, user2, "IS_FRIEND_OF")

		assert_that(rel, is_not(none()))
		assert_that(rel, has_property('id', is_not(none())))
		assert_that(rel, has_property('uri', is_not(none())))
		assert_that(rel, has_property('end', is_not(none())))
		assert_that(rel, has_property('start', is_not(none())))
		assert_that(rel, has_property('type', is_not(none())))

		res = self.db.get_relationship(rel.id)
		assert_that(res, is_not(none()))

		res = self.db.get_relationship(rel)
		assert_that(res, is_not(none()))

		res = self.db.match(start=user2, end=user1, rel_type=FriendOf())
		assert_that(res, has_length(0))

		res = self.db.match(start=user1, end=user2, rel_type=FriendOf())
		assert_that(res, has_length(1))

		rel_type = str(FriendOf())
		rels = self.db.match(start=node1, end=node2, rel_type=rel_type)
		assert_that(rels, has_length(1))

		res = self.db.match(start=user1, end=user2, rel_type="unknown")
		assert_that(res, has_length(0))

		self.db.delete_relationship(rels[0])

		res = self.db.get_relationship(rels[0])
		assert_that(res, is_(none()))

		rels = [ (node1, 'BROTHER_OF', node2, {}, True),
				 (node2, 'FAMILY_OF', node1, {'a':1}, False) ]
		res = self.db.create_relationships(*rels)
		assert_that(res, has_length(2))

		rel_type = 'BROTHER_OF'
		rels = self.db.match(start=node1, end=node2, rel_type=rel_type)
		assert_that(rels, has_length(1))

		splits = unicode(uuid.uuid4()).split('-')
		key, value = splits[-1], splits[0]
		params = ("x%s" % splits[-3], splits[-1])

		res = self.db.update_relationship(rels[0], {params[0]:params[1], 'a':2})
		assert_that(res, is_(True))

		res = self.db.index_relationship(rels[0], key, value)
		assert_that(res, is_(True))

		res = self.db.get_indexed_relationships(key, value)
		assert_that(res, has_length(1))

		self.db.unindex_relationship(key, value)

		res = self.db.get_indexed_relationships(key, value)
		assert_that(res, has_length(0))

		res = self.db.find_relationships(params[0], params[1], rel_type)
		assert_that(res, has_length(1))

		res = self.db.find_relationships(params[0], params[1])
		assert_that(res, has_length(1))
