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
"""Base classes sometimes useful to implement browsers
"""
import cStringIO
import httplib
import mechanize
import socket
import sys
import zope.testbrowser.browser


class Response(object):
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

class HTTPHandler(mechanize.HTTPHandler):

    def _connect(self, *args, **kw):
        raise NotImplementedError("implement")

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
        return self.do_open(self._connect, req)

    https_open = http_open

class MechanizeBrowser(mechanize.Browser):
    """Special ``mechanize`` browser using the Zope Publisher HTTP handler."""

    default_schemes = ['http']
    default_others = ['_http_error', '_http_default_error']
    default_features = ['_redirect', '_cookies', '_referer', '_refresh',
                        '_equiv', '_basicauth', '_digestauth']


    def __init__(self, *args, **kws):
        inherited_handlers = ['_unknown', '_http_error',
            '_http_default_error', '_basicauth',
            '_digestauth', '_redirect', '_cookies', '_referer',
            '_refresh', '_equiv', '_gzip']

        self.handler_classes = {"http": self._http_handler}
        for name in inherited_handlers:
            self.handler_classes[name] = mechanize.Browser.handler_classes[name]

        kws['request_class'] = kws.get('request_class',
                                       mechanize._request.Request)

        mechanize.Browser.__init__(self, *args, **kws)

    def _http_handler(self, *args, **kw):
        return NotImplementedError("Try return a sub-class of PublisherHTTPHandler here")


