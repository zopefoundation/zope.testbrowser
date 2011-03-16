##############################################################################
#
# Copyright (c) 2011 Zope Foundation and Contributors.
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

import unittest
from urllib import urlencode
from wsgiref.simple_server import demo_app

import zope.testbrowser.wsgi
from zope.testbrowser.ftests.wsgitestapp import WSGITestApplication


class SimpleLayer(zope.testbrowser.wsgi.Layer):

    def make_wsgi_app(self):
        return demo_app

SIMPLE_LAYER = SimpleLayer()


class TestBrowser(unittest.TestCase):

    def test_redirect(self):
        app = WSGITestApplication()
        browser = zope.testbrowser.wsgi.Browser(wsgi_app=app)
        # redirecting locally works
        browser.open('http://localhost/redirect.html?%s'
                     % urlencode(dict(to='/set_status.html')))
        self.assertEquals(browser.url, 'http://localhost/set_status.html')
        browser.open('http://localhost/redirect.html?%s'
                     % urlencode(dict(to='/set_status.html', type='301')))
        self.assertEquals(browser.url, 'http://localhost/set_status.html')
        browser.open('http://localhost/redirect.html?%s'
                     % urlencode(dict(to='http://localhost/set_status.html')))
        self.assertEquals(browser.url, 'http://localhost/set_status.html')
        browser.open('http://localhost/redirect.html?%s'
                     % urlencode(dict(to='http://localhost/set_status.html', type='301')))
        self.assertEquals(browser.url, 'http://localhost/set_status.html')
        # non-local redirects raise HostNotAllowed error
        self.assertRaises(zope.testbrowser.wsgi.HostNotAllowed,
                          browser.open,
                          'http://localhost/redirect.html?%s'
                          % urlencode(dict(to='http://www.google.com/')))
        self.assertRaises(zope.testbrowser.wsgi.HostNotAllowed,
                          browser.open,
                          'http://localhost/redirect.html?%s'
                          % urlencode(dict(to='http://www.google.com/', type='301')))

    def test_allowed_domains(self):
        browser = zope.testbrowser.wsgi.Browser(wsgi_app=demo_app)
        # external domains are not allowed
        self.assertRaises(zope.testbrowser.wsgi.HostNotAllowed, browser.open, 'http://www.google.com')
        self.assertRaises(zope.testbrowser.wsgi.HostNotAllowed, browser.open, 'https://www.google.com')
        # internal ones are
        browser.open('http://localhost')
        self.assertTrue(browser.contents.startswith('Hello world!\n'))
        browser.open('http://127.0.0.1')
        self.assertTrue(browser.contents.startswith('Hello world!\n'))
        # as are example ones
        browser.open('http://example.com')
        self.assertTrue(browser.contents.startswith('Hello world!\n'))
        browser.open('http://example.net')
        self.assertTrue(browser.contents.startswith('Hello world!\n'))
        # and subdomains of example
        browser.open('http://foo.example.com')
        self.assertTrue(browser.contents.startswith('Hello world!\n'))
        browser.open('http://bar.example.net')
        self.assertTrue(browser.contents.startswith('Hello world!\n'))


class TestWSGILayer(unittest.TestCase):

    def setUp(self):
        # test the layer without depending on zope.testrunner
        SIMPLE_LAYER.setUp()

    def tearDown(self):
        SIMPLE_LAYER.tearDown()

    def test_layer(self):
        """When the layer is setup, the wsgi_app argument is unnecessary"""
        browser = zope.testbrowser.wsgi.Browser()
        browser.open('http://localhost')
        self.assertTrue(browser.contents.startswith('Hello world!\n'))
        # XXX test for authorization header munging is missing

    def test_app_property(self):
        # The layer has a .app property where the application under test is available
        self.assertTrue(SIMPLE_LAYER.get_app() is demo_app)

    def test_there_can_only_be_one(self):
        another_layer = SimpleLayer()
        # The layer has a .app property where the application under test is available
        self.assertRaises(AssertionError, another_layer.setUp)

class TestAuthorizationMiddleware(unittest.TestCase):

    def setUp(self):
        app = WSGITestApplication()
        self.unwrapped_browser = zope.testbrowser.wsgi.Browser(wsgi_app=app)
        app = zope.testbrowser.wsgi.AuthorizationMiddleware(app)
        self.browser = zope.testbrowser.wsgi.Browser(wsgi_app=app)

    def test_unwanted_headers(self):
        #x-powered-by and x-content-type-warning are filtered
        url = 'http://localhost/set_header.html?x-other=another&x-powered-by=zope&x-content-type-warning=bar'
        self.browser.open(url)
        self.assertEquals(self.browser.headers['x-other'], 'another')
        self.assertTrue('x-other' in self.browser.headers)
        self.assertFalse('x-powered-by' in self.browser.headers)
        self.assertFalse('x-content-type-warning' in self.browser.headers)
        # make sure we are actually testing something
        self.unwrapped_browser.open(url)
        self.assertTrue('x-powered-by' in self.unwrapped_browser.headers)
        self.assertTrue('x-content-type-warning' in self.unwrapped_browser.headers)
    
    def test_authorization(self):
        # Basic authorization headers are encoded in base64
        self.browser.addHeader('Authorization', 'Basic mgr:mgrpw')
        self.browser.open('http://localhost/echo_one.html?var=HTTP_AUTHORIZATION')
        self.assertEquals(self.browser.contents, repr('Basic bWdyOm1ncnB3'))

    def test_authorization_other(self):
        # Non-Basic authorization headers are unmolested
        self.browser.addHeader('Authorization', 'Digest foobar')
        self.browser.open('http://localhost/echo_one.html?var=HTTP_AUTHORIZATION')
        self.assertEquals(self.browser.contents, repr('Digest foobar'))
