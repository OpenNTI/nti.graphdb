#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time
import simplejson as json

import zope.intid
from zope import component

from pyramid.view import view_config
import pyramid.httpexceptions as hexc

from nti.dataserver import authorization as nauth
from nti.dataserver import interfaces as nti_interfaces

from nti.externalization.oids import to_external_oid
from nti.externalization.datastructures import LocatedExternalDict

from nti.utils.maps import CaseInsensitiveDict

from . import views
from . import ratings
from . import sharing
from . import entities
from . import flagging
from . import threadables
from . import assessments
from . import connections
from . import discussions
from . import interfaces as graph_interfaces

from .async.reactor import JobReactor
from .async import interfaces as async_interfaces

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

def all_objects_iids(users=()):
	intids = component.getUtility(zope.intid.IIntIds)
	usernames = {getattr(user, 'username', user) for user in users or ()}
	for uid, obj in intids.items():
		try:
			if nti_interfaces.IEntity.providedBy(obj):
				if not usernames or obj.username in usernames:
					yield uid, obj
			else:
				creator = getattr(obj, 'creator', None)
				if not usernames or getattr(creator, 'username', creator) in usernames:
					yield uid, obj
		except TypeError as e:
			oid = to_external_oid(obj)
			logger.error("Error getting creator for %s(%s,%s). %s",
						 type(obj), uid, oid, e)

def init(db, obj):
	result = False
	for module in (entities, connections, threadables, sharing, flagging,
				   ratings, discussions, assessments):
		result = module.init(db, obj) or result
	return result

def init_db(db, usernames=()):
	count = 0
	for _, obj in all_objects_iids(usernames):
		if init(db, obj):
			count += 1
	return count

@view_config(route_name='objects.generic.traversal',
			 name='init_graphdb',
			 renderer='rest',
			 request_method='POST',
			 context=views.GraphPathAdapter,
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
		usernames = ()
	db = component.getUtility(graph_interfaces.IGraphDB, name=site)

	now = time.time()
	total = init_db(db, usernames)

	result = LocatedExternalDict()
	result['Elapsed'] = time.time() - now
	result['Total'] = total
	return result

@view_config(route_name='objects.generic.traversal',
			 name='start_reactor',
			 request_method='POST',
			 context=views.GraphPathAdapter,
			 permission=nauth.ACT_MODERATE)
def start_reactor(request):
	reactor = component.queryUtility(async_interfaces.IJobReactor)
	if reactor is not None:
		if reactor.isRunning:
			return hexc.HTTPConflict(detail="Reactor already running")
		else:
			component.getSiteManager().unregisterUtility(reactor, async_interfaces.IJobReactor)

	reactor = JobReactor()
	component.provideUtility(reactor, async_interfaces.IJobReactor)
	request.nti_gevent_spawn(reactor)
	return hexc.HTTPNoContent()
