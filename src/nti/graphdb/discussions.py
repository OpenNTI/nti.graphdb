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

from nti.dataserver.interfaces import IDeletedObjectPlaceholder

from nti.dataserver.contenttypes.forums.interfaces import IForum
from nti.dataserver.contenttypes.forums.interfaces import ITopic
from nti.dataserver.contenttypes.forums.interfaces import IGeneralForumComment
from nti.dataserver.contenttypes.forums.interfaces import IPersonalBlogComment

from nti.ntiids.ntiids import find_object_with_ntiid

from .common import get_oid
from .common import get_creator
from .common import get_node_pk

from .relationships import Author
from .relationships import MemberOf
from .relationships import CommentOn

from .interfaces import ADD_EVENT
from .interfaces import MODIFY_EVENT
from .interfaces import REMOVE_EVENT
from .interfaces import IPropertyAdapter
from .interfaces import IObjectProcessor

from . import create_job
from . import get_graph_db
from . import get_job_queue

# utils

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

# forums

def _add_forum_node(db, oid, label, key, value):
	node, forum, _ = _add_node(db, oid, key, value)
	return node, forum

def _update_forum_node(db, oid, label, key, value):
	node, forum = _add_forum_node(db, oid, label, key, value)
	if forum is not None:
		_update_node(db, node, forum)
	return node, forum

# topics

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

def _process_add_topic_event(db, oid, label, key, value, parent):
	# create topic node
	_add_topic_node(db=db, oid=oid,
					label=label,
					key=key,
					value=value)
	# membership
	_add_membership_relationship(db=db, 
								 child=oid,
								 parent=parent)

def _process_topic_event(db, topic, event):
	oid = get_oid(topic)
	pk = get_node_pk(topic)
	queue = get_job_queue()
	if pk is not None:
		if event == ADD_EVENT:
			parent = get_oid(topic.__parent__)
			job = create_job(_process_add_topic_event, 
							 db=db,
							 oid=oid,
							 label=pk.label,
							 key=pk.key,
							 value=pk.value,
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

def _get_comment_relationship(db, comment):
	pk = get_node_pk(comment)
	topic = comment.__parent__
	author = get_creator(comment)
	rels = db.match(author, topic, CommentOn())
	for rel in rels or ():
		props = getattr(rel, 'properties', None) or {}
		if props.get(pk.key) == pk.value:
			return rel
	return None

def _add_comment_relationship(db, oid):
	result = None
	comment = find_object_with_ntiid(oid)
	if comment is not None:
		# Comments are special case. we build a relationship between the
		# commenting user and the topic. We identify the relationship with
		# the primary key of the comment
		# Note we don't create a comment node.
		pk = get_node_pk(comment)
		topic = comment.__parent__
		author = get_creator(comment)
		properties = {pk.key: pk.value}
		result = db.create_relationship(author, topic, CommentOn(),
										properties=properties,
										unique=False)
		logger.debug("CommentOn relationship %s created", result)
	return result

def _delete_comment(db, oid, label, key, value):
	comment = find_object_with_ntiid(oid)
	if comment is not None:
		node = db.get_indexed_node(label, key, value)  # check for comment node
		if node is not None:
			db.delete_node(node)
			logger.debug("Comment node %s deleted", node)

		rel = _get_comment_relationship(db, comment)
		if rel is not None:
			db.delete_relationship(rel)
			logger.debug("Comment-on relationship %s deleted", rel)
			return True
		return False

def _process_add_comment_event(db, oid, parent):
	# add user->topic relationship
	_add_comment_relationship(db=db, oid=oid)
	# create comment->topic relationship
	_add_membership_relationship(db=db, child=oid, parent=parent)

def _process_comment_event(db, comment, event):
	queue = get_job_queue()
	oid = get_oid(comment)
	if event == ADD_EVENT:
		parent = get_oid(comment.__parent__)
		job = create_job(_process_add_comment_event, db=db, oid=oid, parent=parent)
		queue.put(job)
	else:
		pk = get_node_pk(comment)
		job = create_job(_delete_comment, db=db, oid=oid,
						 label=pk.label,
						 key=pk.key, value=pk.value)
		queue.put(job)

@component.adapter(IPersonalBlogComment, IObjectAddedEvent)
def _add_personal_blog_comment(comment, event):
	db = get_graph_db()
	if db is not None:
		_process_comment_event(db, comment, ADD_EVENT)

@component.adapter(IGeneralForumComment, IObjectAddedEvent)
def _add_general_forum_comment(comment, event):
	db = get_graph_db()
	if db is not None:
		_process_comment_event(db, comment, ADD_EVENT)

@component.adapter(IPersonalBlogComment, IObjectModifiedEvent)
def _modify_personal_blog_comment(comment, event):
	db = get_graph_db()
	if db is not None and IDeletedObjectPlaceholder.providedBy(comment):
		_process_comment_event(db, comment, REMOVE_EVENT)

@component.adapter(IGeneralForumComment, IObjectModifiedEvent)
def _modify_general_forum_comment(comment, event):
	_modify_personal_blog_comment(comment, event)

# forums

def _process_forum_event(db, forum, event):
	oid = get_oid(forum)
	pk = get_node_pk(forum)
	queue = get_job_queue()
	func = _add_forum_node if event == ADD_EVENT else _update_forum_node
	job = create_job(func, db=db, oid=oid, label=pk.label, key=pk.key, value=pk.value)
	queue.put(job)

@component.adapter(IForum, IObjectAddedEvent)
def _forum_added(forum, event):
	db = get_graph_db()
	if db is not None:
		_process_forum_event(db, forum, ADD_EVENT)

@component.adapter(IForum, IObjectModifiedEvent)
def _forum_modified(forum, event):
	db = get_graph_db()
	if db is not None:
		_process_forum_event(db, forum, MODIFY_EVENT)

@component.adapter(IForum, IIntIdRemovedEvent)
def _forum_removed(forum, event):
	db = get_graph_db()
	if db is not None:
		# remove topics
		for topic in forum.values():
			_remove_topic(db, topic)
		# remove forum node
		_process_discussion_remove_events(db, [get_node_pk(forum)])

component.moduleProvides(IObjectProcessor)

def init(db, obj):
	result = True
	if IForum.providedBy(obj):
		_process_forum_event(db, obj, ADD_EVENT)
	elif ITopic.providedBy(obj):
		_process_topic_event(db, obj, ADD_EVENT)
	elif IPersonalBlogComment.providedBy(obj) or \
		 IGeneralForumComment.providedBy(obj):
		_process_comment_event(db, obj, ADD_EVENT)
		pass
	else:
		result = False
	return result
