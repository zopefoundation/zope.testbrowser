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


def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    suite = zope.app.testing.functional.FunctionalDocFileSuite(
        'README.txt',
        'cookies.txt',
        'fixed-bugs.txt',
        optionflags=flags,
        checker=zope.testbrowser.tests.helper.checker,
        package='zope.testbrowser')
    suite.layer = TestBrowserLayer

    wire = doctest.DocFileSuite('over_the_wire.txt', optionflags=flags,
                                package='zope.testbrowser')
    wire.level = 2

    return unittest.TestSuite((suite, wire))
