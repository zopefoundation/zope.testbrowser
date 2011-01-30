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
"""WSGI-specific testing code
"""

from __future__ import absolute_import

import cStringIO
import Cookie
import httplib
import socket
import sys

import mechanize
from webtest import TestApp

import zope.testbrowser.browser
import zope.testbrowser.connection

class WSGIConnection(object):
    """A ``mechanize`` compatible connection object."""

    def __init__(self, test_app, host, timeout=None):
        self._test_app = TestApp(test_app)
        self.host = host

    def set_debuglevel(self, level):
        pass

    def _quote(self, url):
        # XXX: is this necessary with WebTest? Was cargeo-culted from the 
        # Zope Publisher Connection
        return url.replace(' ', '%20')

    def request(self, method, url, body=None, headers=None):
        """Send a request to the publisher.

        The response will be stored in ``self.response``.
        """
        if body is None:
            body = ''

        if url == '':
            url = '/'

        url = self._quote(url)

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

    def __init__(self, test_app, url=None):
        mech_browser = WSGIMechanizeBrowser(test_app)
        super(Browser, self).__init__(url=url, mech_browser=mech_browser)
