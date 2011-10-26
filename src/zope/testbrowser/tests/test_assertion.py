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

import unittest
import zope.testbrowser.assertion


class EllipsisTest(unittest.TestCase, zope.testbrowser.assertion.Ellipsis):

    def test_match_found_nothing_happens(self):
        # assert nothing is raised
        self.assertEllipsis('...bar...', 'foo bar baz')

    def test_no_match_found_fails(self):
        try:
            self.assertEllipsis('foo', 'bar')
        except AssertionError, e:
            self.assertEqual(
                'Differences (ndiff with -expected +actual):\n- foo\n+ bar\n',
                str(e))
        else:
            self.fail('nothing raised')

    def test_unicode_matches_encoded(self):
        # assert nothing is raised
        self.assertEllipsis(u'...bar...', u'foo bar baz'.encode('utf-8'))

    def test_encoded_matches_unicode(self):
        # assert nothing is raised
        self.assertEllipsis(u'...bar...'.encode('utf-8'), u'foo bar baz')

    def test_inverse_assertion(self):
        # assert nothing is raised
        self.assertNotEllipsis('foo', 'bar')

        try:
            self.assertNotEllipsis('...bar...', 'foo bar baz')
        except AssertionError, e:
            self.assertEqual(
                "Value unexpectedly matches expression '...bar...'.",
                str(e))
        else:
            self.fail('nothing raised')
