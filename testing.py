##############################################################################
#
# Copyright (c) 2005 Zope Corporation. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Visible Source
# License, Version 1.0 (ZVSL).  A copy of the ZVSL should accompany this
# distribution.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Publisher Hook to ``mechanize``

$Id$
"""
import httplib
import urllib2
from cStringIO import StringIO

import mechanize
import ClientCookie

from zope.app.testing.functional import HTTPCaller
from zope.testbrowser import browser


class PublisherConnection(object):
    """A ``urllib2`` compatible connection obejct."""

    def __init__(self, host):
        self.host = host
        self.caller = HTTPCaller()

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
        handle_errors_key = 'X-zope-handle-errors'
        handle_errors = headers.get(handle_errors_key, True)
        if handle_errors_key in headers:
            del headers[handle_errors_key]

        # Construct the headers.
        header_chunks = []
        if headers is not None:
            for header in headers.items():
                header_chunks.append('%s: %s' % header)
            headers = '\n'.join(header_chunks) + '\n'
        else:
            headers = ''

        # Construct the full HTTP request string, since that is what the
        # ``HTTPCaller`` wants.
        request_string = (method + ' ' + url + ' HTTP/1.1\n'
                          + headers + '\n' + body)
        self.response = self.caller(request_string, handle_errors)

    def getresponse(self):
        """Return a ``urllib2`` compatible response.

        The goal of ths method is to convert the Zope Publisher's reseponse to
        a ``urllib2`` compatible response, which is also understood by
        mechanize.
        """
        real_response = self.response._response
        status = real_response.getStatus()
        reason = real_response._reason # XXX add a getReason method

        headers = real_response.getHeaders()
        headers.sort()
        output = (
            "Status: %s\r\n%s\r\n\r\n%s" % (
            real_response.getStatusString(),
            '\r\n'.join([('%s: %s' % h) for h in headers]),
            real_response.consumeBody(),
            )
            )
        return PublisherResponse(output, status, reason)


class PublisherResponse(object):
    """``urllib2`` compatible response object."""

    def __init__(self, content, status, reason):
        self.content = content
        self.status = status
        self.reason = reason
        self.msg = httplib.HTTPMessage(StringIO(content), 0)
        self.content_as_file = StringIO(content)

    def read(self, amt=None):
        return self.content_as_file.read(amt)


class PublisherHTTPHandler(urllib2.HTTPHandler):
    """Special HTTP handler to use the Zope Publisher."""

    http_request = urllib2.AbstractHTTPHandler.do_request_

    def http_open(self, req):
        """Open an HTTP connection having a ``urllib2`` request."""
        # Here we connect to the publisher.
        return self.do_open(PublisherConnection, req)


class PublisherMechanizeBrowser(mechanize.Browser):
    """Special ``mechanize`` browser using the Zope Publisher HTTP handler."""

    handler_classes = {
        # scheme handlers
        "http": PublisherHTTPHandler,

        "_http_error": ClientCookie.HTTPErrorProcessor,
        "_http_request_upgrade": ClientCookie.HTTPRequestUpgradeProcessor,
        "_http_default_error": urllib2.HTTPDefaultErrorHandler,

        # feature handlers
        "_authen": urllib2.HTTPBasicAuthHandler,
        "_redirect": ClientCookie.HTTPRedirectHandler,
        "_cookies": ClientCookie.HTTPCookieProcessor,
        "_refresh": ClientCookie.HTTPRefreshProcessor,
        "_referer": mechanize.Browser.handler_classes['_referer'],
        "_equiv": ClientCookie.HTTPEquivProcessor,
        "_seek": ClientCookie.SeekableProcessor,
        }

    default_schemes = ["http"]
    default_others = ["_http_error", "_http_request_upgrade",
                      "_http_default_error"]
    default_features = ["_authen", "_redirect", "_cookies", "_seek"]


class Browser(browser.Browser):
    """A Zope ``testbrowser` Browser that uses the Zope Publisher."""

    def __init__(self, url=None):
        mech_browser = PublisherMechanizeBrowser()
        super(Browser, self).__init__(url=url, mech_browser=mech_browser)
