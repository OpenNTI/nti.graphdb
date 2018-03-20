#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import has_length
from hamcrest import assert_that

import time
import unittest

from zope import interface
from zope import lifecycleevent

from nti.dataserver.contenttypes.forums.interfaces import IForum
from nti.dataserver.contenttypes.forums.interfaces import IPersonalBlog

from nti.dataserver.contenttypes.forums.post import PersonalBlogComment

from nti.dataserver.contenttypes.forums.topic import PersonalBlogEntry
from nti.dataserver.contenttypes.forums.topic import CommunityHeadlineTopic

from nti.dataserver.interfaces import IDeletedObjectPlaceholder

from nti.dataserver.users.communities import Community

from nti.dataserver.users.users import User

from nti.graphdb.relationships import MemberOf
from nti.graphdb.relationships import CommentOn

from nti.dataserver.tests import mock_dataserver

from nti.graphdb import get_graph_db

from nti.graphdb.tests import cannot_connect
from nti.graphdb.tests import random_username
from nti.graphdb.tests import GraphDBTestCase


@unittest.skipIf(cannot_connect(), "Neo4j not available")
class TestDiscussions(GraphDBTestCase):

    def _create_user(self, username=u'nt@nti.com', password=u'temp001'):
        usr = User.create_user(username=username, password=password)
        return usr

    def create_random_user(self):
        username = random_username()
        user = self._create_user(username)
        return user

    @mock_dataserver.WithMockDSTrans
    def test_user_blog(self):
        user = self.create_random_user()
        blog = IPersonalBlog(user)
        entry = PersonalBlogEntry()
        entry.creator = user
        blog['bleach'] = entry

        db = get_graph_db()
        rels = db.match(entry, blog, MemberOf())
        assert_that(rels, has_length(1))

        entry.lastModified = time.time()
        lifecycleevent.modified(entry)

        comment = PersonalBlogComment()
        comment.creator = user
        entry['comment316072059'] = comment

        rels = db.match(user, entry, CommentOn())
        assert_that(rels, has_length(1))

        interface.alsoProvides(comment, IDeletedObjectPlaceholder)
        lifecycleevent.modified(comment)

        # delete entry
        del blog[entry.__name__]

    @mock_dataserver.WithMockDSTrans
    def test_community(self):
        username = random_username()
        comm = Community.create_community(username=username)
        forum = IForum(comm)
        topic = CommunityHeadlineTopic()
        forum['bleach'] = topic
        Community.delete_entity(username)
