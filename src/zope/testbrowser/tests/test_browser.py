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
from __future__ import print_function

import io
import doctest

from zope.testbrowser.browser import Browser
import zope.testbrowser.tests.helper

class TestApp(object):
    next_response_body = None
    next_response_headers = None
    next_response_status = '200'
    next_response_reason = 'OK'

    def set_next_response(self, body, headers=None, status='200', reason='OK'):
        if headers is None:
            headers = [('Content-Type', 'text/html'),
                       ('Content-Length', str(len(body)))]
        self.next_response_body = body
        self.next_response_headers = headers
        self.next_response_status = status
        self.next_response_reason = reason

    def __call__(self, environ, start_response):
        print("%s %s HTTP/1.1" % (environ['REQUEST_METHOD'],
                                  environ['PATH_INFO']))
        # print all the headers
        for ek, ev in environ.items():
            if ek.startswith('HTTP_'):
                print("%s: %s" % (ek[5:].title(), ev))
        print()
        print(environ['wsgi.input'].input.getvalue())
        status = '%s %s' % (self.next_response_status, self.next_response_reason)
        start_response(status, self.next_response_headers)
        return [self.next_response_body]


def test_submit_duplicate_name():
    """
    This test was inspired by bug #723 as testbrowser would pick up the wrong
    button when having the same name twice in a form.

    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)


    When given a form with two submit buttons that have the same name:

    >>> app.set_next_response('''\
    ... <html><body>
    ...   <form action="." method="post" enctype="multipart/form-data">
    ...      <input type="submit" name="submit_me" value="GOOD" />
    ...      <input type="submit" name="submit_me" value="BAD" />
    ...   </form></body></html>
    ... ''')
    >>> browser.open('http://localhost/') # doctest: +ELLIPSIS
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
    Content-disposition: form-data; name="submit_me"
    <BLANKLINE>
    BAD
    ...


    This also works if the labels have whitespace around them (this tests a
    regression caused by the original fix for the above):

    >>> app.set_next_response('''\
    ... <html><body>
    ...   <form action="." method="post" enctype="multipart/form-data">
    ...      <input type="submit" name="submit_me" value=" GOOD " />
    ...      <input type="submit" name="submit_me" value=" BAD " />
    ...   </form></body></html>
    ... ''')
    >>> browser.open('http://localhost/') # doctest: +ELLIPSIS 
    GET / HTTP/1.1
    ...

    >>> browser.getControl('BAD')
    <SubmitControl name='submit_me' type='submit'>
    >>> browser.getControl('BAD').value
    ' BAD '
    >>> browser.getControl('BAD').click() # doctest: +REPORT_NDIFF +ELLIPSIS
    POST / HTTP/1.1
    ...
    Content-disposition: form-data; name="submit_me"
    <BLANKLINE>
     BAD
    ...
"""


def test_file_upload():
    """
    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)

    When given a form with a file-upload

    >>> app.set_next_response('''\
    ... <html><body>
    ...   <form action="." method="post" enctype="multipart/form-data">
    ...      <input name="foo" type="file" />
    ...      <input type="submit" value="OK" />
    ...   </form></body></html>
    ... ''') # doctest: +ELLIPSIS
    >>> browser.open('http://localhost/')
    GET / HTTP/1.1
    ...

    Fill in the form value using add_file:

    >>> browser.getControl(name='foo').add_file(
    ...     io.BytesIO(b'sample_data'), 'text/foo', 'x.txt')
    >>> browser.getControl('OK').click() # doctest: +REPORT_NDIFF +ELLIPSIS
    POST / HTTP/1.1
    ...
    Content-Disposition: form-data; name="foo"; filename="x.txt"
    Content-Type: text/plain
    <BLANKLINE>
    sample_data
    ...

    You can pass a string to add_file:

    >>> browser.getControl(name='foo').add_file(
    ...     'blah blah blah', 'text/csv', 'x.csv')
    >>> browser.getControl('OK').click() # doctest: +REPORT_NDIFF +ELLIPSIS
    POST / HTTP/1.1
    ...
    Content-disposition: form-data; name="foo"; filename="x.csv"
    Content-type: text/csv
    <BLANKLINE>
    blah blah blah
    ...
    """


def test_submit_gets_referrer():
    """
    Test for bug #98437: No HTTP_REFERER was sent when submitting a form.

    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)

    A simple form for testing, like abobe.

    >>> app.set_next_response('''\
    ... <html><body>
    ...   <form id="form" action="." method="post"
    ...                   enctype="multipart/form-data">
    ...      <input type="submit" name="submit_me" value="GOOD" />
    ...   </form></body></html>
    ... ''') # doctest: +ELLIPSIS
    >>> browser.open('http://localhost/')
    GET / HTTP/1.1
    ...

    Now submit the form, and see that we get an referrer along:

    >>> form = browser.getForm(id='form')
    >>> form.submit(name='submit_me') # doctest: +ELLIPSIS
    POST / HTTP/1.1
    Referer: http://localhost/
    ...
"""


