
import Cookie
import cookielib
import datetime
import urllib
import urlparse
import UserDict

import mechanize
try:
    from pytz import UTC
except ImportError:

    ZERO = datetime.timedelta(0)
    HOUR = datetime.timedelta(hours=1)


    class _UTC(datetime.tzinfo):
        """UTC

        The reference UTC implementation given in Python docs.
        """
        zone = "UTC"

        def utcoffset(self, dt):
            return ZERO

        def tzname(self, dt):
            return "UTC"

        def dst(self, dt):
            return ZERO

        def localize(self, dt, is_dst=False):
            '''Convert naive time to local time'''
            if dt.tzinfo is not None:
                raise ValueError, 'Not naive datetime (tzinfo is already set)'
            return dt.replace(tzinfo=self)

        def normalize(self, dt, is_dst=False):
            '''Correct the timezone information on the given datetime'''
            if dt.tzinfo is None:
                raise ValueError, 'Naive time - no tzinfo set'
            return dt.replace(tzinfo=self)

        def __repr__(self):
            return "<UTC>"

        def __str__(self):
            return "UTC"

    UTC = _UTC()

import zope.interface
from zope.testbrowser import interfaces

# Cookies class helpers


class _StubHTTPMessage(object):
    def __init__(self, cookies):
        self._cookies = cookies

    def getheaders(self, name):
        if name.lower() != 'set-cookie':
            return []
        else:
            return self._cookies


class _StubResponse(object):
    def __init__(self, cookies):
        self.message = _StubHTTPMessage(cookies)

    def info(self):
        return self.message

def expiration_string(expires): # this is not protected so usable in tests.
    if isinstance(expires, datetime.datetime):
        if expires.tzinfo is not None:
            expires = expires.astimezone(UTC)
        expires = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
    return expires

# end Cookies class helpers


