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

import fudge

from zope import interface

from zope.security.interfaces import IPrincipal

from nti.dataserver.contenttypes.note import Note

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.dataserver.users.users import User

from nti.graphdb.common import get_ntiid
from nti.graphdb.common import get_entity
from nti.graphdb.common import get_creator
from nti.graphdb.common import get_createdTime
from nti.graphdb.common import to_external_oid
from nti.graphdb.common import get_current_user
from nti.graphdb.common import get_lastModified
from nti.graphdb.common import get_principal_id
from nti.graphdb.common import get_node_primary_key
from nti.graphdb.common import get_current_principal_id

from nti.graphdb.tests import GraphDBTestCase


class TestCommon(GraphDBTestCase):

    @property
    def current_transaction(self):
        return mock_dataserver.current_transaction

    def create_user(self, username=u'nt@nti.com', password=u'temp001', **kwargs):
        usr = User.create_user(username=username, password=password, **kwargs)
        return usr

    def create_note(self, creator, text=u'note', containerId=u'foo'):
        note = Note()
        note.body = [text]
        note.creator = creator
        note.containerId = containerId
        self.current_transaction.add(note)
        return note

    @WithMockDSTrans
    def test_get_entity(self):
        user = self.create_user()
        assert_that(get_entity(user), is_(user))
        assert_that(get_entity('nt@nti.com'), is_(user))

    def test_get_current_principal_id(self):
        assert_that(get_current_principal_id(), is_(none()))

    @WithMockDSTrans
    @fudge.patch("nti.graphdb.common.get_current_principal_id")
    def test_get_user(self, mock_gpid):
        user = self.create_user()
        assert_that(get_current_user(user), is_(user))
        mock_gpid.is_callable().returns(user)
        assert_that(get_current_user(), is_(user))

    @WithMockDSTrans
    def test_get_principal_id(self):
        user = self.create_user()
        assert_that(get_principal_id(user), is_('nt@nti.com'))
        assert_that(get_principal_id('nt@nti.com'), is_('nt@nti.com'))

        @interface.implementer(IPrincipal)
        class Fake(object):
            id = 'fake'
        assert_that(get_principal_id(Fake()), is_('fake'))

    @WithMockDSTrans
    def test_get_creator(self):
        user = self.create_user()
        note = self.create_note(user)
        assert_that(get_creator(note), is_(user))

    @WithMockDSTrans
    def test_times_and_oid(self):
        user = self.create_user()
        note = self.create_note(user)
        assert_that(get_createdTime(note), is_not(none()))
        assert_that(get_lastModified(note), is_not(none()))
        assert_that(to_external_oid(note), is_not(none()))

    def test_get_ntiid(self):
        fake = fudge.Fake().has_attr(ntiid='ntiid')
        assert_that(get_ntiid(fake), is_('ntiid'))

    @WithMockDSTrans
    def test_get_node_pk(self):
        assert_that(get_node_primary_key(object()), is_(none()))
        assert_that(get_node_primary_key(self.create_user()), 
                    is_not(none()))
