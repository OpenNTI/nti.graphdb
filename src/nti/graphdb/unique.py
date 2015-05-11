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

from nti.common.property import Lazy
from nti.common.representation import WithRepr

from nti.contentlibrary.interfaces import IContentUnit 

from nti.dataserver.interfaces import IEntity
from nti.dataserver.interfaces import IUseNTIIDAsExternalUsername
from nti.dataserver.interfaces import IDynamicSharingTargetFriendsList

from nti.dataserver.contenttypes.forums.interfaces import ITopic
from nti.dataserver.contenttypes.forums.interfaces import IHeadlinePost

from . common import get_oid
from . common import get_ntiid

from .interfaces import IUniqueAttributeAdapter

@WithRepr
@component.adapter(interface.Interface)
@interface.implementer(IUniqueAttributeAdapter)
class _GenericUniqueAttributeAdpater(object):

	key = value = None

	def __init__(self, obj):
		self.obj = obj

@interface.implementer(IUniqueAttributeAdapter)
class _IntIDUniqueAttributeAdpater(_GenericUniqueAttributeAdpater):

	key = "intid"

	@Lazy
	def value(self):
		intids = component.queryUtility(zope.intid.IIntIds)
		result = intids.queryId(self.obj) if intids is not None else None
		return result

@interface.implementer(IUniqueAttributeAdapter)
class _OIDUniqueAttributeAdpater(_GenericUniqueAttributeAdpater):

	key = "oid"

	@Lazy
	def value(self):
		result = get_oid(self.obj)
		return result

@component.adapter(IEntity)
@interface.implementer(IUniqueAttributeAdapter)
class _EntityUniqueAttributeAdpater(_GenericUniqueAttributeAdpater):

	key = "username"

	@Lazy
	def value(self):
		if IUseNTIIDAsExternalUsername.providedBy(self.obj):
			return get_ntiid(self.obj) or get_oid(self.obj)
		return self.obj.username

@interface.implementer(IUniqueAttributeAdapter)
@component.adapter(IDynamicSharingTargetFriendsList)
class _DFLUniqueAttributeAdpater(_GenericUniqueAttributeAdpater):

	key = "username"

	@Lazy
	def value(self):
		return get_ntiid(self.obj) or get_oid(self.obj)
	
@component.adapter(ITopic)
@interface.implementer(IUniqueAttributeAdapter)
class _TopicUniqueAttributeAdpater(_GenericUniqueAttributeAdpater):

	key = "oid"

	@Lazy
	def value(self):
		return get_oid(self.obj)

@interface.implementer(IUniqueAttributeAdapter)
@component.adapter(IHeadlinePost)
class _HeadlinePostUniqueAttributeAdpater(_TopicUniqueAttributeAdpater):

	def __init__(self, obj):
		super(_HeadlinePostUniqueAttributeAdpater, self).__init__(obj.__parent__)

@component.adapter(IContentUnit)
@interface.implementer(IUniqueAttributeAdapter)
class _ContentUnitAttributeAdpater(_OIDUniqueAttributeAdpater):

	@Lazy
	def value(self):
		return self.obj.ntiid

@interface.implementer(IUniqueAttributeAdapter)
class _NTIIDUniqueAttributeAdpater(_OIDUniqueAttributeAdpater):

	key = "oid"

	@Lazy
	def value(self):
		return get_ntiid(self.obj)
