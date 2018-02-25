#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six
from collections import namedtuple

from zope.security.interfaces import IPrincipal
from zope.security.interfaces import NoInteraction
from zope.security.management import getInteraction

from ZODB.POSException import POSError

from nti.dataserver.interfaces import IEntity

from nti.dataserver.users.entity import Entity

from nti.graphdb import NTIID
from nti.graphdb import CREATOR
from nti.graphdb import CREATED_TIME
from nti.graphdb import LAST_MODIFIED

from nti.graphdb.interfaces import ILabelAdapter
from nti.graphdb.interfaces import IUniqueAttributeAdapter

from nti.externalization.interfaces import StandardExternalFields

from nti.ntiids.oids import to_external_ntiid_oid

EXT_NTIID = StandardExternalFields.NTIID

logger = __import__('logging').getLogger(__name__)


def get_entity(entity):
    """
    Return the dataserver entity for the specified value
    """
    if entity is not None and not IEntity.providedBy(entity):
        entity = Entity.get_entity(str(entity))
    return entity


def get_current_principal():
    """
    Return the current interaction principal
    """
    try:
        return getInteraction().participations[0].principal
    except (NoInteraction, IndexError, AttributeError):
        return None


def get_current_principal_id():
    """
    Return the current interaction principal id
    """
    result = get_current_principal()
    return result.id if result is not None else None


def get_current_user(user=None):
    """
    Return the current dataserver user
    """
    if user is None:
        user = get_current_principal_id()
    elif IPrincipal.providedBy(user):
        user = user.id
    result = get_entity(user)
    return result


def get_creator(obj):
    """
    Return the creator for the specified object
    """
    try:
        creator = getattr(obj, CREATOR, None)
        creator = get_entity(creator) if creator else None
        return creator
    except (TypeError, POSError):  # pragma: no cover
        return None


def get_principal_id(obj):
    """
    Return the principal id from the specified object
    """
    try:
        if IPrincipal.providedBy(obj):
            result = obj.id
        elif IEntity.providedBy(obj):
            result = obj.username
        elif isinstance(obj, six.string_types):
            result = obj
        else:
            result = None
    except (TypeError, POSError):  # pragma: no cover
        result = None
    return result


def get_createdTime(obj, default=0):
    """
    Return the creation time for the specified object
    """
    result = getattr(obj, CREATED_TIME, None) or default
    return result


def get_lastModified(obj, default=0):
    """
    Return the last modified time for the specified object
    """
    result = getattr(obj, LAST_MODIFIED, None) or default
    return result


def to_external_oid(obj):
    """
    Return the external id for the specified object
    """
    result = to_external_ntiid_oid(obj) if obj is not None else None
    return result
get_oid = to_external_oid


def get_ntiid(obj):
    """
    Return the ntiid id for the specified object
    """
    return getattr(obj, EXT_NTIID, None) or getattr(obj, NTIID, None)

#: Node Primary key tuple
NodePK = namedtuple('NodePK', 'label key value')


def get_node_pk(obj):
    """
    Return the primary key for specified object
    """
    label = ILabelAdapter(obj, None)
    unique = IUniqueAttributeAdapter(obj, None)
    if label and unique and unique.key and unique.value:
        return NodePK(label, unique.key, unique.value)
    return None
