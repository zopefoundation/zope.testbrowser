=======
CHANGES
=======

5.2 (2017-02-25)
----------------

- Fixed ``toStr`` to handle lists, for example a list of class names.
  [maurits]

- Fixed browser to only follow redirects for HTTP statuses
  301, 302, 303, and 307; not other 30x statuses such as 304.

- Fix passing a real file to ``add_file``.

- Add `controls` property to Form class to list all form controls.

- Restore the ability to use parts of the actually displayed select box titles.

- Allow to set a string value instead of a list on `Browser.displayValue`.

- Fix setting empty values on a select control.

- Support Python 3.6, PyPy2.7 an PyPy3.3.


5.1 (2017-01-31)
----------------

- Alias ``.browser.urllib_request.HTTPError`` to ``.browser.HTTPError`` to have
  a better API.


5.0.0 (2016-09-30)
------------------

- Converted most doctests to Sphinx documentation, and published to
  http://zopetestbrowser.rtfd.org/ .

- Internal implementation now uses WebTest instead of ``mechanize``.
  The ``mechanize`` dependency is completely dropped.
  **This is a backwards-incompatible change.**

- Remove APIs:

  - ``zope.testbrowser.testing.Browser`` (this is a big one).

    Instead of using ``zope.testbrowser.testing.Browser()`` and relying on
    it to magically pick up the ``zope.app.testing.functional`` singleton
    application, you now have to define a test layer inheriting from
    ``zope.testbrowser.wsgi.Layer``, overrride the ``make_wsgi_app`` method
    to create a WSGI application, and then use
    ``zope.testbrowser.wsgi.Browser()`` in your tests.

    (Or you can set up a WSGI application yourself in whatever way you like
    and pass it explicitly to
    ``zope.testbrowser.browser.Browser(wsgi_app=my_app)``.)

    Example: if your test file looked like this ::

        # my/package/tests.py
        from zope.app.testing.functional import defineLayer
        from zope.app.testing.functional import FunctionalDocFileSuite
        defineLayer('MyFtestLayer', 'ftesting.zcml', allow_teardown=True)

        def test_suite():
            suite = FunctionalDocFileSuite('test.txt', ...)
            suite.layer = MyFtestLayer
            return suite

    now you'll have to use ::

        # my/package/tests.py
        from unittest import TestSuite
        import doctest
        import zope.app.wsgi.testlayer
        import zope.testbrowser.wsgi

        class Layer(zope.testbrowser.wsgi.TestBrowserLayer,
                    zope.app.wsgi.testlayer.BrowserLayer):
            """Layer to prepare zope.testbrowser using the WSGI app."""

        layer = Layer(my.package)

        def test_suite():
            suite = doctest.DocFileSuite('test.txt', ...)
            suite.layer = layer
            return TestSuite((suite,))

    and then change all your tests from ::

        >>> from zope.testbrowser.testing import Browser

    to ::

        >>> from zope.testbrowser.wsgi import Browser

- Remove modules:

  - ``zope.testbrowser.connection``

- Remove internal classes you were not supposed to use anyway:

  - ``zope.testbrowser.testing.PublisherResponse``
  - ``zope.testbrowser.testing.PublisherConnection``
  - ``zope.testbrowser.testing.PublisherHTTPHandler``
  - ``zope.testbrowser.testing.PublisherMechanizeBrowser``
  - ``zope.testbrowser.wsgi.WSGIConnection``
  - ``zope.testbrowser.wsgi.WSGIHTTPHandler``
  - ``zope.testbrowser.wsgi.WSGIMechanizeBrowser``

- Remove internal attributes you were not supposed to use anyway (this
  list is not necessarily complete):

  - ``Browser._mech_browser``

- Remove setuptools extras:

  - ``zope.testbrowser[zope-functional-testing]``

- Changed behavior:

  - The testbrowser no longer follows HTML redirects aka
    ``<meta http-equiv="refresh" ... />``. This was a `mechanize` feature which
    does not seem to be provided by `WebTest`.

- Add support for Python 3.3, 3.4 and 3.5.

