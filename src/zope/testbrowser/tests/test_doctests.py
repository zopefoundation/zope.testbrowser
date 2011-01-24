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
import zope.app.testing.functional


TestBrowserLayer = zope.app.testing.functional.ZCMLLayer(
    pkg_resources.resource_filename(
        'zope.testbrowser', 'ftests/ftesting.zcml'),
    __name__, 'TestBrowserLayer', allow_teardown=True)


def FileSuite(*filenames):
    kw = dict(optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS,
              checker=zope.testbrowser.tests.helper.checker,
              package='zope.testbrowser')
    suite = zope.app.testing.functional.FunctionalDocFileSuite(
        *filenames, **kw)
    suite.layer = TestBrowserLayer
    return suite


def test_suite():
    suite = FileSuite('README.txt', 'cookies.txt', 'fixed-bugs.txt')
    wire = FileSuite('over_the_wire.txt')
    wire.level = 2

    return unittest.TestSuite((suite, wire))
