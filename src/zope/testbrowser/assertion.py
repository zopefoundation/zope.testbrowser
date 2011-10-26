#############################################################################
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

import difflib
import doctest


class Ellipsis(object):
    """Assertion helper that provides doctest-style ellipsis matching.

    Inherit from this class in additition to unittest.TestCase.

    For convenience when using this with a zope.testbrowser, if no ``actual``
    value is provided, ``self.browser.contents`` is used.
    """

    def assertEllipsis(self, expected, actual=None):
        if actual is None:
            actual = self.browser.contents
        # normalize whitespace
        norm_expected = ' '.join(expected.split())
        norm_actual = ' '.join(actual.split())
        if doctest._ellipsis_match(norm_expected, norm_actual):
            return True
        # report ndiff
        engine = difflib.Differ(charjunk=difflib.IS_CHARACTER_JUNK)
        diff = list(engine.compare(expected.splitlines(True),
                                   actual.splitlines(True)))
        kind = 'ndiff with -expected +actual'
        diff = [line.rstrip() + '\n' for line in diff]
        self.fail('Differences (%s):\n' % kind + ''.join(diff))

    def assertNotEllipsis(self, expected, actual=None):
        try:
            self.assertEllipsis(expected, actual)
        except AssertionError:
            pass
        else:
            self.fail('Value unexpectedly matches expression %r.' % expected)
