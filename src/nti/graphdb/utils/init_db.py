#!/usr/bin/env python
"""
nti.graphdb initialization

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import simplejson as json

from zope import component

from pyramid.view import view_config
import pyramid.httpexceptions as hexc

from nti.dataserver import authorization as nauth

from nti.graphdb import modeled
from nti.graphdb import ratings
from nti.graphdb import assessments
from nti.graphdb import connections
from nti.graphdb import discussions
from nti.graphdb import interfaces as graph_interfaces

from nti.utils.maps import CaseInsensitiveDict

def init_db(db, usernames=()):
	modeled.install(db, usernames)
	ratings.install(db, usernames)
	discussions.install(db, usernames)
	connections.install(db, usernames)
	assessments.install(db, usernames)

@view_config(route_name='objects.generic.traversal',
			 name='init_graphdb',
			 request_method='POST',
			 permission=nauth.ACT_MODERATE)
def init_graphdb(request):
	values = json.loads(unicode(request.body, request.charset)) if request.body else {}
	values = CaseInsensitiveDict(**values)
	site = values.get('site', u'')
	usernames = values.get('usernames', values.get('username', u''))
	if isinstance(usernames,six.string_types):
		usernames = usernames.split()
	db = component.getUtility(graph_interfaces.IGraphDB, name=site)
	init_db(db, usernames)
	return hexc.HTTPNoContent()
