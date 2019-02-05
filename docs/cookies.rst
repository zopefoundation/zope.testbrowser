Working with Cookies
====================

Getting started
---------------

The cookies mapping has an extended mapping interface that allows getting,
setting, and deleting the cookies that the browser is remembering for the
current url, or for an explicitly provided URL.

.. doctest::

    >>> from zope.testbrowser.ftests.wsgitestapp import WSGITestApplication
    >>> from zope.testbrowser.wsgi import Browser

    >>> wsgi_app = WSGITestApplication()
    >>> browser = Browser(wsgi_app=wsgi_app)

Initially the browser does not point to a URL, and the cookies cannot be used.

.. doctest::

    >>> len(browser.cookies)
    Traceback (most recent call last):
    ...
    RuntimeError: no request found
    >>> browser.cookies.keys()
    Traceback (most recent call last):
    ...
    RuntimeError: no request found

Once you send the browser to a URL, the cookies attribute can be used.

.. doctest::

    >>> browser.open('http://localhost/@@/testbrowser/simple.html')
    >>> len(browser.cookies)
    0
    >>> browser.cookies.keys()
    []
    >>> browser.url
    'http://localhost/@@/testbrowser/simple.html'
    >>> browser.cookies.url
    'http://localhost/@@/testbrowser/simple.html'
    >>> import zope.testbrowser.interfaces
    >>> from zope.interface.verify import verifyObject
    >>> verifyObject(zope.testbrowser.interfaces.ICookies, browser.cookies)
    True

Alternatively, you can use the ``forURL`` method to get another instance of
the cookies mapping for the given URL.

.. doctest::

    >>> len(browser.cookies.forURL('http://www.example.com'))
    0
    >>> browser.cookies.forURL('http://www.example.com').keys()
    []
    >>> browser.cookies.forURL('http://www.example.com').url
    'http://www.example.com'
    >>> browser.url
    'http://localhost/@@/testbrowser/simple.html'
    >>> browser.cookies.url
    'http://localhost/@@/testbrowser/simple.html'

Here, we use a view that will make the server set cookies with the
values we provide.

.. doctest::

    >>> browser.open('http://localhost/set_cookie.html?name=foo&value=bar')
    >>> browser.headers['set-cookie'].replace(';', '')
    'foo=bar'


Basic Mapping Interface
-----------------------

Now the cookies for localhost have a value.  These are examples of just the
basic accessor operators and methods.

.. doctest::

    >>> browser.cookies['foo']
    'bar'
    >>> list(browser.cookies.keys())
    ['foo']
    >>> list(browser.cookies.values())
    ['bar']
    >>> list(browser.cookies.items())
    [('foo', 'bar')]
    >>> 'foo' in browser.cookies
    True
    >>> 'bar' in browser.cookies
    False
    >>> len(browser.cookies)
    1
    >>> print(dict(browser.cookies))
    {'foo': 'bar'}

As you would expect, the cookies attribute can also be used to examine cookies
that have already been set in a previous request.  To demonstrate this, we use
another view that does not set cookies but reports on the cookies it receives
from the browser.

.. doctest::

    >>> browser.open('http://localhost/get_cookie.html')
    >>> print(browser.headers.get('set-cookie'))
    None
    >>> browser.contents
    'foo: bar'
    >>> browser.cookies['foo']
    'bar'

The standard mapping mutation methods and operators are also available, as
seen here.

