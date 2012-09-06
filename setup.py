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
"""Setup for zope.testbrowser package
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

# pinning version, because of some incompatibility and test failures
# see:
# http://winbot.zope.org/builders/zope.testbrowser_py_265_32/builds/619/steps/test/logs/stdio
WEBTEST = 'WebTest <= 1.3.4'

tests_require = ['zope.testing',
                 WEBTEST]

setup(
    name='zope.testbrowser',
    version='4.0.3dev',
    url='http://pypi.python.org/pypi/zope.testbrowser',
    license='ZPL 2.1',
    description='Programmable browser for functional black-box tests',
    author='Zope Corporation and Contributors',
    author_email='zope-dev@zope.org',
    long_description=long_description,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Testing',
        'Topic :: Internet :: WWW/HTTP',
        ],

    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['zope',],
    test_suite='zope.testbrowser.tests',
    tests_require=tests_require,
    install_requires=[
        # mechanize 0.2.0 folds in ClientForm, makes incompatible API changes
        'mechanize>=0.2.0',
        'setuptools',
        'zope.interface',
        'zope.schema',
        'pytz',
        ],
    extras_require={
        'test': tests_require,
        'test_bbb': [
            'zope.testbrowser [test,zope-functional-testing]',
            ],
        'zope-functional-testing': [
            'zope.app.testing >= 3.9.0dev',
            ],
        'wsgi': [
            WEBTEST,
            ]
        },
    include_package_data=True,
    zip_safe=False,
    )
