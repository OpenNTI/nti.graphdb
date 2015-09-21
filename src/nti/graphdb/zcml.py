#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import functools

from zope import schema
from zope import component
from zope import interface

from zope.component.zcml import utility

from zope.configuration import fields

from nti.async.interfaces import IQueue
from nti.async.interfaces import IRedisQueue
from nti.async.redis_queue import RedisQueue
from nti.async import get_job_queue as async_queue

from nti.dataserver.interfaces import IRedisClient

from .neo4j import Neo4jDB

from .interfaces import NEO4J
from .interfaces import DATABASE_TYPES

from .interfaces import IGraphDB

from . import QUEUE_NAME

class IRegisterGraphDB(interface.Interface):
	"""
	The arguments needed for registering an graph db
	"""
	name = fields.TextLine(title="db name identifier (site)", required=False, default="")
	url = fields.TextLine(title="db url", required=True)
	dbtype = schema.Choice(title="db type", values=DATABASE_TYPES, default=NEO4J,
						   required=False)
	username = fields.TextLine(title="db username", required=False)
	password = schema.Password(title="db password", required=False)
	
	config = fields.TextLine(title="path to config file", required=False)
	
def registerGraphDB(_context, url, username=None, password=None, config=None, name=u""):
	"""
	Register an db
	"""
	factory = functools.partial(Neo4jDB, url=url, username=username, password=password, 
								config=config)
	utility(_context, provides=IGraphDB, factory=factory, name=name)

from .interfaces import IGraphDBQueueFactory

class ImmediateQueueRunner(object):
	"""
	A queue that immediately runs the given job. This is generally
	desired for test or dev mode.
	"""
	def put(self, job):
		job()

@interface.implementer(IGraphDBQueueFactory)
class _ImmediateQueueFactory(object):

	def get_queue( self, name ):
		return ImmediateQueueRunner()

@interface.implementer(IGraphDBQueueFactory)
class _AbstractProcessingQueueFactory(object):

	queue_interface = None

	def get_queue( self, name ):
		queue = async_queue(name, self.queue_interface)
		if queue is None:
			raise ValueError("No queue exists for graphdb processing queue (%s). "
							 "Evolve error?" % name )
		return queue

class _GraphDBProcessingQueueFactory(_AbstractProcessingQueueFactory):
	queue_interface = IQueue

class _GraphDBRedisProcessingQueueFactory(_AbstractProcessingQueueFactory):
	
	queue_interface = IRedisQueue

	def __init__(self, _context):
		for name in (QUEUE_NAME,):
			queue = RedisQueue(self._redis, name)
			utility(_context, provides=IRedisQueue, component=queue, name=name)

	def _redis(self):
		return component.getUtility(IRedisClient)

def registerImmediateProcessingQueue(_context):
	logger.info( "Registering immediate graphdb processing queue" )
	factory = _ImmediateQueueFactory()
	utility( _context, provides=IGraphDBQueueFactory, component=factory)

def registerProcessingQueue(_context):
	logger.info( "Registering graphdb processing queue" )
	factory = _GraphDBProcessingQueueFactory()
	utility( _context, provides=IGraphDBQueueFactory, component=factory)

def registerRedisProcessingQueue(_context):
	logger.info( "Registering graphdb redis processing queue" )
	factory = _GraphDBRedisProcessingQueueFactory(_context)
	utility(_context, provides=IGraphDBQueueFactory, component=factory)