.. doctest::

    >>> browser.cookies['sha'] = 'zam'
    >>> len(browser.cookies)
    2
    >>> import pprint
    >>> pprint.pprint(sorted(browser.cookies.items()))
    [('foo', 'bar'), ('sha', 'zam')]
    >>> browser.open('http://localhost/get_cookie.html')
    >>> print(browser.headers.get('set-cookie'))
    None
    >>> print(browser.contents) # server got the cookie change
    foo: bar
    sha: zam
    >>> browser.cookies.update({'va': 'voom', 'tweedle': 'dee'})
    >>> pprint.pprint(sorted(browser.cookies.items()))
    [('foo', 'bar'), ('sha', 'zam'), ('tweedle', 'dee'), ('va', 'voom')]
    >>> browser.open('http://localhost/get_cookie.html')
    >>> print(browser.headers.get('set-cookie'))
    None
    >>> print(browser.contents)
    foo: bar
    sha: zam
    tweedle: dee
    va: voom
    >>> del browser.cookies['foo']
    >>> del browser.cookies['tweedle']
    >>> browser.open('http://localhost/get_cookie.html')
    >>> print(browser.contents)
    sha: zam
    va: voom


Headers
~~~~~~~

You can see the Cookies header that will be sent to the browser in the
``header`` attribute and the repr and str.

.. doctest::

    >>> browser.cookies.header
    'sha=zam; va=voom'
    >>> browser.cookies # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    <zope.testbrowser.cookies.Cookies object at ... for
     http://localhost/get_cookie.html (sha=zam; va=voom)>
    >>> str(browser.cookies)
    'sha=zam; va=voom'


Extended Mapping Interface
--------------------------

Read Methods: ``getinfo`` and ``iterinfo``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``getinfo``
###########

The ``cookies`` mapping also has an extended interface to get and set extra
information about each cookie.
:meth:`zope.testbrowser.interfaces.ICookie.getinfo` returns a dictionary.

Here are some examples.

.. doctest::

    >>> browser.open('http://localhost/set_cookie.html?name=foo&value=bar')
    >>> pprint.pprint(browser.cookies.getinfo('foo'))
    {'comment': None,
     'commenturl': None,
     'domain': 'localhost.local',
     'expires': None,
     'name': 'foo',
     'path': '/',
     'port': None,
     'secure': False,
     'value': 'bar'}
    >>> pprint.pprint(browser.cookies.getinfo('sha'))
    {'comment': None,
     'commenturl': None,
     'domain': 'localhost.local',
     'expires': None,
     'name': 'sha',
     'path': '/',
     'port': None,
     'secure': False,
     'value': 'zam'}
    >>> import datetime
    >>> expires = datetime.datetime(2030, 1, 1, 12, 22, 33).strftime(
    ...     '%a, %d %b %Y %H:%M:%S GMT')
    >>> browser.open(
    ...     'http://localhost/set_cookie.html?name=wow&value=wee&'
    ...     'expires=%s' %
    ...     (expires,))
    >>> pprint.pprint(browser.cookies.getinfo('wow'))
    {'comment': None,
     'commenturl': None,
     'domain': 'localhost.local',
     'expires': datetime.datetime(2030, 1, 1, 12, 22, ...tzinfo=<UTC>),
     'name': 'wow',
     'path': '/',
     'port': None,
     'secure': False,
     'value': 'wee'}

Max-age is converted to an "expires" value.

.. doctest::

    >>> browser.open(
    ...     'http://localhost/set_cookie.html?name=max&value=min&'
    ...     'max-age=3000&&comment=silly+billy')
    >>> pprint.pprint(browser.cookies.getinfo('max')) # doctest: +ELLIPSIS
    {'comment': '"silly billy"',
     'commenturl': None,
     'domain': 'localhost.local',
     'expires': datetime.datetime(..., tzinfo=<UTC>),
     'name': 'max',
     'path': '/',
     'port': None,
     'secure': False,
     'value': 'min'}


``iterinfo``
############

You can iterate over all of the information about the cookies for the current
page using the ``iterinfo`` method.

