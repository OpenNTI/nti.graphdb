#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
graphdb discussion topics

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import gevent
import functools
import transaction

from zope import component
from zope.lifecycleevent import interfaces as lce_interfaces

from nti.appserver import interfaces as app_interfaces

from nti.dataserver import interfaces as nti_interfaces
from nti.dataserver.contenttypes.forums import interfaces as frm_interfaces

from nti.ntiids import ntiids

from . import utils
from . import relationships
from . import get_possible_site_names
from . import interfaces as graph_interfaces

# topics

def _add_authorship_relationship(db, topic):
	creator = topic.creator
	rel_type = relationships.Author()
	adapted = component.getMultiAdapter((creator, topic, rel_type), graph_interfaces.IPropertyAdapter)
	result = db.create_relationship(creator, topic, rel_type, properties=adapted.properties())
	logger.debug("authorship relationship %s created" % result)
	return result

def add_topic_node(db, key, value):
	result = None
	node = db.get_indexed_node(key, value)
	topic = ntiids.find_object_with_ntiid(value)
	if topic is not None and node is None:
		result = db.create_node(topic)
		logger.debug("topic node %s created" % result)
		_add_authorship_relationship(db, topic)
	return result, topic

def modify_topic_node(db, key, value):
	node, topic = add_topic_node(db, key, value)
	if topic is not None:
		labels = graph_interfaces.ILabelAdapter(topic).labels()
		properties = graph_interfaces.IPropertyAdapter(topic).properties()
		db.update_node(node, labels, properties)
		logger.debug("properties updated for node %s" % node)
	return node, topic

def delete_topic_node(db, key, value):
	node = db.get_indexed_node(key, value)
	if node is not None:
		db.delete_node(node)
		logger.debug("topic node %s deleted" % node)
		return True
	return False

def _process_topic_add_mod_event(key, value, event):
	site = get_possible_site_names()[0]
	def _process_event():
		transaction_runner = component.getUtility(nti_interfaces.IDataserverTransactionRunner)
		db = component.getUtility(graph_interfaces.IGraphDB, name=site)
		func = add_topic_node if event == graph_interfaces.ADD_EVENT else modify_topic_node
		func = functools.partial(func, db=db, key=key, value=value)
		transaction_runner(func)
	transaction.get().addAfterCommitHook(lambda success: success and gevent.spawn(_process_event))

@component.adapter(frm_interfaces.ITopic, lce_interfaces.IObjectAddedEvent)
def _topic_added(topic, event):
	adapted = graph_interfaces.IUniqueAttributeAdapter(topic)
	_process_topic_add_mod_event(adapted.key, adapted.value, graph_interfaces.ADD_EVENT)

@component.adapter(frm_interfaces.ITopic, lce_interfaces.IObjectModifiedEvent)
def _topic_modified(topic, event):
	adapted = graph_interfaces.IUniqueAttributeAdapter(topic)
	_process_topic_add_mod_event(adapted.key, adapted.value, graph_interfaces.MODIFY_EVENT)

def _process_topic_remove_event(key, value, comments=()):
	site = get_possible_site_names()[0]
	def _process_event():
		nodes = []
		nodes.append(utils.UniqueAttribute(key, value))
		for _key, _value in comments:
			nodes.append(utils.UniqueAttribute(_key, _value))
		db = component.getUtility(graph_interfaces.IGraphDB, name=site)
		db.delete_nodes(*nodes)
	transaction.get().addAfterCommitHook(lambda success: success and gevent.spawn(_process_event))
	
@component.adapter(frm_interfaces.ITopic, lce_interfaces.IObjectRemovedEvent)
def _topic_removed(topic, event):
	adapted = graph_interfaces.IUniqueAttributeAdapter(topic)
	comments = []
	for comment in topic.values():
		uaa = graph_interfaces.IUniqueAttributeAdapter(comment)
		comments.append((uaa.key, uaa.value))
	_process_topic_remove_event(adapted.key, adapted.value, comments)

# comments