class Cookies(UserDict.DictMixin):
    """Cookies for mechanize browser.
    """

    zope.interface.implements(interfaces.ICookies)

    def __init__(self, mech_browser, url=None):
        self.mech_browser = mech_browser
        self._url = url
        for handler in self.mech_browser.handlers:
            if getattr(handler, 'cookiejar', None) is not None:
                self._jar = handler.cookiejar
                break
        else:
            raise RuntimeError('no cookiejar found')

    def forURL(self, url):
        return self.__class__(self.mech_browser, url)

    @property
    def url(self):
        if self._url is not None:
            return self._url
        else:
            return self.mech_browser.geturl()

    @property
    def _request(self):
        if self._url is not None:
            return self.mech_browser.request_class(self._url)
        else:
            request = self.mech_browser.request
            if request is None:
                raise RuntimeError('no request found')
            return request

    @property
    def header(self):
        request = self.mech_browser.request_class(self.url)
        self._jar.add_cookie_header(request)
        return request.get_header('Cookie')

    def __str__(self):
        return self.header

    def __repr__(self):
        # get the cookies for the current url
        return '<%s.%s object at %r for %s (%s)>' % (
            self.__class__.__module__, self.__class__.__name__,
            id(self), self.url, self.header)

    def _raw_cookies(self):
        # uses protected method of clientcookie, after agonizingly trying not
        # to. XXX
        res = self._jar._cookies_for_request(self._request)
        # _cookies_for_request does not sort by path, as specified by RFC2109
        # (page 9, section 4.3.4) and RFC2965 (page 12, section 3.3.4).
        # We sort by path match, and then, just for something stable, we sort
        # by domain match and by whether the cookie specifies a port.
        # This maybe should be fixed in clientcookie.
        res.sort(key = lambda ck:
            ((ck.path is not None and -(len(ck.path)) or 0),
             (ck.domain is not None and -(len(ck.domain)) or 0),
             ck.port is None))
        return res

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
                ck.expires, UTC)
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
             ck.domain == domain) and
            (port is None or ck.port == port)):
            # cookie already exists
            raise ValueError('cookie already exists')
        if domain is not None:
            self._verifyDomain(domain, ck)
        if path is not None:
            self._verifyPath(path, ck)
        if expires is not None and self._is_expired(expires):
            raise zope.testbrowser.interfaces.AlreadyExpiredError(
                'May not create a cookie that is immediately expired')
        self._setCookie(name, value, domain, expires, path, secure, comment,
                        commenturl, port)

    def change(self, name, value=None,
            domain=None, expires=None, path=None, secure=None, comment=None,
            commenturl=None, port=None):
        if expires is not None and self._is_expired(expires):
            # shortcut
            del self[name]
        else:
            self._change(self._get(name), value, domain, expires, path, secure,
                         comment, commenturl, port)

    def _change(self, ck, value=None,
                domain=None, expires=None, path=None, secure=None,
                comment=None, commenturl=None, port=None):
        if value is None:
            value = ck.value
        if domain is None:
            domain = ck.domain
        else:
            self._verifyDomain(domain, ck)
        if expires is None:
            expires = ck.expires
        if path is None:
            path = ck.path
        else:
            self._verifyPath(domain, ck)
        if secure is None:
            secure = ck.secure
        if comment is None:
            comment = ck.comment
        if commenturl is None:
            commenturl = ck.comment_url
        if port is None:
            port = ck.port
        self._setCookie(ck.name, value, domain, expires, path, secure, comment,
                        commenturl, port, ck.version, ck=ck)

    def _verifyDomain(self, domain, ck):
        if domain is not None and domain.startswith('.'):
            domain = domain[1:]
        self_host = cookielib.eff_request_host(self._request)[1]
        if (self_host != domain and
            not self_host.endswith('.' + domain)):
            raise ValueError('current url must match given domain')
        if (ck is not None and ck.domain != domain and
            ck.domain.endswith(domain)):
            raise ValueError(
                'cannot set a cookie that will be hidden by another '
                'cookie for this url (%s)' % (self.url,))

    def _verifyPath(self, path, ck):
        self_path = urlparse.urlparse(self.url)[2]
        if not self_path.startswith(path):
            raise ValueError('current url must start with path, if given')
        if ck is not None and ck.path != path and ck.path.startswith(path):
            raise ValueError(
                'cannot set a cookie that will be hidden by another '
                'cookie for this url (%s)' % (self.url,))

    def _setCookie(self, name, value, domain, expires, path, secure, comment,
                   commenturl, port, version=None, ck=None):
        for nm, val in self.mech_browser.addheaders:
            if nm.lower() in ('cookie', 'cookie2'):
                raise ValueError('cookies are already set in `Cookie` header')
        if domain:
            # we do a dance here so that we keep names that have been passed
            # in consistent (i.e., if we get an explicit 'example.com' it stays
            # 'example.com', rather than converting to '.example.com').
            if domain.startswith('.'):
                tmp_domain = domain[1:]
            else:
                tmp_domain = domain
                domain = None
            if secure:
                protocol = 'https'
            else:
                protocol = 'http'
            url = '%s://%s%s' % (protocol, tmp_domain, path or '/')
            request = self.mech_browser.request_class(url)
        else:
            request = self._request
            if request is None:
                raise mechanize.BrowserStateError(
                    'cannot create cookie without request or domain')
        c = Cookie.SimpleCookie()
        name = str(name)
        c[name] = value.encode('utf8')
        if secure:
            c[name]['secure'] = True
        if domain:
            c[name]['domain'] = domain
        if path:
            c[name]['path'] = path
        if expires:
            c[name]['expires'] = expiration_string(expires)
        if comment:
            c[name]['comment'] = urllib.quote(
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
        if ck is not None:
            self._jar.clear(ck.domain, ck.path, ck.name)
        self._jar.set_cookie_if_ok(cookies[0], request)

    def __setitem__(self, key, value):
        ck = self._get(key, None)
        if ck is None:
            self.create(key, value)
        else:
            self._change(ck, value)

    def _is_expired(self, value):
        if isinstance(value, datetime.datetime):
            if value.tzinfo is None:
                 if value <= datetime.datetime.utcnow():
                    return True
            elif value <= datetime.datetime.now(UTC):
                return True
        elif isinstance(value, basestring):
            if datetime.datetime.fromtimestamp(
                mechanize.str2time(value),
                UTC) <= datetime.datetime.now(UTC):
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