.. doctest::

    >>> pprint.pprint(sorted(browser.cookies.iterinfo(),
    ...                      key=lambda info: info['name']))
    ... # doctest: +ELLIPSIS
    [{'comment': None,
      'commenturl': None,
      'domain': 'localhost.local',
      'expires': None,
      'name': 'foo',
      'path': '/',
      'port': None,
      'secure': False,
      'value': 'bar'},
     {'comment': '"silly billy"',
      'commenturl': None,
      'domain': 'localhost.local',
      'expires': datetime.datetime(..., tzinfo=<UTC>),
      'name': 'max',
      'path': '/',
      'port': None,
      'secure': False,
      'value': 'min'},
     {'comment': None,
      'commenturl': None,
      'domain': 'localhost.local',
      'expires': None,
      'name': 'sha',
      'path': '/',
      'port': None,
      'secure': False,
      'value': 'zam'},
     {'comment': None,
      'commenturl': None,
      'domain': 'localhost.local',
      'expires': None,
      'name': 'va',
      'path': '/',
      'port': None,
      'secure': False,
      'value': 'voom'},
     {'comment': None,
      'commenturl': None,
      'domain': 'localhost.local',
      'expires': datetime.datetime(2030, 1, 1, 12, 22, ...tzinfo=<UTC>),
      'name': 'wow',
      'path': '/',
      'port': None,
      'secure': False,
      'value': 'wee'}]


Extended Examples
#################

If you want to look at the cookies for another page, you can either navigate to
the other page in the browser, or, as already mentioned, you can use the
``forURL`` method, which returns an ICookies instance for the new URL.

.. doctest::

    >>> sorted(browser.cookies.forURL(
    ...     'http://localhost/inner/set_cookie.html').keys())
    ['foo', 'max', 'sha', 'va', 'wow']
    >>> extra_cookie = browser.cookies.forURL(
    ...     'http://localhost/inner/set_cookie.html')
    >>> extra_cookie['gew'] = 'gaw'
    >>> extra_cookie.getinfo('gew')['path']
    '/inner'
    >>> sorted(extra_cookie.keys())
    ['foo', 'gew', 'max', 'sha', 'va', 'wow']
    >>> sorted(browser.cookies.keys())
    ['foo', 'max', 'sha', 'va', 'wow']

    >>> browser.open('http://localhost/inner/get_cookie.html')
    >>> print(browser.contents) # has gewgaw
    foo: bar
    gew: gaw
    max: min
    sha: zam
    va: voom
    wow: wee
    >>> browser.open('http://localhost/inner/path/get_cookie.html')
    >>> print(browser.contents) # has gewgaw
    foo: bar
    gew: gaw
    max: min
    sha: zam
    va: voom
    wow: wee
    >>> browser.open('http://localhost/get_cookie.html')
    >>> print(browser.contents) # NO gewgaw
    foo: bar
    max: min
    sha: zam
    va: voom
    wow: wee

Here's an example of the server setting a cookie that is only available on an
inner page.

.. doctest::

    >>> browser.open(
    ...     'http://localhost/inner/path/set_cookie.html?name=big&value=kahuna'
    ...     )
    >>> browser.cookies['big']
    'kahuna'
    >>> browser.cookies.getinfo('big')['path']
    '/inner/path'
    >>> browser.cookies.getinfo('gew')['path']
    '/inner'
    >>> browser.cookies.getinfo('foo')['path']
    '/'
    >>> print(browser.cookies.forURL('http://localhost/').get('big'))
    None


Write Methods: ``create`` and ``change``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The basic mapping API only allows setting values.  If a cookie already exists
for the given name, it's value will be changed; or else a new cookie will be
created for the current request's domain and a path of '/', set to last for
only this browser session (a "session" cookie).

To create or change cookies with different additional information, use the
``create`` and ``change`` methods, respectively.  Here is an example of
``create``.

.. doctest::

    >>> from pytz import UTC
    >>> browser.cookies.create(
    ...     'bling', value='blang', path='/inner',
    ...     expires=datetime.datetime(2030, 1, 1, tzinfo=UTC),
    ...     comment='follow swallow')
    >>> pprint.pprint(browser.cookies.getinfo('bling'))
    {'comment': 'follow%20swallow',
     'commenturl': None,
     'domain': 'localhost.local',
     'expires': datetime.datetime(2030, 1, 1, 0, 0, tzinfo=<UTC>),
     'name': 'bling',
     'path': '/inner',
     'port': None,
     'secure': False,
     'value': 'blang'}

