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

from nti.contentfragments.interfaces import IPlainTextContentFragment

from nti.dataserver.contenttypes.note import Note

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.users.users import User

from nti.graphdb import get_graph_db

from nti.graphdb.relationships import TaggedTo

from nti.graphdb.tests import cannot_connect
from nti.graphdb.tests import random_username
from nti.graphdb.tests import GraphDBTestCase

from nti.ntiids.ntiids import make_ntiid


@unittest.skipIf(cannot_connect(), "Neo4j not available")
class TestTagging(GraphDBTestCase):

    def _create_user(self, username=u'nt@nti.com', password=u'temp001'):
        usr = User.create_user(username=username, password=password)
        return usr

    def create_random_user(self):
        username = random_username()
        user = self._create_user(username)
        return user

    def create_note(self, msg, creator):
        note = Note()
        note.body = [msg]
        note.creator = creator
        note.containerId = make_ntiid(nttype=u'bleach', specific=u'manga')
        return note

    @property
    def current_transaction(self):
        return mock_dataserver.current_transaction

    @mock_dataserver.WithMockDSTrans
    def test_tagging(self):
        user_1 = self.create_random_user()
        user_2 = self.create_random_user()
        user_3 = self.create_random_user()
        note = self.create_note(u'sample note', user_1)
        note.tags = [
            IPlainTextContentFragment(user_2.NTIID),
            IPlainTextContentFragment(user_3.NTIID)
        ]
        self.current_transaction.add(note)
        note = user_1.addContainedObject(note)
        note.tags = [
            IPlainTextContentFragment(user_3.NTIID)
        ]
        lifecycleevent.modified(note)

        db = get_graph_db()
        rels = db.match(note, user_3, TaggedTo())
        assert_that(rels, has_length(1))
