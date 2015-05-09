#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import uuid

from zope.component.hooks import setHooks

from nti.dataserver.tests.mock_dataserver import WithMockDS
from nti.dataserver.tests.mock_dataserver import mock_db_trans

from nti.app.testing.application_webtest import ApplicationTestLayer

from nti.testing.layers import find_test
from nti.testing.layers import GCLayerMixin
from nti.testing.layers import ZopeComponentLayer
from nti.testing.layers import ConfiguringLayerMixin

from nti.dataserver.tests.mock_dataserver import DSInjectorMixin

import zope.testing.cleanup

DEFAULT_URI = 'http://localhost:7474/db/data'

def random_username():
    splits = unicode(uuid.uuid4()).split('-')
    username = "%s@%s" % (splits[-1], splits[0])
    return username

class SharedConfiguringTestLayer(ZopeComponentLayer,
                                 GCLayerMixin,
                                 ConfiguringLayerMixin,
                                 DSInjectorMixin):

    set_up_packages = ('nti.dataserver', 'nti.graphdb')

    @classmethod
    def setUp(cls):
        setHooks()
        cls.setUpPackages()

    @classmethod
    def tearDown(cls):
        cls.tearDownPackages()
        zope.testing.cleanup.cleanUp()

    @classmethod
    def testSetUp(cls, test=None):
        setHooks()
        cls.setUpTestDS(test)
        
    @classmethod
    def testTearDown(cls):
        pass

import unittest

class GraphDBTestCase(unittest.TestCase):
    layer = SharedConfiguringTestLayer

def can_connect(uri=None):
    from py2neo import Graph
    try:
        graph = Graph(uri)
        assert graph.neo4j_version
        return True
    except Exception:
        return False

def cannot_connect(uri=None):
    return not can_connect(uri)
