##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
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
"""Real test for file-upload and beginning of a better internal test framework
"""
import unittest

import cStringIO
import doctest
import httplib
import mechanize
import os
import re
import socket
import sys

from zope.app.testing.functional import FunctionalDocFileSuite
import zope.app.testing.functional
import zope.testbrowser.browser
import zope.testing.renormalizing


def set_next_response(body, headers=None, status='200', reason='OK'):
    global next_response_body
    global next_response_headers
    global next_response_status
    global next_response_reason
    if headers is None:
        headers = (
            'Content-Type: text/html\r\n'
            'Content-Length: %s\r\n'
            % len(body))
    next_response_body = body
    next_response_headers = headers
    next_response_status = status
    next_response_reason = reason


class FauxConnection(object):
    """A ``mechanize`` compatible connection object."""

    def __init__(self, host, timeout=None):
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
        """Return a ``mechanize`` compatible response.

        The goal of this method is to convert the Zope Publisher's response to
        a ``mechanize`` compatible response, which is also understood by
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
        self.msg = httplib.HTTPMessage(cStringIO.StringIO(headers), 0)
        self.content_as_file = cStringIO.StringIO(self.content)

    def read(self, amt=None):
        return self.content_as_file.read(amt)

    def close(self):
        """To overcome changes in mechanize and socket in python2.5"""
        pass


class FauxHTTPHandler(mechanize.HTTPHandler):

    http_request = mechanize.HTTPHandler.do_request_

    def http_open(self, req):
        """Open an HTTP connection having a ``mechanize`` request."""
        # Here we connect to the publisher.

        if sys.version_info > (2, 6) and not hasattr(req, 'timeout'):
            # Workaround mechanize incompatibility with Python
            # 2.6. See: LP #280334
            req.timeout = socket._GLOBAL_DEFAULT_TIMEOUT
        return self.do_open(FauxConnection, req)


class FauxMechanizeBrowser(mechanize.Browser):

    handler_classes = {
        # scheme handlers
        "http": FauxHTTPHandler,

        "_http_error": mechanize.HTTPErrorProcessor,
        "_http_default_error": mechanize.HTTPDefaultErrorHandler,

        # feature handlers
        "_authen": mechanize.HTTPBasicAuthHandler,
        "_redirect": mechanize.HTTPRedirectHandler,
        "_cookies": mechanize.HTTPCookieProcessor,
        "_refresh": mechanize.HTTPRefreshProcessor,
        "_referer": mechanize.Browser.handler_classes['_referer'],
        "_equiv": mechanize.HTTPEquivProcessor,
        }

    default_schemes = ["http"]
    default_others = ["_http_error", "_http_default_error"]
    default_features = ["_authen", "_redirect", "_cookies"]


class Browser(zope.testbrowser.browser.Browser):

    def __init__(self, url=None):
        mech_browser = FauxMechanizeBrowser()
        super(Browser, self).__init__(url=url, mech_browser=mech_browser)

    def open(self, body, headers=None, status=200, reason='OK',
             url='http://localhost/'):
        set_next_response(body, headers, status, reason)
        zope.testbrowser.browser.Browser.open(self, url)


def test_submit_duplicate_name():
    """
    This test was inspired by bug #723 as testbrowser would pick up the wrong
    button when having the same name twice in a form.

    >>> browser = Browser()


    When given a form with two submit buttons that have the same name:

    >>> browser.open('''\
    ... <html><body>
    ...   <form action="." method="post" enctype="multipart/form-data">
    ...      <input type="submit" name="submit_me" value="GOOD" />
    ...      <input type="submit" name="submit_me" value="BAD" />
    ...   </form></body></html>
    ... ''') # doctest: +ELLIPSIS
    GET / HTTP/1.1
    ...


    We can specify the second button through it's label/value:

    >>> browser.getControl('BAD')
    <SubmitControl name='submit_me' type='submit'>
    >>> browser.getControl('BAD').value
    'BAD'
    >>> browser.getControl('BAD').click() # doctest: +REPORT_NDIFF +ELLIPSIS
    POST / HTTP/1.1
    ...
    Content-type: multipart/form-data; ...
    Content-disposition: form-data; name="submit_me"
    <BLANKLINE>
    BAD
    ...


    This also works if the labels have whitespace around them (this tests a
    regression caused by the original fix for the above):

    >>> browser.open('''\
    ... <html><body>
    ...   <form action="." method="post" enctype="multipart/form-data">
    ...      <input type="submit" name="submit_me" value=" GOOD " />
    ...      <input type="submit" name="submit_me" value=" BAD " />
    ...   </form></body></html>
    ... ''') # doctest: +ELLIPSIS
    GET / HTTP/1.1
    ...
    >>> browser.getControl('BAD')
    <SubmitControl name='submit_me' type='submit'>
    >>> browser.getControl('BAD').value
    ' BAD '
    >>> browser.getControl('BAD').click() # doctest: +REPORT_NDIFF +ELLIPSIS
    POST / HTTP/1.1
    ...
    Content-type: multipart/form-data; ...
    Content-disposition: form-data; name="submit_me"
    <BLANKLINE>
     BAD 
    ...
