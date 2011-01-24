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
import base64
import re
import wsgi_intercept
import wsgi_intercept.mechanize_intercept
import zope.testbrowser.browser


# List of hostname where the test browser/http function replies to
TEST_HOSTS = ['localhost', '127.0.0.1']


class InterceptBrowser(wsgi_intercept.mechanize_intercept.Browser):

    default_schemes = ['http']
    default_others = ['_http_error',
                      '_http_default_error']
    default_features = ['_redirect', '_cookies', '_referer', '_refresh',
                        '_equiv', '_basicauth', '_digestauth']


class Browser(zope.testbrowser.browser.Browser):
    """Override the zope.testbrowser.browser.Browser interface so that it
    uses InterceptBrowser.
    """

    def __init__(self, *args, **kw):
        kw['mech_browser'] = InterceptBrowser()
        super(Browser, self).__init__(*args, **kw)


# Compatibility helpers to behave like zope.app.testing

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
        auth = base64.encodestring('%s:%s' % (u, p))
        return 'Basic %s' % auth[:-1]
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


class Layer(object):
    """Test layer which sets up WSGI application for use with
    wsgi_intercept/testbrowser.

    """

    __bases__ = ()
    __name__ = 'Layer'

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
        self.app = self.make_wsgi_app()
        factory = lambda: AuthorizationMiddleware(self.app)

        for host in TEST_HOSTS:
            wsgi_intercept.add_wsgi_intercept(host, 80, factory)

    def tearDown(self):
        for host in TEST_HOSTS:
            wsgi_intercept.remove_wsgi_intercept(host, 80)
        self.cooperative_super('tearDown')
