Overview
========

The zope.testbrowser package provides web user agents (browsers) with
programmatic interfaces designed to be used for testing web applications,
especially in conjunction with doctests.  This project originates in the Zope 3
community, but is not Zope-specific.

There are currently three type of testbrowser provided.  One for accessing web
sites via HTTP (zope.testbrowser.browser), one for directly accessing a Zope 3
application (zope.testbrowser.testing), and one that controls a Firefox web
browser (zope.testbrowser.real).


Changes
=======

3.4.2 (unreleased)
------------------

* ...

3.4.1 (2007-09-01)
------------------

* Updated to mechanize 0.1.7b and ClientForm 0.2.7.  These are now
  pulled in via egg dependencies.

* ``zope.testbrowser`` now works on Python 2.5.

3.4.0 (2007-06-04)
------------------

* Added the ability to suppress raising exceptions on HTTP errors
  (``raiseHttpErrors`` attribute).

* Made the tests more resilient to HTTP header formatting changes with
  the REnormalizer.

3.4.0a1 (2007-04-22)
--------------------

Initial release as a separate project, corresponds to zope.testbrowser
from Zope 3.4.0a1
