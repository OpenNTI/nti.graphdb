#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface
from zope import component

from . import interfaces as graph_interfaces

@interface.implementer(graph_interfaces.IContainer)
class Container(object):
	
	__slots__ = ('id',)

	def __init__(self, containerId):
		self.id = containerId

	def __eq__(self, other):
		try:
			return self is other or self.id == other.id
		except AttributeError:
			return NotImplemented

	def __hash__(self):
		xhash = 47
		xhash ^= hash(self.id)
		return xhash

	def __str__(self):
		return self.id

@interface.implementer(graph_interfaces.IContainer)
@component.adapter(basestring)
def _default_container_adapter(containerId):
	return Container(containerId)
