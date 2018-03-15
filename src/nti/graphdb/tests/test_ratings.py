#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ
 
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property
 
import unittest

from zope.security.interfaces import IParticipation

from zope.security.management import endInteraction
from zope.security.management import newInteraction

from nti.dataserver.contenttypes.note import Note
 
from nti.dataserver.liking import like_object
from nti.dataserver.liking import unlike_object

from nti.dataserver.users.users import User
 
from nti.dataserver.tests import mock_dataserver

from nti.graphdb.relationships import Like
from nti.graphdb.relationships import Rate

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
 
#     @WithMockDSTrans
#     def test_rate(self):
#         user = self.create_random_user()
#         note = self.create_note('sample note', user)
#         mock_dataserver.current_transaction.add(note)
#         note = user.addContainedObject(note)
#          
#         oid = get_oid(note)
#         m = _add_rate_relationship(self.db, user.username, oid, 10)
#         assert_that(m, is_not(none()))
#  
#         rels = self.db.match(user, note, Rate())
#         assert_that(rels, has_length(1))
#         assert_that(rels[0], has_property('properties', has_entry('rating', 10)))
#          
#         m = _add_rate_relationship(self.db, user.username, oid, 100)
#         assert_that(m, is_not(none()))
#         rels = self.db.match(user, note, Rate())
#         assert_that(rels[0], has_property('properties', has_entry('rating', 100)))
#          
#         _remove_rate_relationship(self.db, user.username, oid)
#          
#         rels = self.db.match(user, note, Rate())
#         assert_that(rels, has_length(0))
