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
import re
import StringIO
import mechanize
import pullparser
import zope.interface

from zope.testbrowser import interfaces

RegexType = type(re.compile(''))

class Browser(object):
    """A web user agent."""
    zope.interface.implements(interfaces.IBrowser)

    def __init__(self, url=None, mech_browser=None):
        if mech_browser is None:
            mech_browser = mechanize.Browser()
        self.mech_browser = mech_browser
        
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
    def forms(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        return FormsMapping(self)

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

    def click(self, text=None, url=None, id=None):
        """See zope.testbrowser.interfaces.IBrowser"""
        if id is not None:
            def predicate(link):
                return dict(link.attrs).get('id') == id
            self.mech_browser.follow_link(predicate=predicate)
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

            self.mech_browser.follow_link(
                text_regex=text_regex, url_regex=url_regex)
        self._changed()

    def _findByLabel(self, label, form=None, include_subcontrols=False):
        # form is None or a mech_form
        ids = [id for id, l in self._label_tags if label in l]
        found = []
        for f in self.mech_browser.forms():
            if form is None or form == f:
                for control in f.controls:
                    if control.type in ('radio', 'checkbox'):
                        if include_subcontrols:
                            for ix, attrs in enumerate(control._attrs_list):
                                sub_id = attrs.get('id')
                                if sub_id is not None and sub_id in ids:
                                    found.append(((control, ix), f))
                    elif (control.id in ids or (
                        control.type in ('button', 'submit') and
                        label in str(control.value))):
                        # the str(control.value) is a hack to get
                        # string-in-string behavior when the value is a list.
                        # maybe should be revisited.
                        found.append((control, f))
        return found

    def _findByName(self, name, form=None):
        found = []
        for f in self.mech_browser.forms():
            if form is None or form == f:
                for control in f.controls:
                    if control.name==name:
                        found.append((control, f))
        return found

    def get(self, label=None, name=None, index=None):
        """See zope.testbrowser.interfaces.IBrowser"""
        intermediate, msg = self._get_all(
            label, name, include_subcontrols=True)
        control, form = self._disambiguate(intermediate, msg, index)
        return controlFactory(control, form, self)

    def _get_all(self, label, name, form=None, include_subcontrols=False):
        if not ((label is not None) ^ (name is not None)):
            raise ValueError(
                "Supply one and only one of 'label' and 'name' arguments")
        if label is not None:
            res = self._findByLabel(label, form, include_subcontrols)
            msg = 'label %r' % label
        elif name is not None:
            res = self._findByName(name, form)
            msg = 'name %r' % name
        return res, msg

    def _disambiguate(self, intermediate, msg, index):
        if intermediate:
            if index is None:
                if len(intermediate) > 1:
                    raise interfaces.AmbiguityError(msg)
                else:
                    return intermediate[0]
            else:
                try:
                    return intermediate[index]
                except KeyError:
                    msg = '%s index %d' % (msg, index)
        raise LookupError(msg)
        
    def _findForm(self, id, name, action):
        for form in self.mech_browser.forms():
            if ((id is not None and form.attrs.get('id') == id)
            or (name is not None and form.name == name)
            or (action is not None and re.search(action, str(form.action)))):
                self.mech_browser.form = form
                return form

        return None
        
    def _clickSubmit(self, form, control, coord):
        self.mech_browser.open(form.click(
                    id=control.id, name=control.name, coord=coord))

    # I'd like a different solution for the caching.  Later.

    @property
    def _label_tags(self): # [(id, label)]
        cache = []
        p = pullparser.PullParser(StringIO.StringIO(self.contents))
        for token in p.tags('label'):
            if token.type=='starttag':
                cache.append((dict(token.attrs).get('for'),
                             p.get_compressed_text(
                                endat=("endtag", "label"))))
        self.__dict__['_label_tags'] = cache
        return cache

    @property
    def _label_tags_mapping(self):
        cache = {}
        for i, l in self._label_tags:
            found = cache.get(i)
            if found is None:
                found = cache[i] = []
            found.append(l)
        self.__dict__['_label_tags_mapping'] = cache
        return cache

    def _changed(self):
        try:
            del self.__dict__['_label_tags']
            del self.__dict__['_label_tags_mapping'] # this depends on
            # _label_tags, so combining them in the same block should be fine,
            # as long as _label_tags is first.
        except KeyError:
            pass
        


class Control(object):
    """A control of a form."""
    zope.interface.implements(interfaces.IControl)

    def __init__(self, control, form, browser):
        self.mech_control = control
        self.mech_form = form
        self.browser = browser

        # for some reason ClientForm thinks we shouldn't be able to modify
        # hidden fields, but while testing it is sometimes very important
        if self.mech_control.type == 'hidden':
            self.mech_control.readonly = False

    def __getattr__(self, name):
        # See zope.testbrowser.interfaces.IControl
        names = ['disabled', 'type', 'name', 'multiple']
        booleans = ['disabled', 'multiple']
        if name in names:
            result = getattr(self.mech_control, name, None)
        else:
            raise AttributeError(name)

        if name in booleans:
            result = bool(result)

        return result

    @apply
    def value():
        """See zope.testbrowser.interfaces.IControl"""

        def fget(self):
            value = self.mech_control.value
            if self.type == 'checkbox' and self.options == [True]:
                value = bool(value)
            return value

        def fset(self, value):
            if self.mech_control.type == 'file':
                self.mech_control.add_file(value)
                return
            if self.type == 'checkbox' and self.options == [True]:
                if value: 
                    value = ['on']
                else:
                    value = []
            self.mech_control.value = value
        return property(fget, fset)

    def clear(self):
        self.mech_control.clear()

    def __repr__(self):
        return "<%s name=%r type=%r>" % (
            self.__class__.__name__, self.name, self.type)

def _getLabel(attr, mapping):
    label = None
    attr_id = attr.get('id')
    if attr_id is not None:
        labels = mapping.get(attr_id, ())
        for label in labels:
            if label: # get the first one with text
                break
    return label

def _isSelected(mech_control, ix):
    if mech_control.type == 'radio':
        # we don't have precise ordering, so we have to guess
        attr = mech_control._attrs_list[ix]
        return attr.get('value', 'on') == mech_control._selected
    else:
        return mech_control._selected[ix]

class ListControl(Control):
    zope.interface.implements(interfaces.IListControl)

    @apply
    def displayValue():
        """See zope.testbrowser.interfaces.IListControl"""
        # not implemented for anything other than select;
        # would be nice if ClientForm implemented for checkbox and radio.
        # attribute error for all others.

        def fget(self):
            try:
                return self.mech_control.get_value_by_label()
            except NotImplementedError:
                mapping = self.browser._label_tags_mapping
                res = []
                for ix in range(len(self.mech_control.possible_items())):
                    if _isSelected(self.mech_control, ix):
                        attr = self.mech_control._attrs_list[ix]
                        res.append(_getLabel(attr, mapping))
                        if self.mech_control.type == 'radio':
                            return res
                            # this is not simply an optimization,
                            # unfortunately.  We don't have easy access to
                            # the precise index of the selected radio button,
                            # but merely the current value.  Therefore, if
                            # two or more radio buttons of the same name
                            # have the same value, we can't easily tell which
                            # is actually checked.  Rather than returning
                            # all of them, which would arguably be confusing,
                            # we return the first.
                return res
                    

        def fset(self, value):
            try:
                self.mech_control.set_value_by_label(value)
            except NotImplementedError:
                mapping = self.browser._label_tags_mapping
                res = []
                for v in value:
                    found = []
                    for attr in self.mech_control._attrs_list:
                        attr_value = attr.get('value', 'on')
                        if attr_value not in found:
                            attr_id = attr.get('id')
                            if attr_id is not None:
                                labels = mapping.get(attr_id, ())
                                for l in labels:
                                    if v in l:
                                        found.append(attr_value)
                                        break
                    if not found:
                        raise LookupError(v)
                    elif len(found) > 1:
                        raise interfaces.AmbiguityError(v)
                    res.extend(found)
                self.value = res

        return property(fget, fset)

    @property
    def displayOptions(self):
        """See zope.testbrowser.interfaces.IListControl"""
        try:
            return self.mech_control.possible_items(by_label=True)
        except NotImplementedError:
            mapping = self.browser._label_tags_mapping
            res = []
            for attr in self.mech_control._attrs_list:
                res.append(_getLabel(attr, mapping))
            return res

    @property
    def options(self):
        """See zope.testbrowser.interfaces.IListControl"""
        if (self.type == 'checkbox'
            and self.mech_control.possible_items() == ['on']):
            return [True]
        return self.mech_control.possible_items()

    #@property
    #def subcontrols(self):
        # XXX

class SubmitControl(Control):
    zope.interface.implements(interfaces.ISubmitControl)

    def click(self):
        self.browser._clickSubmit(self.mech_form, self.mech_control, (1,1))
        self.browser._changed()

class ImageControl(Control):
    zope.interface.implements(interfaces.IImageSubmitControl)

    def click(self, coord=(1,1)):
        self.browser._clickSubmit(self.mech_form, self.mech_control, coord)
        self.browser._changed()

class Subcontrol(object):
    zope.interface.implements(interfaces.ISubcontrol)

    def __init__(self, control, index, form, browser):
        self.mech_control = control
        self.index = index
        self.mech_form = form
        self.browser = browser

    @property
    def control(self):
        res = controlFactory(self.mech_control, self.mech_form, self.browser)
        self.__dict__['control'] = res
        return res

    @property
    def disabled(self):
        return bool(self.mech_control._attrs_list[self.index].get('disabled'))

    @apply
    def value():
        """See zope.testbrowser.interfaces.IControl"""

        def fget(self):
            # if a set of radio buttons of the same name have choices
            # that are the same value, and a radio button is selected for
            # one of the identical values, radio buttons will always return 
            # True simply on the basis of whether their value is equal to
            # the control's current value.  An arguably pathological case.
            return _isSelected(self.mech_control, self.index)

        def fset(self, value):
            # if a set of checkboxes of the same name have choices
            # that are the same value, and a checkbox is selected for
            # one of the identical values, the first checkbox will be the one
            # changed in all cases.  An arguably pathological case.
            if not self.disabled: # TODO is readonly an option?
                attrs = self.mech_control._attrs_list[self.index]
                option_value = attrs.get('value', 'on')
                current = self.mech_control.value
                if value:
                    if option_value not in current:
                        if self.mech_control.multiple:
                            current.append(option_value)
                        else:
                            current = [option_value]
                        self.mech_control.value = current
                else:
                    try:
                        current.remove(option_value)
                    except ValueError:
                        pass
                    else:
                        self.mech_control.value = current
            else:
                raise AttributeError("control %r, index %d, is disabled" %
                                     (self.mech_control.name, self.index))
        return property(fget, fset)

    #def click(self):
        # XXX

    def __repr__(self):
        return "<%s name=%r type=%r index=%d>" % (
            self.__class__.__name__, self.mech_control.name,
            self.mech_control.type, self.index)

def controlFactory(control, form, browser):
    if isinstance(control, tuple):
        # it is a subcontrol
        control, index = control
        return Subcontrol(control, index, form, browser)
    else:
        t = control.type
        if t in ('checkbox', 'select', 'radio'):
            return ListControl(control, form, browser)
        elif t=='submit':
            return SubmitControl(control, form, browser)
        elif t=='image':
            return ImageControl(control, form, browser)
        else:
            return Control(control, form, browser)

class FormsMapping(object):
    """All forms on the page of the browser."""
    zope.interface.implements(interfaces.IFormsMapping)
    
    def __init__(self, browser):
        self.browser = browser

    def __getitem__(self, key):
        """See zope.interface.common.mapping.IItemMapping"""
        form = self.browser._findForm(key, key, None)
        if form is None:
            raise KeyError(key)
        return Form(self.browser, form)

    def get(self, key, default=None):
        """See zope.interface.common.mapping.IReadMapping"""
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key):
        """See zope.interface.common.mapping.IReadMapping"""
        return self.browser._findForm(key, key, None) is not None

    def values(self):
        return [Form(self.browser, form) for form in
                self.browser.mech_browser.forms()]


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
        form = self.mech_form
        if label is not None or name is not None:
            intermediate, msg = self.browser._get_all(label, name, form)
            intermediate = [
                (control, form) for (control, form) in intermediate if
                control.type in ('submit', 'image')]
            control, form = self.browser._disambiguate(
                intermediate, msg, index)
            self.browser._clickSubmit(form, control, coord)
        else: # JavaScript sort of submit
            if index is not None or coord != (1,1):
                raise ValueError(
                    'May not use index or coord without a control')
            request = self.mech_form.click()
            self.browser.mech_browser.open(request)
        self.browser._changed()

    def get(self, label=None, name=None, index=None):
        """See zope.testbrowser.interfaces.IBrowser"""
        intermediate, msg = self.browser._get_all(
            label, name, self.mech_form, include_subcontrols=True)
        control, form = self.browser._disambiguate(intermediate, msg, index)
        return controlFactory(control, form, self.browser)
