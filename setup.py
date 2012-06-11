##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
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
# This package is developed by the Zope Toolkit project, documented here:
# http://docs.zope.org/zopetoolkit
# When developing and releasing this package, please follow the documented
# Zope Toolkit policies as described by this documentation.
##############################################################################
"""Setup for zope.testbrowser package

$Id$
"""
import os
from setuptools import setup, find_packages

long_description = (
    '.. contents::\n\n'
    + open('README.txt').read()
    + '\n\n'
    + open(os.path.join('src', 'zope', 'testbrowser', 'README.txt')).read()
    + '\n\n'
    + open('CHANGES.txt').read()
    )

setup(
    name = 'zope.testbrowser',
    version='3.8.3dev',
    url = 'http://pypi.python.org/pypi/zope.testbrowser',
    license = 'ZPL 2.1',
    description = 'Programmable browser for functional black-box tests',
    author = 'Zope Corporation and Contributors',
    author_email = 'zope-dev@zope.org',
    long_description = long_description,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Testing',
        'Topic :: Internet :: WWW/HTTP',
        ],

    packages = find_packages('src'),
    package_dir = {'': 'src'},
    namespace_packages = ['zope',],
    tests_require = ['zope.testing'],
    install_requires = [
        'ClientForm',
        # mechanize 0.2.0 folds in ClientForm, makes incompatible API changes
        'mechanize<0.2dev',
        'setuptools',
        'zope.interface',
        'zope.schema',
        'pytz',
        ],
    extras_require = {
        'test': [
            'zope.browserpage',
            'zope.browserresource',
            'zope.component',
            'zope.container',
            'zope.principalregistry',
            'zope.ptresource',
            'zope.publisher',
            'zope.security',
            'zope.site',
            'zope.traversing',
            'zope.app.appsetup',
            'zope.app.publication',
            'zope.app.testing < 3.8',
            ],
        'zope-functional-testing': [
            'zope.app.testing',
            ],
        },
    include_package_data = True,
    zip_safe = False,
    )
