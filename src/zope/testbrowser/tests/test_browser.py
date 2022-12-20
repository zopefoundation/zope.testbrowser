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

import doctest
import io
import unittest

import zope.testbrowser.tests.helper
from zope.testbrowser.browser import Browser
from zope.testbrowser.browser import ItemCountError
from zope.testbrowser.browser import ItemNotFoundError


class TestApp:
    next_response_body = None
    next_response_headers = None
    next_response_status = '200'
    next_response_reason = 'OK'

    verbose = True

    def set_next_response(self, body, headers=None, status='200', reason='OK'):
        if headers is None:
            headers = [('Content-Type', 'text/html; charset="UTF-8"'),
                       ('Content-Length', str(len(body)))]
        self.next_response_body = body
        self.next_response_headers = headers
        self.next_response_status = status
        self.next_response_reason = reason

    def print(self, *args, **kw):
        if self.verbose:
            print(*args, **kw)

    def __call__(self, environ, start_response):
        qs = environ.get('QUERY_STRING')
        self.print("{} {}{} HTTP/1.1".format(environ['REQUEST_METHOD'],
                                             environ['PATH_INFO'],
                                             ('?' + qs) if qs else ""
                                             ))
        # print all the headers
        for ek, ev in sorted(environ.items()):
            if ek.startswith('HTTP_'):
                self.print("{}: {}".format(ek[5:].title(), ev))
        self.print()
        inp = environ['wsgi.input'].input.getvalue()
        self.print(inp.decode('utf8'))
        status = '{} {}'.format(self.next_response_status,
                                self.next_response_reason)
        start_response(status, self.next_response_headers)
        return [self.next_response_body]


class QuietTestApp(TestApp):
    verbose = False


class YetAnotherTestApp:

    def __init__(self):
        self.requests = []
        self.responses = []
        self.last_environ = {}
        self.last_input = None

    def add_response(self, body, headers=None, status='200', reason='OK'):
        if headers is None:
            headers = [('Content-Type', 'text/html; charset="UTF-8"'),
                       ('Content-Length', str(len(body)))]
        resp = dict(body=body, headers=headers, status=status, reason=reason)
        self.responses.append(resp)

    def __call__(self, environ, start_response):
        self.requests.append(environ)
        next_response = self.responses.pop(0)
        self.last_environ = environ
        self.last_input = environ[
            'wsgi.input'].input.getvalue().decode('utf-8')
        status = '{} {}'.format(
            next_response['status'],
            next_response['reason'])
        start_response(status, next_response['headers'])
        return [next_response['body']]


class TestDisplayValue(unittest.TestCase):
    """Testing ..browser.Browser.displayValue."""

    def setUp(self):
        super().setUp()
        app = QuietTestApp()
        app.set_next_response(b'''\
            <html>
              <body>
                <form>
                  <select name="sel1">
                    <option value="op">Turn</option>
                    <option value="alt">Alternative</option>
                  </select>
                </form>
              </body>
            </html>''')
        browser = Browser(wsgi_app=app)
        browser.open('https://localhost')
        self.control = browser.getControl(name='sel1')

    def test_displayValue_partial_title(self):
        """It matches parts of the display title."""
        self.assertEqual(self.control.displayValue, ['Turn'])
        self.control.displayValue = ['erna']
        self.assertEqual(self.control.displayValue, ['Alternative'])

    def test_displayValue_handles_set_of_string(self):
        self.assertEqual(self.control.displayValue, ['Turn'])
        self.control.displayValue = 'erna'
        self.assertEqual(self.control.displayValue, ['Alternative'])

    def test_displayValue_set_empty_value(self):
        self.assertEqual(self.control.displayValue, ['Turn'])
        self.control.displayValue = []
        self.assertEqual(self.control.displayValue, [])

    def test_displayValue_set_missing_value(self):
        self.assertEqual(self.control.displayValue, ['Turn'])
        self.assertRaises(
            ItemNotFoundError, setattr, self.control, 'displayValue',
            ['Missing'])

    def test_displayValue_set_too_many_values(self):
        self.assertEqual(self.control.displayValue, ['Turn'])
        self.assertRaises(
            ItemCountError, setattr, self.control, 'displayValue',
            ['Turn', 'Alternative'])


