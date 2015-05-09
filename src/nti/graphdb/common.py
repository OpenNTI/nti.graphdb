#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from ZODB.POSException import POSKeyError

from nti.dataserver.users import Entity
from nti.dataserver.interfaces import IEntity

from nti.externalization.externalization import to_external_ntiid_oid

def get_entity(entity):
    if entity is not None and not IEntity.providedBy(entity):
        entity = Entity.get_entity(str(entity))
    return entity

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
