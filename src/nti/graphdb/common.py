#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six

from nti.dataserver.users import Entity
from nti.dataserver import interfaces as nti_interfaces

from nti.externalization import externalization

def get_entity(entity):
    if not nti_interfaces.IEntity.providedBy(entity):
        entity = Entity.get_entity(str(entity))
    return entity

def get_creator(obj):
    creator = getattr(obj, 'creator', None)
    if isinstance(creator, six.string_types):
        creator = Entity.get_entity(creator)
    return creator

def to_external_ntiid_oid(obj):
    return externalization.to_external_ntiid_oid(obj)
