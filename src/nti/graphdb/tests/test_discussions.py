#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property

import unittest

from nti.dataserver.users import User

from nti.dataserver.contenttypes.forums.topic import PersonalBlogEntry
from nti.dataserver.contenttypes.forums.post import PersonalBlogComment
from nti.dataserver.contenttypes.forums.interfaces import IPersonalBlog

from nti.graphdb.neo4j.database import Neo4jDB

from nti.graphdb.common import get_oid
from nti.graphdb.common import get_node_pk
from nti.graphdb.discussions import _delete_node
from nti.graphdb.discussions import _add_topic_node
from nti.graphdb.discussions import _update_topic_node
from nti.graphdb.discussions import _add_membership_relationship

from nti.graphdb.relationships import Author
from nti.graphdb.relationships import MemberOf
from nti.graphdb.relationships import CommentOn

import nti.dataserver.tests.mock_dataserver as mock_dataserver
from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.graphdb.tests import DEFAULT_URI
from nti.graphdb.tests import cannot_connect
from nti.graphdb.tests import random_username
from nti.graphdb.tests import GraphDBTestCase

@unittest.skipIf(cannot_connect(DEFAULT_URI), "Neo4j not available")
class TestDiscussions(GraphDBTestCase):

	def setUp(self):
		super(TestDiscussions, self).setUp()
		self.db = Neo4jDB(DEFAULT_URI)

	def _create_user(self, username='nt@nti.com', password='temp001'):
		usr = User.create_user(self.ds, username=username, password=password)
		return usr

	def _create_random_user(self):
		username = random_username()
		user = self._create_user(username)
		return user

	@WithMockDSTrans
	def xtest_user_blog_node(self):
		user = self._create_random_user()
		blog = IPersonalBlog(user)
		entry = PersonalBlogEntry()
		entry.creator = user
		blog['bleach'] = entry
		entry.__parent__ = blog
		entry.lastModified = 42
		entry.createdTime = 24

		oid = get_oid(entry)
		pk = get_node_pk(entry)

		node, topic = _add_topic_node(self.db, oid, pk.label, pk.key, pk.value)
		assert_that(node, is_not(none()))
		assert_that(topic, is_(entry))

		node = self.db.get_indexed_node(pk.label, pk.key, pk.value)
		assert_that(node, is_not(none()))
		
		rels = self.db.match(user, topic, Author())
		assert_that(rels, has_length(1))
		
		_update_topic_node(self.db, oid, pk.label, pk.key, pk.value)
		
		node = self.db.get_indexed_node(pk.label, pk.key, pk.value)
		assert_that(node, has_property('properties', has_entry('type', 'Topic')))
		assert_that(node, has_property('properties', has_entry('ntiid', is_not(none()))))
		assert_that(node, has_property('properties', has_entry('creator', user.username)))

		_add_membership_relationship(self.db, entry, blog)
		rels = self.db.match(entry, blog, MemberOf())
		assert_that(rels, has_length(1))
		
		res = _delete_node(self.db, pk.label, pk.key, pk.value)
		assert_that(res, is_(True))

		res = _delete_node(self.db, pk.label, pk.key, pk.value)
		assert_that(res, is_(False))

	@WithMockDSTrans
	def test_user_blog_comment(self):
		from IPython.core.debugger import Tracer; Tracer()()
		user = self._create_random_user()
		blog = IPersonalBlog(user)
		entry = PersonalBlogEntry()
		entry.creator = user
		blog['bleach'] = entry
		entry.__parent__ = blog
		entry.createdTime = entry.lastModified = 42
		mock_dataserver.current_transaction.add(entry)

		comment = PersonalBlogComment()
		comment.creator = user
		entry['comment316072059'] = comment
		comment.__parent__ = entry
		comment.createdTime = comment.lastModified = 43
		mock_dataserver.current_transaction.add(comment)

# 		oid = get_oid(comment)
# 		comment_rel_pk = discussions.get_comment_relationship_PK(comment)
# 				
# 		rel = discussions._add_comment_relationship(self.db, oid, comment_rel_pk)
# 		assert_that(rel, is_not(none()))
# 		assert_that(rel, has_property('properties', has_entry('created', 43)))
# 
# 		node = self.db.get_indexed_node("username", user.username)
# 		assert_that(node, is_not(none()))
# 
# 		pk = get_node_pk(entry)
# 		node = self.db.get_indexed_node(pk.label, pk.key, pk.value)
# 		assert_that(node, is_not(none()))
# 
# 		rels = self.db.match(start=user, rel_type=CommentOn())
# 		assert_that(rels, has_length(1))
