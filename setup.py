##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Setup for zope.testbrowser package

$Id$
"""

import os

try:
    from setuptools import setup, Extension
except ImportError, e:
    from distutils.core import setup, Extension

setup(name='zope.testbrowser',
      version='3.4-dev',
      url='http://svn.zope.org/zope.testbrowser',
      license='ZPL 2.1',
      description='Zope testbrowser',
      author='Zope Corporation and Contributors',
      author_email='zope3-dev@zope.org',
      long_description="An easy to use programmatic web browser"
                       "with special focus on testing. Used in"
                       "Zope 3, but not Zope specific."
                       "The zope.testbrowser package used in the"
                       "Zope 3 project for functional testing;"
                       "this stand-alone version can be used to"
                       "test or otherwise interact with any web site.",

      packages=['zope', 'zope.testbrowser', 'zope.testbrowser.ftests'],
      package_dir = {'': 'src'},

      namespace_packages=['zope',],
      tests_require = ['zope.testing'],
      install_requires=['ClientForm'
                        'mechanize',
                        'zope.interface']
      include_package_data = True,

      zip_safe = False,
      )
