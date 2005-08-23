##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
"""Mechanize-based Functional Doctest interfaces

$Id$
"""
__docformat__ = "reStructuredText"
from zope.testbrowser import interfaces
import ClientForm
import mechanize
import operator
import pullparser
import re
import StringIO
import urllib2
import zope.interface

RegexType = type(re.compile(''))
_compress_re = re.compile(r"\s+")
compressText = lambda text: _compress_re.sub(' ', text.strip())

def disambiguate(intermediate, msg, index):
    if intermediate:
        if index is None:
            if len(intermediate) > 1:
                raise ClientForm.AmbiguityError(msg)
            else:
                return intermediate[0]
        else:
            try:
                return intermediate[index]
            except KeyError:
                msg = '%s index %d' % (msg, index)
    raise LookupError(msg)

def controlFactory(control, form, browser):
    if isinstance(control, ClientForm.Item):
        # it is a subcontrol
        return ItemControl(control, form, browser)
    else:
        t = control.type
        if t in ('checkbox', 'select', 'radio'):
            return ListControl(control, form, browser)
        elif t in ('submit', 'submitbutton'):
            return SubmitControl(control, form, browser)
        elif t=='image':
            return ImageControl(control, form, browser)
        else:
            return Control(control, form, browser)

def onlyOne(items, description):
    total = sum([bool(i) for i in items])
    if total == 0 or total > 1:
        raise ValueError(
            "Supply one and only one of %s as arguments" % description)

def zeroOrOne(items, description):
    if sum([bool(i) for i in items]) > 1:
        raise ValueError(
            "Supply no more than one of %s as arguments" % description)


