#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

import uuid
import unittest

import zope.testing.cleanup

from zope.component.hooks import setHooks

from nti.testing.layers import GCLayerMixin
from nti.testing.layers import ZopeComponentLayer
from nti.testing.layers import ConfiguringLayerMixin

from nti.dataserver.tests.mock_dataserver import DSInjectorMixin

DEFAULT_URI = "bolt://localhost:7687"


def random_username():
    splits = unicode(uuid.uuid4()).split('-')
    username = u"%s@%s" % (splits[-1], splits[0])
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


class GraphDBTestCase(unittest.TestCase):
    layer = SharedConfiguringTestLayer


def can_connect(uri=DEFAULT_URI):
    from neo4j.v1 import GraphDatabase
    try:
        graph = GraphDatabase.driver(uri)
        with graph.session():
            return True
    except Exception:  # pylint: disable=broad-except
        return False


def cannot_connect(uri=DEFAULT_URI):
    return not can_connect(uri)
