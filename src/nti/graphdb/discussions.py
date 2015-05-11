#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from six import string_types

from zope import component

from zope.intid.interfaces import IIntIdRemovedEvent

from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent

from nti.dataserver.contenttypes.forums.interfaces import ITopic

from nti.ntiids.ntiids import find_object_with_ntiid

from .common import get_oid
from .common import get_creator
from .common import get_node_pk

from .relationships import Author
from .relationships import MemberOf

from .interfaces import ADD_EVENT
from .interfaces import MODIFY_EVENT
from .interfaces import IPropertyAdapter

from . import create_job
from . import get_graph_db
from . import get_job_queue

## utils

def _add_node(db, oid, label, key, value):
	created = False
	obj = find_object_with_ntiid(oid)
	node = db.get_indexed_node(label, key, value)
	if obj is not None and node is None:
		node = db.create_node(obj)
		created = True
		logger.debug("Node %s created", node)
	return node, obj, created

def _update_node(db, node, obj):
	properties = IPropertyAdapter(obj)
	db.update_node(node, properties)
	logger.debug("Properties updated for node %s", node)
	return node, obj

def _delete_node(db, label, key, value):
	node = db.get_indexed_node(label, key, value)
	if node is not None:
		db.delete_node(node)
		logger.debug("Node %s deleted", node)
		return True
	return False

def _delete_nodes(db, pks=()):
	nodes = db.get_indexed_nodes(*pks)
	result = db.delete_nodes(*nodes)
	logger.debug("%s node(s) deleted", len(result))

## forums

def _add_forum_node(db, oid, label, key, value):
	node, forum, _ = _add_node(db, oid, key, value)
	return node, forum

def _update_forum_node(db, oid, label, key, value):
	node, forum = _add_forum_node(db, oid, label, key, value)
	if forum is not None:
		_update_node(db, node, forum)
	return node, forum

## topics

def _add_topic_node(db, oid, label, key, value):
	node, topic, created = _add_node(db, oid, label, key, value)
	if created:
		creator = get_creator(topic)
		rel = db.create_relationship(creator, topic, Author())
		logger.debug("Authorship relationship %s created", rel)
	return node, topic

def _update_topic_node(db, oid, label, key, value):
	node, topic = _add_topic_node(db, oid, label, key, value)
	if topic is not None:
		_update_node(db, node, topic)
	return node, topic

def _add_membership_relationship(db, child, parent):
	child = find_object_with_ntiid(child) if isinstance(child, string_types) else child
	parent = find_object_with_ntiid(parent) if isinstance(parent, string_types) else parent
	if child is not None and parent is not None:
		result = db.create_relationship(child, parent, MemberOf())
		logger.debug("Membership relationship %s created", result)
		return result

def _process_topic_event(db, topic, event):
	oid = get_oid(topic)
	pk = get_node_pk(topic)
	queue = get_job_queue()
	if pk is not None:
		if event == ADD_EVENT:
			job = create_job(_add_topic_node, db=db,
							 oid=oid,
							 label=pk.label,
							 key=pk.key,
							 value=pk.value)
			queue.put(job)

			## membership
			parent = get_oid(topic.__parent__)
			job = create_job(_add_membership_relationship, db=db,
							 child=oid, 
							 parent=parent)
			queue.put(job)
		else:
			job = create_job(_update_topic_node, db=db, 
							oid=oid, 
							label=pk.label,
							key=pk.key,
							value=pk.value)
			queue.put(job)

@component.adapter(ITopic, IObjectAddedEvent)
def _topic_added(topic, event):
	db = get_graph_db()
	if db is not None:
		_process_topic_event(db, topic, ADD_EVENT)

@component.adapter(ITopic, IObjectModifiedEvent)
def _topic_modified(topic, event):
	db = get_graph_db()
	if db is not None:
		_process_topic_event(db, topic, MODIFY_EVENT)

def _process_discussion_remove_events(db, primary_keys=()):
	if primary_keys:
		queue = get_job_queue()
		job = create_job(_delete_nodes, db=db, nodes=primary_keys)
		queue.put(job)

def _remove_topic(db, topic):
	primary_keys = [get_node_pk(topic)]
	for comment in topic.values():  # remove comments
		primary_keys.append(get_node_pk(comment))
	_process_discussion_remove_events(db, primary_keys)

@component.adapter(ITopic, IIntIdRemovedEvent)
def _topic_removed(topic, event):
	db = get_graph_db()
	if db is not None:
		_remove_topic(db, topic)

# comments

