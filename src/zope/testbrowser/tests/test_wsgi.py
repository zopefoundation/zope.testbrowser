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
import zope.testbrowser.wsgi


# Copied from PEP #333
def simple_app(environ, start_response):
    """Simplest possible application object"""
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return ['Hello world!\n']


class SimpleLayer(zope.testbrowser.wsgi.Layer):

    def make_wsgi_app(self):
        return simple_app

SIMPLE_LAYER = SimpleLayer()


class TestWSGI(unittest.TestCase):

    layer = SIMPLE_LAYER

    def test_(self):
        browser = zope.testbrowser.wsgi.Browser()
        browser.open('http://localhost')
        self.assertEqual('Hello world!\n', browser.contents)
        # XXX test for authorization header munging is missing
