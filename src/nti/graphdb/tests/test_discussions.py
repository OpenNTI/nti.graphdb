#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property

import time
import unittest

from zope import lifecycleevent

from nti.dataserver.contenttypes.forums.interfaces import IPersonalBlog

from nti.dataserver.contenttypes.forums.post import PersonalBlogComment

from nti.dataserver.contenttypes.forums.topic import PersonalBlogEntry

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
        
#         oid = get_oid(entry)
#         pk = get_node_pk(entry)
# 
#         node, topic = _add_topic_node(self.db, oid, pk.label, pk.key, pk.value)
#         assert_that(node, is_not(none()))
#         assert_that(topic, is_(entry))
# 
#         node = self.db.get_indexed_node(pk.label, pk.key, pk.value)
#         assert_that(node, is_not(none()))
# 
#         rels = self.db.match(user, topic, Author())
#         assert_that(rels, has_length(1))
# 
#         _update_topic_node(self.db, oid, pk.label, pk.key, pk.value)
# 
#         node = self.db.get_indexed_node(pk.label, pk.key, pk.value)
#         assert_that(node, has_property(
#             'properties', has_entry('type', 'Topic')))
#         assert_that(node, has_property(
#             'properties', has_entry('ntiid', is_not(none()))))
#         assert_that(node, has_property(
#             'properties', has_entry('creator', user.username)))
# 
#         _add_membership_relationship(self.db, entry, blog)
#         rels = self.db.match(entry, blog, MemberOf())
#         assert_that(rels, has_length(1))
# 
#         res = _delete_node(self.db, pk.label, pk.key, pk.value)
#         assert_that(res, is_(True))
# 
#         res = _delete_node(self.db, pk.label, pk.key, pk.value)
#         assert_that(res, is_(False))

#     @WithMockDSTrans
#     def test_user_blog_comment(self):
#         user = self.create_random_user()
#         blog = IPersonalBlog(user)
#         entry = PersonalBlogEntry()
#         entry.creator = user
#         blog['bleach'] = entry
#         entry.__parent__ = blog
#         entry.createdTime = entry.lastModified = 42
#         mock_dataserver.current_transaction.add(entry)
# 
#         comment = PersonalBlogComment()
#         comment.creator = user
#         entry['comment316072059'] = comment
#         comment.__parent__ = entry
#         comment.createdTime = comment.lastModified = 43
#         mock_dataserver.current_transaction.add(comment)
# 
#         oid = get_oid(comment)
#         res = _add_comment_relationship(self.db, oid)
#         assert_that(res, is_not(none()))
#         assert_that(res, has_property(
#             'properties', has_entry('oid', is_not(none()))))
# 
#         res = _get_comment_relationship(self.db, comment)
#         assert_that(res, is_not(none()))
#         assert_that(res, has_property(
#             'properties', has_entry('oid', is_not(none()))))
# 
#         pk = get_node_pk(comment)
#         res = _delete_comment(self.db, oid, pk.label, pk.key, pk.value)
#         assert_that(res, is_(True))
# 
#         rels = self.db.match(entry, blog, CommentOn())
#         assert_that(rels, has_length(0))
