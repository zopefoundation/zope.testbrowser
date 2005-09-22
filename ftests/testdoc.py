##############################################################################
#
# Copyright (c) 2005 Zope Corporation. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Visible Source
# License, Version 1.0 (ZVSL).  A copy of the ZVSL should accompany this
# distribution.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Test Browser Tests

$Id$
"""
import unittest
import doctest
from zope.app.testing.functional import FunctionalDocFileSuite


def test_suite():
    return FunctionalDocFileSuite(
        '../README.txt', '../over_the_wire.txt',
        optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
