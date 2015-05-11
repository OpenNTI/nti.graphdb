#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
from nti.graphdb.interfaces import ILabelAdapter, IUniqueAttributeAdapter
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from collections import namedtuple

from zope.security.interfaces import IPrincipal
from zope.security.management import queryInteraction

from ZODB.POSException import POSKeyError

from nti.dataserver.users import Entity
from nti.dataserver.interfaces import IEntity

from nti.externalization.externalization import to_external_ntiid_oid

def get_current_principal():
	interaction = queryInteraction()
	participations = list(getattr(interaction, 'participations', None) or ())
	participation = participations[0] if participations else None
	principal = getattr(participation, 'principal', None)
	result = principal.id if principal is not None else None
	return result

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
	except (TypeError, POSKeyError):
		return None

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