class TestMechRepr(unittest.TestCase):
    """Testing ..browser.*.mechRepr()."""

    def setUp(self):
        super().setUp()
        app = QuietTestApp()
        app.set_next_response('''\
            <html>
              <body>
                <form>
                  <input name="inp1" type="text" value="Täkst" />
                  <select name="sel1">
                    <option value="op">Türn</option>
                  </select>
                  <input name="check1" type="checkbox" value="šêlėçtèd" />
                  <input name="mail1" type="email" value="i@me.com" />
                  <input name="sub1" type="submit" value="Yës" />
                </form>
              </body>
            </html>'''.encode())
        self.browser = Browser(wsgi_app=app)
        self.browser.open('https://localhost')

    def test_TextControl_has_str_mechRepr(self):
        mech_repr = self.browser.getControl(name='inp1').mechRepr()
        self.assertIsInstance(mech_repr, str)
        self.assertEqual(mech_repr, '<TextControl(inp1=Täkst)>')

    def test_ItemControl_has_str_mechRepr(self):
        option = self.browser.getControl(name='sel1').getControl(value="op")
        mech_repr = option.mechRepr()
        self.assertIsInstance(mech_repr, str)
        self.assertEqual(
            mech_repr,
            "<Item name='op' id=None contents='Türn' value='op'"
            " label='Türn'>")

    def test_CheckboxListControl_has_str_mechRepr(self):
        from ..browser import CheckboxListControl
        ctrl = self.browser.getControl(name='check1')
        self.assertIsInstance(ctrl, CheckboxListControl)
        mech_repr = ctrl.mechRepr()
        self.assertIsInstance(mech_repr, str)
        self.assertEqual(mech_repr, '<SelectControl(check1=[*, ambiguous])>')

    def test_Control_for_type_email_has_mechRepr(self):
        option = self.browser.getControl(name='mail1')
        mech_repr = option.mechRepr()
        self.assertIsInstance(mech_repr, str)
        self.assertEqual(mech_repr, "<EMailControl(mail1=i@me.com)>")

    def test_SubmitControl_has_str_mechRepr(self):
        mech_repr = self.browser.getControl(name='sub1').mechRepr()
        self.assertIsInstance(mech_repr, str)
        self.assertEqual(mech_repr, '<SubmitControl(sub1=Yës)>')


def test_open_no_referrer(self):
    """
    Successive calls to open() do not send a referrer.

    >>> app = YetAnotherTestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.add_response(b'foo')
    >>> app.add_response(b'bar')
    >>> browser.open('http://localhost/')
    >>> browser.contents
    'foo'
    >>> 'HTTP_REFERER' in app.last_environ
    False
    >>> browser.open('http://localhost/')
    >>> browser.contents
    'bar'
    >>> 'HTTP_REFERER' in app.last_environ
    False
    """


def test_relative_redirect(self):
    """
    >>> app = YetAnotherTestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> body = b'redirecting'
    >>> content_type = ('Content-Type', 'text/html; charset=UTF-8')
    >>> headers = [content_type,
    ...            ('Location', 'foundit'),
    ...            ('Content-Length', str(len(body)))]
    >>> app.add_response(body, headers=headers, status=302, reason='Found')
    >>> app.add_response(b'found_it', headers=[content_type])
    >>> browser.open('https://localhost/foo/bar')
    >>> browser.contents
    'found_it'
    >>> browser.url
    'https://localhost/foo/foundit'
    >>> app.last_environ['HTTP_REFERER']
    'https://localhost/foo/bar'
    """


def test_disable_following_redirects(self):
    """
    If followRedirects is False, the browser does not follow redirects.

    >>> app = YetAnotherTestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> redirect = ('Location', 'http://localhost/the_thing')
    >>> app.add_response(b"Moved", headers=[redirect],
    ...                  status=302, reason='Found')

    >>> browser.followRedirects = False
    >>> browser.open('http://localhost/')
    >>> browser.headers['Status']
    '302 Found'
    >>> browser.headers['Location']
    'http://localhost/the_thing'
    >>> 'HTTP_REFERER' in app.last_environ
    False
    """


def test_relative_open_allowed_after_non_html_page(self):
    """
    >>> app = YetAnotherTestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> content_type = ('Content-Type', 'text/csv')
    >>> app.add_response(b'have,some,csv', headers=[content_type])
    >>> content_type = ('Content-Type', 'text/html; charset=UTF-8')
    >>> app.add_response(b'have some html', headers=[content_type])
    >>> browser.open('https://localhost/foo/bar')
    >>> browser.open('/baz')
    >>> browser.contents
    'have some html'
    >>> browser.url
    'https://localhost/baz'
    """


