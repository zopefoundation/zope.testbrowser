#!/usr/bin/env python
##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Sample test script using zope.testing.testrunner

see zope.testing testrunner.txt

$Id: test.py 70876 2006-10-22 07:42:56Z baijum $
"""

import os, sys

here = os.path.abspath(os.path.dirname(sys.argv[0]))

# Remove this directory from path:
sys.path[:] = [p for p in sys.path if os.path.abspath(p) != here]

src = os.path.join(here, 'src')
sys.path.insert(0, src) # put at beginning to avoid one in site_packages

from zope.testing import testrunner

defaults = [
    '--path', src,
    '--package', 'zope.testbrowser',
    '--tests-pattern', '^tests$',
    ]

sys.exit(testrunner.run(defaults))

