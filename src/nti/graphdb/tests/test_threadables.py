#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import has_length
from hamcrest import assert_that

import unittest

from zope import interface
from zope import lifecycleevent

from nti.dataserver.contenttypes.note import Note

from nti.dataserver.interfaces import IDeletedObjectPlaceholder

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.users.users import User

from nti.graphdb import get_graph_db

from nti.graphdb.relationships import IsReplyOf

from nti.graphdb.tests import cannot_connect
from nti.graphdb.tests import random_username
from nti.graphdb.tests import GraphDBTestCase

from nti.ntiids.ntiids import make_ntiid


@unittest.skipIf(cannot_connect(), "Neo4j not available")
class TestThreadables(GraphDBTestCase):

    def _create_user(self, username='nt@nti.com', password='temp001'):
        usr = User.create_user(username=username, password=password)
        return usr

    def create_random_user(self):
        username = random_username()
        user = self._create_user(username)
        return user

    def create_note(self, msg, creator, inReplyTo=None):
        note = Note()
        note.body = [msg]
        note.creator = creator
        note.containerId = make_ntiid(nttype=u'bleach', specific=u'manga')
        note.inReplyTo = inReplyTo
        return note

    @property
    def current_transaction(self):
        return mock_dataserver.current_transaction

    @mock_dataserver.WithMockDSTrans
    def test_threadables(self):
        user_1 = self.create_random_user()
        parent_note = self.create_note(u'parent note', user_1)
        self.current_transaction.add(parent_note)
        parent_note = user_1.addContainedObject(parent_note)

        user_2 = self.create_random_user()
        child_note = self.create_note(u'child note', user_2, parent_note)
        self.current_transaction.add(parent_note)
        child_note = user_2.addContainedObject(child_note)

        db = get_graph_db()
        rels = db.match(child_note, parent_note, IsReplyOf())
        assert_that(rels, has_length(1))

        # modify
        lifecycleevent.modified(child_note)
        rels = db.match(child_note, parent_note, IsReplyOf())
        assert_that(rels, has_length(1))

        # delete place holder
        interface.alsoProvides(child_note, IDeletedObjectPlaceholder)
        lifecycleevent.modified(child_note)
        rels = db.match(child_note, parent_note, IsReplyOf())
        assert_that(rels, has_length(0))

        # remove
        user_1.deleteContainedObject(parent_note.containerId, parent_note.id)
