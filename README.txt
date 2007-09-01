Overview
========

An easy to use programmatic web browser with special focus on testing. Used in
Zope 3, but not Zope specific.

The zope.testbrowser package used in the Zope 3 project for functional testing;
this stand-alone version can be used to test or otherwise interact with any web
site.

Changes
=======

3.4.1 (unreleased)
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
