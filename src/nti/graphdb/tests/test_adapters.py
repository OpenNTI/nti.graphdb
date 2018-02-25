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
# from hamcrest import none
# from hamcrest import is_not
# from hamcrest import has_entry
# from hamcrest import has_length
# from hamcrest import has_entries
# from hamcrest import assert_that
# from hamcrest import has_property
# 
# from numbers import Number
# 
# from zope import component
# 
# from nti.contentfragments.interfaces import IPlainTextContentFragment
# 
# from nti.dataserver.users import User
# from nti.dataserver.users import Community
# from nti.dataserver.contenttypes import Note
# from nti.dataserver.contenttypes.forums.topic import PersonalBlogEntry
# from nti.dataserver.contenttypes.forums.post import PersonalBlogComment
# from nti.dataserver.contenttypes.forums.interfaces import IPersonalBlog
# 
# from nti.graphdb.relationships import Reply
# 
# from nti.graphdb.interfaces import ILabelAdapter
# from nti.graphdb.interfaces import IPropertyAdapter
# from nti.graphdb.interfaces import IUniqueAttributeAdapter
# 
# import nti.dataserver.tests.mock_dataserver as mock_dataserver
# from nti.dataserver.tests.mock_dataserver import WithMockDSTrans
# 
# from nti.graphdb.tests import GraphDBTestCase
# 
# class TestAdapters(GraphDBTestCase):
# 
# 	def _create_user(self, username='nt@nti.com', password='temp001', **kwargs):
# 		usr = User.create_user(self.ds, username=username, password=password, **kwargs)
# 		return usr
# 
# 	@WithMockDSTrans
# 	def test_entity_adapter(self):
# 		user = self._create_user("owner@bar",
# 						 		 external_value={u'alias':u"owner", u'realname':'na marsh'})
# 
# 		label = ILabelAdapter(user, None)
# 		assert_that(label, is_('User'))
# 
# 		props = IPropertyAdapter(user, None)
# 		assert_that(props, has_entries(	'type', 'User',
# 										'alias', 'owner',
# 										'name', 'na marsh',
# 										'username', 'owner@bar',
# 										'oid', is_not(none()),
# 										'intid', is_(int),
# 										'createdTime', is_(Number) ) )
# 
# 	@WithMockDSTrans
# 	def test_community_adapter(self):
# 		comm = Community.create_community(
# 							username='cs',
# 							external_value={u'alias':u"ComSci", u'realname':'OUCS'})
# 
# 		label = ILabelAdapter(comm, None)
# 		assert_that(label, is_('Community'))
# 
# 		props = IPropertyAdapter(comm, None)
# 		assert_that(props, has_entries(	'type', 'Community',
# 										'alias', 'ComSci',
# 										'name', 'OUCS',
# 										'username', 'cs',
# 										'oid', is_not(none()),
# 										'intid', is_(int),
# 										'createdTime', is_(Number) ) )
# 
# 	@WithMockDSTrans
# 	def test_generic_adapter(self):
# 		obj = object()
# 		label = ILabelAdapter(obj, None)
# 		assert_that(label, is_not(none()))
# 
# 		props = IPropertyAdapter(obj, None)
# 		assert_that(props, is_not(none()))
# 		assert_that(props, has_length(2))
# 		assert_that(props, has_entry('createdTime', is_(Number)))
# 
# 	@WithMockDSTrans
# 	def test_unique_entity_attr_adapter(self):
# 		user = self._create_user(
# 						"owner@bar",
# 						external_value={u'alias':u"owner", u'realname':'na marsh'})
# 		adapted = IUniqueAttributeAdapter(user, None)
# 		assert_that(adapted, is_not(none()))
# 		assert_that(adapted, has_property('key', 'username'))
# 		assert_that(adapted, has_property('value', 'owner@bar'))
# 		
# 		obj = object()
# 		adapted = IUniqueAttributeAdapter(obj, None)
# 		assert_that(adapted, is_not(none()))
# 		assert_that(adapted, has_property('key', is_(none())))
# 		assert_that(adapted, has_property('value', is_(none())))
# 
# 	@WithMockDSTrans
# 	def test_user_blog(self):
# 		user = self._create_user("user1@bar")
# 		blog = IPersonalBlog(user)
# 		entry = PersonalBlogEntry()
# 		entry.creator = user
# 		entry.tags = (IPlainTextContentFragment('bankai'), IPlainTextContentFragment('shikai'))
# 		blog['bleach'] = entry
# 		entry.__parent__ = blog
# 		entry.lastModified = 42.0
# 		entry.createdTime = 24.0
# 
# 		comment = PersonalBlogComment()
# 		comment.creator = user
# 		entry['comment316072059'] = comment
# 		comment.__parent__ = entry
# 		comment.createdTime = comment.lastModified = 43.0
# 		mock_dataserver.current_transaction.add(comment)
# 
# 		label = ILabelAdapter(entry, None)
# 		assert_that(label, is_('Topic'))
# 
# 		props = IPropertyAdapter(entry, None)
# 		assert_that(props, has_entries(	'ntiid', is_not(none()),
# 										'oid', is_not(none()),
# 										'intid', is_(int),
# 										'title', is_(u''),
# 										'type', is_(u'Topic'),
# 										'forum', is_not(none()),
# 										'createdTime', is_(Number) ) )
# 
# 		label = ILabelAdapter(comment, None)
# 		assert_that(label, is_('Comment'))
# 
# 		props = IPropertyAdapter(comment, None)
# 		assert_that(props, has_entries(	'intid', is_(int),
# 										'creator', is_(u'user1@bar'),
# 										'oid', is_not(none()),
# 										'type', is_(u'Comment'),
# 										'topic', is_not(none()),
# 										'createdTime', is_(Number) ) )
# 
# 	@WithMockDSTrans
# 	def test_property(self):
# 		user = self._create_user("user1@bar")
# 		note = Note()
# 		note.body = [unicode('test')]
# 		note.creator = user
# 		note.containerId = 'foo'
# 		mock_dataserver.current_transaction.add(note)
# 		note = user.addContainedObject(note)
# 		properties = component.queryMultiAdapter((user, note, Reply()),
# 												 IPropertyAdapter)
# 		assert_that(properties, is_not(none()))
# 		assert_that(properties, has_entries('intid', is_(int),
# 											'creator', is_(u'user1@bar')))
