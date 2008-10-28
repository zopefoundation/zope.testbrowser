
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


    class UTC(datetime.tzinfo):
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

    def __str__(self):
        return self.header

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

    def set(self, name, value=None,
            domain=None, expires=None, path=None, secure=None, comment=None,
            commenturl=None, port=None):
        request = self._request
        if request is None:
            raise mechanize.BrowserStateError(
                'cannot create cookie without request')
        ck = self._get(name, None)
        use_ck = (ck is not None and
                  (path is None or ck.path == path) and
                  (domain is None or ck.domain == domain))
        if path is not None:
            self_path = urlparse.urlparse(self.url)[2]
            if not self_path.startswith(path):
                raise ValueError('current url must start with path, if given')
            if ck is not None and ck.path != path and ck.path.startswith(path):
                raise ValueError(
                    'cannot set a cookie that will be hidden by another '
                    'cookie for this url (%s)' % (self.url,))
            # you CAN hide an existing cookie, by passing an explicit path
        elif use_ck:
            path = ck.path
        version = None
        if use_ck:
            # keep unchanged existing cookie values
            if domain is None:
                domain = ck.domain
            if value is None:
                value = ck.value
            if port is None:
                port = ck.port
            if comment is None:
                comment = ck.comment
            if commenturl is None:
                commenturl = ck.comment_url
            if secure is None:
                secure = ck.secure
            if expires is None and ck.expires is not None:
                expires = datetime.datetime.fromtimestamp(ck.expires, UTC)
            version = ck.version
        # else...if the domain is bad, set_cookie_if_ok should catch it.
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
        self._jar.set_cookie_if_ok(cookies[0], request)

    def update(self, source=None, **kwargs):
        if isinstance(source, Cookies): # XXX change to ICookies.providedBy
            if self.url != source.url:
                raise ValueError('can only update from another ICookies '
                                 'instance if it shares the identical url')
            elif self is source:
                return
            else:
                for info in source.iterInfo():
                    self.set(info['name'], info['value'], info['expires'],
                             info['domain'], info['path'], info['secure'],
                             info['comment'])
            source = None # to support kwargs
        UserDict.DictMixin.update(self, source, **kwargs)

    def __setitem__(self, key, value):
        self.set(key, value)

    def expire(self, name, expires=None):
        if expires is None:
            del self[name]
        else:
            ck = self._get(name)
            self.set(ck.name, ck.value, expires, ck.domain, ck.path, ck.secure,
                     ck.comment)

    def clear(self):
        # to give expected mapping behavior of resulting in an empty dict,
        # we use _raw_cookies rather than _get_cookies.
        for cookies in self._raw_cookies():
            self._jar.clear(ck.domain, ck.path, ck.name)

    def popinfo(self, key, *args):
        if len(args) > 1:
            raise TypeError, "popinfo expected at most 2 arguments, got "\
                              + repr(1 + len(args))
        ck = self._get(key, None)
        if ck is None:
            if args:
                return args[0]
            raise KeyError(key)
        self._jar.clear(ck.domain, ck.path, ck.name)
        return self._getinfo(ck)

    def clearAllSession(self): # XXX could add optional "domain" filter or similar
        self._jar.clear_session_cookies()

    def clearAll(self): # XXX could add optional "domain" filter or similar
        self._jar.clear()
