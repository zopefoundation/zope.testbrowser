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
import doctest

import zope.testbrowser.ftests.wsgitestapp
import zope.testbrowser.tests.helper


def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS

    suite = doctest.DocFileSuite(
        'fixed-bugs.txt',
        optionflags=flags,
        checker=zope.testbrowser.tests.helper.checker,
        package='zope.testbrowser')

    wire = doctest.DocFileSuite('over_the_wire.txt', optionflags=flags,
                                checker=zope.testbrowser.tests.helper.checker,
                                package='zope.testbrowser')
    wire.level = 2
    suite.addTests(wire)

    return suite


# additional_tests is for setuptools "setup.py test" support
additional_tests = test_suite
