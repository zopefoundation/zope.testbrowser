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
import sys

from webtest import TestApp

import zope.testbrowser.browser
import zope.testbrowser.connection

class HostNotAllowed(Exception):
    pass

_allowed_2nd_level = set(['example.com', 'example.net', 'example.org']) # RFC 2606

_allowed = set(['localhost', '127.0.0.1'])
_allowed.update(_allowed_2nd_level)

class WSGIConnection(object):
    """A ``mechanize`` compatible connection object."""

    _allowed = True

    def __init__(self, test_app, host, timeout=None):
        self._test_app = TestApp(test_app)
        self.host = host
        self.assert_allowed_host()

    def assert_allowed_host(self):
        host = self.host
        if host in _allowed:
            return
        for dom in _allowed_2nd_level:
            if host.endswith('.%s' % dom):
                return
        self._allowed = False

    def set_debuglevel(self, level):
        pass

    def request(self, method, url, body=None, headers=None):
        """Send a request to the publisher.

        The response will be stored in ``self.response``.
        """
        if body is None:
            body = ''

        if url == '':
            url = '/'

        # Extract the handle_error option header
        if sys.version_info >= (2,5):
            handle_errors_key = 'X-Zope-Handle-Errors'
        else:
            handle_errors_key = 'X-zope-handle-errors'
        handle_errors_header = headers.get(handle_errors_key, True)
        if handle_errors_key in headers:
            del headers[handle_errors_key]

        # Translate string to boolean.
        handle_errors = {'False': False}.get(handle_errors_header, True)
        extra_environ = {}
        if not handle_errors:
            # There doesn't seem to be a "Right Way" to do this
            extra_environ['wsgi.handleErrors'] = False # zope.app.wsgi does this
            extra_environ['paste.throw_errors'] = True # the paste way of doing this

        scheme_key = 'X-Zope-Scheme'
        extra_environ['wsgi.url_scheme'] = headers.get(scheme_key, 'http')
        if scheme_key in headers:
            del headers[scheme_key]

        if not self._allowed:
            raise HostNotAllowed('%s://%s%s' % (extra_environ['wsgi.url_scheme'], self.host, url))

        app = self._test_app

        # clear our app cookies so that our testbrowser cookie headers don't
        # get stomped
        app.cookies.clear()

        # pass the request to webtest
        if method == 'GET':
            assert not body, body
            response = app.get(url, headers=headers, expect_errors=True, extra_environ=extra_environ)
        elif method == 'POST':
            response = app.post(url, body, headers=headers, expect_errors=True, extra_environ=extra_environ)
        else:
            raise Exception('Couldnt handle method %s' % method)

        self.response = response

    def getresponse(self):
        """Return a ``mechanize`` compatible response.

        The goal of ths method is to convert the WebTest's reseponse to
        a ``mechanize`` compatible response, which is also understood by
        mechanize.
        """
        response = self.response
        status = int(response.status[:3])
        reason = response.status[4:]

        headers = response.headers.items()
        headers.sort()
        headers.insert(0, ('Status', response.status))
        headers = '\r\n'.join('%s: %s' % h for h in headers)
        # Ugh! WebTest's headers can at times be unicode. That causes weird
        # problems later when they are shoved into a StringIO. So just cast
        # to a string for now using ascii.
        headers = str(headers)
        content = response.body
        return zope.testbrowser.connection.Response(content, headers, status, reason)


class WSGIHTTPHandler(zope.testbrowser.connection.HTTPHandler):

    def __init__(self, test_app, *args, **kw):
        self._test_app = test_app
        zope.testbrowser.connection.HTTPHandler.__init__(self, *args, **kw)

    def _connect(self, *args, **kw):
        return WSGIConnection(self._test_app, *args, **kw)

    def https_request(self, req):
        req.add_unredirected_header('X-Zope-Scheme', 'https')
        return self.http_request(req)


class WSGIMechanizeBrowser(zope.testbrowser.connection.MechanizeBrowser):
    """Special ``mechanize`` browser using the WSGI HTTP handler."""

    def __init__(self, test_app, *args, **kw):
        self._test_app = test_app
        zope.testbrowser.connection.MechanizeBrowser.__init__(self, *args, **kw)

    def _http_handler(self, *args, **kw):
        return WSGIHTTPHandler(self._test_app, *args, **kw)


class Browser(zope.testbrowser.browser.Browser):
    """A WSGI `testbrowser` Browser that uses a WebTest wrapped WSGI app."""

    def __init__(self, url=None, wsgi_app=None):
        if wsgi_app is None:
            wsgi_app = Layer.get_app()
        if wsgi_app is None:
            raise AssertionError("wsgi_app not provided or zope.testbrowser.wsgi.Layer not setup")
        mech_browser = WSGIMechanizeBrowser(wsgi_app)
        super(Browser, self).__init__(url=url, mech_browser=mech_browser)

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
