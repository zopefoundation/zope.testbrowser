##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""A minimal WSGI application used as a test fixture."""

import os
import mimetypes
from datetime import datetime

from webob import Request, Response
from zope.pagetemplate.pagetemplatefile import PageTemplateFile

from zope.testbrowser import ftests

class NotFound(Exception):

    def __init__(self, ob, name):
        self.ob = ob
        self.name = name

    def __str__(self):
        return 'Object: %s, name: %r' % (self.ob, self.name)


class ZopeRequestAdapter(object):
    """Adapt a webob request into enough of a zope.publisher request for the tests to pass"""

    def __init__(self, request, response=None):
        self._request = request
        self._response = response

    @property
    def form(self):
        return self._request.params

    def __getitem__(self, name):
        return self._request.params[name]

_HERE = os.path.dirname(__file__)

class MyPageTemplateFile(PageTemplateFile):

    def pt_getContext(self, args, *extra_args, **kw):
        request = args[0]
        namespace = super(MyPageTemplateFile, self).pt_getContext(args, *extra_args, **kw)
        namespace['request'] = request
        return namespace

class WSGITestApplication(object):

    def __call__(self, environ, start_response):
        req = Request(environ)
        handler = {'/set_status.html': set_status,
                   '/@@echo.html': echo,
                   '/echo_one.html': echo_one,
                   '/set_cookie.html': set_cookie,
                   '/get_cookie.html': get_cookie,
                   '/inner/set_cookie.html': set_cookie,
                   '/inner/get_cookie.html': get_cookie,
                   '/inner/path/set_cookie.html': set_cookie,
                   '/inner/path/get_cookie.html': get_cookie,
                   }.get(req.path_info)
        if handler is None and req.path_info.startswith('/@@/testbrowser/'):
            handler = handle_resource
        if handler is None:
            handler = handle_notfound
        try:
            resp = handler(req)
        except Exception, exc:
            if not environ.get('wsgi.handleErrors', True):
                raise
            resp = Response()
            resp.status = {NotFound: 404}.get(type(exc), 500)
        resp.headers.add('X-Powered-By', 'Zope (www.zope.org), Python (www.python.org)')
        return resp(environ, start_response)

def handle_notfound(req):
    raise NotFound('<WSGI application>', unicode(req.path_info[1:]))

def handle_resource(req):
    filename = req.path_info.split('/')[-1]
    type, _ = mimetypes.guess_type(filename)
    path = os.path.join(_HERE, filename)
    if type == 'text/html':
        pt = MyPageTemplateFile(path)
        zreq = ZopeRequestAdapter(req)
        contents = pt(zreq)
    else:
        contents = open(path, 'r').read()
    return Response(contents, content_type=type)

def get_cookie(req):
    cookies = ['%s: %s' % i for i in sorted(req.cookies.items())]
    return Response('\n'.join(cookies))
    
def set_cookie(req):
    cookie_parms = {'path': None}
    cookie_parms.update(dict((str(k), str(v)) for k, v in req.params.items()))
    name = cookie_parms.pop('name')
    value = cookie_parms.pop('value')
    if 'max-age' in cookie_parms:
        cookie_parms['max_age'] = int(cookie_parms.pop('max-age'))
    if 'expires' in cookie_parms:
        cookie_parms['expires'] = datetime.strptime(cookie_parms.pop('expires'), '%a, %d %b %Y %H:%M:%S GMT')
    resp = Response()
    resp.set_cookie(name, value, **cookie_parms)
    return resp

def echo(req):
    items = []
    for k in ftests._interesting_environ:
        v = req.environ.get(k, None)
        if v is None:
            continue
        items.append('%s: %s' % (k, v))
    items.extend('%s: %s' % x for x in sorted(req.params.items())) 
    if req.method == 'POST' and req.content_type == 'application/x-www-form-urlencoded':
        body = ''
    else:
        body = req.body
    items.append('Body: %r' % body)
    return Response('\n'.join(items))

def echo_one(req):
    resp = repr(req.environ.get(req.params['var']))
    return Response(resp)

def set_status(req):
    status = req.params.get('status')
    if status:
        resp = Response('Just set a status of %s' % status)
        resp.status = int(status)
        return resp
    return Response('Everything fine')
