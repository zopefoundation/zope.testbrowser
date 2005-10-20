##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
"""Test Browser Tests

$Id$
"""
import unittest
import doctest
from zope.app.testing.functional import FunctionalDocFileSuite

def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    readme = FunctionalDocFileSuite('../README.txt', optionflags=flags)
    wire = FunctionalDocFileSuite('../over_the_wire.txt', optionflags=flags)
    wire.level = 2
    return unittest.TestSuite((readme, wire))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
