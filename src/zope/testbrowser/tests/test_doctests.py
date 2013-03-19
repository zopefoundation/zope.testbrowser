##############################################################################
#
# Copyright (c) 2004-2011 Zope Foundation and Contributors.
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
import sys
import doctest
#import pkg_resources
import unittest

import zope.testbrowser.ftests.wsgitestapp
#import zope.testbrowser.wsgi
import zope.testbrowser.tests.helper

def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS

    suite = doctest.DocFileSuite(
        'README.txt',
        'cookies.txt',
        'fixed-bugs.txt',
        optionflags=flags,
        checker=zope.testbrowser.tests.helper.checker,
        package='zope.testbrowser')

    if sys.version_info[:2] != (2, 6):
        # Under python-2.6, python's html parser cannot parse html from google,
        # so we skip this test
        wire = doctest.DocFileSuite('over_the_wire.txt', optionflags=flags,
                                    checker=zope.testbrowser.tests.helper.checker,
                                    package='zope.testbrowser')
        wire.level = 2
        suite.addTests(wire)

    #return unittest.TestSuite([suite, wire])
    return suite

# additional_tests is for setuptools "setup.py test" support
additional_tests = test_suite
