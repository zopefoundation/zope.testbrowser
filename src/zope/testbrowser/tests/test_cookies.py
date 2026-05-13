##############################################################################
#
# Copyright (c) 2019 Zope Foundation and Contributors.
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

import datetime
import locale
import unittest

import pytz

from zope.testbrowser.cookies import expiration_string


class TestCookieInfo(unittest.TestCase):
    """Tests for getinfo/iterinfo that used to be pprint-based doctests."""

    def setUp(self):
        from zope.testbrowser.ftests.wsgitestapp import WSGITestApplication
        from zope.testbrowser.wsgi import Browser
        self.wsgi_app = WSGITestApplication()
        self.browser = Browser(wsgi_app=self.wsgi_app)

    def test_getinfo_foo(self):
        browser = self.browser
        browser.open('http://localhost/set_cookie.html?name=foo&value=bar')
        self.assertEqual(browser.cookies.getinfo('foo'), {
            'comment': None,
            'commenturl': None,
            'domain': 'localhost.local',
            'expires': None,
            'name': 'foo',
            'path': '/',
            'port': None,
            'secure': False,
            'value': 'bar',
        })

    def test_getinfo_sha(self):
        browser = self.browser
        browser.open('http://localhost/set_cookie.html?name=foo&value=bar')
        browser.cookies['sha'] = 'zam'
        self.assertEqual(browser.cookies.getinfo('sha'), {
            'comment': None,
            'commenturl': None,
            'domain': 'localhost.local',
            'expires': None,
            'name': 'sha',
            'path': '/',
            'port': None,
            'secure': False,
            'value': 'zam',
        })

    def test_getinfo_wow_with_expires(self):
        browser = self.browser
        browser.open('http://localhost/set_cookie.html?name=foo&value=bar')
        expires = datetime.datetime(2030, 1, 1, 12, 22, 33).strftime(
            '%a, %d %b %Y %H:%M:%S GMT')
        browser.open(
            'http://localhost/set_cookie.html?name=wow&value=wee&'
            'expires=%s' % (expires,))
        info = browser.cookies.getinfo('wow')
        self.assertEqual(info['name'], 'wow')
        self.assertEqual(info['value'], 'wee')
        self.assertEqual(info['domain'], 'localhost.local')
        self.assertEqual(info['path'], '/')
        self.assertEqual(info['secure'], False)
        self.assertIsNotNone(info['expires'])
        self.assertEqual(info['expires'].year, 2030)
        self.assertEqual(info['expires'].month, 1)
        self.assertEqual(info['expires'].day, 1)

    def test_getinfo_max_with_maxage(self):
        browser = self.browser
        browser.open('http://localhost/set_cookie.html?name=foo&value=bar')
        browser.open(
            'http://localhost/set_cookie.html?name=max&value=min&'
            'max-age=3000&&comment=silly+billy')
        info = browser.cookies.getinfo('max')
        self.assertEqual(info['name'], 'max')
        self.assertEqual(info['value'], 'min')
        self.assertEqual(info['comment'], '"silly billy"')
        self.assertEqual(info['domain'], 'localhost.local')
        self.assertIsNotNone(info['expires'])

    def test_iterinfo_all(self):
        browser = self.browser
        browser.open('http://localhost/set_cookie.html?name=foo&value=bar')
        browser.cookies['sha'] = 'zam'
        browser.cookies.update({'va': 'voom'})
        expires = datetime.datetime(2030, 1, 1, 12, 22, 33).strftime(
            '%a, %d %b %Y %H:%M:%S GMT')
        browser.open(
            'http://localhost/set_cookie.html?name=wow&value=wee&'
            'expires=%s' % (expires,))
        browser.open(
            'http://localhost/set_cookie.html?name=max&value=min&'
            'max-age=3000&&comment=silly+billy')
        infos = sorted(browser.cookies.iterinfo(),
                       key=lambda info: info['name'])
        names = [i['name'] for i in infos]
        self.assertIn('foo', names)
        self.assertIn('sha', names)
        self.assertIn('va', names)
        self.assertIn('wow', names)
        self.assertIn('max', names)

    def test_getinfo_bling_created(self):
        browser = self.browser
        browser.open(
            'http://localhost/inner/set_cookie.html?name=foo&value=bar')
        browser.cookies.create(
            'bling', value='blang', path='/inner',
            expires=datetime.datetime(2030, 1, 1, tzinfo=pytz.UTC),
            comment='follow swallow')
        self.assertEqual(browser.cookies.getinfo('bling'), {
            'comment': 'follow%20swallow',
            'commenturl': None,
            'domain': 'localhost.local',
            'expires': datetime.datetime(2030, 1, 1, 0, 0, tzinfo=pytz.UTC),
            'name': 'bling',
            'path': '/inner',
            'port': None,
            'secure': False,
            'value': 'blang',
        })

    def test_getinfo_tweedle_created(self):
        browser = self.browser
        browser.open('https://dev.example.com/inner/path/get_cookie.html')
        browser.cookies.create('tweedle', 'dee')
        self.assertEqual(browser.cookies.getinfo('tweedle'), {
            'comment': None,
            'commenturl': None,
            'domain': 'dev.example.com',
            'expires': None,
            'name': 'tweedle',
            'path': '/inner/path',
            'port': None,
            'secure': False,
            'value': 'dee',
        })

    def test_getinfo_boo_created_with_domain(self):
        browser = self.browser
        browser.open('https://dev.example.com/inner/path/get_cookie.html')
        browser.cookies.create(
            'boo', 'yah', domain='.example.com', path='/inner', secure=True)
        self.assertEqual(browser.cookies.getinfo('boo'), {
            'comment': None,
            'commenturl': None,
            'domain': '.example.com',
            'expires': None,
            'name': 'boo',
            'path': '/inner',
            'port': None,
            'secure': True,
            'value': 'yah',
        })

    def test_iterinfo_boo_masked_by_path(self):
        browser = self.browser
        browser.open('https://dev.example.com/inner/path/get_cookie.html')
        browser.cookies.create('tweedle', 'dee')
        browser.cookies.create(
            'boo', 'yah', domain='.example.com', path='/inner', secure=True)
        browser.cookies['boo'] = 'hoo'
        browser.cookies.create('boo', 'boo', path='/inner/path')
        infos = list(browser.cookies.iterinfo('boo'))
        self.assertEqual(len(infos), 2)
        self.assertEqual(infos[0]['value'], 'boo')
        self.assertEqual(infos[0]['path'], '/inner/path')
        self.assertEqual(infos[0]['secure'], False)
        self.assertEqual(infos[1]['value'], 'hoo')
        self.assertEqual(infos[1]['path'], '/inner')
        self.assertEqual(infos[1]['secure'], True)

    def test_iterinfo_boo_masked_by_domain(self):
        browser = self.browser
        browser.open('https://dev.example.org/get_cookie.html')
        browser.cookies.create('tweedle', 'dee')
        browser.cookies.create('boo', 'yah', domain='example.org',
                               secure=True)
        browser.cookies['boo'] = 'hoo'
        browser.cookies.create('boo', 'boo', domain='dev.example.org')
        infos = list(browser.cookies.iterinfo('boo'))
        self.assertEqual(len(infos), 2)
        self.assertEqual(infos[0]['value'], 'boo')
        self.assertEqual(infos[0]['domain'], 'dev.example.org')
        self.assertEqual(infos[0]['secure'], False)
        self.assertEqual(infos[1]['value'], 'hoo')
        self.assertEqual(infos[1]['domain'], 'example.org')
        self.assertEqual(infos[1]['secure'], True)


class TestExpirationString(unittest.TestCase):

    def test_string(self):
        self.assertEqual(expiration_string("Wed, 02 Jan 2019 00:00:00 GMT"),
                         "Wed, 02 Jan 2019 00:00:00 GMT")

    def test_naive_datetime(self):
        self.assertEqual(expiration_string(datetime.datetime(2019, 1, 2)),
                         "Wed, 02 Jan 2019 00:00:00 GMT")

    def test_timezone(self):
        zone = pytz.timezone('Europe/Vilnius')
        dt = zone.localize(datetime.datetime(2019, 1, 2, 14, 35))
        self.assertEqual(expiration_string(dt),
                         "Wed, 02 Jan 2019 12:35:00 GMT")

    def test_locale_independence(self):
        old_locale = locale.setlocale(locale.LC_TIME, "")
        self.addCleanup(locale.setlocale, locale.LC_TIME, old_locale)
        self.assertEqual(expiration_string(datetime.datetime(2019, 1, 2)),
                         "Wed, 02 Jan 2019 00:00:00 GMT")
