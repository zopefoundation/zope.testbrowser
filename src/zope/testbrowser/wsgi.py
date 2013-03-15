##############################################################################
#
# Copyright (c) 2010-2011 Zope Foundation and Contributors.
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
"""WSGI-specific testing code
"""

import base64
import re

import zope.testbrowser.browser

from zope.testbrowser.browser import HostNotAllowed # BBB

class Browser(zope.testbrowser.browser.Browser):
    def __init__(self, url=None, wsgi_app=None):
         if wsgi_app is None:
             wsgi_app = Layer.get_app()
         if wsgi_app is None:
             raise AssertionError("wsgi_app not provided or zope.testbrowser.wsgi.Layer not setup")
         super(Browser, self).__init__(url, wsgi_app)

basicre = re.compile('Basic (.+)?:(.+)?$')


def auth_header(header):
    """This function takes an authorization HTTP header and encode the
    couple user, password into base 64 like the HTTP protocol wants
    it.
    """
    match = basicre.match(header)
    if match:
        u, p = match.group(1, 2)
        if u is None:
            u = ''
        if p is None:
            p = ''
        plain = '%s:%s' % (u, p)
        auth = base64.encodestring(plain.encode('utf-8'))
        return 'Basic %s' % str(auth.rstrip().decode('latin1'))
    return header


def is_wanted_header(header):
    """Return True if the given HTTP header key is wanted.
    """
    key, value = header
    return key.lower() not in ('x-content-type-warning', 'x-powered-by')


class AuthorizationMiddleware(object):
    """This middleware makes the WSGI application compatible with the
    HTTPCaller behavior defined in zope.app.testing.functional:
    - It modifies the HTTP Authorization header to encode user and
      password into base64 if it is Basic authentication.
    """

    def __init__(self, wsgi_stack):
        self.wsgi_stack = wsgi_stack

    def __call__(self, environ, start_response):
        # Handle authorization
        auth_key = 'HTTP_AUTHORIZATION'
        if auth_key in environ:
            environ[auth_key] = auth_header(environ[auth_key])

        # Remove unwanted headers
        def application_start_response(status, headers, exc_info=None):
            headers = filter(is_wanted_header, headers)
            start_response(status, headers)

        for entry in self.wsgi_stack(environ, application_start_response):
            yield entry


_APP_UNDER_TEST = None # setup and torn down by the Layer class

class Layer(object):
    """Test layer which sets up WSGI application for use with
    WebTest/testbrowser.

    """

    __bases__ = ()
    __name__ = 'Layer'

    @classmethod
    def get_app(cls):
        return _APP_UNDER_TEST

    def make_wsgi_app(self):
        # Override this method in subclasses of this layer in order to set up
        # the WSGI application.
        raise NotImplementedError

    def cooperative_super(self, method_name):
        # Calling `super` for multiple inheritance:
        method = getattr(super(Layer, self), method_name, None)
        if method is not None:
            method()

    def setUp(self):
        self.cooperative_super('setUp')
        global _APP_UNDER_TEST
        if _APP_UNDER_TEST is not None:
            raise AssertionError("Already Setup")
        _APP_UNDER_TEST = self.make_wsgi_app()

    def tearDown(self):
        global _APP_UNDER_TEST
        _APP_UNDER_TEST = None
        self.cooperative_super('tearDown')
