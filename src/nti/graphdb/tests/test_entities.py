#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import assert_that

import unittest

from zope import component

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.users.friends_lists import DynamicFriendsList

from nti.dataserver.users.users import User

from nti.graphdb.interfaces import IGraphDB

from nti.graphdb.tests import cannot_connect
from nti.graphdb.tests import random_username

from nti.graphdb.tests import GraphDBTestCase


@unittest.skipIf(cannot_connect(), "Neo4j not available")
class TestEntities(GraphDBTestCase):

    @property
    def current_transaction(self):
        return mock_dataserver.current_transaction

    def create_user(self, username=u'nt@nti.com', password=u'temp001', **kwargs):
        usr = User.create_user(username=username, password=password, **kwargs)
        return usr

    @mock_dataserver.WithMockDSTrans
    def test_entities(self):
        # add user
        username = random_username()
        db = component.getUtility(IGraphDB)
        user = self.create_user(username)
        assert_that(db.get_node(user), is_not(none()))
        # add dfl
        dfl = DynamicFriendsList(username=random_username())
        dfl.creator = user
        user.addContainedObject(dfl)
        assert_that(db.get_node(dfl), is_not(none()))
        # delete
        user.deleteContainedObject(dfl.containerId, dfl.id)
        assert_that(db.get_node(dfl), is_(none()))