##############################################################################
#
# Copyright (c) 2004-2011 Zope Foundation and Contributors.
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
import doctest
import pkg_resources
import unittest

import zope.testbrowser.ftests.wsgitestapp
import zope.testbrowser.wsgi

def make_browser(*args, **kw):
    assert 'wsgi_app' not in kw
    kw['wsgi_app'] = zope.testbrowser.ftests.wsgitestapp.WSGITestApplication()
    return zope.testbrowser.wsgi.Browser(*args, **kw)

def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS

    suite = doctest.DocFileSuite(
        'README.txt',
        'cookies.txt',
        'wsgi.txt',
        'fixed-bugs.txt',
        optionflags=flags,
        globs=dict(Browser=make_browser),
        checker=zope.testbrowser.tests.helper.checker,
        package='zope.testbrowser')

    wire = doctest.DocFileSuite('over_the_wire.txt', optionflags=flags,
                                package='zope.testbrowser')
    wire.level = 2

    return unittest.TestSuite((suite, wire))