class Browser(object):
    """A web user agent."""
    zope.interface.implements(interfaces.IBrowser)

    def __init__(self, url=None, mech_browser=None):
        if mech_browser is None:
            mech_browser = mechanize.Browser()
        self.mech_browser = mech_browser
        self._counter = 0
        if url is not None:
            self.open(url)

    @property
    def url(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        return self.mech_browser.geturl()

    @property
    def isHtml(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        return self.mech_browser.viewing_html()

    @property
    def title(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        return self.mech_browser.title()

    @property
    def contents(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        response = self.mech_browser.response()
        old_location = response.tell()
        response.seek(0)
        for line in iter(lambda: response.readline().strip(), ''):
            pass
        contents = response.read()
        response.seek(old_location)
        return contents

    @property
    def headers(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        return self.mech_browser.response().info()

    @apply
    def handleErrors():
        """See zope.testbrowser.interfaces.IBrowser"""
        header_key = 'X-zope-handle-errors'

        def get(self):
            headers = self.mech_browser.addheaders
            return dict(headers).get(header_key, True)

        def set(self, value):
            headers = self.mech_browser.addheaders
            current_value = get(self)
            if current_value == value:
                return
            if header_key in dict(headers):
                headers.remove((header_key, current_value))
            headers.append((header_key, value))
            
        return property(get, set)

    def open(self, url, data=None):
        """See zope.testbrowser.interfaces.IBrowser"""
        self.mech_browser.open(url, data)
        self._changed()

    def reload(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        self.mech_browser.reload()
        self._changed()

    def goBack(self, count=1):
        """See zope.testbrowser.interfaces.IBrowser"""
        self.mech_browser.back(count)
        self._changed()

    def addHeader(self, key, value):
        """See zope.testbrowser.interfaces.IBrowser"""
        self.mech_browser.addheaders.append( (key, value) )

    def getLink(self, text=None, url=None, id=None):
        """See zope.testbrowser.interfaces.IBrowser"""
        if id is not None:
            def predicate(link):
                return dict(link.attrs).get('id') == id
            args = {'predicate': predicate}
        else:
            if isinstance(text, RegexType):
                text_regex = text
            elif text is not None:
                text_regex = re.compile(re.escape(text), re.DOTALL)
            else:
                text_regex = None

            if isinstance(url, RegexType):
                url_regex = url
            elif url is not None:
                url_regex = re.compile(re.escape(url), re.DOTALL)
            else:
                url_regex = None
            args = {'text_regex': text_regex, 'url_regex': url_regex}
        return Link(self.mech_browser.find_link(**args), self)

    def _findByLabel(self, label, forms, include_subcontrols=False):
        # forms are iterable of mech_forms
        matches = re.compile(r'(^|\b|\s)%s(\b|\s|$)'
                             % re.escape(compressText(label))).search
        found = []
        for f in forms:
            for control in f.controls:
                phantom = control.type in ('radio', 'checkbox')
                if include_subcontrols and (
                    phantom or control.type=='select'):
                    for i in control.items:
                        for l in i.getLabels():
                            if matches(l.text):
                                found.append((i, f))
                                break
                if not phantom:
                    for l in control.getLabels():
                        if matches(l.text):
                            found.append((control, f))
                            break
        return found

    def _findByName(self, name, forms):
        found = []
        for f in forms:
            for control in f.controls:
                if control.name==name:
                    found.append((control, f))
        return found

    def getControl(self, label=None, name=None, index=None):
        """See zope.testbrowser.interfaces.IBrowser"""
        intermediate, msg = self._get_all_controls(
            label, name, self.mech_browser.forms(), include_subcontrols=True)
        control, form = disambiguate(intermediate, msg, index)
        return controlFactory(control, form, self)

    def _get_all_controls(self, label, name, forms, include_subcontrols=False):
        onlyOne([label, name], '"label" and "name"')

        if label is not None:
            res = self._findByLabel(label, forms, include_subcontrols)
            msg = 'label %r' % label
        elif name is not None:
            res = self._findByName(name, forms)
            msg = 'name %r' % name
        return res, msg
        
    def getForm(self, id=None, name=None, action=None, index=None):
        zeroOrOne([id, name, action], '"id", "name", and "action"')

        matching_forms = []
        for form in self.mech_browser.forms():
            if ((id is not None and form.attrs.get('id') == id)
            or (name is not None and form.name == name)
            or (action is not None and re.search(action, str(form.action)))
            or id == name == action == None):
                matching_forms.append(form)

        form = disambiguate(matching_forms, '', index)
        self.mech_browser.form = form
        return Form(self, form)
        
    def _clickSubmit(self, form, control, coord):
        self.mech_browser.open(form.click(
                    id=control.id, name=control.name, coord=coord))

    def _changed(self):
        self._counter += 1


class Link(object):
    zope.interface.implements(interfaces.ILink)

    def __init__(self, link, browser):
        self.mech_link = link
        self.browser = browser
        self._browser_counter = self.browser._counter

    def click(self):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        self.browser.mech_browser.follow_link(self.mech_link)
        self.browser._changed()

    @property
    def url(self):
        return self.mech_link.absolute_url

    @property
    def text(self):
        return self.mech_link.text

    @property
    def tag(self):
        return self.mech_link.tag

    @property
    def attrs(self):
        return dict(self.mech_link.attrs)

    def __repr__(self):
        return "<%s text=%r url=%r>" % (
            self.__class__.__name__, self.text, self.url)


class Control(object):
    """A control of a form."""
    zope.interface.implements(interfaces.IControl)

    def __init__(self, control, form, browser):
        self.mech_control = control
        self.mech_form = form
        self.browser = browser
        self._browser_counter = self.browser._counter

        # for some reason ClientForm thinks we shouldn't be able to modify
        # hidden fields, but while testing it is sometimes very important
        if self.mech_control.type == 'hidden':
            self.mech_control.readonly = False

    @property
    def disabled(self):
        return bool(getattr(self.mech_control, 'disabled', False))

    @property
    def type(self):
        return getattr(self.mech_control, 'type', None)

    @property
    def name(self):
        return getattr(self.mech_control, 'name', None)

    @property
    def multiple(self):
        return bool(getattr(self.mech_control, 'multiple', False))

    @apply
    def value():
        """See zope.testbrowser.interfaces.IControl"""

        def fget(self):
            if (self.type == 'checkbox' and
                len(self.mech_control.items) == 1 and
                self.mech_control.items[0].value == 'on'):
                return self.mech_control.items[0].selected
            return self.mech_control.value

        def fset(self, value):
            if self._browser_counter != self.browser._counter:
                raise interfaces.ExpiredError
            if self.mech_control.type == 'file':
                self.mech_control.add_file(value)
            elif self.type == 'checkbox' and len(self.mech_control.items) == 1:
                self.mech_control.items[0].selected = bool(value)
            else:
                self.mech_control.value = value
        return property(fget, fset)

    def clear(self):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        self.mech_control.clear()

    def __repr__(self):
        return "<%s name=%r type=%r>" % (
            self.__class__.__name__, self.name, self.type)


class ListControl(Control):
    zope.interface.implements(interfaces.IListControl)

    @apply
    def displayValue():
        """See zope.testbrowser.interfaces.IListControl"""
        # not implemented for anything other than select;
        # would be nice if ClientForm implemented for checkbox and radio.
        # attribute error for all others.

        def fget(self):
            return self.mech_control.get_value_by_label()

        def fset(self, value):
            if self._browser_counter != self.browser._counter:
                raise interfaces.ExpiredError
            self.mech_control.set_value_by_label(value)

        return property(fget, fset)

    @property
    def displayOptions(self):
        """See zope.testbrowser.interfaces.IListControl"""
        res = []
        for item in self.mech_control.items:
            if not item.disabled:
                for label in item.getLabels():
                    if label.text:
                        res.append(label.text)
                        break
                    else:
                        res.append(None)
        return res

    @property
    def options(self):
        """See zope.testbrowser.interfaces.IListControl"""
        if (self.type == 'checkbox' and len(self.mech_control.items) == 1 and
            self.mech_control.items[0].value == 'on'):
            return [True]
        return [i.value for i in self.mech_control.items if not i.disabled]

    @property
    def controls(self):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        res = [controlFactory(i, self.mech_form, self.browser) for i in 
                self.mech_control.items]
        for s in res:
            s.__dict__['control'] = self
        return res

    def getControl(self, label=None, value=None, index=None):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError

        onlyOne([label, value], '"label" and "value"')

        if label is not None:
            options = self.mech_control.items_from_label(label)
            msg = 'label %r' % label
        elif value is not None:
            options = self.mech_control.items_from_value(value)
            msg = 'value %r' % value
        res = controlFactory(
            disambiguate(options, msg, index), self.mech_form, self.browser)
        res.__dict__['control'] = self
        return res


class SubmitControl(Control):
    zope.interface.implements(interfaces.ISubmitControl)

    def click(self):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        self.browser._clickSubmit(self.mech_form, self.mech_control, (1,1))
        self.browser._changed()


class ImageControl(Control):
    zope.interface.implements(interfaces.IImageSubmitControl)

    def click(self, coord=(1,1)):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        self.browser._clickSubmit(self.mech_form, self.mech_control, coord)
        self.browser._changed()


class ItemControl(object):
    zope.interface.implements(interfaces.IItemControl)

    def __init__(self, item, form, browser):
        self.mech_item = item
        self.mech_form = form
        self.browser = browser
        self._browser_counter = self.browser._counter

    @property
    def control(self):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        res = controlFactory(
            self.mech_item.control, self.mech_form, self.browser)
        self.__dict__['control'] = res
        return res

    @property
    def disabled(self):
        return self.mech_item.disabled

    @apply
    def selected():
        """See zope.testbrowser.interfaces.IControl"""

        def fget(self):
            return self.mech_item.selected

        def fset(self, value):
            if self._browser_counter != self.browser._counter:
                raise interfaces.ExpiredError
            self.mech_item.selected = value

        return property(fget, fset)

    @property
    def optionValue(self):
        return self.mech_item.attrs.get('value')

    def click(self):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        self.mech_item.selected = not self.mech_item.selected

    def __repr__(self):
        return "<%s name=%r type=%r optionValue=%r>" % (
            self.__class__.__name__, self.mech_item.control.name,
            self.mech_item.control.type, self.optionValue)


class Form(object):
    """HTML Form"""
    zope.interface.implements(interfaces.IForm)

    def __init__(self, browser, form):
        """Initialize the Form

        browser - a Browser instance
        form - a ClientForm instance
        """
        self.browser = browser
        self.mech_form = form
        self._browser_counter = self.browser._counter
    
    def __getattr__(self, name):
        # See zope.testbrowser.interfaces.IForm
        names = ['action', 'method', 'enctype', 'name']
        if name in names:
            return getattr(self.mech_form, name, None)
        else:
            raise AttributeError(name)

    @property
    def id(self):
        """See zope.testbrowser.interfaces.IForm"""
        return self.mech_form.attrs.get('id')

    def submit(self, label=None, name=None, index=None, coord=(1,1)):
        """See zope.testbrowser.interfaces.IForm"""
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        form = self.mech_form
        if label is not None or name is not None:
            intermediate, msg = self.browser._get_all_controls(
                label, name, (form,))
            intermediate = [
                (control, form) for (control, form) in intermediate if
                control.type in ('submit', 'submitbutton', 'image')]
            control, form = disambiguate(intermediate, msg, index)
            self.browser._clickSubmit(form, control, coord)
        else: # JavaScript sort of submit
            if index is not None or coord != (1,1):
                raise ValueError(
                    'May not use index or coord without a control')
            request = self.mech_form._switch_click("request", urllib2.Request)
            self.browser.mech_browser.open(request)
        self.browser._changed()

    def getControl(self, label=None, name=None, index=None):
        """See zope.testbrowser.interfaces.IBrowser"""
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        intermediate, msg = self.browser._get_all_controls(
            label, name, (self.mech_form,), include_subcontrols=True)
        control, form = disambiguate(intermediate, msg, index)
        return controlFactory(control, form, self.browser)