"""


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
    ...     cStringIO.StringIO('sample_data'), 'text/foo', 'x.foo')
    >>> browser.getControl('OK').click() # doctest: +REPORT_NDIFF +ELLIPSIS
    POST / HTTP/1.1
    ...
    Content-type: multipart/form-data; ...
    Content-disposition: form-data; name="foo"; filename="x.foo"
    Content-type: text/foo
    <BLANKLINE>
    sample_data
    ...


    You can pass a string to add_file:

    >>> browser.getControl(name='foo').add_file(
    ...     'blah blah blah', 'text/blah', 'x.blah')
    >>> browser.getControl('OK').click() # doctest: +REPORT_NDIFF +ELLIPSIS
    POST / HTTP/1.1
    ...
    Content-type: multipart/form-data; ...
    Content-disposition: form-data; name="foo"; filename="x.blah"
    Content-type: text/blah
    <BLANKLINE>
    blah blah blah
    ...
    """

def test_submit_gets_referrer():
    """
    Test for bug #98437: No HTTP_REFERER was sent when submitting a form.

    >>> browser = Browser()


    A simple form for testing, like abobe.

    >>> browser.open('''\
    ... <html><body>
    ...   <form id="form" action="." method="post"
    ...                   enctype="multipart/form-data">
    ...      <input type="submit" name="submit_me" value="GOOD" />
    ...   </form></body></html>
    ... ''') # doctest: +ELLIPSIS
    GET / HTTP/1.1
    ...


    Now submit the form, and see that we get an referrer along:

    >>> form = browser.getForm(id='form')
    >>> form.submit(name='submit_me') # doctest: +ELLIPSIS
    POST / HTTP/1.1
    ...
    Referer: http://localhost/
    ...
"""


def test_new_instance_no_contents_should_not_fail(self):
    """
    When first instantiated, the browser has no contents.
    (Regression test for <http://bugs.launchpad.net/zope3/+bug/419119>)

    >>> browser = Browser()
    >>> print browser.contents
    None
    """


def test_strip_linebreaks_from_textarea(self):
    """
    >>> browser = Browser()

    According to http://www.w3.org/TR/html4/appendix/notes.html#h-B.3.1 line
    break immediately after start tags or immediately before end tags must be
    ignored, but real browsers only ignore a line break after a start tag.
    So if we give the following form:

    >>> browser.open('''
    ... <html><body>
    ...   <form action="." method="post" enctype="multipart/form-data">
    ...      <textarea name="textarea">
    ... Foo
    ... </textarea>
    ...   </form></body></html>
    ... ''') # doctest: +ELLIPSIS
    GET / HTTP/1.1
    ...


    The value of the textarea won't contain the first line break:

    >>> browser.getControl(name='textarea').value
    'Foo\\n'


    Of course, if we add line breaks, so that there are now two line breaks
    after the start tag, the textarea value will start and end with a line
    break.

    >>> browser.open('''
    ... <html><body>
    ...   <form action="." method="post" enctype="multipart/form-data">
    ...      <textarea name="textarea">
    ...
    ... Foo
    ... </textarea>
    ...   </form></body></html>
    ... ''') # doctest: +ELLIPSIS
    GET / HTTP/1.1
    ...

    >>> browser.getControl(name='textarea').value
    '\\nFoo\\n'


    Also, if there is some other whitespace after the start tag, it will be
    preserved.

    >>> browser.open('''
    ... <html><body>
    ...   <form action="." method="post" enctype="multipart/form-data">
    ...      <textarea name="textarea">  Foo  </textarea>
    ...   </form></body></html>
    ... ''') # doctest: +ELLIPSIS
    GET / HTTP/1.1
    ...

    >>> browser.getControl(name='textarea').value
    '  Foo  '
    """


