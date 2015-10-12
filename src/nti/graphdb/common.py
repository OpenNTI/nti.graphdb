#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
from collections import namedtuple

from zope.security.interfaces import IPrincipal
from zope.security.management import NoInteraction
from zope.security.management import getInteraction

from ZODB.POSException import POSError

from nti.dataserver.users import Entity
from nti.dataserver.interfaces import IEntity

from nti.externalization.externalization import to_external_ntiid_oid

from .interfaces import ILabelAdapter
from .interfaces import IUniqueAttributeAdapter

def get_current_principal():
	try:
		return getInteraction().participations[0].principal.id
	except (NoInteraction, IndexError, AttributeError):
		return None

def get_entity(entity):
	if entity is not None and not IEntity.providedBy(entity):
		entity = Entity.get_entity(str(entity))
	return entity

def get_current_user(user=None):
	if user is None:
		user = get_current_principal()
	elif IPrincipal.providedBy(user):
		user = user.id
	result = get_entity(user)
	return result

def get_creator(obj):
	try:
		creator = getattr(obj, 'creator', None)
		creator = get_entity(creator) if creator else None
		return creator
	except (TypeError, POSError):
		return None

def get_principal_id(obj):
	try:
		if IPrincipal.providedBy(obj):
			result = obj.id
		elif IEntity.providedBy(obj):
			result = obj.username
		elif isinstance(obj, six.string_types):
			result = obj
		else:
			result = None
	except (TypeError, POSError):
		result = None
	return result

def get_createdTime(obj, default=0):
	result = getattr(obj, 'createdTime', None) or default
	return result

def get_lastModified(obj, default=0):
	result = getattr(obj, 'lastModified', None) or default
	return result

def to_external_oid(obj):
	result = to_external_ntiid_oid(obj) if obj is not None else None
	return result
get_oid = to_external_oid

def get_ntiid(obj):
	return getattr(obj, 'NTIID', None) or  getattr(obj, 'ntiid', None)

NodePK = namedtuple('NodePK', 'label key value')

def get_node_pk(obj):
	label = ILabelAdapter(obj, None)
	unique = IUniqueAttributeAdapter(obj, None)
	if label and unique and unique.key and unique.value:
		return NodePK(label, unique.key, unique.value)
	return None
