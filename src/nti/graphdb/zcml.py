#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=inherit-non-class,expression-not-assigned

import functools

from zope import schema
from zope import component
from zope import interface

from zope.component.zcml import utility

from zope.configuration import fields

from nti.asynchronous.interfaces import IRedisQueue
from nti.asynchronous.redis_queue import RedisQueue
from nti.asynchronous import get_job_queue as async_queue

from nti.coremetadata.interfaces import IRedisClient

from nti.graphdb import QUEUE_NAME

from nti.graphdb.interfaces import IGraphDB
from nti.graphdb.interfaces import IGraphDBQueueFactory

from nti.graphdb.neo4j.database import Neo4jDB

logger = __import__('logging').getLogger(__name__)


class IRegisterGraphDB(interface.Interface):
    """
    The arguments needed for registering an graph db
    """
    url = fields.TextLine(title=u"db url", required=True)
    username = fields.TextLine(title=u"db username", required=False)
    password = schema.Password(title=u"db password", required=False)


def registerGraphDB(_context, url, username=None, password=None):
    """
    Register an db
    """
    factory = functools.partial(Neo4jDB, 
								url=url,
								username=username, 
								password=password)
    utility(_context, provides=IGraphDB, factory=factory)


class ImmediateQueueRunner(object):
    """
    A queue that immediately runs the given job. This is generally
    desired for test or dev mode.
    """

    def put(self, job):
        job()


@interface.implementer(IGraphDBQueueFactory)
class ImmediateQueueFactory(object):

    def get_queue(self, unused_name):
        return ImmediateQueueRunner()


@interface.implementer(IGraphDBQueueFactory)
class _AbstractProcessingQueueFactory(object):

    queue_interface = None

    def get_queue(self, name):
        queue = async_queue(name, self.queue_interface)
        if queue is None:
            msg = "No queue exists for content rendering queue (%s)." % name
            raise ValueError(msg)
        return queue


class GraphProcessingQueueFactory(_AbstractProcessingQueueFactory):

    queue_interface = IRedisQueue

    def __init__(self, _context):
        for name in (QUEUE_NAME,):
            queue = RedisQueue(self._redis, name)
            utility(_context, provides=IRedisQueue, component=queue, name=name)

    def _redis(self):
        return component.queryUtility(IRedisClient)


def registerImmediateProcessingQueue(_context):
    logger.info("Registering immediate graphdb processing queue")
    factory = ImmediateQueueFactory()
    utility(_context, provides=IGraphDBQueueFactory, component=factory)


def registerRedisProcessingQueue(_context):
    logger.info("Registering graphdb redis processing queue")
    factory = GraphProcessingQueueFactory(_context)
    utility(_context, provides=IGraphDBQueueFactory, component=factory)
