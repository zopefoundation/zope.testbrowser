##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
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
"""Python compatibility module
"""

import sys


PYTHON3 = sys.version_info[0] == 3
PYTHON2 = sys.version_info[0] == 2

HAVE_MECHANIZE = False

if PYTHON2:
    from base64 import encodestring as base64_encodebytes
    from cgi import escape as html_escape
    from urllib import quote as url_quote
    from urllib import urlencode

    import Cookie as httpcookies
    import httplib as httpclient
    import urllib2 as urllib_request
    import urlparse
else:
    import http.client as httpclient
    import http.cookies as httpcookies
    import urllib.parse as urlparse
    import urllib.request as urllib_request
    from base64 import encodebytes as base64_encodebytes
    from html import escape as html_escape
    from urllib.parse import quote as url_quote
    from urllib.parse import urlencode

try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping
