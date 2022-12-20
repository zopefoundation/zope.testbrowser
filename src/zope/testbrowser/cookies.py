##############################################################################
#
# Copyright (c) 2008 Zope Foundation and Contributors.
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
import http.cookies
import time
import urllib.parse
import urllib.request
from collections.abc import MutableMapping
from urllib.parse import quote as url_quote

import pytz
import zope.interface

from zope.testbrowser import interfaces
from zope.testbrowser import utils


# Cookies class helpers


class BrowserStateError(Exception):
    pass


class _StubHTTPMessage:
    def __init__(self, cookies):
        self._cookies = cookies

    def getheaders(self, name, default=[]):
        if name.lower() != 'set-cookie':
            return default
        else:
            return self._cookies

    get_all = getheaders


class _StubResponse:
    def __init__(self, cookies):
        self.message = _StubHTTPMessage(cookies)

    def info(self):
        return self.message


DAY_OF_WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

MONTH = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def expiration_string(expires):  # this is not protected so usable in tests.
    if isinstance(expires, datetime.datetime):
        if expires.tzinfo is not None:
            expires = expires.astimezone(pytz.UTC)
        expires = expires.strftime(
            '{dow}, %d {mon} %Y %H:%M:%S GMT'.format(
                dow=DAY_OF_WEEK[expires.weekday()],
                mon=MONTH[expires.month - 1],
            )
        )
    return expires

# end Cookies class helpers


