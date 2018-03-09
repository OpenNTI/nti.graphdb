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

from nti.dataserver.contenttypes.note import Note

from nti.dataserver.users.users import User

from nti.dataserver.tests import mock_dataserver

from nti.graphdb import get_graph_db

from nti.graphdb.relationships import Created

from nti.graphdb.tests import cannot_connect
from nti.graphdb.tests import random_username

from nti.graphdb.tests import GraphDBTestCase

from nti.ntiids.ntiids import make_ntiid


@unittest.skipIf(cannot_connect(), "Neo4j not available")
class TestCreated(GraphDBTestCase):

    def _create_user(self, username=u'nt@nti.com', password=u'temp001'):
        usr = User.create_user(username=username, password=password)
        return usr

    def create_random_user(self):
        user = self._create_user(random_username())
        return user

    def create_note(self, msg, creator):
        note = Note()
        note.body = [msg]
        note.creator = creator
        note.containerId = make_ntiid(nttype=u'bleach', specific=u'manga')
        return note

    @property
    def transaction(self):
        return mock_dataserver.current_transaction

    @mock_dataserver.WithMockDSTrans
    def test_events(self):
        user = self.create_random_user()
        note = self.create_note(u'sample note', user)
        self.transaction.add(note)
        note = user.addContainedObject(note)
        # create and modified
        lifecycleevent.created(note)
        lifecycleevent.modified(note)
        db = get_graph_db()
        assert_that(db.match(user, note, Created()),
                    has_length(1))
        # remove
        user.deleteContainedObject(note.containerId, note.id)
