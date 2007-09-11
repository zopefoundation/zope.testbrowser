##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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

$Id$
"""
import re
import sys
import unittest
import httplib
import urllib2
from cStringIO import StringIO

import mechanize

import transaction
from zope.testbrowser import browser
from zope.testing import renormalizing, doctest

from zope.app.testing import functional
from zope.app.folder.folder import Folder
from zope.app.component.site import LocalSiteManager

class PublisherConnection(object):
    """A ``urllib2`` compatible connection obejct."""

    def __init__(self, host):
        self.caller = functional.HTTPCaller()
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
        headers.insert(0, ('Status', real_response.getStatusString()))
        headers = '\r\n'.join('%s: %s' % h for h in headers)
        content = real_response.consumeBody()
        return PublisherResponse(content, headers, status, reason)


class PublisherResponse(object):
    """``urllib2`` compatible response object."""

    def __init__(self, content, headers, status, reason):
        self.content = content
        self.status = status
        self.reason = reason
        self.msg = httplib.HTTPMessage(StringIO(headers), 0)
        self.content_as_file = StringIO(self.content)

    def read(self, amt=None):
        return self.content_as_file.read(amt)

    def close(self):
        """To overcome changes in urllib2 and socket in python2.5"""
        pass


class PublisherHTTPHandler(urllib2.HTTPHandler):
    """Special HTTP handler to use the Zope Publisher."""

    http_request = urllib2.AbstractHTTPHandler.do_request_

    def http_open(self, req):
        """Open an HTTP connection having a ``urllib2`` request."""
        # Here we connect to the publisher.
        return self.do_open(PublisherConnection, req)


class PublisherMechanizeBrowser(mechanize.Browser):
    """Special ``mechanize`` browser using the Zope Publisher HTTP handler."""

    default_schemes = ['http']
    default_others = ['_http_error', '_http_request_upgrade',
                      '_http_default_error']
    default_features = ['_redirect', '_cookies', '_referer', '_refresh',
                        '_equiv', '_basicauth', '_digestauth']

    def __init__(self, *args, **kws):
        inherited_handlers = ['_unknown', '_http_error',
            '_http_request_upgrade', '_http_default_error', '_basicauth',
            '_digestauth', '_redirect', '_cookies', '_referer',
            '_refresh', '_equiv', '_gzip']

        self.handler_classes = {"http": PublisherHTTPHandler}
        for name in inherited_handlers:
            self.handler_classes[name] = mechanize.Browser.handler_classes[name]

        mechanize.Browser.__init__(self, *args, **kws)


class Browser(browser.Browser):
    """A Zope `testbrowser` Browser that uses the Zope Publisher."""

    def __init__(self, url=None):
        mech_browser = PublisherMechanizeBrowser()
        super(Browser, self).__init__(url=url, mech_browser=mech_browser)

#### virtual host test suites ####

example_path_re = re.compile('http://example.com/virtual_path/')

class VirtualHostingPublisherConnection(PublisherConnection):
    def request(self, method, url, body=None, headers=None):
        if self.host == 'example.com':
            assert url.startswith('/virtual_path')
            url = url[13:]
        if not url:
            url = '/'
        url = '/vh_test_folder/++vh++http:example.com:80/virtual_path/++' + url
        super(VirtualHostingPublisherConnection, self).request(
            method, url, body, headers)

class VirtualHostingPublisherHTTPHandler(urllib2.HTTPHandler):
    """Special HTTP handler to use the Zope Publisher."""

    http_request = urllib2.AbstractHTTPHandler.do_request_

    def http_open(self, req):
        """Open an HTTP connection having a ``urllib2`` request."""
        # Here we connect to the publisher.
        return self.do_open(VirtualHostingPublisherConnection, req)

class VirtualHostingPublisherMechanizeBrowser(PublisherMechanizeBrowser):
    handler_classes = PublisherMechanizeBrowser.handler_classes.copy()
    handler_classes['http'] = VirtualHostingPublisherHTTPHandler

class VirtualHostingBrowser(browser.Browser):
    """A Zope ``testbrowser` Browser that inserts ."""

    def __init__(self, url=None):
        mech_browser = VirtualHostingPublisherMechanizeBrowser()
        super(VirtualHostingBrowser, self).__init__(
            url=url, mech_browser=mech_browser)

def virtualHostingSetUp(test):
    # need to create a folder named vh_test_folder in root
    root = test.globs['getRootFolder']()
    f = Folder()
    root['vh_test_folder'] = f
    f.setSiteManager(LocalSiteManager(f))
    transaction.commit()

def VirtualHostTestBrowserSuite(*paths, **kw):
#    layer=None,
#    globs=None, setUp=None, normalizers=None, **kw):

    if 'checker' in kw:
        raise ValueError(
            'Must not supply custom checker.  To provide values for '
            'zope.testing.renormalizing.RENormalizing checkers, include a '
            '"normalizers" argument that is a list of (compiled regex, '
            'replacement) pairs.')
    kw['package'] = doctest._normalize_module(kw.get('package'))
    layer = kw.pop('layer', None)
    normalizers = kw.pop('normalizers', None)
    vh_kw = kw.copy()
    if 'globs' in kw:
        globs = kw['globs'] = kw['globs'].copy() # don't mutate the original
    else:
        globs = kw['globs'] = {}
    if 'Browser' in globs:
        raise ValueError('"Browser" must not be defined in globs')
    vh_kw['globs'] = globs.copy()
    globs['Browser'] = Browser
    vh_kw['globs']['Browser'] = VirtualHostingBrowser
    def vh_setUp(test):
        virtualHostingSetUp(test)
        if 'setUp' in kw:
            kw['setUp'](test)
    vh_kw['setUp'] = vh_setUp
    if normalizers is not None:
        kw['checker'] = renormalizing.RENormalizing(normalizers)
        vh_normalizers = normalizers[:]
    else:
        vh_normalizers = []
    vh_normalizers.append((example_path_re, 'http://localhost/'))
    vh_kw['checker'] = renormalizing.RENormalizing(vh_normalizers)
    suite = unittest.TestSuite()
    test = functional.FunctionalDocFileSuite(*paths, **kw)
    vh_test = functional.FunctionalDocFileSuite(*paths, **vh_kw)
    vh_test.level = 2
    if layer is not None:
        test.layer = layer
        vh_test.layer = layer
    suite.addTest(test)
    suite.addTest(vh_test)
    return suite
