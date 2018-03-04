#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import none
from hamcrest import is_not
from hamcrest import assert_that

from nti.graphdb import get_factory
from nti.graphdb import get_graph_db
from nti.graphdb import get_job_queue

from nti.graphdb.tests import GraphDBTestCase


class TestModule(GraphDBTestCase):

    def test_get_factory(self):
        assert_that(get_factory(), is_not(none()))

    def test_get_graph_db(self):
        assert_that(get_graph_db(), is_not(none()))

    def test_get_job_queue(self):
        assert_that(get_job_queue(), is_not(none()))
