#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

import unittest

from zope.security.interfaces import IParticipation

from zope.security.management import endInteraction
from zope.security.management import newInteraction

from nti.dataserver.flagging import flag_object
from nti.dataserver.flagging import unflag_object

from nti.dataserver.contenttypes.note import Note

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.users.users import User

from nti.graphdb import get_graph_db

from nti.graphdb.flagging import init

from nti.graphdb.tests import cannot_connect
from nti.graphdb.tests import random_username
from nti.graphdb.tests import GraphDBTestCase

from nti.ntiids.ntiids import make_ntiid


@unittest.skipIf(cannot_connect(), "Neo4j not available")
class TestFlagging(GraphDBTestCase):

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
    def test_flagging(self):
        user = self.create_random_user()
        note = self.create_note(u'sample note', user)
        self.current_transaction.add(note)
        note = user.addContainedObject(note)

        flagger = self.create_random_user()
        try:
            newInteraction(IParticipation(flagger))
            flag_object(note)
            unflag_object(note)
        finally:
            endInteraction()
            
    @mock_dataserver.WithMockDSTrans
    def test_init(self):
        user = self.create_random_user()
        note = self.create_note(u'sample note', user)
        self.current_transaction.add(note)
        note = user.addContainedObject(note)
        flag_object(note)
        init(get_graph_db(), note)
