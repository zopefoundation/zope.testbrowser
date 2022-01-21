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

tests_require = ['zope.testing', 'mock', 'zope.testrunner']

setup(
    name='zope.testbrowser',
    version='5.6.1',
    url='https://github.com/zopefoundation/zope.testbrowser',
    license='ZPL 2.1',
    project_urls={
        'Documentation': 'https://zopetestbrowser.readthedocs.io/',
    },
    description='Programmable browser for functional black-box tests',
    author='Zope Corporation and Contributors',
    author_email='zope-dev@zope.org',
    long_description=long_description,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Testing',
        'Topic :: Internet :: WWW/HTTP',
    ],
    keywords='headless browser functional tests WSGI HTTP HTML form',
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
        'pytz',
        'WebTest >= 2.0.30',
        'BeautifulSoup4',
        'SoupSieve >= 1.9.0',
        'WSGIProxy2',
        'six',
    ],
    extras_require={
        'docs': [
            'Sphinx',
            'sphinx_rtd_theme',
            'repoze.sphinx.autointerface',
            'zope.app.wsgi',
        ],
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
