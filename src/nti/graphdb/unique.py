#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import zope.intid

from zope import component
from zope import interface

from nti.common.representation import WithRepr

from nti.contentlibrary.interfaces import IContentUnit 

from nti.dataserver.interfaces import IEntity
from nti.dataserver.contenttypes.forums.interfaces import ITopic
from nti.dataserver.contenttypes.forums.interfaces import IHeadlinePost

from . common import get_ntiid
from . common import to_external_oid

from .interfaces import IUniqueAttributeAdapter

@WithRepr
@interface.implementer(IUniqueAttributeAdapter)
@component.adapter(interface.Interface)
class _GenericUniqueAttributeAdpater(object):

	key = value = None

	def __init__(self, obj):
		self.obj = obj

@interface.implementer(IUniqueAttributeAdapter)
class _IntIDUniqueAttributeAdpater(_GenericUniqueAttributeAdpater):

	key = "intid"

	@property
	def value(self):
		intids = component.queryUtility(zope.intid.IIntIds)
		result = intids.queryId(self.obj) if intids is not None else None
		return result

@interface.implementer(IUniqueAttributeAdapter)
class _OIDUniqueAttributeAdpater(_GenericUniqueAttributeAdpater):

	key = "oid"

	@property
	def value(self):
		result = to_external_oid(self.obj)
		return result

@interface.implementer(IUniqueAttributeAdapter)
@component.adapter(IEntity)
class _EntityUniqueAttributeAdpater(_GenericUniqueAttributeAdpater):

	key = "username"

	@property
	def value(self):
		return self.obj.username

@interface.implementer(IUniqueAttributeAdapter)
@component.adapter(ITopic)
class _TopicUniqueAttributeAdpater(_GenericUniqueAttributeAdpater):

	key = "oid"

	@property
	def value(self):
		return self.obj.NTIID

@interface.implementer(IUniqueAttributeAdapter)
@component.adapter(IHeadlinePost)
class _HeadlinePostUniqueAttributeAdpater(_TopicUniqueAttributeAdpater):

	def __init__(self, obj):
		super(_HeadlinePostUniqueAttributeAdpater, self).__init__(obj.__parent__)

@interface.implementer(IUniqueAttributeAdapter)
@component.adapter(IContentUnit)
class _ContentUnitAttributeAdpater(_OIDUniqueAttributeAdpater):

	@property
	def value(self):
		return self.obj.ntiid

@interface.implementer(IUniqueAttributeAdapter)
class _NTIIDUniqueAttributeAdpater(_OIDUniqueAttributeAdpater):

	key = "oid"

	@property
	def value(self):
		return get_ntiid(self.obj)
