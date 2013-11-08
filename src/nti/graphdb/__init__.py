#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
graphdb module

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

from pyramid.threadlocal import get_current_request

def get_possible_site_names(request=None, include_default=True):
    request = request or get_current_request()
    if not request:
        return () if not include_default else ('',)
    __traceback_info__ = request

    site_names = getattr(request, 'possible_site_names', ())
    if include_default:
        site_names += ('',)
    return site_names
