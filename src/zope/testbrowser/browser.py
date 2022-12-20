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

import http.client
import io
import re
import time
import urllib.parse
import urllib.request
import urllib.robotparser
from contextlib import contextmanager

import webtest
from bs4 import BeautifulSoup
from soupsieve import escape as css_escape
from wsgiproxy.proxies import TransparentProxy
from zope.cachedescriptors.property import Lazy
from zope.interface import implementer

import zope.testbrowser.cookies
from zope.testbrowser import interfaces


__docformat__ = "reStructuredText"

HTTPError = urllib.request.HTTPError
RegexType = type(re.compile(''))
_compress_re = re.compile(r"\s+")


class HostNotAllowed(Exception):
    pass


class RobotExclusionError(HTTPError):
    def __init__(self, *args):
        super().__init__(*args)


# RFC 2606
_allowed_2nd_level = {'example.com', 'example.net', 'example.org'}

_allowed = {'localhost', '127.0.0.1'}
_allowed.update(_allowed_2nd_level)

REDIRECTS = (301, 302, 303, 307)


class TestbrowserApp(webtest.TestApp):
    _last_fragment = ""
    restricted = False

    def _assertAllowed(self, url):
        parsed = urllib.parse.urlparse(url)
        if self.restricted:
            # We are in restricted mode, check host part only
            host = parsed.netloc.partition(':')[0]
            if host in _allowed:
                return
            for dom in _allowed_2nd_level:
                if host.endswith('.%s' % dom):
                    return

            raise HostNotAllowed(url)
        else:
            # Unrestricted mode: retrieve robots.txt and check against it
            robotsurl = urllib.parse.urlunsplit(
                (parsed.scheme, parsed.netloc, '/robots.txt', '', ''))
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robotsurl)
            rp.read()
            if not rp.can_fetch("*", url):
                msg = "request disallowed by robots.txt"
                raise RobotExclusionError(url, 403, msg, [], None)

    def do_request(self, req, status, expect_errors):
        self._assertAllowed(req.url)

        response = super().do_request(req, status,
                                      expect_errors)
        # Store _last_fragment in response to preserve fragment for history
        # (goBack() will not lose fragment).
        response._last_fragment = self._last_fragment
        return response

    def _remove_fragment(self, url):
        # HACK: we need to preserve fragment part of url, but webtest strips it
        # from url on every request. So we override this protected method,
        # assuming it is called on every request and therefore _last_fragment
        # will not get outdated. ``getRequestUrlWithFragment()`` will
        # reconstruct url with fragment for the last request.
        scheme, netloc, path, query, fragment = urllib.parse.urlsplit(url)
        self._last_fragment = fragment
        return super()._remove_fragment(url)

    def getRequestUrlWithFragment(self, response):
        url = response.request.url
        if not self._last_fragment:
            return url
        return "{}#{}".format(url, response._last_fragment)


class SetattrErrorsMixin:
    _enable_setattr_errors = False

    def __setattr__(self, name, value):
        if self._enable_setattr_errors:
            # cause an attribute error if the attribute doesn't already exist
            getattr(self, name)

        # set the value
        object.__setattr__(self, name, value)


