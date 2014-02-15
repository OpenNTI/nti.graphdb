#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope.lifecycleevent import interfaces as lce_interfaces

from nti.dataserver import interfaces as nti_interfaces

# from . import utils
# from . import create_job
from . import get_graph_db
# from . import get_job_queue
# from . import relationships
# from . import interfaces as graph_interfaces

def _process_shareable(db, obj):
	sharedWith = getattr(obj, 'sharedWith', ())
	if not sharedWith:
		return

@component.adapter(nti_interfaces.IReadableShared, lce_interfaces.IObjectAddedEvent)
def _shareable_added(obj, event):
	db = get_graph_db()
	if db is not None:
		_process_shareable(db, obj)

def _process_modified_event(db, obj, oldSharingTargets=()):
	# sharingTargets = getattr(obj, 'sharingTargets')
	pass

@component.adapter(nti_interfaces.IContained, nti_interfaces.IObjectSharingModifiedEvent)
def _shareable_modified(obj, event):
	db = get_graph_db()
	if db is not None:
		_process_modified_event(db, obj, event.oldSharingTargets)

# utils

def init(db, obj):
	result = False
	if nti_interfaces.IShareableModeledContent.providedBy(obj):
		_process_shareable(db, obj)
		result = True
	return result