In these further examples of ``create``, note that the testbrowser sends all
domains to Zope, and both http and https.

.. doctest::

    >>> browser.open('https://dev.example.com/inner/path/get_cookie.html')
    >>> browser.cookies.keys() # a different domain
    []
    >>> browser.cookies.create('tweedle', 'dee')
    >>> pprint.pprint(browser.cookies.getinfo('tweedle'))
    {'comment': None,
     'commenturl': None,
     'domain': 'dev.example.com',
     'expires': None,
     'name': 'tweedle',
     'path': '/inner/path',
     'port': None,
     'secure': False,
     'value': 'dee'}
    >>> browser.cookies.create(
    ...     'boo', 'yah', domain='.example.com', path='/inner', secure=True)
    >>> pprint.pprint(browser.cookies.getinfo('boo'))
    {'comment': None,
     'commenturl': None,
     'domain': '.example.com',
     'expires': None,
     'name': 'boo',
     'path': '/inner',
     'port': None,
     'secure': True,
     'value': 'yah'}
    >>> sorted(browser.cookies.keys())
    ['boo', 'tweedle']
    >>> browser.open('https://dev.example.com/inner/path/get_cookie.html')
    >>> print(browser.contents)
    boo: yah
    tweedle: dee
    >>> browser.open( # not https, so not secure, so not 'boo'
    ...     'http://dev.example.com/inner/path/get_cookie.html')
    >>> sorted(browser.cookies.keys())
    ['tweedle']
    >>> print(browser.contents)
    tweedle: dee
    >>> browser.open( # not tweedle's domain
    ...     'https://prod.example.com/inner/path/get_cookie.html')
    >>> sorted(browser.cookies.keys())
    ['boo']
    >>> print(browser.contents)
    boo: yah
    >>> browser.open( # not tweedle's domain
    ...     'https://example.com/inner/path/get_cookie.html')
    >>> sorted(browser.cookies.keys())
    ['boo']
    >>> print(browser.contents)
    boo: yah
    >>> browser.open( # not tweedle's path
    ...     'https://dev.example.com/inner/get_cookie.html')
    >>> sorted(browser.cookies.keys())
    ['boo']
    >>> print(browser.contents)
    boo: yah


Masking by Path
###############

The API allows creation of cookies that mask existing cookies, but it does not
allow creating a cookie that will be immediately masked upon creation. Having
multiple cookies with the same name for a given URL is rare, and is a
pathological case for using a mapping API to work with cookies, but it is
supported to some degree, as demonstrated below.  Note that the Cookie RFCs
(2109, 2965) specify that all matching cookies be sent to the server, but with
an ordering so that more specific paths come first. We also prefer more
specific domains, though the RFCs state that the ordering of cookies with the
same path is indeterminate.  The best-matching cookie is the one that the
mapping API uses.

Also note that ports, as sent by RFC 2965's Cookie2 and Set-Cookie2 headers,
are parsed and stored by this API but are not used for filtering as of this
writing.

This is an example of making one cookie that masks another because of path.
First, unless you pass an explicit path, you will be modifying the existing
cookie.

.. doctest::

    >>> browser.open('https://dev.example.com/inner/path/get_cookie.html')
    >>> print(browser.contents)
    boo: yah
    tweedle: dee
    >>> browser.cookies.getinfo('boo')['path']
    '/inner'
    >>> browser.cookies['boo'] = 'hoo'
    >>> browser.cookies.getinfo('boo')['path']
    '/inner'
    >>> browser.cookies.getinfo('boo')['secure']
    True

Now we mask the cookie, using the path.

