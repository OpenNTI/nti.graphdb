#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from nti.async import create_job
from nti.async import get_job_queue as async_queue

from . import interfaces as gdb_interfaces

QUEUE_NAME = "++etc++graphdb++queue"

def get_graph_db():
	return component.getUtility(gdb_interfaces.IGraphDB)

def get_job_queue():
	return async_queue(QUEUE_NAME)