- Drop support for Python 2.5 and 2.6.

- Drop the ``WebTest <= 1.3.4`` pin.  We require ``WebTest >= 2.0.8`` now.

- Remove dependency on deprecated ``zope.app.testing``.

- Bugfix: ``browser.getLink()`` could fail if your HTML contained ``<a>``
  elements with no href attribute
  (https://github.com/zopefoundation/zope.testbrowser/pull/3).


4.0.3 (2013-09-04)
------------------

- pinning version 'WebTest <= 1.3.4', because of some incompatibility and
  test failures

- Make zope.testbrowser installable via pip
  (https://github.com/zopefoundation/zope.testbrowser/issues/6).

- When ``Browser.handleErrors`` is False, also add ``x-wsgiorg.throw_errors``
  to the environment. http://wsgi.org/wsgi/Specifications/throw_errors

- Prevent WebTest from always sending ``paste.throw_errors=True`` in the
  environment by setting it to ``None`` when ``Browser.handleErrors`` is
  ``True``.  This makes it easier to test error pages.

- Make Browser.submit() handle ``raiseHttpErrors``
  (https://github.com/zopefoundation/zope.testbrowser/pull/4).

- More friendly error messages from getControl() et al:

  - when you specify an index that is out of bounds, show the available
    choices

  - when you fail to find anything, show all the available items


4.0.2 (2011-05-25)
------------------

- Remove test dependency on zope.pagetemplate.


4.0.1 (2011-05-04)
------------------

- Add a hint in documentation how to use ``zope.testbrowser.wsgi.Browser``
  to test a Zope 2/Zope 3/Bluebream WSGI application.

4.0.0 (2011-03-14)
------------------

- LP #721252: AmbiguityError now shows all matching controls.

- Integrate with WebTest. ``zope.testbrowser.wsgi.Browser`` is a
  ``Browser`` implementation that uses ``webtest.TestApp`` to drive a WSGI
  application. This this replaces the wsgi_intercept support added in 3.11.

- Re-write the test application as a pure WSGI application using WebOb. Run the
  existing tests using the WebTest based Browser

- Move zope.app.testing based Browser into ``zope.app.testing`` (leaving
  backwards compatibility imports in-place). Released in ``zope.app.testing``
  3.9.0.


3.11.1 (2011-01-24)
-------------------

- Fixing brown bag release 3.11.0.


3.11.0 (2011-01-24)
-------------------

- Add `wsgi_intercept` support (came from ``zope.app.wsgi.testlayer``).


3.10.4 (2011-01-14)
-------------------

- Move the over-the-wire.txt doctest out of the TestBrowserLayer as it doesn't
  need or use it.

- Fix test compatibility with zope.app.testing 3.8.1.

3.10.3 (2010-10-15)
-------------------

- Fixed backwards compatibility with ``zope.app.wsgi.testlayer``.


3.10.2 (2010-10-15)
-------------------

- Fixed Python 2.7 compatibility in Browser.handleErrors.


3.10.1 (2010-09-21)
-------------------

- Fixed a bug that caused the ``Browser`` to keep it's previous ``contents``
  The places are:
  - Link.click()
  - SubmitControl.click()
  - ImageControl.click()
  - Form.submit()

- Also adjusted exception messages at the above places to match
  pre version 3.4.1 messages.


3.10.0 (2010-09-14)
-------------------

- LP #98437: use ``mechanize``'s built-in ``submit()`` to submit forms,
  allowing ``mechanize`` to set the "Referer:" (sic) header appropriately.

- Fixed tests to run with ``zope.app.testing`` 3.8 and above.


3.9.0 (2010-05-17)
------------------

- LP #568806: Update dependency ``mechanize >= 0.2.0``, which now includes
  the ``ClientForm`` APIs.  Remove use of ``urllib2`` APIs (incompatible
  with ``mechanize 0.2.0``) in favor of ``mechanize`` equivalents.
  Thanks to John J. Lee for the patch.

- Use stdlib ``doctest`` module, instead of ``zope.testing.doctest``.

- **Caution:** This version is no longer fully compatible with Python 2.4:
  ``handleErrors = False`` no longer works.


3.8.1 (2010-04-19)
------------------

- Pin dependency on ``mechanize`` to prevent use of the upcoming
  0.2.0 release before we have time to adjust to its API changes.

- Fix LP #98396: testbrowser resolves relative URLs incorrectly.


3.8.0 (2010-03-05)
------------------

- Add ``follow`` convenience method which gets and follows a link.


3.7.0 (2009-12-17)
------------------

- Move ``zope.app.testing`` dependency into the scope of the
  ``PublisherConnection`` class. Zope2 specifies its own version of
  ``PublisherConnection`` which isn't dependent on ``zope.app.testing``.

- Fix LP #419119: return ``None`` when the browser has no contents instead
  of raising an exception.


3.7.0a1 (2009-08-29)
--------------------

- Update dependency from ``zope.app.publisher`` to
  ``zope.browserpage``, ``zope.browserresource`` and ``zope.ptresource``.

- Remove dependencies on ``zope.app.principalannotation`` and
  ``zope.securitypolicy`` by using the simple ``PermissiveSecurityPolicy``.

- Replace the testing dependency on ``zope.app.zcmlfiles`` with explicit
  dependencies of a minimal set of packages.

- Remove unneeded ``zope.app.authentication`` from ftesting.zcml.

- Update dependency from ``zope.app.securitypolicy`` to
  ``zope.securitypolicy``.


3.6.0a2 (2009-01-31)
--------------------

- Update dependency from ``zope.app.folder`` to ``zope.site.folder``.

- Remove unnecessary test dependency in ``zope.app.component``.


3.6.0a1 (2009-01-08)
--------------------

- Update author e-mail to ``zope-dev`` rather than ``zope3-dev``.

- No longer strip newlines in XML and HTML code contained in a
  ``<textarea>``; fix requires ClientForm >= 0.2.10 (LP #268139).

- Add ``cookies`` attribute to browser for easy manipulation of browser
  cookies.  See brief example in main documentation, plus new ``cookies.txt``
  documentation.


3.5.1 (2008-10-10)
------------------

- Work around for a ``mechanize``/``urllib2`` bug on Python 2.6 missing
  ``timeout`` attribute on ``Request`` base class.

- Work around for a ``mechanize``/``urllib2`` bug in creating request objects
  that won't handle fragment URLs correctly.


3.5.0 (2008-03-30)
------------------

- Add a ``zope.testbrowser.testing.Browser.post`` method that allows
  tests to supply a body and a content type.  This is handy for
  testing Ajax requests with non-form input (e.g. JSON).

- Remove vendor import of ``mechanize``.

- Fix bug that caused HTTP exception tracebacks to differ between version 3.4.0
  and 3.4.1.

- Work around a bug in Python ``Cookie.SimpleCookie`` when handling unicode
  strings.

- Fix bug introduced in 3.4.1 that created incompatible tracebacks in doctests.
  This necessitated adding a patched ``mechanize`` to the source tree; patches
  have been sent to the ``mechanize`` project.

- Fix https://bugs.launchpad.net/bugs/149517 by adding ``zope.interface`` and
  ``zope.schema`` as real dependencies

- Fix ``browser.getLink`` documentation that was not updated since the last
  API modification.

- Move tests for fixed bugs to a separate file.

- Remove non-functional and undocumented code intended to help test servers
  using virtual hosting.


3.4.2 (2007-10-31)
------------------

- Resolve ``ZopeSecurityPolicy`` deprecation warning.


3.4.1 (2007-09-01)
------------------

* Update dependencies to ``mechanize 0.1.7b`` and ``ClientForm 0.2.7``.

* Add support for Python 2.5.


3.4.0 (2007-06-04)
------------------

* Add the ability to suppress raising exceptions on HTTP errors
  (``raiseHttpErrors`` attribute).

* Make the tests more resilient to HTTP header formatting changes with
  the REnormalizer.


3.4.0a1 (2007-04-22)
--------------------

Initial release as a separate project, corresponds to zope.testbrowser
from Zope 3.4.0a1
