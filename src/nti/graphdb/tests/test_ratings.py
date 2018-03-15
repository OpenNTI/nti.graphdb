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

from nti.dataserver.contenttypes.note import Note

from nti.dataserver.liking import like_object
from nti.dataserver.liking import unlike_object

from nti.dataserver.rating import rate_object
from nti.dataserver.rating import unrate_object

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.users.users import User

from nti.graphdb.tests import cannot_connect
from nti.graphdb.tests import random_username
from nti.graphdb.tests import GraphDBTestCase

from nti.ntiids.ntiids import make_ntiid


@unittest.skipIf(cannot_connect(), "Neo4j not available")
class TestRatings(GraphDBTestCase):

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
    def test_like(self):
        user = self.create_random_user()
        note = self.create_note(u'sample note', user)
        self.current_transaction.add(note)
        note = user.addContainedObject(note)
        try:
            newInteraction(IParticipation(user))
            like_object(note, user.username)
            unlike_object(note, user.username)
        finally:
            endInteraction()

    @mock_dataserver.WithMockDSTrans
    def test_rate(self):
        user = self.create_random_user()
        note = self.create_note(u'sample note', user)
        self.current_transaction.add(note)
        note = user.addContainedObject(note)
        try:
            newInteraction(IParticipation(user))
            rate_object(note, user.username, 1)
            unrate_object(note, user.username)
        finally:
            endInteraction()
