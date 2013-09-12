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
    import Cookie as httpcookies
    import urlparse
    from urllib import quote as url_quote
    import httplib as httpclient
    import urllib2 as urllib_request
    from cgi import escape as html_escape
    from urllib import urlencode
    from UserDict import DictMixin
    from base64 import encodestring as base64_encodebytes
    class MutableMapping(object, DictMixin):
        pass
else:
    import http.cookies as httpcookies
    import urllib.parse as urlparse
    from urllib.parse import quote as url_quote
    import urllib.request as urllib_request
    from urllib.parse import urlencode
    import http.client as httpclient
    from collections import MutableMapping
    from html import escape as html_escape
    from base64 import encodebytes as base64_encodebytes
