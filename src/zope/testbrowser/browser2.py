##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
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
"""Webtest-based Functional Doctest interfaces
"""
__docformat__ = "reStructuredText"

import sys
import re
import time
import urlparse
import io
from contextlib import contextmanager

from zope.interface import implementer

from zope.testbrowser import interfaces
from zope.testbrowser._compat import httpclient
import zope.testbrowser.cookies

import webtest

RegexType = type(re.compile(''))
_compress_re = re.compile(r"\s+")
compressText = lambda text: _compress_re.sub(' ', text.strip())


@implementer(interfaces.IBrowser)
class Browser(object):
    """A web user agent."""

    _contents = None
    _counter = 0
    _response = None
    _req_headers = None

    def __init__(self, url=None, wsgi_app=None):
        self.timer = PystoneTimer()
        self.raiseHttpErrors = True
        self.testapp = webtest.TestApp(wsgi_app)
        self._req_headers = {}

        if url is not None:
            self.open(url)

    @property
    def url(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        if self._response is None:
            return None
        return self._response.request.url

    @property
    def isHtml(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        # TODO
        return self.mech_browser.viewing_html()

    @property
    def title(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        # TODO
        return self.mech_browser.title()

    @property
    def contents(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        return self._response.body
        ## # TODO
        ## if self._contents is not None:
        ##     return self._contents
        ## response = self.mech_browser.response()
        ## if response is None:
        ##     return None
        ## old_location = response.tell()
        ## response.seek(0)
        ## self._contents = response.read()
        ## response.seek(old_location)
        ## return self._contents

    @property
    def headers(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        return self._response.headers

    @property
    def cookies(self):
        if self.url is None:
            raise RuntimeError("no request found")
        return zope.testbrowser.cookies.Cookies(self.testapp, self.url,
                                                self._req_headers)

    HEADER_KEY = 'X-zope-handle-errors'

    @property
    def handleErrors(self):
        # TODO
        headers = self.mech_browser.addheaders
        value = dict(headers).get(self.HEADER_KEY, True)
        return {'False': False}.get(value, True)

    @handleErrors.setter
    def handleErrors(self, value):
        # TODO
        headers = self.mech_browser.addheaders
        current_value = self.handleErrors
        if current_value == value:
            return

        # Remove the current header...
        for key, header_value in headers[:]:
            if key == self.HEADER_KEY:
                headers.remove((key, header_value))
        # ... Before adding the new one.
        headers.append((self.HEADER_KEY, {False: 'False'}.get(value, 'True')))

    def addHeader(self, key, value):
        """See zope.testbrowser.interfaces.IBrowser"""
        if (key.lower() in ('cookie', 'cookie2') and
            self.cookies.header):
            raise ValueError('cookies are already set in `cookies` attribute')
        self._req_headers[key] = value

    def open(self, url, data=None):
        """See zope.testbrowser.interfaces.IBrowser"""

        url = str(url)
        with self._preparedRequest() as reqargs:
            if data is not None:
                self._response = self.testapp.post(url, data, **reqargs)
            else:
                self._response = self.testapp.get(url, **reqargs)

        # if the headers don't have a status, I suppose there can't be an error
        if 'Status' in self.headers:
            code, msg = self.headers['Status'].split(' ', 1)
            code = int(code)
            if self.raiseHttpErrors and code >= 400:
                raise httpclient.HTTPException(url, code, msg, self.headers)

    def getLink(self, text=None, url=None, id=None, index=0):
        """See zope.testbrowser.interfaces.IBrowser"""
        ## pq = 'a'
        ## if id is not None:
        ##     pq = "a.%s" % id
        ## else:
        ##     if not isinstance(url, RegexType) and url is not None:
        ##         pq = "a[href=%s]" % url

        ## links = self._response.pyquery(pq)
        ## matching = []
        ## for elem in links:
        ##     matches = (isMatching(elem.text, text) and
        ##                isMatching(elem.get('href'), url))

        ##     if matches:
        ##         matching.append(elem)

        found = self._response._find_element(tag='a',
                                             href_attr='href',
                                             href_extract=None,
                                             content=text,
                                             id=id,
                                             href_pattern=url,
                                             index=index,
                                             verbose=False)
        html, desc, elem = found
        baseurl = self._getBaseUrl()

        return Link(elem, self, baseurl)

    def _getBaseUrl(self):
        # Look for <base href> tag and use it as base, if it exists
        bases = self._response.html.find_all('base')
        if bases:
            return bases[0]['href']

        # If no base tags found, use last request url as a base
        return self._response.request.url

    def getForm(self, id=None, name=None, action=None, index=None):
        """See zope.testbrowser.interfaces.IBrowser"""
        zeroOrOne([id, name, action], '"id", "name", and "action"')
        matching_forms = []
        allforms = set(self._response.forms.values())
        for form in allforms:
            if ((id is not None and form.id == id)
            or (name is not None and form.html.body.form.get('name') == name)
            or (action is not None and re.search(action, form.action))
            or id == name == action == None):
                matching_forms.append(form)

        if index is None and not any([id, name, action]):
            if len(matching_forms) == 1:
                index = 0
            else:
                raise ValueError(
                    'if no other arguments are given, index is required.')

        form = disambiguate(matching_forms, '', index)
        return Form(self, form)

    def getControl(self, label=None, name=None, index=None):
        """See zope.testbrowser.interfaces.IBrowser"""
        intermediate, msg, available = self._getAllControls(
            label, name, self._response.forms.values(),
            include_subcontrols=True)
        control, form = disambiguate(intermediate, msg, index,
                                     controlFormTupleRepr,
                                     available)
        return controlFactory(control, form, self)


    def _getAllControls(self, label, name, forms, include_subcontrols=False):
        onlyOne([label, name], '"label" and "name"')

        forms = list(forms) # might be an iterator, and we need to iterate twice

        available = None
        if label is not None:
            res = self._findByLabel(label, forms, include_subcontrols)
            msg = 'label %r' % label
        elif name is not None:
            include_subcontrols = False
            res = self._findByName(name, forms)
            msg = 'name %r' % name
        if not res:
            available = list(self._findAllControls(forms, include_subcontrols))
        return res, msg, available


    def _findByLabel(self, label, forms, include_subcontrols=False):
        # forms are iterable of mech_forms
        matches = re.compile(r'(^|\b|\W)%s(\b|\W|$)'
                             % re.escape(compressText(label))).search
        found = []
        for control, form in self._findAllControls(forms, include_subcontrols):
            for l in getControlLabels(control):
                if matches(l):
                    found.append((control, form))
                    break
        return found

    def _findByName(self, name, forms):
        found = []
        for f in forms:
            if name in f.fields:
                found.extend([(c, f) for c in f.fields[name]])
        return found


    def _findAllControls(self, forms, include_subcontrols=False):
        for f in forms:
            for controls in f.fields.values():
                for c in controls:
                    yield (c, f)
                #phantom = control.type in ('radio', 'checkbox')
                #if not phantom:
                #    yield (control, f)
                #if include_subcontrols and (
                #    phantom or control.type=='select'):
                #    for i in control.items:
                #        yield (i, f)


    def _changed(self):
        self._counter += 1
        self._contents = None
        self._req_headers = {}

    def _clickSubmit(self, form, control, coord):
        # TODO: handle coord
        # find index of given control in the form
        with self._preparedRequest() as reqargs:
            try:
                if control:
                    index = form.fields[control.name].index(control)
                    self._response = form.submit(control.name, index, **reqargs)
                else:
                    self._response = form.submit(**reqargs)
                #self.mech_browser.form = form
                #self.mech_browser.submit(id=control.id, name=control.name,
                #                         label=label, coord=coord)
            except Exception as e:
                fix_exception_name(e)
                raise

    @contextmanager
    def _preparedRequest(self):
        self.timer.start()
        if self.url:
            self._req_headers['Referer'] = self.url
        kwargs = {'headers': sorted(self._req_headers.items())}

        yield kwargs

        self._changed()
        self.timer.stop()

@implementer(interfaces.ILink)
class Link(object):

    def __init__(self, link, browser, baseurl=""):
        self._link = link
        self.browser = browser
        self._baseurl = baseurl
        self._browser_counter = self.browser._counter

    def click(self):
        #TODO
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        self.browser._start_timer()
        try:
            try:
                self.browser.mech_browser.follow_link(self.mech_link)
            except Exception as e:
                fix_exception_name(e)
                raise
        finally:
            self.browser._stop_timer()
            self.browser._changed()

    @property
    def url(self):
        relurl = self._link['uri']
        return urlparse.urljoin(self._baseurl, relurl)

    @property
    def text(self):
        return self._link.text

    @property
    def tag(self):
        return self._link.name

    @property
    def attrs(self):
        return self._link.attrs

    def __repr__(self):
        return "<%s text=%r url=%r>" % (
            self.__class__.__name__, self.text, self.url)

def controlFactory(control, form, browser):
    listfields = (webtest.forms.Select,
                  webtest.forms.MultipleSelect,
                  webtest.forms.Radio,
                  webtest.forms.Checkbox)
    # TODO: figure out what in webtest corresponds to mechanize.Item
    ## if isinstance(control, mechanize.Item):
    ##     # it is a subcontrol
    ##     return ItemControl(control, form, browser)
    ## else:
    if isinstance(control, listfields):
        return ListControl(control, form, browser)
    elif isinstance(control, webtest.forms.Submit):
        if control.attrs.get('type', 'submit') == 'image':
            return ImageControl(control, form, browser)
        else:
            return SubmitControl(control, form, browser)
    else:
        return Control(control, form, browser)

def controlFormTupleRepr(arg):
    (ctrl, form) = arg
    return repr(ctrl)

def getControlLabels(control):
    labels = []
    if isinstance(control, webtest.forms.Submit):
        labels.append(control.value_if_submitted())
    return labels

@implementer(interfaces.IControl)
class Control(object):
    def __init__(self, control, form, browser):
        self._control = control
        self._form = form
        self.browser = browser
        self._browser_counter = self.browser._counter

    @property
    def disabled(self):
        # TODO
        return bool(getattr(self.mech_control, 'disabled', False))

    @property
    def type(self):
        return self._control.attrs.get('type', None)

    @property
    def name(self):
        return self._control.name

    @property
    def multiple(self):
        # TODO
        return bool(getattr(self.mech_control, 'multiple', False))

    @property
    def value(self):
        if (self.type == 'checkbox' and
            len(self.mech_control.items) == 1 and  # TODO
            self.mech_control.items[0].name == 'on'):  # TODO

            return self.mech_control.items[0].selected  # TODO

        if isinstance(self._control, webtest.forms.Submit):
            return self._control.value_if_submitted()

        # Remove first newline character
        val = self._control.value
        if val.startswith('\n'):
            val = val[1:]

        return str(val)

    @value.setter
    def value(self, value):
        # TODO
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        if self.type == 'file':
            # TODO
            self.mech_control.add_file(value,
                                       content_type=self.content_type,
                                       filename=self.filename)
        elif self.type == 'checkbox' and len(self.mech_control.items) == 1:
            # TODO
            self.mech_control.items[0].selected = bool(value)
        else:
            self._control.value = value

    def add_file(self, file, content_type, filename):
        if self.type != 'file':
            raise TypeError("Can't call add_file on %s controls"
                            % self.mech_control.type)

        if isinstance(file, io.IOBase):
            contents = file.read()
        else:
            contents = file

        # XXX: webtest relies on mimetypes.guess_type to get mime type of
        # upload file and doesn't let to set it explicitly, so we are ignoring
        # content_type parameter here. If it is still unacceptable, consider
        # using mock.object to force mimetypes to return "right" type.
        self._form[self.name] = webtest.forms.Upload(filename, contents)

    def clear(self):
        # TODO
        if self._browser_counter != self.browser._counter:
            raise zope.testbrowser.interfaces.ExpiredError
        self.mech_control.clear()

    def __repr__(self):
        return "<%s name=%r type=%r>" % (
            self.__class__.__name__, self.name, self.type)

@implementer(interfaces.ISubmitControl)
class SubmitControl(Control):

    def click(self):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        self.browser._clickSubmit(self._form, self._control, (1,1))

@implementer(interfaces.IListControl)
class ListControl(Control):

    @property
    def displayValue(self):
        """See zope.testbrowser.interfaces.IListControl"""
        # not implemented for anything other than select;
        # would be nice if mechanize implemented for checkbox and radio.
        # attribute error for all others.

        # TODO
        return self.mech_control.get_value_by_label()


    @displayValue.setter
    def displayValue(self, value):
        if self.browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        self._control.set_value_by_label(value)  # TODO


    @property
    def displayOptions(self):
        """See zope.testbrowser.interfaces.IListControl"""
        # TODO
        res = []
        for item in self.mech_control.items:
            if not item.disabled:
                for label in item.get_labels():
                    if label.text:
                        res.append(label.text)
                        break
                else:
                    res.append(None)
        return res

    @property
    def options(self):
        """See zope.testbrowser.interfaces.IListControl"""
        # TODO
        if (self.type == 'checkbox' and len(self.mech_control.items) == 1 and
            self.mech_control.items[0].name == 'on'):
            return [True]
        return [i.name for i in self.mech_control.items if not i.disabled]

    @property
    def disabled(self):
        # TODO
        if self.type == 'checkbox' and len(self.mech_control.items) == 1:
            return bool(getattr(self.mech_control.items[0], 'disabled', False))
        return bool(getattr(self.mech_control, 'disabled', False))

    @property
    def controls(self):
        # TODO
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        res = [controlFactory(i, self.mech_form, self.browser) for i in
                self.mech_control.items]
        for s in res:
            s.__dict__['control'] = self
        return res

    def getControl(self, label=None, value=None, index=None):
        # TODO
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError

        onlyOne([label, value], '"label" and "value"')

        if label is not None:
            options = self.mech_control.get_items(label=label)
            msg = 'label %r' % label
        elif value is not None:
            options = self.mech_control.get_items(name=value)
            msg = 'value %r' % value
        res = controlFactory(
            disambiguate(options, msg, index, controlFormTupleRepr),
            self.mech_form, self.browser)
        res.__dict__['control'] = self
        return res



@implementer(interfaces.IImageSubmitControl)
class ImageControl(Control):

    def click(self, coord=(1,1)):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        self.browser._clickSubmit(self._form, self._control, coord)

@implementer(interfaces.IItemControl)
class ItemControl(object):

    def __init__(self, item, form, browser):
        self._item = item
        self._form = form
        self.browser = browser
        self._browser_counter = self.browser._counter
        self._enable_setattr_errors = True

    @property
    def control(self):
        # TODO
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        res = controlFactory(
            self._item._control, self.mech_form, self.browser)
        self.__dict__['control'] = res
        return res

    @property
    def disabled(self):
        # TODO
        return self.mech_item.disabled

    @property
    def selected(self):
        """See zope.testbrowser.interfaces.IControl"""
        # TODO
        return self.mech_item.selected

    @selected.setter
    def selected(self, value):
        # TODO
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        self.mech_item.selected = value

    @property
    def optionValue(self):
        # TODO
        return self.mech_item.attrs.get('value')

    def click(self):
        # TODO
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        self.mech_item.selected = not self.mech_item.selected

    def __repr__(self):
        # TODO
        return "<%s name=%r type=%r optionValue=%r selected=%r>" % (
            self.__class__.__name__, self.mech_item._control.name,
            self.mech_item._control.type, self.optionValue, self.mech_item.selected)


@implementer(interfaces.IForm)
class Form(object):
    """HTML Form"""

    def __init__(self, browser, form):
        """Initialize the Form

        browser - a Browser instance
        form - a mechanize.HTMLForm instance
        """
        self.browser = browser
        self._form = form
        self._browser_counter = self.browser._counter

    @property
    def action(self):
        return self._form.action

    @property
    def method(self):
        return self._form.method

    @property
    def enctype(self):
        return self._form.enctype

    @property
    def name(self):
        return self._form.html.body.form.get('name')

    @property
    def id(self):
        """See zope.testbrowser.interfaces.IForm"""
        return self._form.id

    def submit(self, label=None, name=None, index=None, coord=(1,1)):
        """See zope.testbrowser.interfaces.IForm"""
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError

        form = self._form
        if label is not None or name is not None:
            controls, msg, available = self.browser._getAllControls(
                label, name, [form])
            controls = [(control, form) for (control, form) in controls
                        if isinstance(control, webtest.forms.Submit)]
            control, form = disambiguate(controls, msg, index,
                                         controlFormTupleRepr,
                                         available)
            self.browser._clickSubmit(form, control, coord)

        else: # JavaScript sort of submit
            if index is not None or coord != (1,1):
                raise ValueError(
                    'May not use index or coord without a control')
            self.browser._clickSubmit(form)
            ## # TODO
            ## request = self.mech_form._switch_click("request", mechanize.Request)
            ## self.browser._start_timer()
            ## with self.browser.timer:
            ##     try:
            ##         form.submit()
            ##         self.browser.mech_browser.open(request)
            ##     except Exception as e:
            ##         fix_exception_name(e)
            ##         raise


    def getControl(self, label=None, name=None, index=None):
        """See zope.testbrowser.interfaces.IBrowser"""
        # TODO
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        intermediate, msg, available = self.browser._get_all_controls(
            label, name, (self.mech_form,), include_subcontrols=True)
        control, form = disambiguate(intermediate, msg, index,
                                     controlFormTupleRepr,
                                     available)
        return controlFactory(control, form, self.browser)

def disambiguate(intermediate, msg, index, choice_repr=None, available=None):
    if intermediate:
        if index is None:
            if len(intermediate) > 1:
                if choice_repr:
                    msg += ' matches:' + ''.join([
                                '\n  %s' % choice_repr(choice)
                                for choice in intermediate])
                raise AmbiguityError(msg)
            else:
                return intermediate[0]
        else:
            try:
                return intermediate[index]
            except IndexError:
                msg = '%s\nIndex %d out of range, available choices are 0...%d' % (
                            msg, index, len(intermediate) - 1)
                if choice_repr:
                    msg += ''.join(['\n  %d: %s' % (n, choice_repr(choice))
                                    for n, choice in enumerate(intermediate)])
    else:
        if available:
            msg += '\navailable items:' + ''.join([
                '\n  %s' % choice_repr(choice)
                for choice in available])
        elif available is not None: # empty list
            msg += '\n(there are no form items in the HTML)'
    raise LookupError(msg)


def onlyOne(items, description):
    total = sum([bool(i) for i in items])
    if total == 0 or total > 1:
        raise ValueError(
            "Supply one and only one of %s as arguments" % description)

def zeroOrOne(items, description):
    if sum([bool(i) for i in items]) > 1:
        raise ValueError(
            "Supply no more than one of %s as arguments" % description)


## def isMatching(string, expr):
##     """Determine whether ``expr`` matches to ``string``
## 
##     ``expr`` can be None, plain text or regular expression.
## 
##       * If ``expr`` is ``None``, ``string`` is considered matching
##       * If ``expr`` is plain text, its equality to ``string`` will be checked
##       * If ``expr`` is regexp, regexp matching agains ``string`` will
##         be performed
##     """
##     if expr is None:
##         return True
## 
##     if isinstance(expr, RegexType):
##         return expr.match(string)
##     else:
##         return expr == string


class PystoneTimer(object):
    start_time = 0
    end_time = 0
    _pystones_per_second = None

    @property
    def pystonesPerSecond(self):
        """How many pystones are equivalent to one second on this machine"""

        # deferred import as workaround for Zope 2 testrunner issue:
        # http://www.zope.org/Collectors/Zope/2268
        from test import pystone
        if self._pystones_per_second == None:
            self._pystones_per_second = pystone.pystones(pystone.LOOPS/10)[1]
        return self._pystones_per_second

    def _getTime(self):
        if sys.platform.startswith('win'):
            # Windows' time.clock gives us high-resolution wall-time
            return time.clock()
        else:
            # everyone else uses time.time
            return time.time()

    def start(self):
        """Begin a timing period"""
        self.start_time = self._getTime()
        self.end_time = None

    def stop(self):
        """End a timing period"""
        self.end_time = self._getTime()

    @property
    def elapsedSeconds(self):
        """Elapsed time from calling `start` to calling `stop` or present time

        If `stop` has been called, the timing period stopped then, otherwise
        the end is the current time.
        """
        if self.end_time is None:
            end_time = self._getTime()
        else:
            end_time = self.end_time
        return end_time - self.start_time

    @property
    def elapsedPystones(self):
        """Elapsed pystones in timing period

        See elapsed_seconds for definition of timing period.
        """
        return self.elapsedSeconds * self.pystonesPerSecond


    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

class AmbiguityError(ValueError):
    pass

def fix_exception_name(e):
    pass