@zope.interface.implementer(interfaces.ICookies)
class Cookies(MutableMapping):
    """Cookies for testbrowser.
    """

    def __init__(self, testapp, url=None, req_headers=None):
        self.testapp = testapp
        self._url = url
        self._jar = testapp.cookiejar
        self._req_headers = req_headers if req_headers is not None else {}

    @property
    def strict_domain_policy(self):
        policy = self._jar._policy
        flags = (policy.DomainStrictNoDots | policy.DomainRFC2965Match |
                 policy.DomainStrictNonDomain)
        return policy.strict_ns_domain & flags == flags

    @strict_domain_policy.setter
    def strict_domain_policy(self, value):
        jar = self._jar
        policy = jar._policy
        flags = (policy.DomainStrictNoDots | policy.DomainRFC2965Match |
                 policy.DomainStrictNonDomain)
        policy.strict_ns_domain |= flags
        if not value:
            policy.strict_ns_domain ^= flags

    def forURL(self, url):
        return self.__class__(self.testapp, url)

    @property
    def url(self):
        return self._url

    @property
    def _request(self):
        return urllib.request.Request(self._url)

    @property
    def header(self):
        request = self._request
        self._jar.add_cookie_header(request)

        if not request.has_header('Cookie'):
            return ''

        hdr = request.get_header('Cookie')
        # We need a predictable order of cookies for tests, so we reparse and
        # sort the header here.
        return '; '.join(sorted(hdr.split('; ')))

    def __str__(self):
        return self.header

    def __repr__(self):
        # get the cookies for the current url
        return '<{}.{} object at {!r} for {} ({})>'.format(
            self.__class__.__module__, self.__class__.__name__,
            id(self), self.url, self.header)

    def _raw_cookies(self):
        # We are using protected cookielib _cookies_for_request() here to avoid
        # code duplication.

        # Comply with cookielib internal protocol
        self._jar._policy._now = self._jar._now = int(time.time())
        cookies = self._jar._cookies_for_request(self._request)

        # Sort cookies so that the longer paths would come first. This allows
        # masking parent cookies.
        cookies.sort(key=lambda c: (len(c.path), len(c.domain)), reverse=True)
        return cookies

    def _get_cookies(self, key=None):
        if key is None:
            seen = set()
            for ck in self._raw_cookies():
                if ck.name not in seen:
                    yield ck
                    seen.add(ck.name)
        else:
            for ck in self._raw_cookies():
                if ck.name == key:
                    yield ck

    _marker = object()

    def _get(self, key, default=_marker):
        for ck in self._raw_cookies():
            if ck.name == key:
                return ck
        if default is self._marker:
            raise KeyError(key)
        return default

    def __getitem__(self, key):
        return self._get(key).value

    def getinfo(self, key):
        return self._getinfo(self._get(key))

    def _getinfo(self, ck):
        res = {'name': ck.name,
               'value': ck.value,
               'port': ck.port,
               'domain': ck.domain,
               'path': ck.path,
               'secure': ck.secure,
               'expires': None,
               'comment': ck.comment,
               'commenturl': ck.comment_url}
        if ck.expires is not None:
            res['expires'] = datetime.datetime.fromtimestamp(
                ck.expires, pytz.UTC)
        return res

    def keys(self):
        return [ck.name for ck in self._get_cookies()]

    def __iter__(self):
        return (ck.name for ck in self._get_cookies())

    iterkeys = __iter__

    def iterinfo(self, key=None):
        return (self._getinfo(ck) for ck in self._get_cookies(key))

    def iteritems(self):
        return ((ck.name, ck.value) for ck in self._get_cookies())

    def has_key(self, key):
        return self._get(key, None) is not None

    __contains__ = has_key

    def __len__(self):
        return len(list(self._get_cookies()))

    def __delitem__(self, key):
        ck = self._get(key)
        self._jar.clear(ck.domain, ck.path, ck.name)

    def create(self, name, value,
               domain=None, expires=None, path=None, secure=None, comment=None,
               commenturl=None, port=None):
        if value is None:
            raise ValueError('must provide value')
        ck = self._get(name, None)
        if (ck is not None and
            (path is None or ck.path == path) and
            (domain is None or ck.domain == domain or
             ck.domain == domain) and (port is None or ck.port == port)):
            # cookie already exists
            raise ValueError('cookie already exists')
        if domain is not None:
            self._verifyDomain(domain, ck)
        if path is not None:
            self._verifyPath(path, ck)
        now = int(time.time())
        if expires is not None and self._is_expired(expires, now):
            raise zope.testbrowser.interfaces.AlreadyExpiredError(
                'May not create a cookie that is immediately expired')
        self._setCookie(name, value, domain, expires, path, secure, comment,
                        commenturl, port, now=now)

    def change(self, name, value=None, domain=None, expires=None, path=None,
               secure=None, comment=None, commenturl=None, port=None):
        now = int(time.time())
        if expires is not None and self._is_expired(expires, now):
            # shortcut
            del self[name]
        else:
            self._change(self._get(name), value, domain, expires, path, secure,
                         comment, commenturl, port, now)

    def _change(self, ck, value=None,
                domain=None, expires=None, path=None, secure=None,
                comment=None, commenturl=None, port=None, now=None):
        if value is None:
            value = ck.value
        if domain is None:
            domain = ck.domain
        else:
            self._verifyDomain(domain, None)
        if expires is None:
            expires = ck.expires
        if path is None:
            path = ck.path
        else:
            self._verifyPath(domain, None)
        if secure is None:
            secure = ck.secure
        if comment is None:
            comment = ck.comment
        if commenturl is None:
            commenturl = ck.comment_url
        if port is None:
            port = ck.port
        self._setCookie(ck.name, value, domain, expires, path, secure, comment,
                        commenturl, port, ck.version, ck=ck, now=now)

    def _verifyDomain(self, domain, ck):
        tmp_domain = domain
        if domain is not None and domain.startswith('.'):
            tmp_domain = domain[1:]
        self_host = utils.effective_request_host(self._request)
        if (self_host != tmp_domain and
                not self_host.endswith('.' + tmp_domain)):
            raise ValueError('current url must match given domain')
        if (ck is not None and ck.domain != tmp_domain and
                ck.domain.endswith(tmp_domain)):
            raise ValueError(
                'cannot set a cookie that will be hidden by another '
                'cookie for this url (%s)' % (self.url,))

    def _verifyPath(self, path, ck):
        self_path = urllib.parse.urlparse(self.url)[2]
        if not self_path.startswith(path):
            raise ValueError('current url must start with path, if given')
        if ck is not None and ck.path != path and ck.path.startswith(path):
            raise ValueError(
                'cannot set a cookie that will be hidden by another '
                'cookie for this url (%s)' % (self.url,))

    def _setCookie(self, name, value, domain, expires, path, secure, comment,
                   commenturl, port, version=None, ck=None, now=None):
        for nm, val in self._req_headers.items():
            if nm.lower() in ('cookie', 'cookie2'):
                raise ValueError('cookies are already set in `Cookie` header')

        if domain and not domain.startswith('.'):
            # we do a dance here so that we keep names that have been passed
            # in consistent (i.e., if we get an explicit 'example.com' it stays
            # 'example.com', rather than converting to '.example.com').
            tmp_domain = domain
            domain = None
            if secure:
                protocol = 'https'
            else:
                protocol = 'http'
            url = '{}://{}{}'.format(protocol, tmp_domain, path or '/')
            request = urllib.request.Request(url)
        else:
            request = self._request
            if request is None:
                # TODO: fix exception
                raise BrowserStateError(
                    'cannot create cookie without request or domain')
        c = http.cookies.SimpleCookie()
        name = str(name)
        # Cookie value must be native string
        c[name] = value
        if secure:
            c[name]['secure'] = True
        if domain:
            c[name]['domain'] = domain
        if path:
            c[name]['path'] = path
        if expires:
            c[name]['expires'] = expiration_string(expires)
        if comment:
            c[name]['comment'] = url_quote(
                comment.encode('utf-8'), safe="/?:@&+")
        if port:
            c[name]['port'] = port
        if commenturl:
            c[name]['commenturl'] = commenturl
        if version:
            c[name]['version'] = version
        # this use of objects like _StubResponse and _StubHTTPMessage is in
        # fact supported by the documented client cookie API.
        cookies = self._jar.make_cookies(
            _StubResponse([c.output(header='').strip()]), request)
        assert len(cookies) == 1, (
            'programmer error: %d cookies made' % (len(cookies),))
        policy = self._jar._policy
        if now is None:
            now = int(time.time())
        policy._now = self._jar._now = now
        if not policy.set_ok(cookies[0], request):
            raise ValueError('policy does not allow this cookie')
        if ck is not None:
            self._jar.clear(ck.domain, ck.path, ck.name)
        self._jar.set_cookie(cookies[0])

    def __setitem__(self, key, value):
        ck = self._get(key, None)
        if ck is None:
            self.create(key, value)
        else:
            self._change(ck, value)

    def _is_expired(self, value, now):  # now = int(time.time())
        dnow = datetime.datetime.fromtimestamp(now, pytz.UTC)
        if isinstance(value, datetime.datetime):
            if value.tzinfo is None:
                if value <= dnow.replace(tzinfo=None):
                    return True
            elif value <= dnow:
                return True
        elif isinstance(value, str):
            if datetime.datetime.fromtimestamp(
                    utils.http2time(value), pytz.UTC) <= dnow:
                return True
        return False

    def clear(self):
        # to give expected mapping behavior of resulting in an empty dict,
        # we use _raw_cookies rather than _get_cookies.
        for ck in self._raw_cookies():
            self._jar.clear(ck.domain, ck.path, ck.name)

    def clearAllSession(self):
        self._jar.clear_session_cookies()

    def clearAll(self):
        self._jar.clear()

    def pop(self, k, *args):
        """See zope.interface.common.mapping.IExtendedWriteMapping
        """
        # Python3' MutableMapping doesn't offer pop() with variable arguments,
        # so we are reimplementing it here as defined in IExtendedWriteMapping
        super().pop(k, *args)

    def itervalues(self):
        # Method, missing in Py3' MutableMapping, but required by
        # IIterableMapping
        return self.values()

    def iterkeys(self):
        # Method, missing in Py3' MutableMapping, but required by
        # IIterableMapping
        return self.keys()
