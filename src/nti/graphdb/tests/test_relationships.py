#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import none
from hamcrest import is_not
from hamcrest import assert_that

import sys
import inspect
import unittest

from nti.graphdb import relationships


class TestRelationships(unittest.TestCase):

    def test_classes(self):
        name = relationships.__name__
        for name, obj in inspect.getmembers(sys.modules[name]):
            if inspect.isclass(obj) and obj != relationships.Singleton:
                assert_that(str(obj()), is_not(none()))
