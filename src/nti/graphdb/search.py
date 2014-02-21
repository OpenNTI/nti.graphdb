#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

# from nti.dataserver import interfaces as nti_interfaces

from nti.contentsearch import interfaces as search_interfaces

from nti.externalization import externalization

# from nti.ntiids import ntiids

# from . import create_job
from . import get_graph_db
# from . import get_job_queue
# from . import interfaces as graph_interfaces

def to_external_ntiid_oid(obj):
	return externalization.to_external_ntiid_oid(obj)

@component.adapter(search_interfaces.ISearchCompletedEvent)
def _search_completed(entity, event):
	db = get_graph_db()
	if db is not None:
		pass

# utils

def init(db, obj):
	pass