def test_accept_language_header_non_us():
    """Regression test for Accept-Language header

    Once was hardcoded to us-US!

    >>> app = YetAnotherTestApp()
    >>> app.add_response(b'mundo')
    >>> browser = Browser(wsgi_app=app)
    >>> browser.addHeader('Accept-Language', 'es-ES')
    >>> browser.open("http://localhost/hello")
    >>> app.last_environ['HTTP_ACCEPT_LANGUAGE']
    'es-ES'
    """


def test_redirect_after_reload():
    r"""
    When browser is redirected after a page reload, reload() will follow it

    >>> app = YetAnotherTestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> html = (b'''\
    ... <html><body>
    ...   Please wait, generating the thing
    ... </body></html>
    ... ''')
    >>> content_type = ('Content-Type', 'text/html; charset=UTF-8')
    >>> app.add_response(html, headers=[content_type])

    >>> redirect = ('Location', 'http://localhost/the_thing')
    >>> app.add_response(b"Moved", headers=[redirect],
    ...                  status=302, reason='Found')
    >>> app.add_response(b"The Thing", headers=[content_type])

    Start conversation

    >>> browser.open("http://localhost/")

    After reload, expect the browser to be redirected

    >>> browser.reload()
    >>> browser.url
    'http://localhost/the_thing'
    >>> browser.contents
    'The Thing'
    >>> app.last_environ['HTTP_REFERER']
    'http://localhost/'

    """


def test_error_after_reload():
    r"""
    When browser is redirected after a page reload, reload() will check
    for bad HTTP status codes

    >>> app = YetAnotherTestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> browser.handleErrors = False
    >>> html = (b'''\
    ... <html><body>
    ...   Please wait, generating the thing
    ... </body></html>
    ... ''')
    >>> content_type = ('Content-Type', 'text/html; charset=UTF-8')
    >>> app.add_response(html, headers=[content_type])

    >>> app.add_response(b"These are not the droids you're looking for",
    ...                  status=403, reason='Forbidden')

    Start conversation

    >>> browser.open("http://localhost/")

    After reload, expect the error to be raised

    XXX: I expected

    ## >>> browser.reload()
    ## Traceback (most recent call last):
    ##   ...
    ## HTTPError: HTTP Error 403: Forbidden

    which is what the tests in fixed-bugs.txt get, but what I actually get
    instead is

    >>> browser.reload()
    Traceback (most recent call last):
      ...
    webtest.app.AppError: Bad response: 403 Forbidden
    (not 200 OK or 3xx redirect for http://localhost/)
    These are not the droids you're looking for

    """


def test_reload_after_redirect():
    """
    When browser is redirected after form submit, reload() will not resubmit
    original form data.

    >>> app = YetAnotherTestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> html = (b'''\
    ... <html><body>
    ...   <form action="submit" method="post" enctype="multipart/form-data">
    ...      <input type='text' name='name' value='Linus' />
    ...      <button name="do" type="button">Do Stuff</button>
    ...   </form></body></html>
    ... ''')
    >>> content_type = ('Content-Type', 'text/html; charset=UTF-8')
    >>> app.add_response(html, headers=[content_type])

    >>> redirect = ('Location', 'http://localhost/processed')
    >>> app.add_response(b"Moved", headers=[redirect],
    ...                  status=302, reason='Found')
    >>> app.add_response(b"Processed", headers=[content_type])

    >>> app.add_response(b"Reloaded", headers=[content_type])

    Start conversation

    >>> browser.open("http://localhost/form")
    >>> browser.getControl(name="do").click()

    We should have followed the redirect with GET request
    >>> browser.url
    'http://localhost/processed'
    >>> browser.contents
    'Processed'
    >>> app.last_environ['REQUEST_METHOD']
    'GET'
    >>> app.last_environ['HTTP_REFERER']
    'http://localhost/submit'
    >>> print(app.last_input)
    <BLANKLINE>

    After reload, expect no form data to be submitted
    >>> browser.reload()
    >>> browser.url
    'http://localhost/processed'
    >>> browser.contents
    'Reloaded'
    >>> app.last_environ['REQUEST_METHOD']
    'GET'
    >>> app.last_environ['HTTP_REFERER']
    'http://localhost/submit'
    >>> print(app.last_input)
    <BLANKLINE>
    """