.. doctest::

    >>> browser.cookies.create('boo', 'boo', path='/inner/path')
    >>> browser.cookies['boo']
    'boo'
    >>> browser.cookies.getinfo('boo')['path']
    '/inner/path'
    >>> browser.cookies.getinfo('boo')['secure']
    False
    >>> browser.cookies['boo']
    'boo'
    >>> sorted(browser.cookies.keys())
    ['boo', 'tweedle']

To identify the additional cookies, you can change the URL...

.. doctest::

    >>> extra_cookies = browser.cookies.forURL(
    ...     'https://dev.example.com/inner/get_cookie.html')
    >>> extra_cookies['boo']
    'hoo'
    >>> extra_cookies.getinfo('boo')['path']
    '/inner'
    >>> extra_cookies.getinfo('boo')['secure']
    True

...or use ``iterinfo`` and pass in a name.

.. doctest::

    >>> pprint.pprint(list(browser.cookies.iterinfo('boo')))
    [{'comment': None,
      'commenturl': None,
      'domain': 'dev.example.com',
      'expires': None,
      'name': 'boo',
      'path': '/inner/path',
      'port': None,
      'secure': False,
      'value': 'boo'},
     {'comment': None,
      'commenturl': None,
      'domain': '.example.com',
      'expires': None,
      'name': 'boo',
      'path': '/inner',
      'port': None,
      'secure': True,
      'value': 'hoo'}]

An odd situation in this case is that deleting a cookie can sometimes reveal
another one.

.. doctest::

    >>> browser.open('https://dev.example.com/inner/path/get_cookie.html')
    >>> browser.cookies['boo']
    'boo'
    >>> del browser.cookies['boo']
    >>> browser.cookies['boo']
    'hoo'

Creating a cookie that will be immediately masked within the current url is not
allowed.

