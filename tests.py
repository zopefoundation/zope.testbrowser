##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Real test for file-upload and beginning of a better internal test framework

$Id$
"""

import unittest
import httplib
import re
import urllib2
from cStringIO import StringIO

import mechanize
import ClientCookie

from zope.testbrowser import browser
from zope.testing import renormalizing, doctest


def set_next_response(body, headers=None, status='200', reason='OK'):
    global next_response_body
    global next_response_headers
    global next_response_status
    global next_response_reason
    if headers is None:
        headers = (
            'Content-Type: text/html\r\n'
            'Content-Length: %s\r\n'
            % len(body)
            )
    next_response_body = body
    next_response_headers = headers
    next_response_status = status
    next_response_reason = reason


class FauxConnection(object):
    """A ``urllib2`` compatible connection obejct."""

    def __init__(self, host):
        pass

    def set_debuglevel(self, level):
        pass

    def _quote(self, url):
        # the publisher expects to be able to split on whitespace, so we have
        # to make sure there is none in the URL
        return url.replace(' ', '%20')


    def request(self, method, url, body=None, headers=None):
        if body is None:
            body = ''

        if url == '':
            url = '/'

        url = self._quote(url)

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

        print request_string.replace('\r', '')

    def getresponse(self):
        """Return a ``urllib2`` compatible response.

        The goal of ths method is to convert the Zope Publisher's reseponse to
        a ``urllib2`` compatible response, which is also understood by
        mechanize.
        """
        return FauxResponse(next_response_body,
                            next_response_headers,
                            next_response_status,
                            next_response_reason,
                            )

class FauxResponse(object):

    def __init__(self, content, headers, status, reason):
        self.content = content
        self.status = status
        self.reason = reason
        self.msg = httplib.HTTPMessage(StringIO(headers), 0)
        self.content_as_file = StringIO(self.content)

    def read(self, amt=None):
        return self.content_as_file.read(amt)


class FauxHTTPHandler(urllib2.HTTPHandler):

    http_request = urllib2.AbstractHTTPHandler.do_request_

    def http_open(self, req):
        """Open an HTTP connection having a ``urllib2`` request."""
        # Here we connect to the publisher.
        return self.do_open(FauxConnection, req)


class FauxMechanizeBrowser(mechanize.Browser):

    handler_classes = {
        # scheme handlers
        "http": FauxHTTPHandler,

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

    def __init__(self, url=None):
        mech_browser = FauxMechanizeBrowser()
        super(Browser, self).__init__(url=url, mech_browser=mech_browser)

    def open(self, body, headers=None, status=200, reason='OK'):
        set_next_response(body, headers, status, reason)
        browser.Browser.open(self, 'http://localhost/')

def test_file_upload():
    """
    
    >>> browser = Browser()

When given a form with a file-upload

    >>> browser.open('''\
    ... <html><body>
    ...   <form action="." method="post" enctype="multipart/form-data">
    ...      <input name="foo" type="file" />
    ...      <input type="submit" value="OK" />
    ...   </form></body></html>
    ... ''') # doctest: +ELLIPSIS
    GET / HTTP/1.1
    ...

Fill in the form value using add_file:

    >>> browser.getControl(name='foo').add_file(
    ...     StringIO('sample_data'), 'text/foo', 'x.foo')
    >>> browser.getControl('OK').click()
    POST / HTTP/1.1
    Content-length: 173
    Connection: close
    Content-type: multipart/form-data; boundary=127.0.0.11000318041146699896411
    Host: localhost
    User-agent: Python-urllib/2.99
    <BLANKLINE>
    --127.0.0.11000318041146699896411
    Content-disposition: form-data; name="foo"; filename="x.foo"
    Content-type: text/foo
    <BLANKLINE>
    sample_data
    --127.0.0.11000318041146699896411--
    <BLANKLINE>

You can pass s atring to add_file:


    >>> browser.getControl(name='foo').add_file(
    ...     'blah blah blah', 'text/blah', 'x.blah')
    >>> browser.getControl('OK').click()
    POST / HTTP/1.1
    Content-length: 178
    Connection: close
    Content-type: multipart/form-data; boundary=127.0.0.11000318541146700017052
    Host: localhost
    User-agent: Python-urllib/2.98
    <BLANKLINE>
    --127.0.0.11000318541146700017052
    Content-disposition: form-data; name="foo"; filename="x.blah"
    Content-type: text/blah
    <BLANKLINE>
    blah blah blah
    --127.0.0.11000318541146700017052--
    <BLANKLINE>


    """

checker = renormalizing.RENormalizing([
    (re.compile('127.0.0.\S+'), '-'*30),
    (re.compile('User-agent:\s+\S+'), 'User-agent: XXX'),
    ])

def test_suite():
    from zope.testing import doctest
    return unittest.TestSuite((
        doctest.DocTestSuite(checker=checker),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

