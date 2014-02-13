#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pyramid views.

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface
from zope.location.interfaces import IContained
from zope.container import contained as zcontained
from zope.traversing.interfaces import IPathAdapter

from pyramid.view import view_config
from pyramid import httpexceptions as hexc
from pyramid.security import authenticated_userid

from nti.dataserver import users
from nti.dataserver import authorization as nauth

from nti.externalization.datastructures import LocatedExternalDict

from . import get_graph_db

@interface.implementer(IPathAdapter, IContained)
class GraphPathAdapter(zcontained.Contained):

	__name__ = 'graphdb'

	def __init__(self, context, request):
		self.context = context
		self.request = request
		self.__parent__ = context

_view_defaults = dict(route_name='objects.generic.traversal',
					  renderer='rest',
					  permission=nauth.ACT_READ,
					  context=GraphPathAdapter,
					  request_method='GET')
_post_view_defaults = _view_defaults.copy()
_post_view_defaults['request_method'] = 'POST'

@view_config(name="suggest_friends", **_view_defaults)
class SuggestFriendsView(object):

	def __init__(self, request):
		self.request = request

	def __call__(self):
		items = []
		request = self.request
		result = LocatedExternalDict({'Items': items})
		db = get_graph_db()
		if db is None:
			return result
		provider = db.provider

		# validate user
		username = request.params.get('username') or  authenticated_userid(request)
		user = users.User.get_user(username)
		if user is None:
			raise hexc.HTTPNotFound("user not found")

		# check other params
		try:
			max_depth = int(request.params.get('max_depth', 2))
			limit = request.params.get('limit', None)
			limit = int(limit) if limit is not None else None
		except:
			raise hexc.HTTPUnprocessableEntity()

		tuples = provider.suggest_friends_to(user, max_depth=max_depth, limit=limit)
		for friend, mutualFriends in tuples:
			items.append({"username": friend, "MutualFriends":mutualFriends})
		return result

