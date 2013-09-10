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
    + open('README.rst').read()
    + '\n\n'
    + open(os.path.join('src', 'zope', 'testbrowser', 'README.txt')).read()
    + '\n\n'
    + open('CHANGES.rst').read()
    )

# Pinning WebTest version, because of some incompatibility causing three test
# failures -- but only when using buildout + bin/test, not with tox/detox.
#
# 1 Failure in test /home/mg/src/new-zope-order/zope.testbrowser/src/zope/testbrowser/README.txt
#   ----------------------------------------------------------------------
#   File "/home/mg/src/new-zope-order/zope.testbrowser/src/zope/testbrowser/README.txt", line 32, in README.txt
#   Failed example:
#       browser = Browser('http://localhost/', wsgi_app=demo_app)
#   Exception raised:
#       Traceback (most recent call last):
#         File "/usr/lib/python2.7/doctest.py", line 1289, in __run
#           compileflags, 1) in test.globs
#         File "<doctest README.txt[4]>", line 1, in <module>
#           browser = Browser('http://localhost/', wsgi_app=demo_app)
#         File "/home/mg/src/new-zope-order/zope.testbrowser/src/zope/testbrowser/wsgi.py", line 171, in __init__
#           super(Browser, self).__init__(url=url, mech_browser=mech_browser)
#         File "/home/mg/src/new-zope-order/zope.testbrowser/src/zope/testbrowser/browser.py", line 196, in __init__
#           self.open(url)
#         File "/home/mg/src/new-zope-order/zope.testbrowser/src/zope/testbrowser/browser.py", line 264, in open
#           self.mech_browser.open(url, data)
#         File "/home/mg/.buildout/eggs/mechanize-0.2.5-py2.7.egg/mechanize/_mechanize.py", line 203, in open
#           return self._mech_open(url, data, timeout=timeout)
#         File "/home/mg/.buildout/eggs/mechanize-0.2.5-py2.7.egg/mechanize/_mechanize.py", line 230, in _mech_open
#           response = UserAgentBase.open(self, request, data)
#         File "/home/mg/.buildout/eggs/mechanize-0.2.5-py2.7.egg/mechanize/_opener.py", line 193, in open
#           response = urlopen(self, req, data)
#         File "/home/mg/.buildout/eggs/mechanize-0.2.5-py2.7.egg/mechanize/_urllib2_fork.py", line 344, in _open
#           '_open', req)
#         File "/home/mg/.buildout/eggs/mechanize-0.2.5-py2.7.egg/mechanize/_urllib2_fork.py", line 332, in _call_chain
#           result = func(*args)
#         File "/home/mg/src/new-zope-order/zope.testbrowser/src/zope/testbrowser/connection.py", line 65, in http_open
#           return self.do_open(self._connect, req)
#         File "/home/mg/.buildout/eggs/mechanize-0.2.5-py2.7.egg/mechanize/_urllib2_fork.py", line 1115, in do_open
#           h.request(req.get_method(), req.get_selector(), req.data, headers)
#         File "/home/mg/src/new-zope-order/zope.testbrowser/src/zope/testbrowser/wsgi.py", line 106, in request
#           response = app.get(url, headers=headers, expect_errors=True, extra_environ=extra_environ)
#         File "/home/mg/.buildout/eggs/WebTest-2.0.7-py2.7.egg/webtest/app.py", line 199, in get
#           expect_errors=expect_errors)
#         File "/home/mg/.buildout/eggs/WebTest-2.0.7-py2.7.egg/webtest/app.py", line 481, in do_request
#           res.body
#         File "/home/mg/.buildout/eggs/WebOb-1.2.3-py2.7.egg/webob/response.py", line 345, in _body__get
#           body = b''.join(app_iter)
#         File "/home/mg/.buildout/eggs/WebTest-2.0.7-py2.7.egg/webtest/lint.py", line 297, in next
#           % (self.iterator, binary_type, v))
#       AssertionError: Iterator <listiterator object at 0x3400450> returned a non-<type 'str'> object: u"Hello world!\n\nHTTP_CONNECTION = 'close'\nHTTP_HOST = 'localhost'\nHTTP_USER_AGENT = 'Python-urllib/2.7'\nPATH_INFO = '/'\nQUERY_STRING = ''\nREQUEST_METHOD = 'GET'\nSCRIPT_NAME = ''\nSERVER_NAME = 'localhost'\nSERVER_PORT = '80'\nSERVER_PROTOCOL = 'HTTP/1.0'\npaste.testing = True\npaste.testing_variables = {}\npaste.throw_errors = None\nwsgi.errors = <webtest.lint.ErrorWrapper object at 0x7f5234d3ce10>\nwsgi.input = <webtest.lint.InputWrapper object at 0x7f5234ca9090>\nwsgi.multiprocess = False\nwsgi.multithread = False\nwsgi.run_once = False\nwsgi.url_scheme = 'http'\nwsgi.version = (1, 0)\n"
#
# 2 Failure in test test_allowed_domains (zope.testbrowser.tests.test_wsgi.TestBrowser)
#   Traceback (most recent call last):
#     File "/usr/lib/python2.7/unittest/case.py", line 332, in run
#       testMethod()
#     File "/home/mg/src/new-zope-order/zope.testbrowser/src/zope/testbrowser/tests/test_wsgi.py", line 100, in test_allowed_domains
#       browser.open('http://localhost')
#     File "/home/mg/src/new-zope-order/zope.testbrowser/src/zope/testbrowser/browser.py", line 264, in open
#       self.mech_browser.open(url, data)
#     File "/home/mg/.buildout/eggs/mechanize-0.2.5-py2.7.egg/mechanize/_mechanize.py", line 203, in open
#       return self._mech_open(url, data, timeout=timeout)
#     File "/home/mg/.buildout/eggs/mechanize-0.2.5-py2.7.egg/mechanize/_mechanize.py", line 230, in _mech_open
#       response = UserAgentBase.open(self, request, data)
#     File "/home/mg/.buildout/eggs/mechanize-0.2.5-py2.7.egg/mechanize/_opener.py", line 193, in open
#       response = urlopen(self, req, data)
#     File "/home/mg/.buildout/eggs/mechanize-0.2.5-py2.7.egg/mechanize/_urllib2_fork.py", line 344, in _open
#       '_open', req)
#     File "/home/mg/.buildout/eggs/mechanize-0.2.5-py2.7.egg/mechanize/_urllib2_fork.py", line 332, in _call_chain
#       result = func(*args)
#     File "/home/mg/src/new-zope-order/zope.testbrowser/src/zope/testbrowser/connection.py", line 65, in http_open
#       return self.do_open(self._connect, req)
#     File "/home/mg/.buildout/eggs/mechanize-0.2.5-py2.7.egg/mechanize/_urllib2_fork.py", line 1115, in do_open
#       h.request(req.get_method(), req.get_selector(), req.data, headers)
#     File "/home/mg/src/new-zope-order/zope.testbrowser/src/zope/testbrowser/wsgi.py", line 106, in request
#       response = app.get(url, headers=headers, expect_errors=True, extra_environ=extra_environ)
#     File "/home/mg/.buildout/eggs/WebTest-2.0.7-py2.7.egg/webtest/app.py", line 199, in get
#       expect_errors=expect_errors)
#     File "/home/mg/.buildout/eggs/WebTest-2.0.7-py2.7.egg/webtest/app.py", line 481, in do_request
#       res.body
#     File "/home/mg/.buildout/eggs/WebOb-1.2.3-py2.7.egg/webob/response.py", line 345, in _body__get
#       body = b''.join(app_iter)
#     File "/home/mg/.buildout/eggs/WebTest-2.0.7-py2.7.egg/webtest/lint.py", line 297, in next
#       % (self.iterator, binary_type, v))
#   AssertionError: Iterator <listiterator object at 0x375fc10> returned a non-<type 'str'> object: u"Hello world!\n\nHTTP_CONNECTION = 'close'\nHTTP_HOST = 'localhost'\nHTTP_USER_AGENT = 'Python-urllib/2.7'\nPATH_INFO = '/'\nQUERY_STRING = ''\nREQUEST_METHOD = 'GET'\nSCRIPT_NAME = ''\nSERVER_NAME = 'localhost'\nSERVER_PORT = '80'\nSERVER_PROTOCOL = 'HTTP/1.0'\npaste.testing = True\npaste.testing_variables = {}\npaste.throw_errors = None\nwsgi.errors = <webtest.lint.ErrorWrapper object at 0x375fc90>\nwsgi.input = <webtest.lint.InputWrapper object at 0x375f950>\nwsgi.multiprocess = False\nwsgi.multithread = False\nwsgi.run_once = False\nwsgi.url_scheme = 'http'\nwsgi.version = (1, 0)\n"
#
# 3 Failure in test test_layer (zope.testbrowser.tests.test_wsgi.TestWSGILayer)
#   Traceback (most recent call last):
#     File "/usr/lib/python2.7/unittest/case.py", line 332, in run
#       testMethod()
#     File "/home/mg/src/new-zope-order/zope.testbrowser/src/zope/testbrowser/tests/test_wsgi.py", line 145, in test_layer
#       browser.open('http://localhost')
#     File "/home/mg/src/new-zope-order/zope.testbrowser/src/zope/testbrowser/browser.py", line 264, in open
#       self.mech_browser.open(url, data)
#     File "/home/mg/.buildout/eggs/mechanize-0.2.5-py2.7.egg/mechanize/_mechanize.py", line 203, in open
#       return self._mech_open(url, data, timeout=timeout)
#     File "/home/mg/.buildout/eggs/mechanize-0.2.5-py2.7.egg/mechanize/_mechanize.py", line 230, in _mech_open
#       response = UserAgentBase.open(self, request, data)
#     File "/home/mg/.buildout/eggs/mechanize-0.2.5-py2.7.egg/mechanize/_opener.py", line 193, in open
#       response = urlopen(self, req, data)
#     File "/home/mg/.buildout/eggs/mechanize-0.2.5-py2.7.egg/mechanize/_urllib2_fork.py", line 344, in _open
#       '_open', req)
#     File "/home/mg/.buildout/eggs/mechanize-0.2.5-py2.7.egg/mechanize/_urllib2_fork.py", line 332, in _call_chain
#       result = func(*args)
#     File "/home/mg/src/new-zope-order/zope.testbrowser/src/zope/testbrowser/connection.py", line 65, in http_open
#       return self.do_open(self._connect, req)
#     File "/home/mg/.buildout/eggs/mechanize-0.2.5-py2.7.egg/mechanize/_urllib2_fork.py", line 1115, in do_open
#       h.request(req.get_method(), req.get_selector(), req.data, headers)
#     File "/home/mg/src/new-zope-order/zope.testbrowser/src/zope/testbrowser/wsgi.py", line 106, in request
#       response = app.get(url, headers=headers, expect_errors=True, extra_environ=extra_environ)
#     File "/home/mg/.buildout/eggs/WebTest-2.0.7-py2.7.egg/webtest/app.py", line 199, in get
#       expect_errors=expect_errors)
#     File "/home/mg/.buildout/eggs/WebTest-2.0.7-py2.7.egg/webtest/app.py", line 481, in do_request
#       res.body
#     File "/home/mg/.buildout/eggs/WebOb-1.2.3-py2.7.egg/webob/response.py", line 345, in _body__get
#       body = b''.join(app_iter)
#     File "/home/mg/.buildout/eggs/WebTest-2.0.7-py2.7.egg/webtest/lint.py", line 297, in next
#       % (self.iterator, binary_type, v))
#   AssertionError: Iterator <listiterator object at 0x37d5e10> returned a non-<type 'str'> object: u"Hello world!\n\nHTTP_CONNECTION = 'close'\nHTTP_HOST = 'localhost'\nHTTP_USER_AGENT = 'Python-urllib/2.7'\nPATH_INFO = '/'\nQUERY_STRING = ''\nREQUEST_METHOD = 'GET'\nSCRIPT_NAME = ''\nSERVER_NAME = 'localhost'\nSERVER_PORT = '80'\nSERVER_PROTOCOL = 'HTTP/1.0'\npaste.testing = True\npaste.testing_variables = {}\npaste.throw_errors = None\nwsgi.errors = <webtest.lint.ErrorWrapper object at 0x37d5350>\nwsgi.input = <webtest.lint.InputWrapper object at 0x37d5ad0>\nwsgi.multiprocess = False\nwsgi.multithread = False\nwsgi.run_once = False\nwsgi.url_scheme = 'http'\nwsgi.version = (1, 0)\n"
#
# Ran 20 tests with 3 failures, 0 errors, 0 skipped in 0.357 seconds.
WEBTEST = 'WebTest <= 1.3.4'

tests_require = ['zope.testing',
                 WEBTEST]

setup(
    name='zope.testbrowser',
    version='4.0.4.dev0',
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
        'pytz > dev',
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