def test_reload_after_post():
    """
    If we reload page just after submitting the form, all form data should be
    submitted again (just as real browsers do).

    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)

    First response is a form:

    >>> html = (b'''\
    ... <html><body>
    ...   <form action="submit" method="post" enctype="multipart/form-data">
    ...      <input type='text' name='name' value='Linus' />
    ...      <button name="do" type="button">Do Stuff</button>
    ...   </form></body></html>
    ... ''')
    >>> content_type = ('Content-Type', 'text/html; charset=UTF-8')
    >>> app.set_next_response(html, headers=[content_type])

    >>> browser.open('https://localhost/foo/bar')
    GET /foo/bar HTTP/1.1
    ...

    After submit, show result page
    >>> app.set_next_response(b'OK', headers=[content_type])

    Form data is there in POST request
    >>> browser.getControl(name="do").click()
    POST /foo/submit HTTP/1.1
    ...
    Content-Disposition: form-data; name="name"
    <BLANKLINE>
    Linus
    ...

    >>> browser.contents
    'OK'

    >>> browser.url
    'https://localhost/foo/submit'

    POST data is still there after reload
    >>> browser.reload()
    POST /foo/submit HTTP/1.1
    ...
    Content-Disposition: form-data; name="name"
    <BLANKLINE>
    Linus
    ...

    """


def test_goBack_changes_cached_html(self):
    """
    goBack() causes the browser to clear its cached parsed HTML, so queries
    that rely on that use the correct response.

    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.set_next_response(b'''\
    ... <html>
    ...   <head><title>First page</title></head>
    ...   <body><a href="foo">link</a></body>
    ... </html>
    ... ''')
    >>> browser.open('http://localhost/')
    GET / HTTP/1.1
    ...
    >>> browser.title
    'First page'
    >>> browser.getLink('link').url
    'http://localhost/foo'

    >>> app.set_next_response(b'''\
    ... <html>
    ...   <head><title>Second page</title></head>
    ...   <body><a href="bar">link</a></body>
    ... </html>
    ... ''')
    >>> browser.open('http://localhost/')
    GET / HTTP/1.1
    ...
    >>> browser.title
    'Second page'
    >>> browser.getLink('link').url
    'http://localhost/bar'

    After going back, queries once again return answers based on the first
    response.

    >>> browser.goBack()
    >>> browser.title
    'First page'
    >>> browser.getLink('link').url
    'http://localhost/foo'
    """


def test_button_without_name(self):
    """
    This once blew up.

    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.set_next_response(b'''\
    ... <html><body>
    ...   <form action="." method="post" enctype="multipart/form-data">
    ...      <button type="button">Do Stuff</button>
    ...   </form></body></html>
    ... ''')
    >>> browser.open('http://localhost/') # doctest: +ELLIPSIS
    GET / HTTP/1.1
    ...
    >>> browser.getControl('NotThere') # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    LookupError: ...
    ...
    """


def test_submit_duplicate_name():
    """
    This test was inspired by bug #723 as testbrowser would pick up the wrong
    button when having the same name twice in a form.

    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)


    When given a form with two submit buttons that have the same name:

    >>> app.set_next_response(b'''\
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

    >>> app.set_next_response(b'''\
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

    >>> app.set_next_response(b'''\
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

    >>> import tempfile
    >>> data = tempfile.NamedTemporaryFile()
    >>> num_bytes = data.write(b'sample_data')
    >>> position = data.seek(0)
    >>> browser.getControl(name='foo').add_file(data, 'text/foo', 'x.txt')
    >>> browser.getControl('OK').click() # doctest: +REPORT_NDIFF +ELLIPSIS
    POST / HTTP/1.1
    ...
    Content-Disposition: form-data; name="foo"; filename="x.txt"
    Content-Type: text/foo
    <BLANKLINE>
    sample_data
    ...
    >>> del data

    You can pass a string to add_file:

    >>> browser.getControl(name='foo').add_file(
    ...     b'blah blah blah', 'text/csv', 'x.csv')
    >>> browser.getControl('OK').click() # doctest: +REPORT_NDIFF +ELLIPSIS
    POST / HTTP/1.1
    ...
    Content-disposition: form-data; name="foo"; filename="x.csv"
    Content-type: text/csv
    <BLANKLINE>
    blah blah blah
    ...

    or a BytesIO object:

    >>> browser.getControl(name='foo').add_file(
    ...     io.BytesIO(b'sample_data'), 'text/foo', 'x.txt')
    >>> browser.getControl('OK').click() # doctest: +REPORT_NDIFF +ELLIPSIS
    POST / HTTP/1.1
    ...
    Content-Disposition: form-data; name="foo"; filename="x.txt"
    Content-Type: text/foo
    <BLANKLINE>
    sample_data
    ...

    You can assign a value

    >>> browser.getControl(name='foo').value = b'bluh bluh'
    >>> browser.getControl('OK').click() # doctest: +REPORT_NDIFF +ELLIPSIS
    POST / HTTP/1.1
    ...
    Content-disposition: form-data; name="foo"; filename=""
    Content-type: application/octet-stream
    <BLANKLINE>
    bluh bluh
    ...

    """


