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
"""BBB for Zope 3-specific testing code
"""

from wsgiref.simple_server import demo_app as wsgiref_demo_app


class Browser(object):
    """zope.testbrowser.testing.Browser is no longer supported.

    Please use zope.testbrowser.wsgi.Browser() in conjuction with
    zope.app.wsgi.testlayer.BrowserLayer(), or some other custom test layer
    that inherits from zope.testbrowser.wsgi.Layer.

    Alternatively pin zope.testbrowser version to < 5.0.0 if you don't care
    for Python 3 support and don't have the time to update your tests now.
    """

    def __init__(self, *args, **kw):
        raise NotImplementedError(self.__doc__)


def demo_app(environ, start_response):
    """PEP-3333 compatible demo app, that will never return unicode
    """
    refout = wsgiref_demo_app(environ, start_response)
    return [s if isinstance(s, bytes) else s.encode('utf-8') for s in refout]
