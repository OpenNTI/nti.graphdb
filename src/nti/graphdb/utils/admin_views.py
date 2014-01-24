#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
nti.graphdb initialization

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import simplejson as json

from zope import component

from pyramid.view import view_config
import pyramid.httpexceptions as hexc

from nti.dataserver import users
from nti.dataserver import authorization as nauth
from nti.dataserver import interfaces as nti_interfaces

from nti.utils.maps import CaseInsensitiveDict

from .. import ratings
from .. import threadables
from .. import assessments
from .. import connections
from .. import discussions
from .. import interfaces as graph_interfaces

def _make_min_max_btree_range(search_term):
	min_inclusive = search_term # start here
	max_exclusive = search_term[0:-1] + unichr(ord(search_term[-1]) + 1)
	return min_inclusive, max_exclusive

def username_search(search_term):
	min_inclusive, max_exclusive = _make_min_max_btree_range(search_term)
	dataserver = component.getUtility(nti_interfaces.IDataserver)
	_users = nti_interfaces.IShardLayout(dataserver).users_folder
	usernames = list(_users.iterkeys(min_inclusive, max_exclusive, excludemax=True))
	return usernames

def init(db, entity):
	ratings.init(db, entity)
	threadables.init(db, entity)
	connections.init(db, entity)
	discussions.init(db, entity)
	assessments.init(db, entity)

def init_db(db, usernames=()):
	for username in usernames:
		entity = users.Entity.get_entity(username)
		if entity is not None:
			init(db, entity)

@view_config(route_name='objects.generic.traversal',
			 name='init_graphdb',
			 request_method='POST',
			 permission=nauth.ACT_MODERATE)
def init_graphdb(request):
	values = json.loads(unicode(request.body, request.charset)) if request.body else {}
	values = CaseInsensitiveDict(values)
	site = values.get('site', u'')
	term = values.get('term', values.get('search', None))
	usernames = values.get('usernames', values.get('username', None))
	if term:
		usernames = username_search(term)
	elif usernames:
		usernames = usernames.split()
	else:
		dataserver = component.getUtility(nti_interfaces.IDataserver)
		_users = nti_interfaces.IShardLayout(dataserver).users_folder
		usernames = _users.iterkeys()
	db = component.getUtility(graph_interfaces.IGraphDB, name=site)
	init_db(db, usernames)
	return hexc.HTTPNoContent()