def add_comment_relationship(db, key, value):
	result = None
	comment = ntiids.find_object_with_ntiid(value)
	if comment is not None:
		# comment are special case. we build a relationship between the comment-user and
		# the topic. We force key/value to identify the relationship
		# Note we don't create a comment node.
		author = comment.creator
		topic = comment.__parent__
		rel_type = relationships.CommentOn()
		adapted = component.getMultiAdapter((author, comment, rel_type), graph_interfaces.IPropertyAdapter)
		result = db.create_relationship(author, topic, rel_type, properties=adapted.properties(), key=key, value=value)
		logger.debug("comment-on relationship %s created" % result)
	return result

def delete_comment(db, key, value):
	node = db.get_indexed_node(key, value)# check for comment node
	if node is not None:
		db.delete_node(node)
		logger.debug("comment-on node %s deleted" % value)
	elif db.delete_indexed_relationship(key, value):
		logger.debug("comment-on relationship %s deleted" % value)
		return True
	return False

def _process_comment_event(key, value, event):
	site = get_possible_site_names()[0]
	def _process_event():
		func = None
		transaction_runner = component.getUtility(nti_interfaces.IDataserverTransactionRunner)
		db = component.getUtility(graph_interfaces.IGraphDB, name=site)
		if event == graph_interfaces.ADD_EVENT:
			func = functools.partial(add_comment_relationship, db=db, key=key, value=value)
		elif event == graph_interfaces.REMOVE_EVENT:
			func = functools.partial(delete_comment, db=db, key=key, value=value)
		if func:
			transaction_runner(func)
	transaction.get().addAfterCommitHook(lambda success: success and gevent.spawn(_process_event))

def _get_comment_rel_PK(comment):
	key, value = (None, None)
	if comment is not None:
		author = comment.creator
		rel_type = relationships.CommentOn()
		adapted = component.getMultiAdapter((author, comment, rel_type), graph_interfaces.IUniqueAttributeAdapter)
		key = adapted.key if adapted is not None else None
		value = adapted.value if adapted is not None else None
	return key, value

@component.adapter(frm_interfaces.IPersonalBlogComment, lce_interfaces.IObjectAddedEvent)
def _add_personal_blog_comment(comment, event):
	key, value = _get_comment_rel_PK(comment)
	_process_comment_event(key, value, graph_interfaces.ADD_EVENT)

@component.adapter(frm_interfaces.IGeneralForumComment, lce_interfaces.IObjectAddedEvent)
def _add_general_forum_comment(comment, event):
	key, value = _get_comment_rel_PK(comment)
	_process_comment_event(key, value, graph_interfaces.ADD_EVENT)

@component.adapter(frm_interfaces.IPersonalBlogComment, lce_interfaces.IObjectModifiedEvent)
def _modify_personal_blog_comment(comment, event):
	if app_interfaces.IDeletedObjectPlaceholder.providedBy(comment):
		key, value = _get_comment_rel_PK(comment)
		_process_comment_event(key, value, graph_interfaces.REMOVE_EVENT)

@component.adapter(frm_interfaces.IGeneralForumComment, lce_interfaces.IObjectModifiedEvent)
def _modify_general_forum_comment(comment, event):
	_modify_personal_blog_comment(comment, event)

# utils

def _build_graph_forum(db, forum):
	result = 0
	for topic in forum.values():
		adapted = graph_interfaces.IUniqueAttributeAdapter(topic)
		# add create/node
		add_topic_node(db, adapted.key, adapted.value)
		# add comments
		for comment in topic.values():
			key, value = _get_comment_rel_PK(comment)
			rel = db.get_indexed_relationship(key, value)
			if rel is None:
				add_comment_relationship(db, adapted.key, adapted.value)
				result += 1
	return result

def build_graph_community(db, community):
	result = 0
	board = frm_interfaces.IBoard(community, None) or {}
	for forum in board.values():
		result += _build_graph_forum(db, forum)
	return result
		
def build_graph_user(db, user):
	forum = frm_interfaces.IPersonalBlog(user, None) or {}
	return _build_graph_forum(db, forum)
