#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import has_length
from hamcrest import assert_that

import unittest

from zope import lifecycleevent

from nti.dataserver.users.friends_lists import FriendsList
from nti.dataserver.users.friends_lists import DynamicFriendsList

from nti.dataserver.users.users import User

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.graphdb import get_graph_db

from nti.graphdb.connections import init
from nti.graphdb.connections import graph_friends

from nti.graphdb.tests import cannot_connect
from nti.graphdb.tests import random_username
from nti.graphdb.tests import GraphDBTestCase


@unittest.skipIf(cannot_connect(), "Neo4j not available")
class TestFriendships(GraphDBTestCase):

    def _create_user(self, username=u'nt@nti.com', password=u'temp001'):
        usr = User.create_user(username=username, password=password)
        return usr

    def create_random_user(self):
        username = random_username()
        user = self._create_user(username)
        return user

    def create_friendslist(self, owner, name, *friends):
        result = FriendsList(username=name)
        result.creator = owner
        for friend in friends:
            result.addFriend(friend)
        owner.addContainedObject(result)
        return result

    @WithMockDSTrans
    def test_entity_friends(self):
        owner = self.create_random_user()
        user1 = self.create_random_user()
        user2 = self.create_random_user()
        user3 = self.create_random_user()

        # create friends
        friendList = self.create_friendslist(owner, u"myUserFriends",
                                             user1, user2, user3)
        friends = graph_friends(get_graph_db(), owner)
        assert_that(friends, has_length(3))

        # remove friend
        friendList.removeFriend(user2)
        lifecycleevent.modified(friendList)
        friends = graph_friends(get_graph_db(), owner)
        assert_that(friends, has_length(2))

        # remove friend list
        owner.deleteContainedObject(friendList.containerId, friendList.id)

    @WithMockDSTrans
    def test_memberships(self):
        user1 = self.create_random_user()
        user2 = self.create_random_user()
        user3 = self.create_random_user()

        dfl = DynamicFriendsList(username=u'myFriendsDFL')
        dfl.creator = user1  # Creator must be set
        user1.addContainedObject(dfl)

        # start memberships
        dfl.addFriend(user2)
        dfl.addFriend(user3)

        # remove membership
        dfl.removeFriend(user3)
        lifecycleevent.modified(dfl)

        # delete dfl
        user1.deleteContainedObject(dfl.containerId, dfl.id)

    @WithMockDSTrans
    def test_following(self):
        user1 = self.create_random_user()
        user2 = self.create_random_user()
        user3 = self.create_random_user()

        user1.follow(user2)
        user1.follow(user3)
        user1.stop_following(user2)

    @WithMockDSTrans
    def test_init(self):
        user1 = self.create_random_user()
        init(get_graph_db(), user1)
