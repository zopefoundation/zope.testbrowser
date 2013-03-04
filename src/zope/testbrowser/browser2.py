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

from zope.interface import implementer

from zope.testbrowser import interfaces
from zope.testbrowser._compat import httpclient

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

    def __init__(self, url=None, application=None):
        self.timer = PystoneTimer()
        self.raiseHttpErrors = True
        self.testapp = webtest.TestApp(application)

        if url is not None:
            self.open(url)

    @property
    def headers(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        return self._response.headers

    def open(self, url, data=None):
        """See zope.testbrowser.interfaces.IBrowser"""

        url = str(url)
        with self.timer:
            try:
                if data is not None:
                    self._response = self.testapp.post(url, data)
                else:
                    self._response = self.testapp.get(url)
                pass
            finally:
                self._changed()

        # if the headers don't have a status, I suppose there can't be an error
        if 'Status' in self.headers:
            code, msg = self.headers['Status'].split(' ', 1)
            code = int(code)
            if self.raiseHttpErrors and code >= 400:
                raise httpclient.HTTPException(url, code, msg, self.headers)

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

    def _clickSubmit(self, form, control, coord):
        # find index of given control in the form
        index = form.fields[control.name].index(control)
        with self.timer:
            try:
                self._response = form.submit(control.name, index)
                #self.mech_browser.form = form
                #self.mech_browser.submit(id=control.id, name=control.name,
                #                         label=label, coord=coord)
            except Exception as e:
                fix_exception_name(e)
                raise

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

        return self._control.value_if_submitted()

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
        # TODO
        if not self.mech_control.type == 'file':
            raise TypeError("Can't call add_file on %s controls"
                            % self.mech_control.type)
        if isinstance(file, str):
            import cStringIO
            file = cStringIO.StringIO(file)
        self.mech_control.add_file(file, content_type, filename)

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
        try:
            self.browser._clickSubmit(self._form, self._control, (1,1))
        finally:
            self.browser._changed()

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
        try:
            self.browser._clickSubmit(self._form, self._control, coord)
        finally:
            self.browser._changed()

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
