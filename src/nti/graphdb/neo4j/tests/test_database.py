#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
# from hamcrest import contains
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property
does_not = is_not

import sys
import uuid
import unittest

from zope import component

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.dataserver.users.users import User

from nti.graphdb.interfaces import IGraphDB
from nti.graphdb.interfaces import ILabelAdapter

from nti.graphdb.tests import GraphDBTestCase

from nti.graphdb.tests import cannot_connect
from nti.graphdb.tests import random_username


class FakeObject(object):

    def __conform__(self, iface):
        if iface == ILabelAdapter:
            return "Fake"

    def get(self, key):
        pass


@unittest.skipIf(cannot_connect(), "Neo4j not available")
class TestNeo4jDB(GraphDBTestCase):

    def create_user(self, username=u'nt@nti.com', password=u'temp001'):
        return User.create_user(username=username, password=password,
                                parent=FakeObject())  # pass parent to avoid added event

    def test_create_node(self):
        db = component.getUtility(IGraphDB)
        # node w/ primary key
        node = db.create_node(object(),
                              label="User",
                              key="username",
                              value=random_username(),
                              properties={"oid": str(uuid.uuid4())})
        assert_that(node, is_not(none()))
        assert_that(node, has_property('id', is_not(none())))
        # node w/o primary key
        node = db.create_node(object(),
                              label="User",
                              properties={"oid": str(uuid.uuid4())})
        assert_that(node, is_not(none()))

    @WithMockDSTrans
    def test_create_nodes(self):
        db = component.getUtility(IGraphDB)
        user = self.create_user(random_username())
        nodes = db.create_nodes(user, FakeObject())
        assert_that(nodes, has_length(2))

    @WithMockDSTrans
    def test_get_node_funcs(self):
        db = component.getUtility(IGraphDB)
        username = random_username()
        user = self.create_user(username)
        node = db.create_node(user)
        # test exists
        assert_that(db.get_node(user), is_not(none()))
        assert_that(db.get_node(node), is_not(none()))
        assert_that(db.get_node(node.id), is_not(none()))
        assert_that(db.get_node(node.neo), is_not(none()))
        # test does not exists
        assert_that(db.get_node(sys.maxint), is_(none()))
        # get or create
        assert_that(db.get_or_create_node(user), is_not(none()))
        # get nodes
        assert_that(db.get_nodes(user), has_length(1))
        # get index nodess
        assert_that(db.get_indexed_node("User", 'username', username),
                    is_not(none()))
        data = ('fake', 'key', 'value')
        assert_that(db.get_indexed_nodes(data),
                    is_([None]))

    @WithMockDSTrans
    def test_update_node(self):
        db = component.getUtility(IGraphDB)
        user = self.create_user(random_username())
        db.create_node(user)
        assert_that(db.update_node(user, {'foo': 'bar'}),
                    is_(True))
        node = db.get_node(user)
        assert_that(node,
                    has_property('properties', has_entry('foo', 'bar')))

    @WithMockDSTrans
    def test_delete_node(self):
        db = component.getUtility(IGraphDB)
        user = self.create_user(random_username())
        db.create_node(user)
        assert_that(db.delete_node(user), is_(True))

        user = self.create_user(random_username())
        db.create_node(user)
        assert_that(db.delete_nodes(user), is_(1))

        node = db.get_node(user)
        assert_that(node, is_(none()))

    @WithMockDSTrans
    def test_relationships(self):
        db = component.getUtility(IGraphDB)
        user_1 = self.create_user(random_username())
        user_2 = self.create_user(random_username())
        user_3 = self.create_user(random_username())
        # create unique relationship
        rel = db.create_relationship(user_1, user_2, "Friend", unique=True,
                                     properties={"foo": "bar"})
        assert_that(rel, is_not(none()))
        assert_that(rel, has_property('id', is_not(none())))
        assert_that(rel, has_property('end', is_not(none())))
        assert_that(rel, has_property('start', is_not(none())))
        assert_that(rel,
                    has_property('properties', has_entry('foo', 'bar')))
        # create normal relationship
        rel = db.create_relationship(user_1, user_2, "Visited", unique=False,
                                     properties={"foo": "bar"})
        assert_that(rel, is_not(none()))
        assert_that(rel, has_property('id', is_not(none())))
        assert_that(rel, has_property('neo', is_not(none())))
        # test get relationship
        assert_that(db.get_relationship(rel), is_not(none()))
        assert_that(db.get_relationship(rel.id), is_not(none()))
        assert_that(db.get_relationship(rel.neo), is_not(none()))
        # create multiple relastionships
        rels = [(user_1, 'BrotherOf', user_2, None, True),
                (user_1, 'FamilyOf', user_2, {'a': 1}, False)]
        res = db.create_relationships(*rels)
        assert_that(res, has_length(2))
        # match
        res = db.match(user_2, user_1, 'BrotherOf')
        assert_that(res, has_length(0))
        res = db.match(user_1, user_2, 'BrotherOf')
        assert_that(res, has_length(1))
        res = db.match(user_3, user_2, 'Friend')
        assert_that(res, has_length(0))
        # test match transitive
        db.create_relationship(user_2, user_3, "Friend", unique=True)
        res = db.match(user_1, user_3, 'Friend')
        assert_that(res, has_length(0))
#
#         res = self.db.match(start=user1, end=user2, rel_type=FriendOf())
#         assert_that(res, has_length(1))
#
#         rel_type = str(FriendOf())
#         rels = self.db.match(start=node1, end=node2, rel_type=rel_type)
#         assert_that(rels, has_length(1))
#
#         res = self.db.match(start=user1, end=user2, rel_type="unknown")
#         assert_that(res, has_length(0))
#
#         result = self.db.delete_relationship(rels[0])
#         assert_that(result, is_(True))
#
#         rels = self.db.match(start=node1, end=node2, rel_type=rel_type)
#         assert_that(rels, has_length(0))
#

#
#         rel_type = 'BROTHER_OF'
#         rels = self.db.match(start=node1, end=node2, rel_type=rel_type)
#         assert_that(rels, has_length(1))
#
#         splits = unicode(uuid.uuid4()).split('-')
#         key, value = splits[-1], splits[0]
#         params = ("x%s" % splits[-3], splits[-1])
#
#         res = self.db.update_relationship(rels[0], {params[0]:params[1], 'a':2})
#         assert_that(res, is_(True))
#
#         res = self.db.index_relationship(rels[0], key, value)
#         assert_that(res, is_(True))
#
#         res = self.db.get_indexed_relationships(key, value)
#         assert_that(res, has_length(1))
#
#         self.db.unindex_relationship(key, value)
#
#         res = self.db.get_indexed_relationships(key, value)
#         assert_that(res, has_length(0))
#
#         res = self.db.find_relationships(params[0], params[1], rel_type)
#         assert_that(res, has_length(1))
#
#         res = self.db.find_relationships(params[0], params[1])
#         assert_that(res, has_length(1))
