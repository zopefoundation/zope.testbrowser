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
from setuptools import setup, find_packages

with open('README.rst') as f:
    README = f.read()

with open('CHANGES.rst') as f:
    CHANGES = f.read()

long_description = (README + '\n\n' + CHANGES)

tests_require = ['zope.testing', 'mock']

setup(
    name='zope.testbrowser',
    version='5.2',
    url='https://github.com/zopefoundation/zope.testbrowser',
    license='ZPL 2.1',
    description='Programmable browser for functional black-box tests',
    author='Zope Corporation and Contributors',
    author_email='zope-dev@zope.org',
    long_description=long_description,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Testing',
        'Topic :: Internet :: WWW/HTTP',
    ],

    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['zope'],
    test_suite='zope.testbrowser.tests',
    tests_require=tests_require,
    install_requires=[
        'setuptools',
        'zope.interface',
        'zope.schema',
        'zope.cachedescriptors',
        'pytz > dev',
        'WebTest >= 2.0.9',
        'WSGIProxy2',
        'six',
    ],
    extras_require={
        'test': tests_require,
        'test_bbb': [
            'zope.testbrowser [test]',
        ],
        'wsgi': [
            # BBB
        ]
    },
    include_package_data=True,
    zip_safe=False,
)
