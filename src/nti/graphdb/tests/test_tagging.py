# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
# 
# from __future__ import print_function, unicode_literals, absolute_import, division
# __docformat__ = "restructuredtext en"
# 
# # disable: accessing protected members, too many methods
# # pylint: disable=W0212,R0904
# 
# from hamcrest import is_
# from hamcrest import has_length
# from hamcrest import assert_that
# 
# import fudge
# import unittest
# 
# from nti.contentfragments.interfaces import IPlainTextContentFragment
# 
# from nti.dataserver.users import User
# from nti.dataserver.contenttypes import Note
# 
# from nti.graphdb.relationships import TaggedTo
# 
# from nti.graphdb.neo4j.database import Neo4jDB
# 
# from nti.graphdb.common import get_oid
# from nti.graphdb.tagging import _get_username_tags
# from nti.graphdb.tagging import _process_modify_rels
# from nti.graphdb.tagging import _create_is_tagged_to_rels
# from nti.graphdb.tagging import _delete_is_tagged_to_rels
# 
# from nti.ntiids.ntiids import make_ntiid
# 
# import nti.dataserver.tests.mock_dataserver as mock_dataserver
# from nti.dataserver.tests.mock_dataserver import WithMockDSTrans
# 
# from nti.graphdb.tests import DEFAULT_URI
# from nti.graphdb.tests import cannot_connect
# from nti.graphdb.tests import random_username
# from nti.graphdb.tests import GraphDBTestCase
# 
# @unittest.skipIf(cannot_connect(DEFAULT_URI), "Neo4j not available")
# class TestSharing(GraphDBTestCase):
# 
# 	def setUp(self):
# 		super(TestSharing, self).setUp()
# 		self.db = Neo4jDB(DEFAULT_URI)
# 
# 	def _create_user(self, username='nt@nti.com', password='temp001'):
# 		usr = User.create_user(self.ds, username=username, password=password)
# 		return usr
# 
# 	def _create_random_user(self):
# 		username = random_username()
# 		user = self._create_user(username)
# 		return user
# 
# 	def _create_note(self, msg, creator, containerId=None):
# 		note = Note()
# 		note.body = [unicode(msg)]
# 		note.creator = creator
# 		note.containerId = containerId or make_ntiid(nttype='bleach', specific='manga')
# 		return note
# 
# 	@fudge.patch('nti.graphdb.tagging.get_graph_db')
# 	@WithMockDSTrans
# 	def test_tagging(self, mock_ggdb):
# 		mock_ggdb.is_callable().with_args().returns(None)
# 
# 		user_1 = self._create_random_user()
# 		user_2 = self._create_random_user()
# 		user_3 = self._create_random_user()
# 		note = self._create_note('sample note', user_1)
# 		note.tags = [IPlainTextContentFragment(user_2.NTIID),
# 					 IPlainTextContentFragment(user_3.NTIID)]
# 		mock_dataserver.current_transaction.add(note)
# 		note = user_1.addContainedObject(note)
# 
# 		oid = get_oid(note)
# 		username_tags = _get_username_tags(note)
# 		m = _create_is_tagged_to_rels(self.db, oid, username_tags)
# 		assert_that(m, has_length(2))
# 
# 		rels = self.db.match(note, TaggedTo(), loose=True)
# 		assert_that(rels, has_length(2))
# 
# 		note.tags = [IPlainTextContentFragment(user_2.NTIID)]
# 		_process_modify_rels(self.db, oid)
# 		
# 		rels = self.db.match(note, TaggedTo(), loose=True)
# 		assert_that(rels, has_length(1))
# 		
# 		res = _delete_is_tagged_to_rels(self.db, oid)
# 		assert_that(res, is_(True))
# 		
# 		rels = self.db.match(note, TaggedTo(), loose=True)
# 		assert_that(rels, has_length(0))