def test_relative_link():
    """
    RFC 1808 specifies how relative URLs should be resolved, let's see
    that we conform to it. Let's start with a simple example.

    >>> browser = Browser()
    >>> browser.open('''\
    ... <html><body>
    ...     <a href="foo">link</a>
    ... </body></html>
    ... ''', url='http://localhost/bar') # doctest: +ELLIPSIS
    GET /bar HTTP/1.1
    ...

    >>> link = browser.getLink('link')
    >>> link.url
    'http://localhost/foo'


    It's possible to have a relative URL consisting of only a query part. In
    that case it should simply be appended to the base URL.

    >>> browser.open('''\
    ... <html><body>
    ...     <a href="?key=value">link</a>
    ... </body></html>
    ... ''', url='http://localhost/bar') # doctest: +ELLIPSIS
    GET /bar HTTP/1.1
    ...

    >>> link = browser.getLink('link')
    >>> link.url
    'http://localhost/bar?key=value'


    In the example above, the base URL was the page URL, but we can also
    specify a base URL using a <base> tag.

    >>> browser.open('''\
    ... <html><head><base href="http://localhost/base" /></head><body>
    ...     <a href="?key=value">link</a>
    ... </body></html>
    ... ''', url='http://localhost/base/bar') # doctest: +ELLIPSIS
    GET /base/bar HTTP/1.1
    ...

    >>> link = browser.getLink('link')
    >>> link.url
    'http://localhost/base?key=value'
    """


class win32CRLFtransformer(object):
    def sub(self, replacement, text):
        return text.replace(r'\r', '')

checker = zope.testing.renormalizing.RENormalizing([
    (re.compile(r'^--\S+\.\S+\.\S+', re.M), '-' * 30),
    (re.compile(r'boundary=\S+\.\S+\.\S+'), 'boundary=' + '-' * 30),
    (re.compile(r'^---{10}.*', re.M), '-' * 30),
    (re.compile(r'boundary=-{10}.*'), 'boundary=' + '-' * 30),
    (re.compile(r'User-agent:\s+\S+'), 'User-agent: Python-urllib/2.4'),
    (re.compile(r'HTTP_USER_AGENT:\s+\S+'),
     'HTTP_USER_AGENT: Python-urllib/2.4'),
    (re.compile(r'Content-[Ll]ength:.*'), 'Content-Length: 123'),
    (re.compile(r'Status: 200.*'), 'Status: 200 OK'),
    (win32CRLFtransformer(), None),
    (re.compile(r'User-Agent: Python-urllib/2.5'),
     'User-agent: Python-urllib/2.4'),
    (re.compile(r'User-Agent: Python-urllib/2.6'),
     'User-agent: Python-urllib/2.4'),
    (re.compile(r'Host: localhost'), 'Connection: close'),
    (re.compile(r'Content-Type: '), 'Content-type: '),
    (re.compile(r'Content-Disposition: '), 'Content-disposition: '),
    ])

TestBrowserLayer = zope.app.testing.functional.ZCMLLayer(
    os.path.join(os.path.split(__file__)[0], 'ftests/ftesting.zcml'),
    __name__, 'TestBrowserLayer', allow_teardown=True)


def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS

    readme = FunctionalDocFileSuite('README.txt', optionflags=flags,
        checker=checker)
    readme.layer = TestBrowserLayer

    cookies = FunctionalDocFileSuite('cookies.txt', optionflags=flags,
        checker=checker)
    cookies.layer = TestBrowserLayer

    fixed_bugs = FunctionalDocFileSuite('fixed-bugs.txt', optionflags=flags)
    fixed_bugs.layer = TestBrowserLayer

    wire = doctest.DocFileSuite('over_the_wire.txt', optionflags=flags)
    wire.level = 2

    this_file = doctest.DocTestSuite(checker=checker)

    return unittest.TestSuite((this_file, readme, fixed_bugs, wire, cookies))

def run_suite(suite):
    runner = unittest.TextTestRunner(sys.stdout, verbosity=1)
    result = runner.run(suite)
    if not result.wasSuccessful():
        if len(result.errors) == 1 and not result.failures:
            err = result.errors[0][1]
        elif len(result.failures) == 1 and not result.errors:
            err = result.failures[0][1]
        else:
            err = "errors occurred; run in verbose mode for details"
        print err

if __name__ == "__main__":
    run_suite(test_suite())