@implementer(interfaces.IBrowser)
class Browser(SetattrErrorsMixin):
    """A web user agent."""

    _contents = None
    _controls = None
    _counter = 0
    _response = None
    _req_headers = None
    _req_content_type = None
    _req_referrer = None
    _history = None
    __html = None

    def __init__(self, url=None, wsgi_app=None):
        self.timer = Timer()
        self.raiseHttpErrors = True
        self.handleErrors = True
        self.followRedirects = True

        if wsgi_app is None:
            self.testapp = TestbrowserApp(TransparentProxy())
        else:
            self.testapp = TestbrowserApp(wsgi_app)
            self.testapp.restricted = True

        self._req_headers = {}
        self._history = History()
        self._enable_setattr_errors = True
        self._controls = {}

        if url is not None:
            self.open(url)

    @property
    def url(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        if self._response is None:
            return None
        return self.testapp.getRequestUrlWithFragment(self._response)

    @property
    def isHtml(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        return self._response and 'html' in self._response.content_type

    @property
    def lastRequestSeconds(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        return self.timer.elapsedSeconds

    @property
    def title(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        if not self.isHtml:
            raise BrowserStateError('not viewing HTML')

        titles = self._html.find_all('title')
        if not titles:
            return None
        return self.toStr(titles[0].text)

    def reload(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        if self._response is None:
            raise BrowserStateError("no URL has yet been .open()ed")

        def make_request(args):
            return self.testapp.request(self._response.request)

        # _req_referrer is left intact, so will be the referrer (if any) of
        # the request being reloaded.
        self._processRequest(self.url, make_request)

    def goBack(self, count=1):
        """See zope.testbrowser.interfaces.IBrowser"""
        resp = self._history.back(count, self._response)
        self._setResponse(resp)

    @property
    def contents(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        if self._response is not None:
            return self.toStr(self._response.body)
        else:
            return None

    @property
    def headers(self):
        """See zope.testbrowser.interfaces.IBrowser"""
        resptxt = []
        resptxt.append('Status: %s' % self._response.status)
        for h, v in sorted(self._response.headers.items()):
            resptxt.append(str("{}: {}".format(h, v)))

        inp = '\n'.join(resptxt)
        stream = io.BytesIO(inp.encode('latin1'))
        return http.client.parse_headers(stream)

    @property
    def cookies(self):
        if self.url is None:
            raise RuntimeError("no request found")
        return zope.testbrowser.cookies.Cookies(self.testapp, self.url,
                                                self._req_headers)

    def addHeader(self, key, value):
        """See zope.testbrowser.interfaces.IBrowser"""
        if (self.url and key.lower() in ('cookie', 'cookie2') and
                self.cookies.header):
            raise ValueError('cookies are already set in `cookies` attribute')
        self._req_headers[key] = value

    def open(self, url, data=None, referrer=None):
        """See zope.testbrowser.interfaces.IBrowser"""
        url = self._absoluteUrl(url)
        if data is not None:
            def make_request(args):
                return self.testapp.post(url, data, **args)
        else:
            def make_request(args):
                return self.testapp.get(url, **args)

        self._req_referrer = referrer
        self._processRequest(url, make_request)

    def post(self, url, data, content_type=None, referrer=None):
        if content_type is not None:
            self._req_content_type = content_type
        self._req_referrer = referrer
        return self.open(url, data)

    def _clickSubmit(self, form, control=None, coord=None):
        # find index of given control in the form
        url = self._absoluteUrl(form.action)
        if control:
            def make_request(args):
                index = form.fields[control.name].index(control)
                return self._submit(
                    form, control.name, index, coord=coord, **args)
        else:
            def make_request(args):
                return self._submit(form, coord=coord, **args)

        self._req_referrer = self.url
        self._processRequest(url, make_request)

    def _processRequest(self, url, make_request):
        with self._preparedRequest(url) as reqargs:
            self._history.add(self._response)
            resp = make_request(reqargs)
            if self.followRedirects:
                remaining_redirects = 100  # infinite loops protection
                while resp.status_int in REDIRECTS and remaining_redirects:
                    remaining_redirects -= 1
                    self._req_referrer = url
                    url = urllib.parse.urljoin(url, resp.headers['location'])
                    with self._preparedRequest(url) as reqargs:
                        resp = self.testapp.get(url, **reqargs)
                assert remaining_redirects > 0, (
                    "redirects chain looks infinite")
            self._setResponse(resp)
            self._checkStatus()

    def _checkStatus(self):
        # if the headers don't have a status, I suppose there can't be an error
        if 'Status' in self.headers:
            code, msg = self.headers['Status'].split(' ', 1)
            code = int(code)
            if self.raiseHttpErrors and code >= 400:
                raise HTTPError(self.url, code, msg, [], None)

    def _submit(self, form, name=None, index=None, coord=None, **args):
        # A reimplementation of webtest.forms.Form.submit() to allow to insert
        # coords into the request
        fields = form.submit_fields(name, index=index)
        if coord is not None:
            fields.extend([('%s.x' % name, coord[0]),
                           ('%s.y' % name, coord[1])])

        url = self._absoluteUrl(form.action)
        if form.method.upper() != "GET":
            args.setdefault("content_type", form.enctype)
        else:
            parsed = urllib.parse.urlparse(url)._replace(query='', fragment='')
            url = urllib.parse.urlunparse(parsed)
        return form.response.goto(url, method=form.method,
                                  params=fields, **args)

    def _setResponse(self, response):
        self._response = response
        self._changed()

    def getLink(self, text=None, url=None, id=None, index=0):
        """See zope.testbrowser.interfaces.IBrowser"""
        qa = 'a' if id is None else 'a#%s' % css_escape(id)
        qarea = 'area' if id is None else 'area#%s' % css_escape(id)
        html = self._html
        links = html.select(qa)
        links.extend(html.select(qarea))

        matching = []
        for elem in links:
            matches = (isMatching(elem.text, text) and
                       isMatching(elem.get('href', ''), url))

            if matches:
                matching.append(elem)

        if index >= len(matching):
            raise LinkNotFoundError()
        elem = matching[index]

        baseurl = self._getBaseUrl()

        return Link(elem, self, baseurl)

    def follow(self, *args, **kw):
        """Select a link and follow it."""
        self.getLink(*args, **kw).click()

    def _getBaseUrl(self):
        # Look for <base href> tag and use it as base, if it exists
        url = self._response.request.url
        if b"<base" not in self._response.body:
            return url

        # we suspect there is a base tag in body, try to find href there
        html = self._html
        if not html.head:
            return url
        base = html.head.base
        if not base:
            return url
        return base['href'] or url

    def getForm(self, id=None, name=None, action=None, index=None):
        """See zope.testbrowser.interfaces.IBrowser"""
        zeroOrOne([id, name, action], '"id", "name", and "action"')
        matching_forms = []
        allforms = self._getAllResponseForms()
        for form in allforms:
            if ((id is not None and form.id == id) or
                (name is not None and form.html.form.get('name') == name) or
                (action is not None and re.search(action, form.action)) or
                    id == name == action is None):
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
            label, name, self._getAllResponseForms(),
            include_subcontrols=True)
        control = disambiguate(intermediate, msg, index,
                               controlFormTupleRepr,
                               available)
        return control

    def _getAllResponseForms(self):
        """ Return set of response forms in the order they appear in
        ``self._response.form``."""
        respforms = self._response.forms
        idxkeys = [k for k in respforms.keys() if isinstance(k, int)]
        return [respforms[k] for k in sorted(idxkeys)]

    def _getAllControls(self, label, name, forms, include_subcontrols=False):
        onlyOne([label, name], '"label" and "name"')

        # might be an iterator, and we need to iterate twice
        forms = list(forms)

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
                             % re.escape(normalizeWhitespace(label))).search
        found = []
        for wtcontrol in self._findAllControls(forms, include_subcontrols):
            control = getattr(wtcontrol, 'control', wtcontrol)
            if control.type == 'hidden':
                continue
            for label in wtcontrol.labels:
                if matches(label):
                    found.append(wtcontrol)
                    break
        return found

    def _indexControls(self, form):
        # Unfortunately, webtest will remove all 'name' attributes from
        # form.html after parsing. But we need them (at least to locate labels
        # for radio buttons). So we are forced to reparse part of html, to
        # extract elements.
        html = BeautifulSoup(form.text, 'html.parser')
        tags = ('input', 'select', 'textarea', 'button')
        return html.find_all(tags)

    def _findByName(self, name, forms):
        return [c for c in self._findAllControls(forms) if c.name == name]

    def _findAllControls(self, forms, include_subcontrols=False):
        res = []
        for f in forms:
            if f not in self._controls:
                fc = []
                allelems = self._indexControls(f)
                already_processed = set()
                for cname, wtcontrol in f.field_order:
                    # we need to group checkboxes by name, but leave
                    # the other controls in the original order,
                    # even if the name repeats
                    if isinstance(wtcontrol, webtest.forms.Checkbox):
                        if cname in already_processed:
                            continue
                        already_processed.add(cname)
                        wtcontrols = f.fields[cname]
                    else:
                        wtcontrols = [wtcontrol]
                    for c in controlFactory(cname, wtcontrols, allelems, self):
                        fc.append((c, False))

                        for subcontrol in c.controls:
                            fc.append((subcontrol, True))

                self._controls[f] = fc

            controls = [c for c, subcontrol in self._controls[f]
                        if not subcontrol or include_subcontrols]
            res.extend(controls)

        return res

    def _changed(self):
        self._counter += 1
        self._contents = None
        self._controls = {}
        self.__html = None

    @contextmanager
    def _preparedRequest(self, url):
        self.timer.start()

        headers = {}
        if self._req_referrer is not None:
            headers['Referer'] = self._req_referrer

        if self._req_content_type:
            headers['Content-Type'] = self._req_content_type

        headers['Connection'] = 'close'
        headers['Host'] = urllib.parse.urlparse(url).netloc
        headers['User-Agent'] = 'Python-urllib/2.4'

        headers.update(self._req_headers)

        extra_environ = {}
        if self.handleErrors:
            extra_environ['paste.throw_errors'] = None
            headers['X-zope-handle-errors'] = 'True'
        else:
            extra_environ['wsgi.handleErrors'] = False
            extra_environ['paste.throw_errors'] = True
            extra_environ['x-wsgiorg.throw_errors'] = True
            headers.pop('X-zope-handle-errors', None)

        kwargs = {'headers': sorted(headers.items()),
                  'extra_environ': extra_environ,
                  'expect_errors': True}

        yield kwargs

        self._req_content_type = None
        self.timer.stop()

    def _absoluteUrl(self, url):
        absolute = url.startswith('http://') or url.startswith('https://')
        if absolute:
            return str(url)

        if self._response is None:
            raise BrowserStateError(
                "can't fetch relative reference: not viewing any document")

        return str(urllib.parse.urljoin(self._getBaseUrl(), url))

    def toStr(self, s):
        """Convert possibly unicode object to native string using response
        charset"""
        if not self._response.charset:
            return s
        if s is None:
            return None
        # Might be an iterable, especially the 'class' attribute.
        if isinstance(s, (list, tuple)):
            subs = [self.toStr(sub) for sub in s]
            if isinstance(s, tuple):
                return tuple(subs)
            return subs
        if isinstance(s, bytes):
            return s.decode(self._response.charset)
        return s

    @property
    def _html(self):
        if self.__html is None:
            self.__html = self._response.html
        return self.__html


def controlFactory(name, wtcontrols, elemindex, browser):
    assert len(wtcontrols) > 0

    first_wtc = wtcontrols[0]
    checkbox = isinstance(first_wtc, webtest.forms.Checkbox)

    # Create control list
    if checkbox:
        ctrlelems = [(wtc, elemindex[wtc.pos]) for wtc in wtcontrols]
        controls = [CheckboxListControl(name, ctrlelems, browser)]

    else:
        controls = []
        for wtc in wtcontrols:
            controls.append(simpleControlFactory(
                wtc, wtc.form, elemindex, browser))

    return controls


def simpleControlFactory(wtcontrol, form, elemindex, browser):
    if isinstance(wtcontrol, webtest.forms.Radio):
        elems = [e for e in elemindex
                 if e.attrs.get('name') == wtcontrol.name]
        return RadioListControl(wtcontrol, form, elems, browser)

    elem = elemindex[wtcontrol.pos]
    if isinstance(wtcontrol, (webtest.forms.Select,
                              webtest.forms.MultipleSelect)):
        return ListControl(wtcontrol, form, elem, browser)

    elif isinstance(wtcontrol, webtest.forms.Submit):
        if wtcontrol.attrs.get('type', 'submit') == 'image':
            return ImageControl(wtcontrol, form, elem, browser)
        else:
            return SubmitControl(wtcontrol, form, elem, browser)
    else:
        return Control(wtcontrol, form, elem, browser)


@implementer(interfaces.ILink)
class Link(SetattrErrorsMixin):

    def __init__(self, link, browser, baseurl=""):
        self._link = link
        self.browser = browser
        self._baseurl = baseurl
        self._browser_counter = self.browser._counter
        self._enable_setattr_errors = True

    def click(self):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        self.browser.open(self.url, referrer=self.browser.url)

    @property
    def url(self):
        relurl = self._link['href']
        return self.browser._absoluteUrl(relurl)

    @property
    def text(self):
        txt = normalizeWhitespace(self._link.text)
        return self.browser.toStr(txt)

    @property
    def tag(self):
        return str(self._link.name)

    @property
    def attrs(self):
        toStr = self.browser.toStr
        return {toStr(k): toStr(v) for k, v in self._link.attrs.items()}

    def __repr__(self):
        return "<{} text='{}' url='{}'>".format(
            self.__class__.__name__, normalizeWhitespace(self.text), self.url)


def controlFormTupleRepr(wtcontrol):
    return wtcontrol.mechRepr()


@implementer(interfaces.IControl)
class Control(SetattrErrorsMixin):

    _enable_setattr_errors = False

    def __init__(self, control, form, elem, browser):
        self._control = control
        self._form = form
        self._elem = elem
        self.browser = browser
        self._browser_counter = self.browser._counter

        # disable addition of further attributes
        self._enable_setattr_errors = True

    @property
    def disabled(self):
        return 'disabled' in self._control.attrs

    @property
    def readonly(self):
        return 'readonly' in self._control.attrs

    @property
    def type(self):
        typeattr = self._control.attrs.get('type', None)
        if typeattr is None:
            # try to figure out type by tag
            if self._control.tag == 'textarea':
                return 'textarea'
            else:
                # By default, inputs are of 'text' type
                return 'text'
        return self.browser.toStr(typeattr)

    @property
    def name(self):
        if self._control.name is None:
            return None
        return self.browser.toStr(self._control.name)

    @property
    def multiple(self):
        return 'multiple' in self._control.attrs

    @property
    def value(self):
        if self.type == 'file':
            if not self._control.value:
                return None

        if self.type == 'image':
            if not self._control.value:
                return ''

        if isinstance(self._control, webtest.forms.Submit):
            return self.browser.toStr(self._control.value_if_submitted())

        val = self._control.value
        if val is None:
            return None

        return self.browser.toStr(val)

    @value.setter
    def value(self, value):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        if self.readonly:
            raise AttributeError("Trying to set value of readonly control")
        if self.type == 'file':
            self.add_file(value, content_type=None, filename=None)
        else:
            self._control.value = value

    def add_file(self, file, content_type, filename):
        if self.type != 'file':
            raise TypeError("Can't call add_file on %s controls"
                            % self.type)

        if hasattr(file, 'read'):
            contents = file.read()
        else:
            contents = file

        self._form[self.name] = webtest.forms.Upload(filename or '', contents,
                                                     content_type)

    def clear(self):
        if self._browser_counter != self.browser._counter:
            raise zope.testbrowser.interfaces.ExpiredError
        self.value = None

    def __repr__(self):
        return "<{} name='{}' type='{}'>".format(
            self.__class__.__name__, self.name, self.type)

    @Lazy
    def labels(self):
        return [self.browser.toStr(label)
                for label in getControlLabels(self._elem, self._form.html)]

    @property
    def controls(self):
        return []

    def mechRepr(self):
        # emulate mechanize control representation
        toStr = self.browser.toStr
        ctrl = self._control
        if isinstance(ctrl, (webtest.forms.Text, webtest.forms.Email)):
            tp = ctrl.attrs.get('type')
            infos = []
            if 'readonly' in ctrl.attrs or tp == 'hidden':
                infos.append('readonly')
            if 'disabled' in ctrl.attrs:
                infos.append('disabled')

            classnames = {'password': "PasswordControl",
                          'hidden': "HiddenControl",
                          'email': "EMailControl",
                          }
            clname = classnames.get(tp, "TextControl")
            return "<{}({}={}){}>".format(
                clname, toStr(ctrl.name), toStr(ctrl.value),
                ' (%s)' % (', '.join(infos)) if infos else '')

        if isinstance(ctrl, (webtest.forms.File, webtest.forms.Field)):
            return repr(ctrl) + "<-- unknown"
        raise NotImplementedError(str((self, ctrl)))


@implementer(interfaces.ISubmitControl)
class SubmitControl(Control):

    def click(self):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        self.browser._clickSubmit(self._form, self._control)

    @Lazy
    def labels(self):
        labels = super().labels
        labels.append(self._control.value_if_submitted())
        if self._elem.text:
            labels.append(normalizeWhitespace(self._elem.text))
        return [label for label in labels if label]

    def mechRepr(self):
        name = self.name if self.name is not None else "<None>"
        value = self.value if self.value is not None else "<None>"
        extra = ' (disabled)' if self.disabled else ''
        # Mechanize explicitly told us submit controls were readonly, as
        # if they could be any other way.... *sigh*  Let's take this
        # opportunity and strip that off.
        return "<SubmitControl({}={}){}>".format(name, value, extra)


@implementer(interfaces.IListControl)
class ListControl(Control):

    def __init__(self, control, form, elem, browser):
        super().__init__(control, form, elem, browser)
        # HACK: set default value of a list control and then forget about
        # initial default values. Otherwise webtest will not allow to set None
        # as a value of select and radio controls.
        v = control.value
        if v:
            control.value = v
            # Uncheck all the options   Carefully: WebTest used to have
            # 2-tuples here before commit 1031d82e, and 3-tuples since then.
            control.options = [option[:1] + (False,) + option[2:]
                               for option in control.options]

    @property
    def type(self):
        return 'select'

    @property
    def value(self):
        val = self._control.value
        if val is None:
            return []

        if self.multiple and isinstance(val, (list, tuple)):
            return [self.browser.toStr(v) for v in val]
        else:
            return [self.browser.toStr(val)]

    @value.setter
    def value(self, value):
        if not value:
            self._set_falsy_value(value)
        else:
            if not self.multiple and isinstance(value, (list, tuple)):
                value = value[0]
            self._control.value = value

    @property
    def _selectedIndex(self):
        return self._control.selectedIndex

    @_selectedIndex.setter
    def _selectedIndex(self, index):
        self._control.force_value(webtest.forms.NoValue)
        self._control.selectedIndex = index

    def _set_falsy_value(self, value):
        self._control.force_value(value)

    @property
    def displayValue(self):
        """See zope.testbrowser.interfaces.IListControl"""
        # not implemented for anything other than select;
        cvalue = self._control.value
        if cvalue is None:
            return []

        if not isinstance(cvalue, list):
            cvalue = [cvalue]

        alltitles = []
        for key, titles in self._getOptions():
            if key in cvalue:
                alltitles.append(titles[0])
        return alltitles

    @displayValue.setter
    def displayValue(self, value):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError

        if isinstance(value, str):
            value = [value]
        if not self.multiple and len(value) > 1:
            raise ItemCountError(
                "single selection list, must set sequence of length 0 or 1")
        values = []
        found = set()
        for key, titles in self._getOptions():
            matches = {v for t in titles for v in value if v in t}
            if matches:
                values.append(key)
                found.update(matches)
        for v in value:
            if v not in found:
                raise ItemNotFoundError(v)
        self.value = values

    @property
    def displayOptions(self):
        """See zope.testbrowser.interfaces.IListControl"""
        return [titles[0] for key, titles in self._getOptions()]

    @property
    def options(self):
        """See zope.testbrowser.interfaces.IListControl"""
        return [key for key, title in self._getOptions()]

    def getControl(self, label=None, value=None, index=None):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError

        return getControl(self.controls, label, value, index)

    @property
    def controls(self):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        ctrls = []
        for idx, elem in enumerate(self._elem.select('option')):
            ctrls.append(ItemControl(self, elem, self._form, self.browser,
                                     idx))

        return ctrls

    def _getOptions(self):
        return [(c.optionValue, c.labels) for c in self.controls]

    def mechRepr(self):
        # TODO: figure out what is replacement for "[*, ambiguous])"
        return "<SelectControl(%s=[*, ambiguous])>" % self.name


class RadioListControl(ListControl):

    _elems = None

    def __init__(self, control, form, elems, browser):
        super().__init__(
            control, form, elems[0], browser)
        self._elems = elems

    @property
    def type(self):
        return 'radio'

    def __repr__(self):
        # Return backwards compatible representation
        return "<ListControl name='%s' type='radio'>" % self.name

    @property
    def controls(self):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        for idx, opt in enumerate(self._elems):
            yield RadioItemControl(self, opt, self._form, self.browser, idx)

    @Lazy
    def labels(self):
        # Parent radio button control has no labels. Children are labeled.
        return []

    def _set_falsy_value(self, value):
        # HACK: Force unsetting selected value, by avoiding validity check.
        # Note, that force_value will not work for webtest.forms.Radio
        # controls.
        self._control.selectedIndex = None


@implementer(interfaces.IListControl)
class CheckboxListControl(SetattrErrorsMixin):
    def __init__(self, name, ctrlelems, browser):
        self.name = name
        self.browser = browser
        self._browser_counter = self.browser._counter
        self._ctrlelems = ctrlelems
        self._enable_setattr_errors = True

    @property
    def options(self):
        opts = [self._trValue(c.optionValue) for c in self.controls]
        return opts

    @property
    def displayOptions(self):
        return [c.labels[0] for c in self.controls]

    @property
    def value(self):
        ctrls = self.controls
        val = [self._trValue(c.optionValue) for c in ctrls if c.selected]

        if len(self._ctrlelems) == 1 and val == [True]:
            return True
        return val

    @value.setter
    def value(self, value):
        ctrls = self.controls
        if isinstance(value, (list, tuple)):
            for c in ctrls:
                c.selected = c.optionValue in value
        else:
            ctrls[0].selected = value

    @property
    def displayValue(self):
        return [c.labels[0] for c in self.controls if c.selected]

    @displayValue.setter
    def displayValue(self, value):
        found = set()
        for c in self.controls:
            matches = {v for v in value if v in c.labels}
            c.selected = bool(matches)
            found.update(matches)
        for v in value:
            if v not in found:
                raise ItemNotFoundError(v)

    @property
    def multiple(self):
        return True

    @property
    def disabled(self):
        return all('disabled' in e.attrs for c, e in self._ctrlelems)

    @property
    def type(self):
        return 'checkbox'

    def getControl(self, label=None, value=None, index=None):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError

        return getControl(self.controls, label, value, index)

    @property
    def controls(self):
        return [CheckboxItemControl(self, c, e, c.form, self.browser, i)
                for i, (c, e) in enumerate(self._ctrlelems)]

    def clear(self):
        if self._browser_counter != self.browser._counter:
            raise zope.testbrowser.interfaces.ExpiredError
        self.value = []

    def mechRepr(self):
        return "<SelectControl(%s=[*, ambiguous])>" % self.browser.toStr(
            self.name)

    @Lazy
    def labels(self):
        return []

    def __repr__(self):
        # Return backwards compatible representation
        return "<ListControl name='%s' type='checkbox'>" % self.name

    def _trValue(self, chbval):
        return True if chbval == 'on' else chbval


@implementer(interfaces.IImageSubmitControl)
class ImageControl(Control):

    def click(self, coord=(1, 1)):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        self.browser._clickSubmit(self._form, self._control, coord)

    def mechRepr(self):
        return "ImageControl???"  # TODO


@implementer(interfaces.IItemControl)
class ItemControl(SetattrErrorsMixin):

    def __init__(self, parent, elem, form, browser, index):
        self._parent = parent
        self._elem = elem
        self._index = index
        self._form = form
        self.browser = browser
        self._browser_counter = self.browser._counter
        self._enable_setattr_errors = True

    @property
    def control(self):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        return self._parent

    @property
    def _value(self):
        return self._elem.attrs.get('value', self._elem.text)

    @property
    def disabled(self):
        return 'disabled' in self._elem.attrs

    @property
    def selected(self):
        """See zope.testbrowser.interfaces.IControl"""
        if self._parent.multiple:
            return self._value in self._parent.value
        else:
            return self._parent._selectedIndex == self._index

    @selected.setter
    def selected(self, value):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        if self._parent.multiple:
            values = list(self._parent.value)
            if value:
                values.append(self._value)
            else:
                values = [v for v in values if v != self._value]
            self._parent.value = values
        else:
            if value:
                self._parent._selectedIndex = self._index
            else:
                self._parent.value = None

    @property
    def optionValue(self):
        return self.browser.toStr(self._value)

    @property
    def value(self):
        # internal alias for convenience implementing getControl()
        return self.optionValue

    def click(self):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        self.selected = not self.selected

    def __repr__(self):
        return (
            "<ItemControl name='%s' type='select' optionValue=%r selected=%r>"
        ) % (self._parent.name, self.optionValue, self.selected)

    @Lazy
    def labels(self):
        labels = [self._elem.attrs.get('label'), self._elem.text]
        return [self.browser.toStr(normalizeWhitespace(lbl))
                for lbl in labels if lbl]

    def mechRepr(self):
        toStr = self.browser.toStr
        contents = toStr(normalizeWhitespace(self._elem.text))
        id = toStr(self._elem.attrs.get('id'))
        label = toStr(self._elem.attrs.get('label', contents))
        value = toStr(self._value)
        name = toStr(self._elem.attrs.get('name', value))  # XXX wha????
        return (
            "<Item name='%s' id=%s contents='%s' value='%s' label='%s'>"
        ) % (name, id, contents, value, label)


class RadioItemControl(ItemControl):
    @property
    def optionValue(self):
        return self.browser.toStr(self._elem.attrs.get('value'))

    @Lazy
    def labels(self):
        return [self.browser.toStr(label)
                for label in getControlLabels(self._elem, self._form.html)]

    def __repr__(self):
        return (
            "<ItemControl name='%s' type='radio' optionValue=%r selected=%r>"
        ) % (self._parent.name, self.optionValue, self.selected)

    def click(self):
        # Radio buttons cannot be unselected by clicking on them, see
        # https://github.com/zopefoundation/zope.testbrowser/issues/68
        if not self.selected:
            super().click()

    def mechRepr(self):
        toStr = self.browser.toStr
        id = toStr(self._elem.attrs.get('id'))
        value = toStr(self._elem.attrs.get('value'))
        name = toStr(self._elem.attrs.get('name'))

        props = []
        if self._elem.parent.name == 'label':
            props.append((
                '__label', {'__text': toStr(self._elem.parent.text)}))
        if self.selected:
            props.append(('checked', 'checked'))
        props.append(('type', 'radio'))
        props.append(('name', name))
        props.append(('value', value))
        props.append(('id', id))

        propstr = ' '.join('{}={!r}'.format(pk, pv) for pk, pv in props)
        return "<Item name='{}' id='{}' {}>".format(value, id, propstr)


class CheckboxItemControl(ItemControl):
    _control = None

    def __init__(self, parent, wtcontrol, elem, form, browser, index):
        super().__init__(parent, elem, form, browser,
                         index)
        self._control = wtcontrol

    @property
    def selected(self):
        """See zope.testbrowser.interfaces.IControl"""
        return self._control.checked

    @selected.setter
    def selected(self, value):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        self._control.checked = value

    @property
    def optionValue(self):
        return self.browser.toStr(self._control._value or 'on')

    @Lazy
    def labels(self):
        return [self.browser.toStr(label)
                for label in getControlLabels(self._elem, self._form.html)]

    def __repr__(self):
        return (
            "<ItemControl name='%s' type='checkbox' "
            "optionValue=%r selected=%r>"
        ) % (self._control.name, self.optionValue, self.selected)

    def mechRepr(self):
        id = self.browser.toStr(self._elem.attrs.get('id'))
        value = self.browser.toStr(self._elem.attrs.get('value'))
        name = self.browser.toStr(self._elem.attrs.get('name'))

        props = []
        if self._elem.parent.name == 'label':
            props.append(('__label', {'__text': self.browser.toStr(
                self._elem.parent.text)}))
        if self.selected:
            props.append(('checked', 'checked'))
        props.append(('name', name))
        props.append(('type', 'checkbox'))
        props.append(('id', id))
        props.append(('value', value))

        propstr = ' '.join('{}={!r}'.format(pk, pv) for pk, pv in props)
        return "<Item name='{}' id='{}' {}>".format(value, id, propstr)


@implementer(interfaces.IForm)
class Form(SetattrErrorsMixin):
    """HTML Form"""

    def __init__(self, browser, form):
        """Initialize the Form

        browser - a Browser instance
        form - a webtest.Form instance
        """
        self.browser = browser
        self._form = form
        self._browser_counter = self.browser._counter
        self._enable_setattr_errors = True

    @property
    def action(self):
        return self.browser._absoluteUrl(self._form.action)

    @property
    def method(self):
        return str(self._form.method)

    @property
    def enctype(self):
        return str(self._form.enctype)

    @property
    def name(self):
        return str(self._form.html.form.get('name'))

    @property
    def id(self):
        """See zope.testbrowser.interfaces.IForm"""
        return str(self._form.id)

    def submit(self, label=None, name=None, index=None, coord=None):
        """See zope.testbrowser.interfaces.IForm"""
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError

        form = self._form
        if label is not None or name is not None:
            controls, msg, available = self.browser._getAllControls(
                label, name, [form])
            controls = [c for c in controls
                        if isinstance(c, (ImageControl, SubmitControl))]
            control = disambiguate(
                controls, msg, index, controlFormTupleRepr, available)
            self.browser._clickSubmit(form, control._control, coord)
        else:  # JavaScript sort of submit
            if index is not None or coord is not None:
                raise ValueError(
                    'May not use index or coord without a control')
            self.browser._clickSubmit(form)

    def getControl(self, label=None, name=None, index=None):
        """See zope.testbrowser.interfaces.IBrowser"""
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        intermediate, msg, available = self.browser._getAllControls(
            label, name, [self._form], include_subcontrols=True)
        return disambiguate(intermediate, msg, index,
                            controlFormTupleRepr, available)

    @property
    def controls(self):
        return list(self.browser._findAllControls(
            [self._form], include_subcontrols=True))


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
                msg = (
                    '%s\nIndex %d out of range, available choices are 0...%d'
                ) % (msg, index, len(intermediate) - 1)
                if choice_repr:
                    msg += ''.join(['\n  %d: %s' % (n, choice_repr(choice))
                                    for n, choice in enumerate(intermediate)])
    else:
        if available:
            msg += '\navailable items:' + ''.join([
                '\n  %s' % choice_repr(choice)
                for choice in available])
        elif available is not None:  # empty list
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


def getControl(controls, label=None, value=None, index=None):
    onlyOne([label, value], '"label" and "value"')

    if label is not None:
        options = [c for c in controls
                   if any(isMatching(control_label, label)
                          for control_label in c.labels)]
        msg = 'label %r' % label
    elif value is not None:
        options = [c for c in controls if isMatching(c.value, value)]
        msg = 'value %r' % value

    res = disambiguate(options, msg, index, controlFormTupleRepr,
                       available=controls)
    return res


def getControlLabels(celem, html):
    labels = []

    # In case celem is contained in label element, use its text as a label
    if celem.parent.name == 'label':
        labels.append(normalizeWhitespace(celem.parent.text))

    # find all labels, connected by 'for' attribute
    controlid = celem.attrs.get('id')
    if controlid:
        forlbls = html.select('label[for="%s"]' % controlid)
        labels.extend([normalizeWhitespace(label.text) for label in forlbls])

    return [label for label in labels if label is not None]


def normalizeWhitespace(string):
    return ' '.join(string.split())


def isMatching(string, expr):
    """Determine whether ``expr`` matches to ``string``

    ``expr`` can be None, plain text or regular expression.

      * If ``expr`` is ``None``, ``string`` is considered matching
      * If ``expr`` is plain text, its equality to ``string`` will be checked
      * If ``expr`` is regexp, regexp matching agains ``string`` will
        be performed
    """
    if expr is None:
        return True

    if isinstance(expr, RegexType):
        return expr.match(normalizeWhitespace(string))
    else:
        return normalizeWhitespace(expr) in normalizeWhitespace(string)


class Timer:
    start_time = 0
    end_time = 0

    def _getTime(self):
        return time.perf_counter()

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

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()


class History:
    """

    Though this will become public, the implied interface is not yet stable.

    """

    def __init__(self):
        self._history = []  # LIFO

    def add(self, response):
        self._history.append(response)

    def back(self, n, _response):
        response = _response
        while n > 0 or response is None:
            try:
                response = self._history.pop()
            except IndexError:
                raise BrowserStateError("already at start of history")
            n -= 1
        return response

    def clear(self):
        del self._history[:]


class AmbiguityError(ValueError):
    pass


class BrowserStateError(Exception):
    pass


class LinkNotFoundError(IndexError):
    pass


class ItemCountError(ValueError):
    pass


class ItemNotFoundError(ValueError):
    pass
