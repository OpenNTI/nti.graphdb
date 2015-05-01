#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import assert_that

from nti.graphdb.utils import UniqueAttribute
from nti.graphdb.interfaces import IUniqueAttributeAdapter

from nti.graphdb.tests import GraphDBTestCase

class TestUtils(GraphDBTestCase):

	def test_unique_attribute(self):
		ua = UniqueAttribute("a", "b")
		assert_that(IUniqueAttributeAdapter.providedBy(ua), is_(True))

		adapted = IUniqueAttributeAdapter(ua, None)
		assert_that(adapted, is_not(none()))

		ub = UniqueAttribute("a", "b")
		assert_that(ua, is_(ub))

		uc = UniqueAttribute("a", "c")
		assert_that(ua, is_not(uc))
