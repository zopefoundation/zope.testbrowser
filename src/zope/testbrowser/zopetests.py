##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Real test for file-upload and beginning of a better internal test framework

$Id$
"""

from zope.testing import doctest
import os.path
import unittest
import zope.app.testing.functional
import zope.testbrowser.testing
import zope.testbrowser.tests

TestBrowserLayer = zope.app.testing.functional.ZCMLLayer(
    os.path.join(os.path.split(__file__)[0], 'ftests/ftesting.zcml'),
    __name__, 'TestBrowserLayer', allow_teardown=True)

def setUp(test):
    test.globs['browser'] = zope.testbrowser.testing.Browser()

def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS

    readme = zope.app.testing.functional.FunctionalDocFileSuite('Zope.txt',
        optionflags=flags, checker=zope.testbrowser.tests.checker, setUp=setUp)
    readme.layer = TestBrowserLayer

    return unittest.TestSuite((readme,))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