def test_submit_gets_referrer():
    """
    Test for bug #98437: No HTTP_REFERER was sent when submitting a form.

    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)

    A simple form for testing, like abobe.

    >>> app.set_next_response(b'''\
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
    ...
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

    >>> app.set_next_response(b'''\
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

    >>> app.set_next_response(b'''\
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

    >>> app.set_next_response(b'''\
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

    >>> app.set_next_response(b'''\
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

    >>> app.set_next_response(b'''\
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

    >>> app.set_next_response(b'''\
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


def test_relative_open():
    """
    Browser is capable of opening relative urls as well as relative links

    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)

    >>> app.set_next_response(b'''\
    ... <html><body>
    ...     <a href="foo">link</a>
    ... </body></html>
    ... ''')
    >>> browser.open('bar') # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    BrowserStateError: can't fetch relative reference: not viewing any document

    >>> browser.open('http://localhost/hello/foo') # doctest: +ELLIPSIS
    GET /hello/foo HTTP/1.1
    ...

    >>> browser.open('bar') # doctest: +ELLIPSIS
    GET /hello/bar HTTP/1.1
    ...

    >>> browser.open('/bar') # doctest: +ELLIPSIS
    GET /bar HTTP/1.1
    ...

    """


def test_submit_button():
    """
    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.set_next_response(b'''\
    ... <html><body>
    ...     <form method='get' action='action'>
    ...         <button name='clickable' value='test' type='submit'>
    ...         Click Me</button>
    ...         <button name='simple' value='value'>
    ...         Don't Click</button>
    ...     </form>
    ...     <a href="foo">link</a>
    ... </body></html>
    ... ''')
    >>> browser.open('http://localhost/foo') # doctest: +ELLIPSIS
    GET /foo HTTP/1.1
    ...

    >>> browser.getControl('Click Me')
    <SubmitControl name='clickable' type='submit'>

    >>> browser.getControl('Click Me').click()
    GET /action?clickable=test HTTP/1.1
    ...
    """


def test_repeated_button():
    """
    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.set_next_response(b'''\
    ... <html><body>
    ...     <form method='get' action='action'>
    ...         <input name='one' value='Button' type='submit'>
    ...         <input name='two' value='Button' type='submit'>
    ...         <input name='one' value='Button' type='submit'>
    ...     </form>
    ... </body></html>
    ... ''')
    >>> browser.open('http://localhost/foo') # doctest: +ELLIPSIS
    GET /foo HTTP/1.1
    ...

    >>> browser.getControl('Button')
    Traceback (most recent call last):
      ...
    AmbiguityError: label 'Button' matches:
      <SubmitControl(one=Button)>
      <SubmitControl(two=Button)>
      <SubmitControl(one=Button)>

    >>> browser.getControl('Button', index=0)
    <SubmitControl name='one' type='submit'>
    >>> browser.getControl('Button', index=1)
    <SubmitControl name='two' type='submit'>
    >>> browser.getControl('Button', index=2)
    <SubmitControl name='one' type='submit'>
    """


def test_subcontrols_can_be_selected_by_value():
    """
    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.set_next_response(b'''\
    ... <html><body>
    ...     <form method='get' action='action'>
    ...         <input id="foo1" type='checkbox' name='foo' value="1">
    ...         <label for="foo1">One</label>
    ...         <input id="foo2" type='checkbox' name='foo' value="2">
    ...         <label for="foo2">Two</label>
    ...         <input id="foo3" type='checkbox' name='foo' value="3">
    ...         <label for="foo3">Three</label>
    ...         <br>
    ...         <input id="bar1" type='radio' name='bar' value="1">
    ...         <label for="bar1">First</label>
    ...         <input id="bar2" type='radio' name='bar' value="2">
    ...         <label for="bar2">Second</label>
    ...         <input id="bar3" type='radio' name='bar' value="3">
    ...         <label for="bar3">Third</label>
    ...         <br>
    ...         <select name="baz">
    ...             <option value="1">uno</option>
    ...             <option value="2">duos</option>
    ...             <option>tres</option>
    ...         </select>
    ...     </form>
    ... </body></html>
    ... ''')
    >>> browser.open('http://localhost/foo') # doctest: +ELLIPSIS
    GET /foo HTTP/1.1
    ...

    >>> form_controls = browser.getForm(index=0).controls
    >>> len(form_controls)
    12

    >>> checkboxes = browser.getControl(name='foo')
    >>> checkboxes
    <ListControl name='foo' type='checkbox'>
    >>> checkboxes.getControl('One')
    <ItemControl name='foo' type='checkbox' optionValue='1' selected=False>
    >>> checkboxes.getControl(value='1')
    <ItemControl name='foo' type='checkbox' optionValue='1' selected=False>

    >>> radiobuttons = browser.getControl(name='bar')
    >>> radiobuttons
    <ListControl name='bar' type='radio'>
    >>> radiobuttons.getControl('First')
    <ItemControl name='bar' type='radio' optionValue='1' selected=False>
    >>> radiobuttons.getControl(value='1')
    <ItemControl name='bar' type='radio' optionValue='1' selected=False>

    >>> listcontrol = browser.getControl(name='baz')
    >>> listcontrol
    <ListControl name='baz' type='select'>
    >>> listcontrol.getControl('uno')
    <ItemControl name='baz' type='select' optionValue='1' selected=True>
    >>> listcontrol.getControl(value='1')
    <ItemControl name='baz' type='select' optionValue='1' selected=True>

    >>> listcontrol.getControl('tres')
    <ItemControl name='baz' type='select' optionValue='tres' selected=False>
    >>> listcontrol.getControl(value='tres')
    <ItemControl name='baz' type='select' optionValue='tres' selected=False>

    """


def test_subcontrols_with_same_value_can_be_distinguished():
    """Regression test for GH #31.

    https://github.com/zopefoundation/zope.testbrowser/issues/31

    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.set_next_response(b'''\
    ... <html><body>
    ...     <form method='get' action='action'>
    ...         <input id="bar1" type='radio' name='bar' value="a">
    ...         <label for="bar1">First</label>
    ...         <input id="bar2" type='radio' name='bar' value="a">
    ...         <label for="bar2">Second</label>
    ...         <br>
    ...         <select name="baz">
    ...             <option value="b">uno</option>
    ...             <option value="b">duos</option>
    ...         </select>
    ...     </form>
    ... </body></html>
    ... ''')
    >>> browser.open('http://localhost/foo') # doctest: +ELLIPSIS
    GET /foo HTTP/1.1
    ...

    >>> radiobuttons = browser.getControl(name='bar')
    >>> radiobuttons.getControl(value='a', index=1).selected = True
    >>> radiobuttons.getControl(value='a', index=0)
    <ItemControl name='bar' type='radio' optionValue='a' selected=False>
    >>> radiobuttons.getControl(value='a', index=1)
    <ItemControl name='bar' type='radio' optionValue='a' selected=True>

    >>> listcontrol = browser.getControl(name='baz')
    >>> listcontrol.getControl(value='b', index=1).selected = True
    >>> listcontrol.getControl(value='b', index=0)
    <ItemControl name='baz' type='select' optionValue='b' selected=False>
    >>> listcontrol.getControl(value='b', index=1)
    <ItemControl name='baz' type='select' optionValue='b' selected=True>

    """


def test_option_with_explicit_value_and_first_value_an_empty_string():
    """
    >>> app = YetAnotherTestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.add_response(b'''\
    ... <html><body>
    ...     <form method='get' action='action'>
    ...         <select name="baz">
    ...             <option value="">uno</option>
    ...             <option value="2" selected="selected">duos</option>
    ...             <option>tres</option>
    ...         </select>
    ...     </form>
    ... </body></html>
    ... ''')
    >>> browser.open('http://localhost/foo')
    >>> browser.getControl(name='baz').displayValue
    ['duos']
    """


def test_option_without_explicit_value():
    """
    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.set_next_response(b'''\
    ... <html><body>
    ...     <form method='get' action='action'>
    ...         <select name="baz">
    ...             <option value="1">uno</option>
    ...             <option value="2">duos</option>
    ...             <option>tres</option>
    ...         </select>
    ...     </form>
    ... </body></html>
    ... ''')
    >>> browser.open('http://localhost/foo') # doctest: +ELLIPSIS
    GET /foo HTTP/1.1
    ...
    >>> listcontrol = browser.getControl(name='baz')
    >>> listcontrol
    <ListControl name='baz' type='select'>
    >>> listcontrol.getControl('uno')
    <ItemControl name='baz' type='select' optionValue='1' selected=True>
    >>> listcontrol.getControl(value='1')
    <ItemControl name='baz' type='select' optionValue='1' selected=True>

    >>> listcontrol.getControl('uno').selected = True
    >>> listcontrol.value
    ['1']
    >>> listcontrol.displayValue
    ['uno']

    >>> listcontrol.getControl(value='2').selected = True
    >>> listcontrol.value
    ['2']
    >>> listcontrol.displayValue
    ['duos']

    >>> listcontrol.getControl('tres').selected = True
    >>> listcontrol.value
    ['tres']
    >>> listcontrol.displayValue
    ['tres']

    """


def test_multiselect_option_without_explicit_value():
    """
    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.set_next_response(b'''\
    ... <html><body>
    ...     <form method='get' action='action'>
    ...         <select name="baz" multiple>
    ...             <option>uno</option>
    ...             <option selected value="2">duos</option>
    ...             <option selected>tres</option>
    ...         </select>
    ...     </form>
    ... </body></html>
    ... ''')
    >>> browser.open('http://localhost/foo') # doctest: +ELLIPSIS
    GET /foo HTTP/1.1
    ...
    >>> listcontrol = browser.getControl(name='baz')
    >>> listcontrol
    <ListControl name='baz' type='select'>
    >>> listcontrol.getControl('uno')
    <ItemControl name='baz' type='select' optionValue='uno' selected=False>
    >>> listcontrol.getControl('duos')
    <ItemControl name='baz' type='select' optionValue='2' selected=True>
    >>> listcontrol.getControl('tres')
    <ItemControl name='baz' type='select' optionValue='tres' selected=True>

    >>> listcontrol.value
    ['2', 'tres']

    >>> listcontrol.getControl(value='uno').selected = True
    >>> listcontrol.value
    ['uno', '2', 'tres']
    >>> listcontrol.displayValue
    ['uno', 'duos', 'tres']

    """


def test_subcontrols_can_be_selected_by_label_substring():
    """
    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.set_next_response(b'''
    ... <html><body>
    ...     <form method='get' action='action'>
    ...         <select name="foo">
    ...             <option>one/two</option>
    ...             <option>three</option>
    ...         </select>
    ...     </form>
    ... </body></html>
    ... ''')
    >>> browser.open('http://localhost/foo') # doctest: +ELLIPSIS
    GET /foo HTTP/1.1
    ...
    >>> listcontrol = browser.getControl(name='foo')
    >>> listcontrol.getControl('one')
    <ItemControl name='foo' type='select' optionValue='one/two' selected=True>

    """


def test_radio_buttons_cannot_be_unselected():
    """
    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.set_next_response(b'''
    ... <html><body>
    ...     <form method='get' action='action'>
    ...         <input type="radio" name="foo" id="foo1" value="v1" checked>
    ...         <label for="foo1">label 1</label>
    ...         <input type="radio" name="foo" id="foo2" value="v2">
    ...         <label for="foo2">label 2</label>
    ...     </form>
    ... </body></html>
    ... ''')
    >>> browser.open('http://localhost/foo') # doctest: +ELLIPSIS
    GET /foo HTTP/1.1
    ...
    >>> browser.getControl(name='foo').value
    ['v1']

    >>> browser.getControl('label 1').click()
    >>> browser.getControl(name='foo').value
    ['v1']

    >>> browser.getControl('label 2').click()
    >>> browser.getControl(name='foo').value
    ['v2']

    """


UNICODE_TEST = '\u4e2d\u6587\u7dad'  # unicode in doctests is hard!


def test_non_ascii_in_input_field(self):
    """
    Test non-ascii chars in form postings.

    >>> app = YetAnotherTestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> body = u'''\
    ... <html><body>
    ...   <form action="." method="post" enctype="multipart/form-data">
    ...      <input name="text" type="text" value="{0}"/>
    ...      <button name="do" type="button">Do Stuff</button>
    ...   </form></body></html>
    ... '''.format(UNICODE_TEST).encode('utf-8')
    >>> headers = [('Content-Type', 'text/html; charset="UTF-8"'),
    ...             ('Content-Length', str(len(body)))]
    >>> app.add_response(body, headers=headers)
    >>> app.add_response(body, headers=headers)

    Getting a form with non-ascii form values should do something sane:

    >>> browser.open('http://localhost/')
    >>> non_ascii = browser.getControl(name='text').value
    >>> non_ascii == UNICODE_TEST
    True

    Posting a form with non-ascii values should give the server access to the
    real data:

    >>> browser.getControl("Do Stuff").click()
    >>> UNICODE_TEST in app.last_input
    True
