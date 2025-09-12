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
from setuptools import setup


with open('README.rst') as f:
    README = f.read()

with open('CHANGES.rst') as f:
    CHANGES = f.read()

long_description = (README + '\n\n' + CHANGES)

tests_require = ['zope.testing', 'mock', 'zope.testrunner >= 6.4']

setup(
    name='zope.testbrowser',
    version='8.0',
    url='https://github.com/zopefoundation/zope.testbrowser',
    license='ZPL-2.1',
    project_urls={
        'Documentation': 'https://zopetestbrowser.readthedocs.io/',
    },
    description='Programmable browser for functional black-box tests',
    author='Zope Foundation and Contributors',
    author_email='zope-dev@zope.dev',
    long_description=long_description,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Testing',
        'Topic :: Internet :: WWW/HTTP',
    ],
    keywords='headless browser functional tests WSGI HTTP HTML form',
    python_requires='>=3.9',
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
        'legacy-cgi; python_version > "3.12"',  # WebOb uses the cgi module
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