def test_new_instance_no_contents_should_not_fail(self):
    """
    When first instantiated, the browser has no contents.
    (Regression test for <http://bugs.launchpad.net/zope3/+bug/419119>)

    >>> browser = Browser()
    >>> print(browser.contents)
    None
    """


def test_strip_linebreaks_from_textarea(self):
    """
    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)

    According to http://www.w3.org/TR/html4/appendix/notes.html#h-B.3.1 line
    break immediately after start tags or immediately before end tags must be
    ignored, but real browsers only ignore a line break after a start tag.
    So if we give the following form:

    >>> app.set_next_response('''\
    ... <html><body>
    ...   <form action="." method="post" enctype="multipart/form-data">
    ...      <textarea name="textarea">
    ... Foo
    ... </textarea>
    ...   </form></body></html>
    ... ''')
    >>> browser.open('http://localhost/')
    GET / HTTP/1.1
    ...

    The value of the textarea won't contain the first line break:

    >>> browser.getControl(name='textarea').value
    'Foo\\n'


    Of course, if we add line breaks, so that there are now two line breaks
    after the start tag, the textarea value will start and end with a line
    break.

    >>> app.set_next_response('''\
    ... <html><body>
    ...   <form action="." method="post" enctype="multipart/form-data">
    ...      <textarea name="textarea">
    ...
    ... Foo
    ... </textarea>
    ...   </form></body></html>
    ... ''')
    >>> browser.open('http://localhost/')
    GET / HTTP/1.1
    ...

    >>> browser.getControl(name='textarea').value
    '\\nFoo\\n'


    Also, if there is some other whitespace after the start tag, it will be
    preserved.

    >>> app.set_next_response('''\
    ... <html><body>
    ...   <form action="." method="post" enctype="multipart/form-data">
    ...      <textarea name="textarea">  Foo  </textarea>
    ...   </form></body></html>
    ... ''')
    >>> browser.open('http://localhost/')
    GET / HTTP/1.1
    ...

    >>> browser.getControl(name='textarea').value
    '  Foo  '
    """


def test_relative_link():
    """
    RFC 1808 specifies how relative URLs should be resolved, let's see
    that we conform to it. Let's start with a simple example.

    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)

    >>> app.set_next_response('''\
    ... <html><body>
    ...     <a href="foo">link</a>
    ... </body></html>
    ... ''')
    >>> browser.open('http://localhost/bar') # doctest: +ELLIPSIS
    GET /bar HTTP/1.1
    ...

    >>> link = browser.getLink('link')
    >>> link.url
    'http://localhost/foo'


    It's possible to have a relative URL consisting of only a query part. In
    that case it should simply be appended to the base URL.

    >>> app.set_next_response('''\
    ... <html><body>
    ...     <a href="?key=value">link</a>
    ... </body></html>
    ... ''')
    >>> browser.open('http://localhost/bar') # doctest: +ELLIPSIS
    GET /bar HTTP/1.1
    ...

    >>> link = browser.getLink('link')
    >>> link.url
    'http://localhost/bar?key=value'


    In the example above, the base URL was the page URL, but we can also
    specify a base URL using a <base> tag.

    >>> app.set_next_response('''\
    ... <html><head><base href="http://localhost/base" /></head><body>
    ...     <a href="?key=value">link</a>
    ... </body></html>
    ... ''')
    >>> browser.open('http://localhost/base/bar') # doctest: +ELLIPSIS
    GET /base/bar HTTP/1.1
    ...

    >>> link = browser.getLink('link')
    >>> link.url
    'http://localhost/base?key=value'
    """


def test_links_without_href(self):
    """
    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.set_next_response('''\
    ... <html><body>
    ... <a href="/foo">Foo</a>
    ... <a>Missing href</a>
    ... </body></html>
    ... ''')
    >>> browser.open('http://localhost/')
    GET / HTTP/1.1
    ...
    >>> browser.getLink(url='/foo').url
    'http://localhost/foo'
    """


def test_controls_without_value(self):
    """
    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.set_next_response('''\
    ... <html><body>
    ... <form action="." method="post">
    ... <label for="foo-field">Foo Label</label>
    ... <input type="text" id="foo-field" value="Foo"/>
    ... <button type="submit">Submit</button>
    ... </form>
    ... </body></html>
    ... ''')
    >>> browser.open('http://localhost/')
    GET / HTTP/1.1
    ...
    >>> browser.getControl('Foo Label').value
    'Foo'
    """


def test_suite():
    return doctest.DocTestSuite(
        checker=zope.testbrowser.tests.helper.checker,
        optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)

# additional_tests is for setuptools "setup.py test" support
additional_tests = test_suite
