##############################################################################
#
# Copyright (c) 2019 Zope Foundation and Contributors.
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

import datetime
import locale
import unittest

import pytz

from zope.testbrowser.cookies import expiration_string


class TestExpirationString(unittest.TestCase):

    def test_string(self):
        self.assertEqual(expiration_string("Wed, 02 Jan 2019 00:00:00 GMT"),
                         "Wed, 02 Jan 2019 00:00:00 GMT")

    def test_naive_datetime(self):
        self.assertEqual(expiration_string(datetime.datetime(2019, 1, 2)),
                         "Wed, 02 Jan 2019 00:00:00 GMT")

    def test_timezone(self):
        zone = pytz.timezone('Europe/Vilnius')
        dt = zone.localize(datetime.datetime(2019, 1, 2, 14, 35))
        self.assertEqual(expiration_string(dt),
                         "Wed, 02 Jan 2019 12:35:00 GMT")

    def test_locale_independence(self):
        old_locale = locale.setlocale(locale.LC_TIME, "")
        self.addCleanup(locale.setlocale, locale.LC_TIME, old_locale)
        self.assertEqual(expiration_string(datetime.datetime(2019, 1, 2)),
                         "Wed, 02 Jan 2019 00:00:00 GMT")
