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
"""Browser Simulator for Functional DocTests

$Id$
"""

# TODO We really don't want to be doing these sys.browser hacks.  We're doing
# them because zpkg doesn't support packaging top-level modules at the moment,
# and because we have patches, incorporated in these versions, that are not
# yet part of an official release of the dependencies (although they have been
# submitted to the maintainer).  It looks likely that 3.2 will ship using these
# hacks, but they will hopefully be addressed by 3.3.
import sys

# stitch in ClientForm
from zope.testbrowser import ClientForm

if 'ClientForm' not in sys.modules:
    sys.modules['ClientForm'] = ClientForm
else:
    assert sys.modules['ClientForm'] is ClientForm
import ClientForm as x
assert x is ClientForm

# stitch in pullparser
from zope.testbrowser import pullparser

if 'pullparser' not in sys.modules:
    sys.modules['pullparser'] = pullparser
else:
    assert sys.modules['pullparser'] is pullparser
import pullparser as x
assert x is pullparser
# end TODO

from testing import Browser