.. doctest::

    >>> browser.cookies.getinfo('tweedle')['path']
    '/inner/path'
    >>> browser.cookies.create('tweedle', 'dum', path='/inner')
    ... # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    ...
    ValueError: cannot set a cookie that will be hidden by another cookie for
    this url (https://dev.example.com/inner/path/get_cookie.html)
    >>> browser.cookies['tweedle']
    'dee'


Masking by Domain
#################

All of the same behavior is also true for domains.  The only difference is a
theoretical one: while the behavior of masking cookies via paths is defined by
the relevant IRCs, it is not defined for domains.  Here, we simply follow a
"best match" policy.

We initialize by setting some cookies for example.org.

.. doctest::

    >>> browser.open('https://dev.example.org/get_cookie.html')
    >>> browser.cookies.keys() # a different domain
    []
    >>> browser.cookies.create('tweedle', 'dee')
    >>> browser.cookies.create('boo', 'yah', domain='example.org',
    ...                     secure=True)

Before we look at the examples, note that the default behavior of the cookies
is to be liberal in the matching of domains.  

.. doctest::

    >>> browser.cookies.strict_domain_policy
    False

According to the RFCs, a domain of 'example.com' can only be set implicitly
from the server, and implies an exact match, so example.com URLs will get
the cookie, but not ``*.example.com`` (i.e., ``dev.example.com``).  Real
browsers vary in their behavior in this regard.  The cookies collection, by
default, has a looser interpretation of this, such that domains are always
interpreted as effectively beginning with a ".", so ``dev.example.com`` will
include a cookie from the ``example.com`` domain filter as if it were a
``.example.com`` filter.

Here's an example.  If we go to ``dev.example.org``, we should only see the
"tweedle" cookie if we are using strict rules.  But right now we are using
loose rules, so 'boo' is around too.

    >>> browser.open('https://dev.example.org/get_cookie.html')
    >>> sorted(browser.cookies)
    ['boo', 'tweedle']
    >>> print(browser.contents)
    boo: yah
    tweedle: dee

If we set ``strict_domain_policy`` to True, then only tweedle is included.

.. doctest::

    >>> browser.cookies.strict_domain_policy = True
    >>> sorted(browser.cookies)
    ['tweedle']
    >>> browser.open('https://dev.example.org/get_cookie.html')
    >>> print(browser.contents)
    tweedle: dee

If we set the "boo" domain to ``.example.org`` (as it would be set under
the more recent Cookie RFC if a server sent the value) then maybe we get
the "boo" value again.

.. doctest::

    >>> browser.cookies.forURL('https://example.org').change(
    ...     'boo', domain=".example.org")
    Traceback (most recent call last):
    ...
    ValueError: policy does not allow this cookie

Whoa!  Why couldn't we do that?

Well, the strict_domain_policy affects what cookies we can set also.  With
strict rules, ".example.org" can only be set by "*.example.org" domains, *not*
example.org itself.

OK, we'll create a new cookie then.

.. doctest::

    >>> browser.cookies.forURL('https://snoo.example.org').create(
    ...     'snoo', 'kums', domain=".example.org")

    >>> sorted(browser.cookies)
    ['snoo', 'tweedle']
    >>> browser.open('https://dev.example.org/get_cookie.html')
    >>> print(browser.contents)
    snoo: kums
    tweedle: dee

Let's set things back to the way they were.

.. doctest::

    >>> del browser.cookies['snoo']
    >>> browser.cookies.strict_domain_policy = False
    >>> browser.open('https://dev.example.org/get_cookie.html')
    >>> sorted(browser.cookies)
    ['boo', 'tweedle']
    >>> print(browser.contents)
    boo: yah
    tweedle: dee

Now back to the the examples of masking by domain.  First, unless you pass an
explicit domain, you will be modifying the existing cookie.

.. doctest::

    >>> browser.cookies.getinfo('boo')['domain']
    'example.org'
    >>> browser.cookies['boo'] = 'hoo'
    >>> browser.cookies.getinfo('boo')['domain']
    'example.org'
    >>> browser.cookies.getinfo('boo')['secure']
    True

Now we mask the cookie, using the domain.

.. doctest::

    >>> browser.cookies.create('boo', 'boo', domain='dev.example.org')
    >>> browser.cookies['boo']
    'boo'
    >>> browser.cookies.getinfo('boo')['domain']
    'dev.example.org'
    >>> browser.cookies.getinfo('boo')['secure']
    False
    >>> browser.cookies['boo']
    'boo'
    >>> sorted(browser.cookies.keys())
    ['boo', 'tweedle']

To identify the additional cookies, you can change the URL...

.. doctest::

    >>> extra_cookies = browser.cookies.forURL(
    ...     'https://example.org/get_cookie.html')
    >>> extra_cookies['boo']
    'hoo'
    >>> extra_cookies.getinfo('boo')['domain']
    'example.org'
    >>> extra_cookies.getinfo('boo')['secure']
    True

...or use ``iterinfo`` and pass in a name.

.. doctest::

    >>> pprint.pprint(list(browser.cookies.iterinfo('boo'))) # doctest: +REPORT_NDIFF
    [{'comment': None,
      'commenturl': None,
      'domain': 'dev.example.org',
      'expires': None,
      'name': 'boo',
      'path': '/',
      'port': None,
      'secure': False,
      'value': 'boo'},
     {'comment': None,
      'commenturl': None,
      'domain': 'example.org',
      'expires': None,
      'name': 'boo',
      'path': '/',
      'port': None,
      'secure': True,
      'value': 'hoo'}]

An odd situation in this case is that deleting a cookie can sometimes reveal
another one.

.. doctest::

    >>> browser.open('https://dev.example.org/get_cookie.html')
    >>> browser.cookies['boo']
    'boo'
    >>> del browser.cookies['boo']
    >>> browser.cookies['boo']
    'hoo'

Setting a cookie with a foreign domain from the current URL is not allowed (use
forURL to get around this).

.. doctest::

    >>> browser.cookies.create('tweedle', 'dum', domain='locahost.local')
    Traceback (most recent call last):
    ...
    ValueError: current url must match given domain
    >>> browser.cookies['tweedle']
    'dee'

Setting a cookie that will be immediately masked within the current url is also
not allowed.

.. doctest::

    >>> browser.cookies.getinfo('tweedle')['domain']
    'dev.example.org'
    >>> browser.cookies.create('tweedle', 'dum', domain='.example.org')
    ... # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    ...
    ValueError: cannot set a cookie that will be hidden by another cookie for
    this url (https://dev.example.org/get_cookie.html)
    >>> browser.cookies['tweedle']
    'dee'


``change``
##########

So far all of our examples in this section have centered on ``create``.
``change`` allows making changes to existing cookies.  Changing expiration
is a good example.

.. doctest::

    >>> browser.open("http://localhost/@@/testbrowser/cookies.html")
    >>> browser.cookies['foo'] = 'bar'
    >>> browser.cookies.change('foo', expires=datetime.datetime(2031, 1, 1))
    >>> browser.cookies.getinfo('foo')['expires']
    datetime.datetime(2031, 1, 1, 0, 0, tzinfo=<UTC>)

That's the main story.  Now here are some edge cases.

.. doctest::

    >>> browser.cookies.change(
    ...     'foo',
    ...     expires=zope.testbrowser.cookies.expiration_string(
    ...         datetime.datetime(2030, 1, 1)))
    >>> browser.cookies.getinfo('foo')['expires']
    datetime.datetime(2030, 1, 1, 0, 0, tzinfo=<UTC>)

    >>> browser.cookies.forURL(
    ...   'http://localhost/@@/testbrowser/cookies.html').change(
    ...     'foo',
    ...     expires=zope.testbrowser.cookies.expiration_string(
    ...         datetime.datetime(2029, 1, 1)))
    >>> browser.cookies.getinfo('foo')['expires']
    datetime.datetime(2029, 1, 1, 0, 0, tzinfo=<UTC>)
    >>> browser.cookies['foo']
    'bar'
    >>> browser.cookies.change('foo', expires=datetime.datetime(1999, 1, 1))
    >>> len(browser.cookies)
    4

While we are at it, it is worth noting that trying to create a cookie that has
already expired raises an error.

.. doctest::

    >>> browser.cookies.create('foo', 'bar',
    ...                        expires=datetime.datetime(1999, 1, 1))
    Traceback (most recent call last):
    ...
    AlreadyExpiredError: May not create a cookie that is immediately expired


Clearing cookies
~~~~~~~~~~~~~~~~

clear, clearAll, clearAllSession allow various clears of the cookies.

The ``clear`` method clears all of the cookies for the current page.

.. doctest::

    >>> browser.open('http://localhost/@@/testbrowser/cookies.html')
    >>> len(browser.cookies)
    4
    >>> browser.cookies.clear()
    >>> len(browser.cookies)
    0

The ``clearAllSession`` method clears *all* session cookies (for all domains
and paths, not just the current URL), as if the browser had been restarted.

.. doctest::

    >>> browser.cookies.clearAllSession()
    >>> len(browser.cookies)
    0

The ``clearAll`` removes all cookies for the browser.

.. doctest::

    >>> browser.cookies.clearAll()
    >>> len(browser.cookies)
    0

Note that explicitly setting a Cookie header is an error if the ``cookies``
mapping has any values; and adding a new cookie to the ``cookies`` mapping
is an error if the Cookie header is already set.  This is to prevent hard-to-
diagnose intermittent errors when one header or the other wins.

    >>> browser.cookies['boo'] = 'yah'
    >>> browser.addHeader('Cookie', 'gee=gaw')
    Traceback (most recent call last):
    ...
    ValueError: cookies are already set in `cookies` attribute

    >>> browser.cookies.clearAll()
    >>> browser.addHeader('Cookie', 'gee=gaw')
    >>> browser.cookies['fee'] = 'fi'
    Traceback (most recent call last):
    ...
    ValueError: cookies are already set in `Cookie` header
