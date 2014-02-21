#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope.processlifetime import IDatabaseOpenedWithRoot

from nti.dataserver import interfaces as nti_interfaces

def onChange(datasvr, msg, target=None, broadcast=None, **kwargs):
	pass

@component.adapter(IDatabaseOpenedWithRoot)
def _set_change_listener(database_event):
	dataserver = component.queryUtility(nti_interfaces.IDataserver)
	if dataserver is not None:
		dataserver.add_change_listener(onChange)