# def get_comment_relationship_PK(comment):
# 	author = get_creator(comment)
# 	rel_type = relationships.CommentOn()
# 	adapted = component.getMultiAdapter(
# 							(author, comment, rel_type),
# 							graph_interfaces.IUniqueAttributeAdapter)
# 	return utils.PrimaryKey(adapted.key, adapted.value)
# 
# def _add_comment_relationship(db, oid, comment_rel_pk):
# 	result = None
# 	comment = ntiids.find_object_with_ntiid(oid)
# 	if comment is not None:
# 		# comment are special case. we build a relationship between the commenting user
# 		# and the topic. We force key/value to identify the relationship
# 		# Note we don't create a comment node.
# 		author = get_creator(comment)
# 		topic = comment.__parent__
# 		rel_type = relationships.CommentOn()
# 		properties = component.getMultiAdapter(
# 									(author, comment, rel_type),
# 									graph_interfaces.IPropertyAdapter)
# 		result = db.create_relationship(author, topic, rel_type,
# 										properties=properties,
# 										key=comment_rel_pk.key,
# 										value=comment_rel_pk.value)
# 		logger.debug("comment-on relationship %s created", result)
# 	return result
#  
# def _delete_comment(db, comment_pk, comment_rel_pk):
# 	node = db.get_indexed_node(comment_pk.key, comment_pk.value) # check for comment node
# 	if node is not None:
# 		db.delete_node(node)
# 		logger.debug("comment-on node %s deleted", node)
# 	rel = db.delete_indexed_relationship(comment_rel_pk.key, comment_rel_pk.value)
# 	if rel is not None:
# 		logger.debug("comment-on relationship %s deleted", rel)
# 		return True
# 	return False
#  
# def _process_comment_event(db, comment, event):
# 	queue = get_job_queue()
# 	oid = to_external_ntiid_oid(comment)
# 	comment_pk = get_primary_key(comment)
# 	comment_rel_pk = get_comment_relationship_PK(comment)
#  
# 	if event == graph_interfaces.ADD_EVENT:
# 		job = create_job(_add_comment_relationship, db=db, oid=oid,
# 						 comment_rel_pk=comment_rel_pk)
# 		queue.put(job)
#  		
# 		parent = to_external_ntiid_oid(comment.__parent__)
# 		job = create_job(add_membership_relationship, db=db, child=oid, parent=parent)
# 		queue.put(job)
# 	else:
# 		job = create_job(_delete_comment, db=db, comment_pk=comment_pk,
# 						 comment_rel_pk=comment_rel_pk)
# 		queue.put(job)
#  	
# @component.adapter(frm_interfaces.IPersonalBlogComment, lce_interfaces.IObjectAddedEvent)
# def _add_personal_blog_comment(comment, event):
# 	db = get_graph_db()
# 	if db is not None:
# 		_process_comment_event(db, comment, graph_interfaces.ADD_EVENT)
#  
# @component.adapter(frm_interfaces.IGeneralForumComment, lce_interfaces.IObjectAddedEvent)
# def _add_general_forum_comment(comment, event):
# 	db = get_graph_db()
# 	if db is not None:
# 		_process_comment_event(db, comment, graph_interfaces.ADD_EVENT)
#  
# @component.adapter(frm_interfaces.IPersonalBlogComment,
# 				   lce_interfaces.IObjectModifiedEvent)
# def _modify_personal_blog_comment(comment, event):
# 	db = get_graph_db()
# 	if db is not None and nti_interfaces.IDeletedObjectPlaceholder.providedBy(comment):
# 		_process_comment_event(db, comment, graph_interfaces.REMOVE_EVENT)
#  
# @component.adapter(frm_interfaces.IGeneralForumComment,
# 				   lce_interfaces.IObjectModifiedEvent)
# def _modify_general_forum_comment(comment, event):
# 	_modify_personal_blog_comment(comment, event)
#  
# # forums
#  
# def _process_forum_add_mod_event(db, forum, event):
# 	oid = to_external_ntiid_oid(forum)
# 	adapted = graph_interfaces.IUniqueAttributeAdapter(forum)
# 	key, value = adapted.key, adapted.value
#  
# 	func = 	add_forum_node \
# 			if event == graph_interfaces.ADD_EVENT else modify_forum_node
#  
# 	queue = get_job_queue()
# 	job = create_job(func, db=db, oid=oid, key=key, value=value)
# 	queue.put(job)
#  
# @component.adapter(frm_interfaces.IForum, lce_interfaces.IObjectAddedEvent)
# def _forum_added(forum, event):
# 	db = get_graph_db()
# 	if db is not None:
# 		_process_forum_add_mod_event(db, forum, graph_interfaces.ADD_EVENT)
#  
# @component.adapter(frm_interfaces.IForum, lce_interfaces.IObjectModifiedEvent)
# def _forum_modified(forum, event):
# 	db = get_graph_db()
# 	if db is not None:
# 		_process_forum_add_mod_event(db, forum, graph_interfaces.MODIFY_EVENT)
#  
# @component.adapter(frm_interfaces.IForum, intid_interfaces.IIntIdRemovedEvent)
# def _forum_removed(forum, event):
# 	db = get_graph_db()
# 	if db is not None:
# 		for topic in forum.values():  # remove topics
# 			_remove_topic(db, topic)
# 		_process_discussion_remove_events(db, [get_primary_key(forum)])
#  
# component.moduleProvides(graph_interfaces.IObjectProcessor)
#  
# def init(db, obj):
# 	result = True
# 	if frm_interfaces.IForum.providedBy(obj):
# 		_process_forum_add_mod_event(db, obj, graph_interfaces.ADD_EVENT)
# 	elif frm_interfaces.ITopic.providedBy(obj):
# 		_process_topic_add_mod_event(db, obj, graph_interfaces.ADD_EVENT)
# 	elif frm_interfaces.IPersonalBlogComment.providedBy(obj) or \
# 		 frm_interfaces.IGeneralForumComment.providedBy(obj):
# 		_process_comment_event(db, obj, graph_interfaces.ADD_EVENT)
# 	else:
# 		result = False
# 	return result