"""


def test_post_encoding_doesnt_leak_between_requests(self):
    """
    >>> app = YetAnotherTestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> body = b'''\
    ... <html><body>
    ...   <form action="." method="POST" enctype="multipart/form-data">
    ...      <input name="text.other-e" type="text" value="somedata"/>
    ...      <button name="do" type="button">Do Stuff</button>
    ...   </form></body></html>
    ... '''
    >>> app.add_response(b'json')
    >>> app.add_response(body)
    >>> app.add_response(b'done')

    Post some JSON

    >>> browser.post('http://localhost/', '1', 'application/json')
    >>> browser.contents
    'json'

    then get a form and post it

    >>> browser.open('http://localhost/')
    >>> browser.getControl("Do Stuff").click()
    >>> browser.contents
    'done'

    The content_type of the last post should come from the form's enctype attr:

    >>> print(app.last_environ['CONTENT_TYPE'])
    multipart/form-data...
"""


def test_links_without_href(self):
    """
    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.set_next_response(b'''\
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


def test_links_with_complicated_id(self):
    """
    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.set_next_response(b'''\
    ... <html><body>
    ... <a href="/foo" id="form.foo">Foo</a>
    ... </body></html>
    ... ''')
    >>> browser.open('http://localhost/')
    GET / HTTP/1.1
    ...
    >>> browser.getLink(id='form.foo').url
    'http://localhost/foo'
    """


def test_link_click_sends_referrer(self):
    """
    Clicking on a link sends the previous URL as the referrer.

    >>> app = YetAnotherTestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.add_response(b'''\
    ... <html><body>
    ...   <a href="/foo">Foo</a>
    ... </body</html>
    ... ''')
    >>> app.add_response(b'foo')
    >>> browser.open('http://localhost/')
    >>> 'HTTP_REFERER' in app.last_environ
    False
    >>> browser.getLink(url='/foo').click()
    >>> browser.contents
    'foo'
    >>> browser.url
    'http://localhost/foo'
    >>> app.last_environ['HTTP_REFERER']
    'http://localhost/'
    """


def test_controls_without_value(self):
    """
    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.set_next_response(b'''\
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


def test_controls_with_slightly_invalid_ids(self):
    """
    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.set_next_response(b'''\
    ... <html><body>
    ... <form action="." method="post">
    ... <label for="foo.field">Foo Label</label>
    ... <input type="text" id="foo.field" value="Foo"/>
    ... </form>
    ... </body></html>
    ... ''')
    >>> browser.open('http://localhost/')
    GET / HTTP/1.1
    ...
    >>> browser.getControl('Foo Label').value
    'Foo'
    """


def test_multiple_classes(self):
    """
    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.set_next_response(b'''\
    ... <html><body>
    ... <a href="" class="one two">A link</a>
    ... </body></html>
    ... ''')
    >>> browser.open('http://localhost/')
    GET / HTTP/1.1
    ...
    >>> from pprint import pprint
    >>> pprint(browser.getLink('A link').attrs)
    {'class': ['one', 'two'], 'href': ''}
    """


def test_form_get_method_with_querystring_in_action(self):
    """
    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.set_next_response(b'''\
    ... <html><body>
    ... <form action="/?bar=1" method="get">
    ... <input type="text" name="foo" />
    ... <input type="submit" />
    ... </form>
    ... </body></html>
    ... ''')
    >>> browser.open('http://localhost/?bar=1')
    GET /?bar=1 HTTP/1.1
    ...
    >>> browser.getControl(name="foo").value = "bar"
    >>> browser.getForm().submit()
    GET /?foo=bar HTTP/1.1
    ...
    """


def test_additional_hidden_element_with_by_label_search():
    """
    >>> app = TestApp()
    >>> browser = Browser(wsgi_app=app)
    >>> app.set_next_response(b'''
    ...   <html><body>
    ...   <form>
    ...     <label>Label with additional hidden element
    ...       <input type="text" name="text-next-to-hidden" />
    ...       <input type="hidden" name="hidden-next-to-text" />
    ...     </label>
    ...   </form></body></html>
    ... ''')
    >>> browser.open('http://localhost/')
    GET / HTTP/1.1
    ...
    >>> c = browser.getControl("Label with additional")
    >>> c.name
    'text-next-to-hidden'
    """


def test_suite():
    optionflags = (
        doctest.NORMALIZE_WHITESPACE
        | doctest.ELLIPSIS
        | doctest.IGNORE_EXCEPTION_DETAIL
    )
    suite = unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromName(__name__),
        doctest.DocTestSuite(
            checker=zope.testbrowser.tests.helper.checker,
            optionflags=optionflags),
    ])
    return suite


# additional_tests is for setuptools "setup.py test" support
additional_tests = test_suite
