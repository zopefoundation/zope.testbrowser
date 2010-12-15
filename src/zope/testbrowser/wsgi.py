##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
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
"""Zope 3-specific testing code
"""
import cStringIO
import Cookie
import httplib
import mechanize
import socket
import sys
import zope.testbrowser.browser


class TestAppConnection(object):
    """A ``mechanize`` compatible connection object."""

    def __init__(self, test_app, host, timeout=None):
        self._test_app = test_app
        self.host = host

    def set_debuglevel(self, level):
        pass

    def _quote(self, url):
        # the publisher expects to be able to split on whitespace, so we have
        # to make sure there is none in the URL
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

        app = self._test_app

        # Here we do a complicated dance to sync the webtest apps idea of what
        # cookies there are with the testbrowsers. It's not quite perfect as
        # they can still get un-synced if you don't execute a request via the
        # testbrowser. But that's a veryvery edge case.
        app.cookies.clear()
        for h, v in headers.items():
            if h.lower() == 'cookie':
                cookies = Cookie.SimpleCookie()
                cookies.load(v)
                for key, morsel in cookies.items():
                    app.cookies[key] = morsel.value
                break

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

        The goal of ths method is to convert the Zope Publisher's reseponse to
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
        return PublisherResponse(content, headers, status, reason)


class PublisherResponse(object):
    """``mechanize`` compatible response object."""

    def __init__(self, content, headers, status, reason):
        self.content = content
        self.status = status
        self.reason = reason
        self.msg = httplib.HTTPMessage(cStringIO.StringIO(headers), 0)
        self.content_as_file = cStringIO.StringIO(self.content)

    def read(self, amt=None):
        return self.content_as_file.read(amt)

    def close(self):
        """To overcome changes in mechanize and socket in python2.5"""
        pass


class PublisherHTTPHandler(mechanize.HTTPHandler):
    """Special HTTP handler to use the Zope Publisher."""

    def __init__(self, test_app, *args, **kw):
        mechanize.HTTPHandler.__init__(self, *args, **kw)
        self._test_app = test_app

    def http_request(self, req):
        # look at data and set content type
        if req.has_data():
            data = req.get_data()
            if isinstance(data, dict):
                req.add_data(data['body'])
                req.add_unredirected_header('Content-type',
                                            data['content-type'])
        return mechanize.HTTPHandler.do_request_(self, req)

    https_request = http_request

    def http_open(self, req):
        """Open an HTTP connection having a ``mechanize`` request."""
        # Here we connect to the publisher.
        if sys.version_info > (2, 6) and not hasattr(req, 'timeout'):
            # Workaround mechanize incompatibility with Python
            # 2.6. See: LP #280334
            req.timeout = socket._GLOBAL_DEFAULT_TIMEOUT
        def do_open(*args, **kw):
            return TestAppConnection(self._test_app, *args, **kw)
        return self.do_open(do_open, req)

    https_open = http_open


class PublisherMechanizeBrowser(mechanize.Browser):
    """Special ``mechanize`` browser using the Zope Publisher HTTP handler."""

    default_schemes = ['http']
    default_others = ['_http_error', '_http_default_error']
    default_features = ['_redirect', '_cookies', '_referer', '_refresh',
                        '_equiv', '_basicauth', '_digestauth']

    def __init__(self, test_app, *args, **kws):
        inherited_handlers = ['_unknown', '_http_error',
            '_http_default_error', '_basicauth',
            '_digestauth', '_redirect', '_cookies', '_referer',
            '_refresh', '_equiv', '_gzip']

        def http_handler(*args, **kw):
            return PublisherHTTPHandler(test_app, *args, **kw)

        self.handler_classes = {"http": http_handler}
        for name in inherited_handlers:
            self.handler_classes[name] = mechanize.Browser.handler_classes[name]

        kws['request_class'] = kws.get('request_class',
                                       mechanize._request.Request)

        mechanize.Browser.__init__(self, *args, **kws)


class Browser(zope.testbrowser.browser.Browser):
    """A Zope `testbrowser` Browser that uses the Zope Publisher."""

    def __init__(self, test_app, url=None):
        mech_browser = PublisherMechanizeBrowser(test_app)
        super(Browser, self).__init__(url=url, mech_browser=mech_browser)
