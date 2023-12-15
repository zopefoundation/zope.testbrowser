##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
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
import re

import zope.testing.renormalizing


class win32CRLFtransformer:
    def sub(self, replacement, text):
        return text.replace(r'\r', '')


checker = zope.testing.renormalizing.RENormalizing([
    (re.compile(r'^--\S+\.\S+\.\S+', re.M), '-' * 30),
    (re.compile(r'boundary=\S+\.\S+\.\S+'), 'boundary=' + '-' * 30),
    (re.compile(r'^---{10}.*', re.M), '-' * 30),
    (re.compile(r'boundary=-{10}.*'), 'boundary=' + '-' * 30),
    (re.compile(r'Content-[Ll]ength:.*'), 'Content-Length: 123'),
    (re.compile(r'Status: 200.*'), 'Status: 200 OK'),
    (win32CRLFtransformer(), None),
    # (re.compile(r'Host: localhost(:80)?'), 'Connection: close'),
    (re.compile(r'Content-Type: '), 'Content-type: '),
    (re.compile(r'Content-Disposition: '), 'Content-disposition: '),
    (re.compile(r'; charset=UTF-8'), ';charset=utf-8'),
    # webtest seems to expire cookies one second before the date
    # set in set_cookie
    (re.compile(r"'expires': datetime.datetime\(2029, 12, 31, 23, "
                r"59, 59, tzinfo=<UTC>\),"),
     "'expires': datetime.datetime(2030, 1, 1, 0, 0, tzinfo=<UTC>),"),

    # Ignore output returned by GHA for PyPy3
    (re.compile('/etc/ssl/certs/ca-certificates.crt /etc/ssl/certs'), ''),
])
