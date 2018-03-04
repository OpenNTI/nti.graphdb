#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component

from nti.asynchronous import create_job
from nti.asynchronous import get_job_queue as async_queue

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import StandardInternalFields

from nti.graphdb.interfaces import IGraphDB
from nti.graphdb.interfaces import IGraphDBQueueFactory

#: OID field
OID = StandardExternalFields.OID.lower()

#: NTIID field
NTIID = StandardInternalFields.NTIID

#: IntId field
INTID = StandardExternalFields.INTID.lower()

#: Creator field
CREATOR = StandardInternalFields.CREATOR

#: Created time field
CREATED_TIME = StandardInternalFields.CREATED_TIME

#: Last modified field
LAST_MODIFIED = StandardInternalFields.LAST_MODIFIED

#: ContainerId field
CONTAINER_ID = StandardInternalFields.CONTAINER_ID

#: Type field
TYPE = u'type'

#: title field
TITLE = u'title'

#: Username field
USERNAME = u'username'

#: Redis queue name
QUEUE_NAME = "++etc++graphdb++queue"

DEFAULT_URI = u"bolt://localhost:7687"

logger = __import__('logging').getLogger(__name__)


def get_graph_db():
    return component.queryUtility(IGraphDB)


def get_factory():
    return component.getUtility(IGraphDBQueueFactory)


def get_job_queue(name=QUEUE_NAME):
    return get_factory().get_queue(name)
