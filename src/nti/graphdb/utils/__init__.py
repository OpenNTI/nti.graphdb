#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.common.representation import WithRepr

from nti.graphdb.interfaces import IUniqueAttributeAdapter

from nti.schema.schema import EqHash

@WithRepr
@EqHash('key', 'value')
@interface.implementer(IUniqueAttributeAdapter)
class UniqueAttribute(object):

    def __init__(self, key, value):
        self.key = key
        self.value = value

PrimaryKey = UniqueAttribute
