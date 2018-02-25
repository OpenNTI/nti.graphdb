#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import assert_that

from zope import component

from nti.graphdb import QUEUE_NAME

from nti.graphdb.interfaces import IGraphDBQueueFactory

import nti.testing.base


ZCML_STRING = u"""
<configure  xmlns="http://namespaces.zope.org/zope"
            xmlns:zcml="http://namespaces.zope.org/zcml"
            xmlns:graphdb="http://nextthought.com/ntp/graphdb"
            i18n_domain='nti.dataserver'>

    <include package="zope.component" />

    <include package="." file="meta.zcml" />
    <graphdb:registerRedisProcessingQueue />

</configure>
"""


class TestZcml(nti.testing.base.ConfiguringTestBase):

    def test_registration(self):
        self.configure_string(ZCML_STRING)
        factory = component.queryUtility(IGraphDBQueueFactory)
        assert_that(factory, is_not(none()))

        assert_that(factory.get_queue(QUEUE_NAME),
                    is_not(none()))

        assert_that(factory._redis(), is_(none()))
