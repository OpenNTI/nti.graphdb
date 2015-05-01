#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from nti.async import create_job
from nti.async import get_job_queue as async_queue

from .interfaces import IGraphDB
from .interfaces import IGraphDBQueueFactory

QUEUE_NAME = "++etc++graphdb++queue"

def get_graph_db():
	return component.queryUtility(IGraphDB)

def get_factory():
	return component.getUtility(IGraphDBQueueFactory)

def get_job_queue(name=QUEUE_NAME):
	return get_factory().get_queue(name)
