#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
graphdb discussion topics

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope.lifecycleevent import interfaces as lce_interfaces

from nti.appserver import interfaces as app_interfaces

from nti.dataserver import interfaces as nti_interfaces
from nti.dataserver.contenttypes.forums import interfaces as frm_interfaces

from nti.externalization import externalization

from nti.ntiids import ntiids

from . import utils
from . import create_job
from . import get_graph_db
from . import get_job_queue
from . import relationships
from . import interfaces as graph_interfaces

def to_external_ntiid_oid(obj):
	return externalization.to_external_ntiid_oid(obj)

def get_primary_key(obj):
	adapted = graph_interfaces.IUniqueAttributeAdapter(obj)
	return utils.PrimaryKey(adapted.key, adapted.value)

# topics

def _add_authorship_relationship(db, topic):
	creator = topic.creator
	rel_type = relationships.Author()
	properties = component.getMultiAdapter(
								(creator, topic, rel_type),
								graph_interfaces.IPropertyAdapter)
	result = db.create_relationship(creator, topic, rel_type, properties=properties)
	logger.debug("authorship relationship %s created" % result)
	return result

def add_topic_node(db, oid, key, value):
	result = None
	node = db.get_indexed_node(key, value)
	topic = ntiids.find_object_with_ntiid(oid)
	if topic is not None and node is None:
		result = db.create_node(topic)
		logger.debug("topic node %s created" % result)
		_add_authorship_relationship(db, topic)
	return result, topic

def modify_topic_node(db, oid, key, value):
	node, topic = add_topic_node(db, oid, key, value)
	if topic is not None:
		labels = graph_interfaces.ILabelAdapter(topic)
		properties = graph_interfaces.IPropertyAdapter(topic)
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

def _process_topic_add_mod_event(db, topic, event):
	oid = to_external_ntiid_oid(topic)
	adapted = graph_interfaces.IUniqueAttributeAdapter(topic)
	key, value = adapted.key, adapted.value

	if event == graph_interfaces.ADD_EVENT:
		func = add_topic_node
	else:
		func = modify_topic_node

	queue = get_job_queue()
	job = create_job(func, db=db, oid=oid, key=key, value=value)
	queue.put(job)

@component.adapter(frm_interfaces.ITopic, lce_interfaces.IObjectAddedEvent)
def _topic_added(topic, event):
	db = get_graph_db()
	if db is not None:
		_process_topic_add_mod_event(db, topic, graph_interfaces.ADD_EVENT)

@component.adapter(frm_interfaces.ITopic, lce_interfaces.IObjectModifiedEvent)
def _topic_modified(topic, event):
	db = get_graph_db()
	if db is not None:
		_process_topic_add_mod_event(db, topic, graph_interfaces.MODIFY_EVENT)

def _delete_nodes(db, *args):
	result = db.delete_nodes(*args)
	logger.debug("%s node(s) deleted", result)

def _process_topic_remove_event(db, primary_keys=()):
	if primary_keys:
		queue = get_job_queue()
		job = create_job(_delete_nodes, db=db, *primary_keys)
		queue.put(job)
	
@component.adapter(frm_interfaces.ITopic, lce_interfaces.IObjectRemovedEvent)
def _topic_removed(topic, event):
	db = get_graph_db()
	if db is not None:
		primary_keys = [get_primary_key(topic)]
		for comment in topic.values():  # remove comments
			primary_keys.append(get_primary_key(comment))
		_process_topic_remove_event(db, primary_keys)

# comments

def get_comment_relationship_PK(comment):
	author = comment.creator
	rel_type = relationships.CommentOn()
	adapted = component.getMultiAdapter(
							(author, comment, rel_type),
							graph_interfaces.IUniqueAttributeAdapter)
	return utils.PrimaryKey(adapted.key, adapted.value)

def _add_comment_relationship(db, oid, comment_rel_pk):
	result = None
	comment = ntiids.find_object_with_ntiid(oid)
	if comment is not None:
		# comment are special case. we build a relationship between the commenting user and
		# the topic. We force key/value to identify the relationship
		# Note we don't create a comment node.
		author = comment.creator
		topic = comment.__parent__
		rel_type = relationships.CommentOn()
		properties = component.getMultiAdapter(
									(author, comment, rel_type),
									graph_interfaces.IPropertyAdapter)
		result = db.create_relationship(author, topic, rel_type,
										properties=properties,
										key=comment_rel_pk.key,
										value=comment_rel_pk.value)
		logger.debug("comment-on relationship %s created" % result)
	return result

def _delete_comment(db, comment_pk, comment_rel_pk):
	node = db.get_indexed_node(comment_pk.key, comment_pk.value) # check for comment node
	if node is not None:
		db.delete_node(node)
		logger.debug("comment-on node %s deleted" % comment_pk)
	if db.delete_indexed_relationship(comment_rel_pk.key, comment_rel_pk.value):
		logger.debug("comment-on relationship %s deleted" % comment_rel_pk)
		return True
	return False

def _process_comment_event(db, comment, event):
	oid = to_external_ntiid_oid(comment)
	comment_pk = get_primary_key(comment)
	comment_rel_pk = get_comment_relationship_PK(comment)

	queue = get_job_queue()
	if event == graph_interfaces.ADD_EVENT:
		job = create_job(_add_comment_relationship, db=db, oid=oid,
						 comment_rel_pk=comment_rel_pk)
	else:
		job = create_job(_delete_comment, db=db, comment_pk=comment_pk,
						 comment_rel_pk=comment_rel_pk)
	queue.put(job)

@component.adapter(frm_interfaces.IPersonalBlogComment, lce_interfaces.IObjectAddedEvent)
def _add_personal_blog_comment(comment, event):
	db = get_graph_db()
	if db is not None:
		_process_comment_event(db, comment, graph_interfaces.ADD_EVENT)

@component.adapter(frm_interfaces.IGeneralForumComment, lce_interfaces.IObjectAddedEvent)
def _add_general_forum_comment(comment, event):
	db = get_graph_db()
	if db is not None:
		_process_comment_event(db, comment, graph_interfaces.ADD_EVENT)

@component.adapter(frm_interfaces.IPersonalBlogComment,
				   lce_interfaces.IObjectModifiedEvent)
def _modify_personal_blog_comment(comment, event):
	db = get_graph_db()
	if db is not None and app_interfaces.IDeletedObjectPlaceholder.providedBy(comment):
		_process_comment_event(db, comment, graph_interfaces.REMOVE_EVENT)

@component.adapter(frm_interfaces.IGeneralForumComment,
				   lce_interfaces.IObjectModifiedEvent)
def _modify_general_forum_comment(comment, event):
	_modify_personal_blog_comment(comment, event)

# utils

def _record_author(db, topic):
	oid = to_external_ntiid_oid(topic)
	adapted = graph_interfaces.IUniqueAttributeAdapter(topic)
	add_topic_node(db, oid, adapted.key, adapted.value)

def _record_comment(db, comment):
	oid = to_external_ntiid_oid(comment)
	comment_rel_pk = get_comment_relationship_PK(comment)
	_add_comment_relationship(db, oid, comment_rel_pk)

def init(db, entity):
	if nti_interfaces.IUser.providedBy(entity):
		blog = frm_interfaces.IPersonalBlog(entity)
		for topic in blog.values():
			_record_author(topic)
			for comment in topic.values():
				_record_comment(comment)
	elif nti_interfaces.ICommunity.providedBy(entity):
		board = frm_interfaces.ICommunityBoard(entity)
		for forum in board.values():
			for topic in forum.values():
				_record_author(topic)
				for comment in topic.values():
					_record_comment(comment)
