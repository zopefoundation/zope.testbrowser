"""HTML form handling for web clients.

ClientForm is a Python module for handling HTML forms on the client
side, useful for parsing HTML forms, filling them in and returning the
completed forms to the server.  It has developed from a port of Gisle
Aas' Perl module HTML::Form, from the libwww-perl library, but the
interface is not the same.

The most useful docstring is the one for HTMLForm.

RFC 1866: HTML 2.0
RFC 1867: Form-based File Upload in HTML
RFC 2388: Returning Values from Forms: multipart/form-data
HTML 3.2 Specification, W3C Recommendation 14 January 1997 (for ISINDEX)
HTML 4.01 Specification, W3C Recommendation 24 December 1999


Copyright 2002-2005 John J. Lee <jjl@pobox.com>
Copyright 1998-2000 Gisle Aas.

This code is free software; you can redistribute it and/or modify it
under the terms of the BSD License (see the file COPYING included with
the distribution).

"""

# XXX
# Add some functional tests
#  Especially single and multiple file upload on the internet.
#  Does file upload work when name is missing?  Sourceforge tracker form
#   doesn't like it.  Check standards, and test with Apache.  Test
#   binary upload with Apache.
# Unicode: see Wichert Akkerman's 2004-01-22 message to c.l.py.
# Controls can have name=None (eg. forms constructed partly with
#  JavaScript), but find_control can't be told to find a control
#  with that name, because None there means 'unspecified'.  Can still
#  get at by nr, but would be nice to be able to specify something
#  equivalent to name=None, too.
# Support for list item ids.  How to handle missing ids? (How do I deal
#  with duplicate OPTION labels ATM?  Can't remember...)
# Deal with character sets properly.  Not sure what the issues are here.
#  Do URL encodings need any attention?
#  I don't *think* any encoding of control names, filenames or data is
#   necessary -- HTML spec. doesn't require it, and Mozilla Firebird 0.6
#   doesn't seem to do it.
#  Add charset parameter to Content-type headers?  How to find value??
# I'm not going to fix this unless somebody tells me what real servers
#  that want this encoding actually expect: If enctype is
#  application/x-www-form-urlencoded and there's a FILE control present.
#  Strictly, it should be 'name=data' (see HTML 4.01 spec., section
#  17.13.2), but I send "name=" ATM.  What about multiple file upload??
# Get rid of MapBase, AList and MimeWriter.
# Should really use sgmllib, not htmllib.
# Factor out multiple-selection list code?  May not be easy.  Maybe like
#  this:

#         ListControl
#             ^
#             |       MultipleListControlMixin
#             |             ^
#        SelectControl     /
#             ^           /
#              \         /
#          MultiSelectControl


# Plan
# ----
# Maybe a 0.2.x, cleaned up a bit and with id support for list items?
# Not sure it's worth it...
#   action should probably be an absolute URI, like DOMForm.
#   Replace by_label with choice between value / id / label /
#    element contents (see discussion with Gisle about labels on
#    libwww-perl list).
#   ...what else?
# Work on DOMForm.
# XForms?  Don't know if there's a need here.


try: True
except NameError:
    True = 1
    False = 0

try: bool
except NameError:
    def bool(expr):
        if expr: return True
        else: return False

import sys, urllib, urllib2, types, string, mimetools, copy, urlparse, \
       htmlentitydefs, re
from urlparse import urljoin
from cStringIO import StringIO
try:
    from types import UnicodeType
except ImportError:
    UNICODE = False
else:
    UNICODE = True

try:
    import warnings
except ImportError:
    def deprecation(message):
        pass
else:
    def deprecation(message):
        warnings.warn(message, DeprecationWarning, stacklevel=2)

VERSION = "0.1.18"

CHUNK = 1024  # size of chunks fed to parser, in bytes

_compress_re = re.compile(r"\s+")
compressText = lambda text: _compress_re.sub(' ', text.strip())

# This version of urlencode is from my Python 1.5.2 back-port of the
# Python 2.1 CVS maintenance branch of urllib.  It will accept a sequence
# of pairs instead of a mapping -- the 2.0 version only accepts a mapping.
def urlencode(query,doseq=False,):
    """Encode a sequence of two-element tuples or dictionary into a URL query \
string.

    If any values in the query arg are sequences and doseq is true, each
    sequence element is converted to a separate parameter.

    If the query arg is a sequence of two-element tuples, the order of the
    parameters in the output will match the order of parameters in the
    input.
    """

    if hasattr(query,"items"):
        # mapping objects
        query = query.items()
    else:
        # it's a bother at times that strings and string-like objects are
        # sequences...
        try:
            # non-sequence items should not work with len()
            x = len(query)
            # non-empty strings will fail this
            if len(query) and type(query[0]) != types.TupleType:
                raise TypeError()
            # zero-length sequences of all types will get here and succeed,
            # but that's a minor nit - since the original implementation
            # allowed empty dicts that type of behavior probably should be
            # preserved for consistency
        except TypeError:
            ty,va,tb = sys.exc_info()
            raise TypeError("not a valid non-string sequence or mapping "
                            "object", tb)

    l = []
    if not doseq:
        # preserve old behavior
        for k, v in query:
            k = urllib.quote_plus(str(k))
            v = urllib.quote_plus(str(v))
            l.append(k + '=' + v)
    else:
        for k, v in query:
            k = urllib.quote_plus(str(k))
            if type(v) == types.StringType:
                v = urllib.quote_plus(v)
                l.append(k + '=' + v)
            elif UNICODE and type(v) == types.UnicodeType:
                # is there a reasonable way to convert to ASCII?
                # encode generates a string, but "replace" or "ignore"
                # lose information and "strict" can raise UnicodeError
                v = urllib.quote_plus(v.encode("ASCII","replace"))
                l.append(k + '=' + v)
            else:
                try:
                    # is this a sufficient test for sequence-ness?
                    x = len(v)
                except TypeError:
                    # not a sequence
                    v = urllib.quote_plus(str(v))
                    l.append(k + '=' + v)
                else:
                    # loop over the sequence
                    for elt in v:
                        l.append(k + '=' + urllib.quote_plus(str(elt)))
    return string.join(l, '&')

# Grabbed from 2.4 xml.sax.saxutils, and modified
def __dict_replace(s, d):
    """Replace substrings of a string using a dictionary."""
    for key, value in d.items():
        s = string.replace(s, key, value)
    return s
def unescape(data, entities):
    if data is None:
        return None
    do_amp = False
    if entities:
        # must do ampersand last
        ents = entities.copy()
        try:
            del ents["&amp;"]
        except KeyError:
            pass
        else:
            do_amp = True
        data = __dict_replace(data, ents)
    if do_amp:
        data = string.replace(data, "&amp;", "&")
    return data

def startswith(string, initial):
    if len(initial) > len(string): return False
    return string[:len(initial)] == initial

def issequence(x):
    try:
        x[0]
    except (TypeError, KeyError):
        return False
    except IndexError:
        pass
    return True

def isstringlike(x):
    try: x+""
    except: return False
    else: return True


# XXX don't really want to drag this along (MapBase, AList, MimeWriter,
#  _choose_boundary)

# This is essentially the same as UserDict.DictMixin.  I wrote this before
# that, and DictMixin isn't available in 1.5.2 anyway.
class MapBase:
    """Mapping designed to be easily derived from.

    Subclass it and override __init__, __setitem__, __getitem__, __delitem__
    and keys.  Nothing else should need to be overridden, unlike UserDict.
    This significantly simplifies dictionary-like classes.

    Also different from UserDict in that it has a redonly flag, and can be
    updated (and initialised) with a sequence of pairs (key, value).

    """
    def __init__(self, init=None):
        self._data = {}
        self.readonly = False
        if init is not None: self.update(init)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, item):
        if not self.readonly:
            self._data[key] = item
        else:
            raise TypeError("object doesn't support item assignment")

    def __delitem__(self, key):
        if not self.readonly:
            del self._data[key]
        else:
            raise TypeError("object doesn't support item deletion")

    def keys(self):
        return self._data.keys()

    # now the internal workings, there should be no need to override these:

    def clear(self):
        for k in self.keys():
            del self[k]

    def __repr__(self):
        rep = []
        for k, v in self.items():
            rep.append("%s: %s" % (repr(k), repr(v)))
        return self.__class__.__name__+"{"+(string.join(rep, ", "))+"}"

    def copy(self):
        return copy.copy(self)

    def __cmp__(self, dict):
        # note: return value is *not* boolean
        for k, v in self.items():
            if not (dict.has_key(k) and dict[k] == v):
                return 1  # different
        return 0  # the same

    def __len__(self):
        return len(self.keys())

    def values(self):
        r = []
        for k in self.keys():
            r.append(self[k])
        return r

    def items(self):
        keys = self.keys()
        vals = self.values()
        r = []
        for i in len(self):
            r.append((keys[i], vals[i]))
        return r

    def has_key(self, key):
        return key in self.keys()

    def update(self, map):
        if issequence(map) and not isstringlike(map):
            items = map
        else:
            items = map.items()
        for tup in items:
            if not isinstance(tup, TupleType):
                raise TypeError(
                    "MapBase.update requires a map or a sequence of pairs")
            k, v = tup
            self[k] = v

    def get(self, key, failobj=None):
        if key in self.keys():
            return self[key]
        else:
            return failobj

    def setdefault(self, key, failobj=None):
        if not self.has_key(key):
            self[key] = failobj
        return self[key]


class AList(MapBase):
    """Read-only ordered mapping."""
    def __init__(self, seq=[]):
        self.readonly = True
        self._inverted = False
        self._data = list(seq[:])
        self._keys = []
        self._values = []
        for key, value in seq:
            self._keys.append(key)
            self._values.append(value)

    def set_inverted(self, inverted):
        if (inverted and not self._inverted) or (
            not inverted and self._inverted):
            self._keys, self._values = self._values, self._keys
        if inverted: self._inverted = True
        else: self._inverted = False

    def __getitem__(self, key):
        try:
            i = self._keys.index(key)
        except ValueError:
            raise KeyError(key)
        return self._values[i]

    def __delitem__(self, key):
        try:
            i = self._keys.index[key]
        except ValueError:
            raise KeyError(key)
        del self._values[i]

    def keys(self): return list(self._keys[:])
    def values(self): return list(self._values[:])
    def items(self):
        data = self._data[:]
        if not self._inverted:
            return data
        else:
            newdata = []
            for k, v in data:
                newdata.append((v, k))
            return newdata

# --------------------------------------------------------------------
# grabbed from Python standard library mimetools module and tweaked to
# avoid socket.gaierror
try:
    import thread
    _thread = thread; del thread
except ImportError:
    import dummy_thread
    _thread = dummy_thread; del dummy_thread
_counter_lock = _thread.allocate_lock()
del _thread

_counter = 0
def _get_next_counter():
    global _counter
    _counter_lock.acquire()
    _counter = _counter + 1
    result = _counter
    _counter_lock.release()
    return result

_prefix = None

def _choose_boundary():
    """Return a string usable as a multipart boundary.

    The string chosen is unique within a single program run, and
    incorporates the user id (if available), process id (if available),
    and current time.  So it's very unlikely the returned string appears
    in message text, but there's no guarantee.

    The boundary contains dots so you have to quote it in the header."""

    global _prefix
    import time
    import os
    import socket
    if _prefix is None:
        try:
            socket.gaierror
        except AttributeError:
            exc = socket.error
        else:
            exc = socket.gaierror

        try:
            hostid = socket.gethostbyname(socket.gethostname())
        except exc:
            hostid = 'localhost'
        try:
            uid = repr(os.getuid())
        except AttributeError:
            uid = '1'
        try:
            pid = repr(os.getpid())
        except AttributeError:
            pid = '1'
        _prefix = hostid + '.' + uid + '.' + pid
    return "%s.%.3f.%d" % (_prefix, time.time(), _get_next_counter())

# end of code from mimetools module
# --------------------------------------------------------------------

def choose_boundary():
    b = _choose_boundary()
    b = string.replace(b, ".", "")
    return b

# This cut-n-pasted MimeWriter from standard library is here so can add
# to HTTP headers rather than message body when appropriate.  It also uses
# \r\n in place of \n.  This is nasty.
class MimeWriter:

    """Generic MIME writer.

    Methods:

    __init__()
    addheader()
    flushheaders()
    startbody()
    startmultipartbody()
    nextpart()
    lastpart()

    A MIME writer is much more primitive than a MIME parser.  It
    doesn't seek around on the output file, and it doesn't use large
    amounts of buffer space, so you have to write the parts in the
    order they should occur on the output file.  It does buffer the
    headers you add, allowing you to rearrange their order.

    General usage is:

    f = <open the output file>
    w = MimeWriter(f)
    ...call w.addheader(key, value) 0 or more times...

    followed by either:

    f = w.startbody(content_type)
    ...call f.write(data) for body data...

    or:

    w.startmultipartbody(subtype)
    for each part:
        subwriter = w.nextpart()
        ...use the subwriter's methods to create the subpart...
    w.lastpart()

    The subwriter is another MimeWriter instance, and should be
    treated in the same way as the toplevel MimeWriter.  This way,
    writing recursive body parts is easy.

    Warning: don't forget to call lastpart()!

    XXX There should be more state so calls made in the wrong order
    are detected.

    Some special cases:

    - startbody() just returns the file passed to the constructor;
      but don't use this knowledge, as it may be changed.

    - startmultipartbody() actually returns a file as well;
      this can be used to write the initial 'if you can read this your
      mailer is not MIME-aware' message.

    - If you call flushheaders(), the headers accumulated so far are
      written out (and forgotten); this is useful if you don't need a
      body part at all, e.g. for a subpart of type message/rfc822
      that's (mis)used to store some header-like information.

    - Passing a keyword argument 'prefix=<flag>' to addheader(),
      start*body() affects where the header is inserted; 0 means
      append at the end, 1 means insert at the start; default is
      append for addheader(), but insert for start*body(), which use
      it to determine where the Content-type header goes.

    """

    def __init__(self, fp, http_hdrs=None):
        self._http_hdrs = http_hdrs
        self._fp = fp
        self._headers = []
        self._boundary = []
        self._first_part = True

    def addheader(self, key, value, prefix=0,
                  add_to_http_hdrs=0):
        """
        prefix is ignored if add_to_http_hdrs is true.
        """
        lines = string.split(value, "\r\n")
        while lines and not lines[-1]: del lines[-1]
        while lines and not lines[0]: del lines[0]
        if add_to_http_hdrs:
            value = string.join(lines, "")
            self._http_hdrs.append((key, value))
        else:
            for i in range(1, len(lines)):
                lines[i] = "    " + string.strip(lines[i])
            value = string.join(lines, "\r\n") + "\r\n"
            line = key + ": " + value
            if prefix:
                self._headers.insert(0, line)
            else:
                self._headers.append(line)

    def flushheaders(self):
        self._fp.writelines(self._headers)
        self._headers = []

    def startbody(self, ctype=None, plist=[], prefix=1,
                  add_to_http_hdrs=0, content_type=1):
        """
        prefix is ignored if add_to_http_hdrs is true.
        """
        if content_type and ctype:
            for name, value in plist:
                ctype = ctype + ';\r\n %s=%s' % (name, value)
            self.addheader("Content-type", ctype, prefix=prefix,
                           add_to_http_hdrs=add_to_http_hdrs)
        self.flushheaders()
        if not add_to_http_hdrs: self._fp.write("\r\n")
        self._first_part = True
        return self._fp

    def startmultipartbody(self, subtype, boundary=None, plist=[], prefix=1,
                           add_to_http_hdrs=0, content_type=1):
        boundary = boundary or choose_boundary()
        self._boundary.append(boundary)
        return self.startbody("multipart/" + subtype,
                              [("boundary", boundary)] + plist,
                              prefix=prefix,
                              add_to_http_hdrs=add_to_http_hdrs,
                              content_type=content_type)

    def nextpart(self):
        boundary = self._boundary[-1]
        if self._first_part:
            self._first_part = False
        else:
            self._fp.write("\r\n")
        self._fp.write("--" + boundary + "\r\n")
        return self.__class__(self._fp)

    def lastpart(self):
        if self._first_part:
            self.nextpart()
        boundary = self._boundary.pop()
        self._fp.write("\r\n--" + boundary + "--\r\n")


class ControlNotFoundError(ValueError): pass
class ItemNotFoundError(ValueError): pass
class ItemCountError(ValueError): pass

class ParseError(Exception): pass


class _AbstractFormParser:
    """forms attribute contains HTMLForm instances on completion."""
    # thanks to Moshe Zadka for an example of sgmllib/htmllib usage
    def __init__(self, entitydefs=None):
        if entitydefs is None:
            entitydefs = get_entitydefs()
        self._entitydefs = entitydefs

        self.base = None
        self.forms = []
        self.labels = []
        self._current_label = None
        self._current_form = None
        self._select = None
        self._optgroup = None
        self._option = None
        self._textarea = None

    def do_base(self, attrs):
        for key, value in attrs:
            if key == "href":
                self.base = value

    def end_body(self):
        if self._current_label is not None:
            self.end_label()
        if self._current_form is not None:
            self.end_form()

    def start_form(self, attrs):
        if self._current_form is not None:
            raise ParseError("nested FORMs")
        name = None
        action = None
        enctype = "application/x-www-form-urlencoded"
        method = "GET"
        d = {}
        for key, value in attrs:
            if key == "name":
                name = value
            elif key == "action":
                action = value
            elif key == "method":
                method = string.upper(value)
            elif key == "enctype":
                enctype = string.lower(value)
            d[key] = value
        controls = []
        self._current_form = (name, action, method, enctype), d, controls

    def end_form(self):
        if self._current_label is not None:
            self.end_label()
        if self._current_form is None:
            raise ParseError("end of FORM before start")
        self.forms.append(self._current_form)
        self._current_form = None

    def start_select(self, attrs):
        if self._current_form is None:
            raise ParseError("start of SELECT before start of FORM")
        if self._select is not None:
            raise ParseError("nested SELECTs")
        if self._textarea is not None:
            raise ParseError("SELECT inside TEXTAREA")
        d = {}
        d.update(attrs)

        self._select = d
        self._add_label(d)

        self._append_select_control({"__select": d})

    def end_select(self):
        if self._current_form is None:
            raise ParseError("end of SELECT before start of FORM")
        if self._select is None:
            raise ParseError("end of SELECT before start")

        if self._option is not None:
            self._end_option()

        self._select = None

    def start_optgroup(self, attrs):
        if self._select is None:
            raise ParseError("OPTGROUP outside of SELECT")
        d = {}
        d.update(attrs)

        self._optgroup = d

    def end_optgroup(self):
        if self._optgroup is None:
            raise ParseError("end of OPTGROUP before start")
        self._optgroup = None

    def _start_option(self, attrs):
        if self._select is None:
            raise ParseError("OPTION outside of SELECT")
        if self._option is not None:
            self._end_option()

        self._option = {}
        self._option.update(attrs)
        if (self._optgroup and self._optgroup.has_key("disabled") and
            not self._option.has_key("disabled")):
            self._option["disabled"] = None

    def _end_option(self):
        if self._option is None:
            raise ParseError("end of OPTION before start")

        contents = string.strip(self._option.get("contents", ""))
        self._option["contents"] = contents
        if not self._option.has_key("value"):
            self._option["value"] = contents
        if not self._option.has_key("label"):
            self._option["label"] = contents
        # stuff dict of SELECT HTML attrs into a special private key
        #  (gets deleted again later)
        self._option["__select"] = self._select
        self._append_select_control(self._option)
        self._option = None

    def _append_select_control(self, attrs):
        controls = self._current_form[2]
        name = self._select.get("name")
        controls.append(("select", name, attrs))

    def start_textarea(self, attrs):
        if self._current_form is None:
            raise ParseError("start of TEXTAREA before start of FORM")
        if self._textarea is not None:
            raise ParseError("nested TEXTAREAs")
        if self._select is not None:
            raise ParseError("TEXTAREA inside SELECT")
        d = {}
        d.update(attrs)
        self._add_label(d)

        self._textarea = d

    def end_textarea(self):
        if self._current_form is None:
            raise ParseError("end of TEXTAREA before start of FORM")
        if self._textarea is None:
            raise ParseError("end of TEXTAREA before start")
        controls = self._current_form[2]
        name = self._textarea.get("name")
        controls.append(("textarea", name, self._textarea))
        self._textarea = None

    def start_label(self, attrs):
        if self._current_label:
            self.end_label()
        attrs = dict(attrs)
        taken = bool(attrs.get('for')) # empty id is invalid
        attrs['__text'] = ''
        attrs['__taken'] = taken
        if taken:
            self.labels.append(attrs)
        self._current_label = attrs

    def end_label(self):
        label = self._current_label
        if label is None:
            # something is ugly in the HTML, but we're ignoring it
            return
        self._current_label = None
        label['__text'] = label['__text']
        del label['__taken'] # if it is staying around, it is True in all cases

    def _add_label(self, d):
        if self._current_label is not None:
            if self._current_label['__taken']:
                self.end_label() # be fuzzy
            else:
                self._current_label['__taken'] = True
                d['__label'] = self._current_label

    def handle_data(self, data):
        if self._option is not None:
            # self._option is a dictionary of the OPTION element's HTML
            # attributes, but it has two special keys, one of which is the
            # special "contents" key contains text between OPTION tags (the
            # other is the "__select" key: see the end_option method)
            map = self._option
            key = "contents"
        elif self._textarea is not None:
            map = self._textarea
            key = "value"
        elif self._current_label is not None: # not if within option or
            # textarea
            map = self._current_label
            key = "__text"
        else:
            return

        if not map.has_key(key):
            map[key] = data
        else:
            map[key] = map[key] + data

    def do_button(self, attrs):
        if self._current_form is None:
            raise ParseError("start of BUTTON before start of FORM")
        d = {}
        d["type"] = "submit"  # default
        d.update(attrs)
        controls = self._current_form[2]

        type = d["type"]
        name = d.get("name")
        # we don't want to lose information, so use a type string that
        # doesn't clash with INPUT TYPE={SUBMIT,RESET,BUTTON}
        # eg. type for BUTTON/RESET is "resetbutton"
        #     (type for INPUT/RESET is "reset")
        type = type+"button"
        self._add_label(d)
        controls.append((type, name, d))

    def do_input(self, attrs):
        if self._current_form is None:
            raise ParseError("start of INPUT before start of FORM")
        d = {}
        d["type"] = "text"  # default
        d.update(attrs)
        controls = self._current_form[2]

        type = d["type"]
        name = d.get("name")
        self._add_label(d)
        controls.append((type, name, d))

    def do_isindex(self, attrs):
        if self._current_form is None:
            raise ParseError("start of ISINDEX before start of FORM")
        d = {}
        d.update(attrs)
        controls = self._current_form[2]

        self._add_label(d)
        # isindex doesn't have type or name HTML attributes
        controls.append(("isindex", None, d))

    def handle_entityref(self, name):
        table = self._entitydefs
        fullname = '&%s;' % name
        if table.has_key(fullname):
            self.handle_data(table[fullname])
        else:
            self.unknown_entityref(name)
            return

    def unescape_attr(self, name):
        return unescape(name, self._entitydefs)

    def unescape_attrs(self, attrs):
        escaped_attrs = {}
        for key, val in attrs.items():
            try:
                val.items
            except AttributeError:
                escaped_attrs[key] = self.unescape_attr(val)
            else:
                # eg. "__select" -- yuck!
                escaped_attrs[key] = self.unescape_attrs(val)
        return escaped_attrs

    def unknown_entityref(self, ref): self.handle_data('&%s;' % ref)
    def unknown_charref(self, ref): self.handle_data('&#%s;' % ref)


# HTMLParser.HTMLParser is recent, so live without it if it's not available
# (also, htmllib.HTMLParser is much more tolerant of bad HTML)
try:
    import HTMLParser
except ImportError:
    class XHTMLCompatibleFormParser:
        def __init__(self, entitydefs=None):
            raise ValueError("HTMLParser could not be imported")
else:
    class XHTMLCompatibleFormParser(_AbstractFormParser, HTMLParser.HTMLParser):
        """Good for XHTML, bad for tolerance of incorrect HTML."""
        # thanks to Michael Howitz for this!
        def __init__(self, entitydefs=None):
            HTMLParser.HTMLParser.__init__(self)
            _AbstractFormParser.__init__(self, entitydefs)

        def start_option(self, attrs):
            _AbstractFormParser._start_option(self, attrs)

        def end_option(self):
            _AbstractFormParser._end_option(self)

        def handle_starttag(self, tag, attrs):
            try:
                method = getattr(self, 'start_' + tag)
            except AttributeError:
                try:
                    method = getattr(self, 'do_' + tag)
                except AttributeError:
                    pass # unknown tag
                else:
                    method(attrs)
            else:
                method(attrs)

        def handle_endtag(self, tag):
            try:
                method = getattr(self, 'end_' + tag)
            except AttributeError:
                pass # unknown tag
            else:
                method()

        # taken from sgmllib, with changes
        def handle_charref(self, name):
            try:
                n = int(name)
            except ValueError:
                self.unknown_charref(name)
                return
            if not 0 <= n <= 255:
                self.unknown_charref(name)
                return
            self.handle_data(chr(n))

        def unescape(self, name):
            # Use the entitydefs passed into constructor, not
            # HTMLParser.HTMLParser's entitydefs.
            return self.unescape_attr(name)

        def unescape_attr_if_required(self, name):
            return name  # HTMLParser.HTMLParser already did it
        def unescape_attrs_if_required(self, attrs):
            return attrs  # ditto

import htmllib, formatter
class FormParser(_AbstractFormParser, htmllib.HTMLParser):
    """Good for tolerance of incorrect HTML, bad for XHTML."""
    def __init__(self, entitydefs=None):
        htmllib.HTMLParser.__init__(self, formatter.NullFormatter())
        _AbstractFormParser.__init__(self, entitydefs)

    def do_option(self, attrs):
        _AbstractFormParser._start_option(self, attrs)

    def unescape_attr_if_required(self, name):
        return self.unescape_attr(name)
    def unescape_attrs_if_required(self, attrs):
        return self.unescape_attrs(attrs)

#FormParser = XHTMLCompatibleFormParser  # testing hack

def get_entitydefs():
    entitydefs = {}
    for name, char in htmlentitydefs.entitydefs.items():
        entitydefs["&%s;" % name] = char
    return entitydefs

def ParseResponse(response, select_default=False,
                  ignore_errors=False,  # ignored!
                  form_parser_class=FormParser,
                  request_class=urllib2.Request,
                  entitydefs=None):
    """Parse HTTP response and return a list of HTMLForm instances.

    The return value of urllib2.urlopen can be conveniently passed to this
    function as the response parameter.

    ClientForm.ParseError is raised on parse errors.

    response: file-like object (supporting read() method) with a method
     geturl(), returning the URI of the HTTP response
    select_default: for multiple-selection SELECT controls and RADIO controls,
     pick the first item as the default if none are selected in the HTML
    form_parser_class: class to instantiate and use to pass
    request_class: class to return from .click() method (default is
     urllib2.Request)
    entitydefs: mapping like {'&amp;': '&', ...} containing HTML entity
     definitions (a sensible default is used)

    Pass a true value for select_default if you want the behaviour specified by
    RFC 1866 (the HTML 2.0 standard), which is to select the first item in a
    RADIO or multiple-selection SELECT control if none were selected in the
    HTML.  Most browsers (including Microsoft Internet Explorer (IE) and
    Netscape Navigator) instead leave all items unselected in these cases.  The
    W3C HTML 4.0 standard leaves this behaviour undefined in the case of
    multiple-selection SELECT controls, but insists that at least one RADIO
    button should be checked at all times, in contradiction to browser
    behaviour.

    There is a choice of parsers.  ClientForm.XHTMLCompatibleFormParser (uses
    HTMLParser.HTMLParser) works best for XHTML, ClientForm.FormParser (uses
    htmllib.HTMLParser) (the default) works best for ordinary grubby HTML.
    Note that HTMLParser is only available in Python 2.2 and later.  You can
    pass your own class in here as a hack to work around bad HTML, but at your
    own risk: there is no well-defined interface.

    """
    return ParseFile(response, response.geturl(), select_default,
                     False,
                     form_parser_class,
                     request_class,
                     entitydefs)

def ParseFile(file, base_uri, select_default=False,
              ignore_errors=False,  # ignored!
              form_parser_class=FormParser,
              request_class=urllib2.Request,
              entitydefs=None):
    """Parse HTML and return a list of HTMLForm instances.

    ClientForm.ParseError is raised on parse errors.

    file: file-like object (supporting read() method) containing HTML with zero
     or more forms to be parsed
    base_uri: the URI of the document (note that the base URI used to submit
     the form will be that given in the BASE element if present, not that of
     the document)

    For the other arguments and further details, see ParseResponse.__doc__.

    """
    fp = form_parser_class(entitydefs)
    while 1:
        data = file.read(CHUNK)
        try:
            fp.feed(data)
        except ParseError, e:
            e.base_uri = base_uri
            raise
        if len(data) != CHUNK: break
    if fp.base is not None:
        # HTML BASE element takes precedence over document URI
        base_uri = fp.base
    labels = [] # Label(label) for label in fp.labels]
    id_to_labels = {}
    for l in fp.labels:
        label = Label(l)
        labels.append(label)
        for_id = l['for']
        coll = id_to_labels.get(for_id)
        if coll is None:
            id_to_labels[for_id] = [label]
        else:
            coll.append(label)
    forms = []
    for (name, action, method, enctype), attrs, controls in fp.forms:
        if action is None:
            action = base_uri
        else:
            action = urljoin(base_uri, action)
        action = fp.unescape_attr_if_required(action)
        name = fp.unescape_attr_if_required(name)
        attrs = fp.unescape_attrs_if_required(attrs)
        form = HTMLForm( # would be nice to make class (form builder) pluggable
            action, method, enctype, name, attrs, request_class,
            forms, labels, id_to_labels)
        for type, name, attrs in controls:
            attrs = fp.unescape_attrs_if_required(attrs)
            name = fp.unescape_attr_if_required(name)
            form.new_control(type, name, attrs, select_default=select_default)
        forms.append(form)
    for form in forms:
        form.fixup()
    return forms

class Label(object):
    def __init__(self, attrs):
        self.id = attrs.get('for')
        self.text = compressText(attrs.get('__text'))
        self.attrs = attrs

def _getLabel(attrs):
    label = attrs.get('__label')
    if label is not None:
        label = Label(label)
    return label

class Control:
    """An HTML form control.

    An HTMLForm contains a sequence of Controls.  HTMLForm delegates lots of
    things to Control objects, and most of Control's methods are, in effect,
    documented by the HTMLForm docstrings.

    The Controls in an HTMLForm can be got at via the HTMLForm.find_control
    method or the HTMLForm.controls attribute.

    Control instances are usually constructed using the ParseFile /
    ParseResponse functions, so you can probably ignore the rest of this
    paragraph.  A Control is only properly initialised after the fixup method
    has been called.  In fact, this is only strictly necessary for ListControl
    instances.  This is necessary because ListControls are built up from
    ListControls each containing only a single item, and their initial value(s)
    can only be known after the sequence is complete.

    The types and values that are acceptable for assignment to the value
    attribute are defined by subclasses.

    If the disabled attribute is true, this represents the state typically
    represented by browsers by `greying out' a control.  If the disabled
    attribute is true, the Control will raise AttributeError if an attempt is
    made to change its value.  In addition, the control will not be considered
    `successful' as defined by the W3C HTML 4 standard -- ie. it will
    contribute no data to the return value of the HTMLForm.click* methods.  To
    enable a control, set the disabled attribute to a false value.

    If the readonly attribute is true, the Control will raise AttributeError if
    an attempt is made to change its value.  To make a control writable, set
    the readonly attribute to a false value.

    All controls have the disabled and readonly attributes, not only those that
    may have the HTML attributes of the same names.

    On assignment to the value attribute, the following exceptions are raised:
    TypeError, AttributeError (if the value attribute should not be assigned
    to, because the control is disabled, for example) and ValueError.

    If the name or value attributes are None, or the value is an empty list, or
    if the control is disabled, the control is not successful.

    Public attributes:

    type: string describing type of control (see the keys of the
     HTMLForm.type2class dictionary for the allowable values) (readonly)
    name: name of control (readonly)
    value: current value of control (subclasses may allow a single value, a
     sequence of values, or either)
    disabled: disabled state
    readonly: readonly state
    id: value of id HTML attribute

    """
    def __init__(self, type, name, attrs):
        """
        type: string describing type of control (see the keys of the
         HTMLForm.type2class dictionary for the allowable values)
        name: control name
        attrs: HTML attributes of control's HTML element

        """
        raise NotImplementedError()

    def add_to_form(self, form):
        self._form = form
        form.controls.append(self)

    def fixup(self):
        pass

    def is_of_kind(self, kind):
        raise NotImplementedError()

    def clear(self):
        raise NotImplementedError()

    def __getattr__(self, name): raise NotImplementedError()
    def __setattr__(self, name, value): raise NotImplementedError()

    def pairs(self):
        """Return list of (key, value) pairs suitable for passing to urlencode.
        """
        raise NotImplementedError()

    def _write_mime_data(self, mw):
        """Write data for this control to a MimeWriter."""
        # called by HTMLForm
        for name, value in self.pairs():
            mw2 = mw.nextpart()
            mw2.addheader("Content-disposition",
                          'form-data; name="%s"' % name, 1)
            f = mw2.startbody(prefix=0)
            f.write(value)

    def __str__(self):
        raise NotImplementedError()

    def getLabels(self):
        res = []
        if self._label:
            res.append(self._label)
        if self.id:
            res.extend(self._form._id_to_labels.get(self.id, ()))
        return res


#---------------------------------------------------
class ScalarControl(Control):
    """Control whose value is not restricted to one of a prescribed set.

    Some ScalarControls don't accept any value attribute.  Otherwise, takes a
    single value, which must be string-like.

    Additional read-only public attribute:

    attrs: dictionary mapping the names of original HTML attributes of the
     control to their values

    """
    def __init__(self, type, name, attrs):
        self._label = _getLabel(attrs)
        self.__dict__["type"] = string.lower(type)
        self.__dict__["name"] = name
        self._value = attrs.get("value")
        self.disabled = attrs.has_key("disabled")
        self.readonly = attrs.has_key("readonly")
        self.id = attrs.get("id")

        self.attrs = attrs.copy()

        self._clicked = False

    def __getattr__(self, name):
        if name == "value":
            return self.__dict__["_value"]
        else:
            raise AttributeError("%s instance has no attribute '%s'" %
                                 (self.__class__.__name__, name))

    def __setattr__(self, name, value):
        if name == "value":
            if not isstringlike(value):
                raise TypeError("must assign a string")
            elif self.readonly:
                raise AttributeError("control '%s' is readonly" % self.name)
            elif self.disabled:
                raise AttributeError("control '%s' is disabled" % self.name)
            self.__dict__["_value"] = value
        elif name in ("name", "type"):
            raise AttributeError("%s attribute is readonly" % name)
        else:
            self.__dict__[name] = value

    def pairs(self):
        name = self.name
        value = self.value
        if name is None or value is None or self.disabled:
            return []
        return [(name, value)]

    def clear(self):
        if self.readonly:
            raise AttributeError("control '%s' is readonly" % self.name)
        self.__dict__["_value"] = None

    def __str__(self):
        name = self.name
        value = self.value
        if name is None: name = "<None>"
        if value is None: value = "<None>"

        infos = []
        if self.disabled: infos.append("disabled")
        if self.readonly: infos.append("readonly")
        info = string.join(infos, ", ")
        if info: info = " (%s)" % info

        return "<%s(%s=%s)%s>" % (self.__class__.__name__, name, value, info)


#---------------------------------------------------
class TextControl(ScalarControl):
    """Textual input control.

    Covers:

    INPUT/TEXT
    INPUT/PASSWORD
    INPUT/FILE
    INPUT/HIDDEN
    TEXTAREA

    """
    def __init__(self, type, name, attrs):
        ScalarControl.__init__(self, type, name, attrs)
        if self.type == "hidden": self.readonly = True
        if self._value is None:
            self._value = ""

    def is_of_kind(self, kind): return kind == "text"

#---------------------------------------------------
class FileControl(ScalarControl):
    """File upload with INPUT TYPE=FILE.

    The value attribute of a FileControl is always None.  Use add_file instead.

    Additional public method: add_file

    """

    def __init__(self, type, name, attrs):
        ScalarControl.__init__(self, type, name, attrs)
        self._value = None
        self._upload_data = []

    def is_of_kind(self, kind): return kind == "file"

    def clear(self):
        if self.readonly:
            raise AttributeError("control '%s' is readonly" % self.name)
        self._upload_data = []

    def __setattr__(self, name, value):
        if name in ("value", "name", "type"):
            raise AttributeError("%s attribute is readonly" % name)
        else:
            self.__dict__[name] = value

    def add_file(self, file_object, content_type=None, filename=None):
        if not hasattr(file_object, "read"):
            raise TypeError("file-like object must have read method")
        if content_type is not None and not isstringlike(content_type):
            raise TypeError("content type must be None or string-like")
        if filename is not None and not isstringlike(filename):
            raise TypeError("filename must be None or string-like")
        if content_type is None:
            content_type = "application/octet-stream"
        self._upload_data.append((file_object, content_type, filename))

    def pairs(self):
        # XXX should it be successful even if unnamed?
        if self.name is None or self.disabled:
            return []
        return [(self.name, "")]

    def _write_mime_data(self, mw):
        # called by HTMLForm
        if len(self._upload_data) == 1:
            # single file
            file_object, content_type, filename = self._upload_data[0]
            mw2 = mw.nextpart()
            fn_part = filename and ('; filename="%s"' % filename) or ''
            disp = 'form-data; name="%s"%s' % (self.name, fn_part)
            mw2.addheader("Content-disposition", disp, prefix=1)
            fh = mw2.startbody(content_type, prefix=0)
            fh.write(file_object.read())
        elif len(self._upload_data) != 0:
            # multiple files
            mw2 = mw.nextpart()
            disp = 'form-data; name="%s"' % self.name
            mw2.addheader("Content-disposition", disp, prefix=1)
            fh = mw2.startmultipartbody("mixed", prefix=0)
            for file_object, content_type, filename in self._upload_data:
                mw3 = mw2.nextpart()
                fn_part = filename and ('; filename="%s"' % filename) or ''
                disp = 'file%s' % fn_part
                mw3.addheader("Content-disposition", disp, prefix=1)
                fh2 = mw3.startbody(content_type, prefix=0)
                fh2.write(file_object.read())
            mw2.lastpart()

    def __str__(self):
        name = self.name
        if name is None: name = "<None>"

        if not self._upload_data:
            value = "<No files added>"
        else:
            value = []
            for file, ctype, filename in self._upload_data:
                if filename is None:
                    value.append("<Unnamed file>")
                else:
                    value.append(filename)
            value = string.join(value, ", ")

        info = []
        if self.disabled: info.append("disabled")
        if self.readonly: info.append("readonly")
        info = string.join(info, ", ")
        if info: info = " (%s)" % info

        return "<%s(%s=%s)%s>" % (self.__class__.__name__, name, value, info)


#---------------------------------------------------
class IsindexControl(ScalarControl):
    """ISINDEX control.

    ISINDEX is the odd-one-out of HTML form controls.  In fact, it isn't really
    part of regular HTML forms at all, and predates it.  You're only allowed
    one ISINDEX per HTML document.  ISINDEX and regular form submission are
    mutually exclusive -- either submit a form, or the ISINDEX.

    Having said this, since ISINDEX controls may appear in forms (which is
    probably bad HTML), ParseFile / ParseResponse will include them in the
    HTMLForm instances it returns.  You can set the ISINDEX's value, as with
    any other control (but note that ISINDEX controls have no name, so you'll
    need to use the type argument of set_value!).  When you submit the form,
    the ISINDEX will not be successful (ie., no data will get returned to the
    server as a result of its presence), unless you click on the ISINDEX
    control, in which case the ISINDEX gets submitted instead of the form:

    form.set_value("my isindex value", type="isindex")
    urllib2.urlopen(form.click(type="isindex"))

    ISINDEX elements outside of FORMs are ignored.  If you want to submit one
    by hand, do it like so:

    url = urlparse.urljoin(page_uri, "?"+urllib.quote_plus("my isindex value"))
    result = urllib2.urlopen(url)

    """
    def __init__(self, type, name, attrs):
        ScalarControl.__init__(self, type, name, attrs)
        if self._value is None:
            self._value = ""

    def is_of_kind(self, kind): return kind in ["text", "clickable"]

    def pairs(self):
        return []

    def _click(self, form, coord, return_type, request_class=urllib2.Request):
        # Relative URL for ISINDEX submission: instead of "foo=bar+baz",
        # want "bar+baz".
        # This doesn't seem to be specified in HTML 4.01 spec. (ISINDEX is
        # deprecated in 4.01, but it should still say how to submit it).
        # Submission of ISINDEX is explained in the HTML 3.2 spec, though.
        parts = urlparse.urlparse(form.action)
        rest, (query, frag) = parts[:-2], parts[-2:]
        parts = rest + (urllib.quote_plus(self.value), "")
        url = urlparse.urlunparse(parts)
        req_data = url, None, []

        if return_type == "pairs":
            return []
        elif return_type == "request_data":
            return req_data
        else:
            return request_class(url)

    def __str__(self):
        value = self.value
        if value is None: value = "<None>"

        infos = []
        if self.disabled: infos.append("disabled")
        if self.readonly: infos.append("readonly")
        info = string.join(infos, ", ")
        if info: info = " (%s)" % info

        return "<%s(%s)%s>" % (self.__class__.__name__, value, info)


#---------------------------------------------------
class IgnoreControl(ScalarControl):
    """Control that we're not interested in.

    Covers:

    INPUT/RESET
    BUTTON/RESET
    INPUT/BUTTON
    BUTTON/BUTTON

    These controls are always unsuccessful, in the terminology of HTML 4 (ie.
    they never require any information to be returned to the server).

    BUTTON/BUTTON is used to generate events for script embedded in HTML.

    The value attribute of IgnoreControl is always None.

    """
    def __init__(self, type, name, attrs):
        ScalarControl.__init__(self, type, name, attrs)
        self._value = None

    def is_of_kind(self, kind): return False

    def __setattr__(self, name, value):
        if name == "value":
            raise AttributeError(
                "control '%s' is ignored, hence read-only" % self.name)
        elif name in ("name", "type"):
            raise AttributeError("%s attribute is readonly" % name)
        else:
            self.__dict__[name] = value


#---------------------------------------------------
# ListControls

# helpers and subsidiary classes

class Item(object):
    def __init__(self, control, attrs):
        label = _getLabel(attrs)
        self.__dict__.update({
            'value': attrs['value'],
            '_labels': label and [label] or [],
            'attrs': attrs,
            'control': control,
            '_disabled': attrs.has_key("disabled"),
            '_selected': False,
            'id': attrs.get('id'),
            })

    def getLabels(self):
        res = []
        res.extend(self._labels)
        if self.id:
            res.extend(self.control._form._id_to_labels.get(self.id, ()))
        return res

    # selected and disabled properties
    def __getattr__(self, name):
        if name=='selected':
            return self._selected
        elif name=='disabled':
            return self._disabled
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name == 'selected':
            if bool(value) != bool(self._selected):
                self.control._set_selected_state(self, value)
        elif name == 'disabled':
            if bool(value) != bool(self._disabled):
                self.control._set_item_disabled(self, value)
        else:
            raise AttributeError(name)

    def __str__(self):
        res = self.value
        if self.selected:
            res = '*' + res
        if self.disabled:
            res = '(%s)' % res
        return res

    def __repr__(self):
        return "<%s value=%r id=%r>" % (
            self.__class__.__name__, self.value, self.id)

# how to remove items from a list container: delete them as usual
# ("del control.items[:]", for instance).
# how to add items to a list container: instantiate Item with control, and add
# to list ("control.items.append(Item(control, {...attrs...}))", for instance).
# You never want an item to have an incorrect reference to its control (and
# thus you never want an item to be in more than one control).

class AmbiguityError(Exception):
    pass

def disambiguate(items, count, value):
    if not items:
        raise ItemNotFoundError(value)
    if count is None:
        if len(items) > 1:
            raise AmbiguityError(value)
        return items[0]
    else:
        return items[count]

class ListControl(Control):
    """Control representing a sequence of items.

    The value attribute of a ListControl represents the selected list items in
    the control.

    ListControl implements both list controls that take a single value and
    those that take multiple values.

    ListControls accept sequence values only.  Some controls only accept
    sequences of length 0 or 1 (RADIO, and single-selection SELECT).
    In those cases, ItemCountError is raised if len(sequence) > 1.  CHECKBOXes
    and multiple-selection SELECTs (those having the "multiple" HTML attribute)
    accept sequences of any length.

    Note the following mistake:

    control.value = some_value
    assert control.value == some_value    # not necessarily true

    The reason for this is that the value attribute always gives the list items
    in the order they were listed in the HTML.

    ListControl items can also be referred to by their labels instead of names.
    Use the by_label argument, and the set_value_by_label, get_value_by_label
    methods.

    Note that, rather confusingly, though SELECT controls are represented in
    HTML by SELECT elements (which contain OPTION elements, representing
    individual list items), CHECKBOXes and RADIOs are not represented by *any*
    element.  Instead, those controls are represented by a collection of INPUT
    elements.  For example, this is a SELECT control, named "control1":

    <select name="control1">
     <option>foo</option>
     <option value="1">bar</option>
    </select>

    and this is a CHECKBOX control, named "control2":

    <input type="checkbox" name="control2" value="foo" id="cbe1">
    <input type="checkbox" name="control2" value="bar" id="cbe2">

    The id attribute of a CHECKBOX or RADIO ListControl is always that of its
    first element (for example, "cbe1" above).


    Additional read-only public attribute: multiple.

    """

    # ListControls are built up by the parser from their component items by
    # creating one ListControl per item, consolidating them into a single
    # master ListControl held by the HTMLForm:

    # -User calls form.new_control(...)
    # -Form creates Control, and calls control.add_to_form(self).
    # -Control looks for a Control with the same name and type in the form,
    #  and if it finds one, merges itself with that control by calling
    #  control.merge_control(self).  The first Control added to the form, of
    #  a particular name and type, is the only one that survives in the
    #  form.
    # -Form calls control.fixup for all its controls.  ListControls in the
    #  form know they can now safely pick their default values.

    # To create a ListControl without an HTMLForm, use:

    # control.merge_control(new_control)

    # (actually, it's much easier just to use ParseFile)

    _label = None

    def __init__(self, type, name, attrs={}, select_default=False,
                 called_as_base_class=False):
        """
        select_default: for RADIO and multiple-selection SELECT controls, pick
         the first item as the default if no 'selected' HTML attribute is
         present

        """
        if not called_as_base_class:
            raise NotImplementedError()

        self.__dict__["type"] = string.lower(type)
        self.__dict__["name"] = name
        self._value = attrs.get("value")
        self.disabled = False
        self.readonly = False
        self.id = attrs.get("id")

        # As Controls are merged in with .merge_control(), self.attrs will
        # refer to each Control in turn -- always the most recently merged
        # control.  Each merged-in Control instance corresponds to a single
        # list item: see ListControl.__doc__.
        self.items = []

        self._select_default = select_default
        self._clicked = False

    def clear(self):
        self.value = []

    def is_of_kind(self, kind):
        if kind  == "list":
            return True
        elif kind == "multilist":
            return bool(self.multiple)
        elif kind == "singlelist":
            return not self.multiple
        else:
            return False

    def items_from_label(self, label, exclude_disabled=False):
        if not isstringlike(label): # why not isinstance basestring?
            raise TypeError("item label must be string-like")
        # check all labels on the items, then if any of the values have
        # an id, go through all the collected labels on self._form._labels and
        # see if any of them match.
        items = [] # order is important
        mapping = self._form._id_to_labels
        for o in self.items:
            if not exclude_disabled or not o.disabled:
                for l in o.getLabels():
                    if label in l.text:
                        items.append(o)
                        break
        return items

    def items_from_value(self, value, exclude_disabled=False):
        if not isstringlike(value):
            raise TypeError("item value must be string-like")
        return [o for o in self.items if
                o.value == value and (not exclude_disabled or not o.disabled)]

    def get(self, name, by_label=False, count=None, exclude_disabled=False):
        if by_label:
            method = self.items_from_label
        else:
            method = self.items_from_value
        return disambiguate(method(name, exclude_disabled), count, name)

    def toggle(self, name, by_label=False, count=None):
        deprecation(
            "item = control.get(...); item.selected = not item.selected")
        o = self.get(name, by_label, count)
        self._set_selected_state(o, not o.selected)

    def set(self, selected, name, by_label=False, count=None):
        deprecation(
            "control.get(...).selected = <boolean>")
        self._set_selected_state(self.get(name, by_label, count), selected)

    def _set_selected_state(self, item, action):
        """
        index: index of item
        action:
         bool False: off
         bool True: on
        """
        if self.disabled:
            raise AttributeError("control '%s' is disabled" % self.name)
        if self.readonly:
            raise AttributeError("control '%s' is readonly" % self.name)
        action == bool(action)
        if item.disabled:
            # I'd prefer ValueError
            raise AttributeError("item is disabled")
        elif action != item.selected:
            if self.multiple:
                item.__dict__['_selected'] = action
            else:
                if not action:
                    item.__dict__['_selected'] = action
                else:
                    selected = [o for o in self.items
                                if o.selected and not o.disabled]
                    # disabled items are not changeable but also
                    # not 'successful': their values should not be sent to
                    # the server, so they are effectively invisible,
                    # whether or not the control considers itself to be
                    # selected
                    for s in selected:
                        s.__dict__['_selected'] = False
                    item.__dict__['_selected'] = True

    def toggle_single(self, by_label=None):
        deprecation(
            "control.items[0].selected = not control.items[0].selected")
        if len(self.items) != 1:
            raise ItemCountError(
                "'%s' is not a single-item control" % self.name)
        item = self.items[0]
        self._set_selected_state(item, not item.selected)

    def set_single(self, selected, by_label=None):
        deprecation(
            "control.items[0].selected = <boolean>")
        if len(self.items) != 1:
            raise ItemCountError(
                "'%s' is not a single-item control" % self.name)
        self._set_selected_state(self.items[0], selected)

    def get_item_disabled(self, name, by_label=False, count=None):
        """Get disabled state of named list item in a ListControl."""
        deprecation(
            "control.get(...).disabled")
        return self.get(name, by_label, count).disabled

    def set_item_disabled(self, disabled, name, by_label=False, count=None):
        """Set disabled state of named list item in a ListControl.

        disabled: boolean disabled state

        """
        deprecation(
            "control.get(...).disabled = <boolean>")
        self.get(name, by_label, count).disabled = disabled

    def _set_item_disabled(self, item, disabled):
        if not self.multiple and item.selected and self.value:
            item.__dict__['_selected'] = False
        item.__dict__['_disabled'] = bool(disabled)

    def set_all_items_disabled(self, disabled):
        """Set disabled state of all list items in a ListControl.

        disabled: boolean disabled state

        """
        disabled = bool(disabled)
        if not self.multiple: # make sure that re-emerging items don't
            # make single-choice controls insane
            value = bool(self.value)
            for o in self.items:
                if not disabled and o.disabled:
                    o.__dict__['_disabled'] = disabled
                    if not self.multiple and o.selected:
                        if value:
                            o.selected = False
                        else:
                            value = True
                else:
                    o.__dict__['_disabled'] = disabled
        else:
            for o in self.items:
                o.__dict__['_disabled'] = disabled

    def get_item_attrs(self, name, by_label=False, count=None):
        """Return dictionary of HTML attributes for a single ListControl item.

        The HTML element types that describe list items are: OPTION for SELECT
        controls, INPUT for the rest.  These elements have HTML attributes that
        you may occasionally want to know about -- for example, the "alt" HTML
        attribute gives a text string describing the item (graphical browsers
        usually display this as a tooltip).

        The returned dictionary maps HTML attribute names to values.  The names
        and values are taken from the original HTML.
        """
        deprecation(
            "control.get(...).attrs")
        return self.get(name, by_label, count).attrs

    def add_to_form(self, form):
        self._form = form
        try:
            control = form.find_control(self.name, self.type)
        except ControlNotFoundError:
            Control.add_to_form(self, form)
        else:
            control.merge_control(self)

    def merge_control(self, control):
        assert bool(control.multiple) == bool(self.multiple)
        assert isinstance(control, self.__class__)
        self.items.extend(control.items)

    def fixup(self):
        """
        ListControls are built up from component list items (which are also
        ListControls) during parsing.  This method should be called after all
        items have been added.  See ListControl.__doc__ for the reason this is
        required.

        """
        # Need to set default selection where no item was indicated as being
        # selected by the HTML:

        # CHECKBOX:
        #  Nothing should be selected.
        # SELECT/single, SELECT/multiple and RADIO:
        #  RFC 1866 (HTML 2.0): says first item should be selected.
        #  W3C HTML 4.01 Specification: says that client behaviour is
        #   undefined in this case.  For RADIO, exactly one must be selected,
        #   though which one is undefined.
        #  Both Netscape and Microsoft Internet Explorer (IE) choose first
        #   item for SELECT/single.  However, both IE5 and Mozilla (both 1.0
        #   and Firebird 0.6) leave all items unselected for RADIO and
        #   SELECT/multiple.

        # Since both Netscape and IE all choose the first item for
        # SELECT/single, we do the same.  OTOH, both Netscape and IE
        # leave SELECT/multiple with nothing selected, in violation of RFC 1866
        # (but not in violation of the W3C HTML 4 standard); the same is true
        # of RADIO (which *is* in violation of the HTML 4 standard).  We follow
        # RFC 1866 if the _select_default attribute is set, and Netscape and IE
        # otherwise.  RFC 1866 and HTML 4 are always violated insofar as you
        # can deselect all items in a RadioControl.
        
        for o in self.items: 
            # set items' controls to self, now that we've merged
            o.__dict__['control'] = self

    def __getattr__(self, name):
        if name == "value":
            return [o.value for o in self.items if
                    not o.disabled and o.selected]
        else:
            raise AttributeError("%s instance has no attribute '%s'" %
                                 (self.__class__.__name__, name))

    def __setattr__(self, name, value):
        if name == "value":
            if self.disabled:
                raise AttributeError("control '%s' is disabled" % self.name)
            if self.readonly:
                raise AttributeError("control '%s' is readonly" % self.name)
            self._set_value(value)
        elif name in ("name", "type", "multiple"):
            raise AttributeError("%s attribute is readonly" % name)
        else:
            self.__dict__[name] = value

    def _set_value(self, value):
        if value is None or isstringlike(value):
            raise TypeError("ListControl, must set a sequence")
        if not value:
            for o in self.items:
                if not o.disabled:
                    o.selected = False
        elif self.multiple:
            self._multiple_set_value(value)
        elif len(value) > 1:
            raise ItemCountError(
                "single selection list, must set sequence of "
                "length 0 or 1")
        else:
            self._single_set_value(value)

    def _get_items(self, value, target=1):
        all_items = self.items_from_value(value)
        items = [o for o in all_items if not o.disabled]
        if len(items) < target:
            if len(all_items) < target:
                raise ItemNotFoundError(
                    "insufficient items with value %r" % value)
            else:
                raise AttributeError('disabled item with value %s' % value)
        on = []
        off = []
        for o in items:
            if o.selected:
                on.append(o)
            else:
                off.append(o)
        return on, off

    def _single_set_value(self, value):
        on, off = self._get_items(value[0])
        if not on:
            off[0].selected = True

    def _multiple_set_value(self, value):
        turn_on = [] # transactional-ish
        turn_off = [o for o in self.items if o.selected and not o.disabled]
        values = {}
        for v in value:
            if v in values:
                values[v] += 1
            else:
                values[v] = 1
        for value, count in values.items():
            on, off = self._get_items(value, count)
            for i in range(count):
                if on:
                    o = on[0]
                    del on[0]
                    del turn_off[turn_off.index(o)]
                else:
                    o = off[0]
                    del off[0]
                    turn_on.append(o)
        for o in turn_off:
            o.selected = False
        for o in turn_on:
            o.selected = True

    def set_value_by_label(self, value):
        if isinstance(value, (str, unicode)):
            raise TypeError(value)
        items = []
        for v in value:
            found = self.items_from_label(v)
            if len(found) > 1:
                # ambiguous labels are fine as long as values are same
                opt_value = found[0].value
                if [o for o in found[1:] if o != opt_value]:
                    raise AmbiguityError(v)
            for o in found: # for the multiple-item case, we could try to
                # be smarter, saving them up and trying to resolve, but that's
                # too much.
                if o not in items:
                    items.append(o)
                    break
            else: # all of them are used
                raise ItemNotFoundError(v)
        # now we have all the items that should be on
        # let's just turn everything off and then back on.
        self.value = []
        for o in items:
            o.selected = True

    def get_value_by_label(self):
        res = []
        for o in self.items:
            if not o.disabled and o.selected:
                for l in o.getLabels():
                    if l.text:
                        res.append(l.text)
                        break
                else:
                    res.append(None)
        return res

    def possible_items(self, by_label=False): # disabled are not possible
        deprecation(
            "[o.value for o in self.items]")
        if by_label:
            res = []
            for o in self.items:
                for l in o.getLabels():
                    if l.text:
                        res.append(l.text)
                        break
                else:
                    res.append(None)
            return res
        return [o.value for o in self.items]

    def pairs(self):
        if self.disabled:
            return []
        else:
            return [(self.name, o.value) for o in self.items
                    if o.selected and not o.disabled]

    def __str__(self):
        name = self.name
        if name is None: name = "<None>"

        display = [str(o) for o in self.items]

        infos = []
        if self.disabled: infos.append("disabled")
        if self.readonly: infos.append("readonly")
        info = string.join(infos, ", ")
        if info: info = " (%s)" % info

        return "<%s(%s=[%s])%s>" % (self.__class__.__name__,
                                    name, string.join(display, ", "), info)


class RadioControl(ListControl):
    """
    Covers:

    INPUT/RADIO

    """
    def __init__(self, type, name, attrs, select_default=False):
        attrs.setdefault('value', 'on')
        ListControl.__init__(self, type, name, attrs, select_default,
                             called_as_base_class=True)
        self.__dict__["multiple"] = False
        o = Item(self, attrs)
        o.__dict__['_selected'] = attrs.has_key("checked")
        self.items.append(o)

    def fixup(self):
        ListControl.fixup(self)
        found = [o for o in self.items if o.selected and not o.disabled]
        if not found:
            if self._select_default:
                for o in self.items:
                    if not o.disabled:
                        o.selected = True
                        break
        else: # eliminate any duplicate selected.  Choose the last one.
            for o in found[:-1]:
                o.selected = False

    def getLabels(self):
        return []

class CheckboxControl(ListControl):
    """
    Covers:

    INPUT/CHECKBOX

    """
    def __init__(self, type, name, attrs, select_default=False):
        attrs.setdefault('value', 'on')
        ListControl.__init__(self, type, name, attrs, select_default,
                             called_as_base_class=True)
        self.__dict__["multiple"] = True
        o = Item(self, attrs)
        o.__dict__['_selected'] = attrs.has_key("checked")
        self.items.append(o)

    def getLabels(self):
        return []


class SelectControl(ListControl):
    """
    Covers:

    SELECT (and OPTION)

    SELECT control values and labels are subject to some messy defaulting
    rules.  For example, if the HTML representation of the control is:

    <SELECT name=year>
      <OPTION value=0 label="2002">current year</OPTION>
      <OPTION value=1>2001</OPTION>
      <OPTION>2000</OPTION>
    </SELECT>

    The items, in order, have labels "2002", "2001" and "2000", whereas their
    values are "0", "1" and "2000" respectively.  Note that the value of the
    last OPTION in this example defaults to its contents, as specified by RFC
    1866, as do the labels of the second and third OPTIONs.

    The OPTION labels are sometimes more meaningful than the OPTION values,
    which can make for more maintainable code.

    Additional read-only public attribute: attrs

    The attrs attribute is a dictionary of the original HTML attributes of the
    SELECT element.  Other ListControls do not have this attribute, because in
    other cases the control as a whole does not correspond to any single HTML
    element.  The get_item_attrs method may be used as usual to get at the
    HTML attributes of the HTML elements corresponding to individual list items
    (for SELECT controls, these are OPTION elements).

    Another special case is that the attributes dictionaries returned by
    get_item_attrs have a special key "contents" which does not correspond to
    any real HTML attribute, but rather contains the contents of the OPTION
    element:

    <OPTION>this bit</OPTION>

    """
    # HTML attributes here are treated slightly from other list controls:
    # -The SELECT HTML attributes dictionary is stuffed into the OPTION
    #  HTML attributes dictionary under the "__select" key.
    # -The content of each OPTION element is stored under the special
    #  "contents" key of the dictionary.
    # After all this, the dictionary is passed to the SelectControl constructor
    # as the attrs argument, as usual.  However:
    # -The first SelectControl constructed when building up a SELECT control
    #  has a constructor attrs argument containing only the __select key -- so
    #  this SelectControl represents an empty SELECT control.
    # -Subsequent SelectControls have both OPTION HTML-attribute in attrs and
    #  the __select dictionary containing the SELECT HTML-attributes.

    def __init__(self, type, name, attrs, select_default=False):
        # fish out the SELECT HTML attributes from the OPTION HTML attributes
        # dictionary
        self.attrs = attrs["__select"].copy()
        self.__dict__['_label'] = _getLabel(self.attrs)
        self.__dict__['id'] = self.attrs.get('id')
        self.__dict__["multiple"] = self.attrs.has_key("multiple")
        # the majority of the contents, label, and value dance already happened
        contents = attrs.get('contents')
        attrs = attrs.copy()
        del attrs["__select"]

        ListControl.__init__(self, type, name, self.attrs, select_default,
                             called_as_base_class=True)
        self.disabled = self.attrs.has_key("disabled")
        self.readonly = self.attrs.has_key("readonly")
        if attrs.has_key('value'):
            # otherwise it is a marker 'select started' token
            o = Item(self, attrs)
            o.__dict__['_selected'] = attrs.has_key("selected")
            # add 'label' label and contents label, if different.  If both are
            # provided, the 'label' label is used for display in HTML 
            # 4.0-compliant browsers (and any lower spec? not sure) while the
            # contents are used for display in older or less-compliant
            # browsers.  We make label objects for both, if the values are
            # different.
            label = attrs.get('label')
            if label:
                o._labels.append(Label({'__text': label}))
                if contents and contents != label:
                    o._labels.append(Label({'__text': contents}))
            elif contents:
                o._labels.append(Label({'__text': contents}))
            self.items.append(o)

    def fixup(self):
        ListControl.fixup(self)
        found = [o for o in self.items if o.selected and not o.disabled]
        if not found:
            if not self.multiple or self._select_default:
                for o in self.items:
                    if not o.disabled:
                        o.selected = True
                        break
        elif not self.multiple: # eliminate any duplicate selected.
            # Choose the last one.
            for o in found[:-1]:
                o.selected = False


#---------------------------------------------------
class SubmitControl(ScalarControl):
    """
    Covers:

    INPUT/SUBMIT
    BUTTON/SUBMIT

    """
    def __init__(self, type, name, attrs):
        ScalarControl.__init__(self, type, name, attrs)
        # IE5 defaults SUBMIT value to "Submit Query"; Firebird 0.6 leaves it
        # blank, Konqueror 3.1 defaults to "Submit".  HTML spec. doesn't seem
        # to define this.
        if self.value is None: self.value = ""
        self.readonly = True

    def getLabels(self):
        res = []
        if self.value:
            res.append(Label({'__text': self.value}))
        res.extend(ScalarControl.getLabels(self))
        return res

    def is_of_kind(self, kind): return kind == "clickable"

    def _click(self, form, coord, return_type, request_class=urllib2.Request):
        self._clicked = coord
        r = form._switch_click(return_type, request_class)
        self._clicked = False
        return r

    def pairs(self):
        if not self._clicked:
            return []
        return ScalarControl.pairs(self)


#---------------------------------------------------
class ImageControl(SubmitControl):
    """
    Covers:

    INPUT/IMAGE

    Coordinates are specified using one of the HTMLForm.click* methods.

    """
    def __init__(self, type, name, attrs):
        SubmitControl.__init__(self, type, name, attrs)
        self.readonly = False

    def pairs(self):
        clicked = self._clicked
        if self.disabled or not clicked:
            return []
        name = self.name
        if name is None: return []
        pairs = [
            ("%s.x" % name, str(clicked[0])),
            ("%s.y" % name, str(clicked[1])),
            ]
        value = self._value
        if value:
            pairs.append((name, value))
        return pairs

    getLabels = ScalarControl.getLabels

# aliases, just to make str(control) and str(form) clearer
class PasswordControl(TextControl): pass
class HiddenControl(TextControl): pass
class TextareaControl(TextControl): pass
class SubmitButtonControl(SubmitControl): pass


def is_listcontrol(control): return control.is_of_kind("list")


class HTMLForm:
    """Represents a single HTML <form> ... </form> element.

    A form consists of a sequence of controls that usually have names, and
    which can take on various values.  The values of the various types of
    controls represent variously: text, zero-or-one-of-many or many-of-many
    choices, and files to be uploaded.  Some controls can be clicked on to
    submit the form, and clickable controls' values sometimes include the
    coordinates of the click.

    Forms can be filled in with data to be returned to the server, and then
    submitted, using the click method to generate a request object suitable for
    passing to urllib2.urlopen (or the click_request_data or click_pairs
    methods if you're not using urllib2).

    import ClientForm
    forms = ClientForm.ParseFile(html, base_uri)
    form = forms[0]

    form["query"] = "Python"
    form.set("lots", "nr_results")

    response = urllib2.urlopen(form.click())

    Usually, HTMLForm instances are not created directly.  Instead, the
    ParseFile or ParseResponse factory functions are used.  If you do construct
    HTMLForm objects yourself, however, note that an HTMLForm instance is only
    properly initialised after the fixup method has been called (ParseFile and
    ParseResponse do this for you).  See ListControl.__doc__ for the reason
    this is required.

    Indexing a form (form["control_name"]) returns the named Control's value
    attribute.  Assignment to a form index (form["control_name"] = something)
    is equivalent to assignment to the named Control's value attribute.  If you
    need to be more specific than just supplying the control's name, use the
    set_value and get_value methods.

    ListControl values are lists of item names.  The list item's name is the
    value of the corresponding HTML element's "value" attribute.

    Example:

      <INPUT type="CHECKBOX" name="cheeses" value="leicester"></INPUT>
      <INPUT type="CHECKBOX" name="cheeses" value="cheddar"></INPUT>

    defines a CHECKBOX control with name "cheeses" which has two items, named
    "leicester" and "cheddar".

    Another example:

      <SELECT name="more_cheeses">
        <OPTION>1</OPTION>
        <OPTION value="2" label="CHEDDAR">cheddar</OPTION>
      </SELECT>

    defines a SELECT control with name "more_cheeses" which has two items,
    named "1" and "2" (because the OPTION element's value HTML attribute
    defaults to the element contents).

    To set, clear or toggle individual list items, use the set and toggle
    methods.  To set the whole value, do as for any other control:use indexing
    or the set_/get_value methods.

    Example:

    # select *only* the item named "cheddar"
    form["cheeses"] = ["cheddar"]
    # select "cheddar", leave other items unaffected
    form.set("cheddar", "cheeses")

    Some controls (RADIO and SELECT without the multiple attribute) can only
    have zero or one items selected at a time.  Some controls (CHECKBOX and
    SELECT with the multiple attribute) can have multiple items selected at a
    time.  To set the whole value of a ListControl, assign a sequence to a form
    index:

    form["cheeses"] = ["cheddar", "leicester"]

    If the ListControl is not multiple-selection, the assigned list must be of
    length one.

    To check whether a control has an item, or whether an item is selected,
    respectively:

    "cheddar" in form.possible_items("cheeses")
    "cheddar" in form["cheeses"]  # (or "cheddar" in form.get_value("cheeses"))

    Note that some list items may be disabled (see below).

    Note the following mistake:

    form[control_name] = control_value
    assert form[control_name] == control_value  # not necessarily true

    The reason for this is that form[control_name] always gives the list items
    in the order they were listed in the HTML.

    List items (hence list values, too) can be referred to in terms of list
    item labels rather than list item names.  Currently, this is only possible
    for SELECT controls (this is a bug).  To use this feature, use the by_label
    arguments to the various HTMLForm methods.  Note that it is *item* names
    (hence ListControl values also), not *control* names, that can be referred
    to by label.

    The question of default values of OPTION contents, labels and values is
    somewhat complicated: see SelectControl.__doc__ and
    ListControl.get_item_attrs.__doc__ if you think you need to know.

    Controls can be disabled or readonly.  In either case, the control's value
    cannot be changed until you clear those flags (see example below).
    Disabled is the state typically represented by browsers by `greying out' a
    control.  Disabled controls are not `successful' -- they don't cause data
    to get returned to the server.  Readonly controls usually appear in
    browsers as read-only text boxes.  Readonly controls are successful.  List
    items can also be disabled.  Attempts to select disabled items (with
    form[name] = value, or using the ListControl.set method, for example) fail.
    Attempts to clear disabled items are allowed.

    If a lot of controls are readonly, it can be useful to do this:

    form.set_all_readonly(False)

    To clear a control's value attribute, so that it is not successful (until a
    value is subsequently set):

    form.clear("cheeses")

    When you want to do several things with a single control, or want to do
    less common things, like changing which controls and items are disabled,
    you can get at a particular control:

    control = form.find_control("cheeses")
    control.disabled = False
    control.readonly = False
    control.set_item_disabled(False, "gruyere")
    control.set("gruyere")

    Most methods on HTMLForm just delegate to the contained controls, so see
    the docstrings of the various Control classes for further documentation.
    Most of these delegating methods take name, type, kind, id and nr arguments
    to specify the control to be operated on: see
    HTMLForm.find_control.__doc__.

    ControlNotFoundError (subclass of ValueError) is raised if the specified
    control can't be found.  This includes occasions where a non-ListControl
    is found, but the method (set, for example) requires a ListControl.
    ItemNotFoundError (subclass of ValueError) is raised if a list item can't
    be found.  ItemCountError (subclass of ValueError) is raised if an attempt
    is made to select more than one item and the control doesn't allow that, or
    set/get_single are called and the control contains more than one item.
    AttributeError is raised if a control or item is readonly or disabled and
    an attempt is made to alter its value.

    Security note: Remember that any passwords you store in HTMLForm instances
    will be saved to disk in the clear if you pickle them (directly or
    indirectly).  The simplest solution to this is to avoid pickling HTMLForm
    objects.  You could also pickle before filling in any password, or just set
    the password to "" before pickling.


    Public attributes:

    action: full (absolute URI) form action
    method: "GET" or "POST"
    enctype: form transfer encoding MIME type
    name: name of form (None if no name was specified)
    attrs: dictionary mapping original HTML form attributes to their values

    controls: list of Control instances; do not alter this list
     (instead, call form.new_control to make a Control and add it to the
     form, or control.add_to_form if you already have a Control instance)



    Methods for form filling:
    -------------------------

    Most of the these methods have very similar arguments.  See
    HTMLForm.find_control.__doc__ for details of the name, type, kind and nr
    arguments.  See above for a description of by_label.

    def find_control(self,
                     name=None, type=None, kind=None, id=None, predicate=None,
                     nr=None)

    get_value(name=None, type=None, kind=None, id=None, nr=None,
              by_label=False)
    set_value(value,
              name=None, type=None, kind=None, id=None, nr=None,
              by_label=False)

    set_all_readonly(readonly)


    Methods applying only to ListControls:

    possible_items(name=None, type=None, kind=None, id=None, nr=None,
                   by_label=False)

    set(selected, item_name,
        name=None, type=None, kind=None, id=None, nr=None,
        by_label=False)
    toggle(item_name,
           name=None, type=None, id=None, nr=None,
           by_label=False)

    set_single(selected,
               name=None, type=None, kind=None, id=None, nr=None,
               by_label=False)
    toggle_single(name=None, type=None, kind=None, id=None, nr=None,
                  by_label=False)


    Method applying only to FileControls:

    add_file(file_object,
             content_type="application/octet-stream", filename=None,
             name=None, id=None, nr=None)


    Methods applying only to clickable controls:

    click(name=None, type=None, id=None, nr=0, coord=(1,1))
    click_request_data(name=None, type=None, id=None, nr=0, coord=(1,1))
    click_pairs(name=None, type=None, id=None, nr=0, coord=(1,1))

    """

    type2class = {
        "text": TextControl,
        "password": PasswordControl,
        "hidden": HiddenControl,
        "textarea": TextareaControl,

        "isindex": IsindexControl,

        "file": FileControl,

        "button": IgnoreControl,
        "buttonbutton": IgnoreControl,
        "reset": IgnoreControl,
        "resetbutton": IgnoreControl,

        "submit": SubmitControl,
        "submitbutton": SubmitButtonControl,
        "image": ImageControl,

        "radio": RadioControl,
        "checkbox": CheckboxControl,
        "select": SelectControl,
        }

#---------------------------------------------------
# Initialisation.  Use ParseResponse / ParseFile instead.

    def __init__(self, action, method="GET",
                 enctype="application/x-www-form-urlencoded",
                 name=None, attrs=None,
                 request_class=urllib2.Request,
                 forms=None, labels=None, id_to_labels=None):
        """
        In the usual case, use ParseResponse (or ParseFile) to create new
        HTMLForm objects.

        action: full (absolute URI) form action
        method: "GET" or "POST"
        enctype: form transfer encoding MIME type
        name: name of form
        attrs: dictionary mapping original HTML form attributes to their values

        """
        self.action = action
        self.method = method
        self.enctype = enctype
        self.name = name
        if attrs is not None:
            self.attrs = attrs.copy()
        else:
            self.attrs = {}
        self.controls = []
        self._request_class = request_class
        self._forms = forms # this is a semi-public API!
        self._labels = labels # this is a semi-public API!
        self._id_to_labels = id_to_labels # this is a semi-public API!

    def new_control(self, type, name, attrs,
                    ignore_unknown=False, select_default=False):
        """Adds a new control to the form.

        This is usually called by ParseFile and ParseResponse.  Don't call it
        youself unless you're building your own Control instances.

        Note that controls representing lists of items are built up from
        controls holding only a single list item.  See ListControl.__doc__ for
        further information.

        type: type of control (see Control.__doc__ for a list)
        attrs: HTML attributes of control
        ignore_unknown: if true, use a dummy Control instance for controls of
         unknown type; otherwise, use a TextControl
        select_default: for RADIO and multiple-selection SELECT controls, pick
         the first item as the default if no 'selected' HTML attribute is
         present (this defaulting happens when the HTMLForm.fixup method is
         called)

        """
        type = string.lower(type)
        klass = self.type2class.get(type)
        if klass is None:
            if ignore_unknown:
                klass = IgnoreControl
            else:
                klass = TextControl

        a = attrs.copy()
        if issubclass(klass, ListControl):
            control = klass(type, name, a, select_default)
        else:
            control = klass(type, name, a)
        control.add_to_form(self)

    def fixup(self):
        """Normalise form after all controls have been added.

        This is usually called by ParseFile and ParseResponse.  Don't call it
        youself unless you're building your own Control instances.

        This method should only be called once, after all controls have been
        added to the form.

        """
        for control in self.controls:
            control.fixup()

#---------------------------------------------------
    def __str__(self):
        header = "%s %s %s" % (self.method, self.action, self.enctype)
        rep = [header]
        for control in self.controls:
            rep.append("  %s" % str(control))
        return "<%s>" % string.join(rep, "\n")

#---------------------------------------------------
# Form-filling methods.

    def __getitem__(self, name):
        return self.find_control(name).value
    def __setitem__(self, name, value):
        control = self.find_control(name)
        try:
            control.value = value
        except AttributeError, e:
            raise ValueError(str(e))

    def get_value(self,
                  name=None, type=None, kind=None, id=None, nr=None,
                  by_label=False):
        """Return value of control.

        If only name and value arguments are supplied, equivalent to

        form[name]

        """
        c = self.find_control(name, type, kind, id, nr=nr)
        if by_label:
            try:
                meth = c.get_value_by_label
            except AttributeError:
                raise NotImplementedError(
                    "control '%s' does not yet support by_label" % c.name)
            else:
                return meth()
        else:
            return c.value
    def set_value(self, value,
                  name=None, type=None, kind=None, id=None, nr=None,
                  by_label=False):
        """Set value of control.

        If only name and value arguments are supplied, equivalent to

        form[name] = value

        """
        c = self.find_control(name, type, kind, id, nr=nr)
        if by_label:
            try:
                meth = c.set_value_by_label
            except AttributeError:
                raise NotImplementedError(
                    "control '%s' does not yet support by_label" % c.name)
            else:
                meth(value)
        else:
            c.value = value

    def set_all_readonly(self, readonly):
        for control in self.controls:
            control.readonly = bool(readonly)

    def clear_all(self):
        """Clear the value attributes of all controls in the form.

        See HTMLForm.clear.__doc__.

        """
        for control in self.controls:
            control.clear()

    def clear(self,
              name=None, type=None, kind=None, id=None, nr=None):
        """Clear the value attributes of all controls in the form.

        As a result, the affected controls will not be successful until a value
        is subsequently set.  AttributeError is raised on readonly controls.

        """
        c = self.find_control(name, type, kind, id, nr=nr)
        c.clear()


#---------------------------------------------------
# Form-filling methods applying only to ListControls.

    def possible_items(self, # deprecated
                       name=None, type=None, kind=None, id=None, label=None,
                       nr=None, by_label=False):
        """Return a list of all values that the specified control can take."""
        c = self._find_list_control(name, type, kind, id, label, nr)
        return c.possible_items(by_label)

    def set(self, selected, item_name, # deprecated
            name=None, type=None, kind=None, id=None, label=None, nr=None,
            by_label=False):
        """Select / deselect named list item.

        selected: boolean selected state

        """
        self._find_list_control(name, type, kind, id, label, nr).set(
            selected, item_name, by_label)
    def toggle(self, item_name, # deprecated
               name=None, type=None, kind=None, id=None, label=None, nr=None,
               by_label=False):
        """Toggle selected state of named list item."""
        self._find_list_control(name, type, kind, id, label, nr).toggle(
            item_name, by_label)

    def set_single(self, selected, # deprecated
                   name=None, type=None, kind=None, id=None, label=None,
                   nr=None, by_label=None):
        """Select / deselect list item in a control having only one item.

        If the control has multiple list items, ItemCountError is raised.

        This is just a convenience method, so you don't need to know the item's
        name -- the item name in these single-item controls is usually
        something meaningless like "1" or "on".

        For example, if a checkbox has a single item named "on", the following
        two calls are equivalent:

        control.toggle("on")
        control.toggle_single()

        """ # by_label ignored and deprecated
        self._find_list_control(
            name, type, kind, id, label, nr).set_single(selected)
    def toggle_single(self, name=None, type=None, kind=None, id=None,
                      label=None, nr=None, by_label=None): # deprecated
        """Toggle selected state of list item in control having only one item.

        The rest is as for HTMLForm.set_single.__doc__.

        """ # by_label ignored and deprecated
        self._find_list_control(name, type, kind, id, label, nr).toggle_single()

#---------------------------------------------------
# Form-filling method applying only to FileControls.

    def add_file(self, file_object, content_type=None, filename=None,
                 name=None, id=None, label=None, nr=None):
        """Add a file to be uploaded.

        file_object: file-like object (with read method) from which to read
         data to upload
        content_type: MIME content type of data to upload
        filename: filename to pass to server

        If filename is None, no filename is sent to the server.

        If content_type is None, the content type is guessed based on the
        filename and the data from read from the file object.

        XXX
        At the moment, guessed content type is always application/octet-stream.
        Use sndhdr, imghdr modules.  Should also try to guess HTML, XML, and
        plain text.

        Note the following useful HTML attributes of file upload controls (see
        HTML 4.01 spec, section 17):

        accept: comma-separated list of content types that the server will
         handle correctly; you can use this to filter out non-conforming files
        size: XXX IIRC, this is indicative of whether form wants multiple or
         single files
        maxlength: XXX hint of max content length in bytes?

        """
        self.find_control(name, "file", id=id, label=label, nr=nr).add_file(
            file_object, content_type, filename)

#---------------------------------------------------
# Form submission methods, applying only to clickable controls.

    def click(self, name=None, type=None, id=None, label=None, nr=0, coord=(1,1),
              request_class=urllib2.Request):
        """Return request that would result from clicking on a control.

        The request object is a urllib2.Request instance, which you can pass to
        urllib2.urlopen (or ClientCookie.urlopen).

        Only some control types (INPUT/SUBMIT & BUTTON/SUBMIT buttons and
        IMAGEs) can be clicked.

        Will click on the first clickable control, subject to the name, type
        and nr arguments (as for find_control).  If no name, type, id or number
        is specified and there are no clickable controls, a request will be
        returned for the form in its current, un-clicked, state.

        IndexError is raised if any of name, type, id or nr is specified but no
        matching control is found.  ValueError is raised if the HTMLForm has an
        enctype attribute that is not recognised.

        You can optionally specify a coordinate to click at, which only makes a
        difference if you clicked on an image.

        """
        return self._click(name, type, id, label, nr, coord, "request",
                           self._request_class)

    def click_request_data(self,
                           name=None, type=None, id=None, label=None, 
                           nr=0, coord=(1,1),
                           request_class=urllib2.Request):
        """As for click method, but return a tuple (url, data, headers).

        You can use this data to send a request to the server.  This is useful
        if you're using httplib or urllib rather than urllib2.  Otherwise, use
        the click method.

        # Untested.  Have to subclass to add headers, I think -- so use urllib2
        # instead!
        import urllib
        url, data, hdrs = form.click_request_data()
        r = urllib.urlopen(url, data)

        # Untested.  I don't know of any reason to use httplib -- you can get
        # just as much control with urllib2.
        import httplib, urlparse
        url, data, hdrs = form.click_request_data()
        tup = urlparse(url)
        host, path = tup[1], urlparse.urlunparse((None, None)+tup[2:])
        conn = httplib.HTTPConnection(host)
        if data:
            httplib.request("POST", path, data, hdrs)
        else:
            httplib.request("GET", path, headers=hdrs)
        r = conn.getresponse()

        """
        return self._click(name, type, id, label, nr, coord, "request_data",
                           self._request_class)

    def click_pairs(self, name=None, type=None, id=None, label=None,
                    nr=0, coord=(1,1)):
        """As for click_request_data, but returns a list of (key, value) pairs.

        You can use this list as an argument to ClientForm.urlencode.  This is
        usually only useful if you're using httplib or urllib rather than
        urllib2 or ClientCookie.  It may also be useful if you want to manually
        tweak the keys and/or values, but this should not be necessary.
        Otherwise, use the click method.

        Note that this method is only useful for forms of MIME type
        x-www-form-urlencoded.  In particular, it does not return the
        information required for file upload.  If you need file upload and are
        not using urllib2, use click_request_data.

        Also note that Python 2.0's urllib.urlencode is slightly broken: it
        only accepts a mapping, not a sequence of pairs, as an argument.  This
        messes up any ordering in the argument.  Use ClientForm.urlencode
        instead.

        """
        return self._click(name, type, id, label, nr, coord, "pairs",
                           self._request_class)

#---------------------------------------------------

    def find_control(self,
                     name=None, type=None, kind=None, id=None, label=None,
                     predicate=None, nr=None):
        """Locate and return some specific control within the form.

        At least one of the name, type, kind, predicate and nr arguments must
        be supplied.  If no matching control is found, ControlNotFoundError is
        raised.

        If name is specified, then the control must have the indicated name.

        If type is specified then the control must have the specified type (in
        addition to the types possible for <input> HTML tags: "text",
        "password", "hidden", "submit", "image", "button", "radio", "checkbox",
        "file" we also have "reset", "buttonbutton", "submitbutton",
        "resetbutton", "textarea", "select" and "isindex").

        If kind is specified, then the control must fall into the specified
        group, each of which satisfies a particular interface.  The types are
        "text", "list", "multilist", "singlelist", "clickable" and "file".

        If id is specified, then the control must have the indicated id.

        If predicate is specified, then the control must match that function.
        The predicate function is passed the control as its single argument,
        and should return a boolean value indicating whether the control
        matched.

        nr, if supplied, is the sequence number of the control (where 0 is the
        first).  Note that control 0 is the first control matching all the
        other arguments (if supplied); it is not necessarily the first control
        in the form.

        """
        if ((name is None) and (type is None) and (kind is None) and
            (id is None) and (label is None) and (predicate is None) and
            (nr is None)):
            raise ValueError(
                "at least one argument must be supplied to specify control")
        if nr is None: nr = 0

        return self._find_control(name, type, kind, id, label, predicate, nr)

#---------------------------------------------------
# Private methods.

    def _find_list_control(self,
                           name=None, type=None, kind=None, id=None, 
                           label=None, nr=None):
        if ((name is None) and (type is None) and (kind is None) and
            (id is None) and (label is None) and (nr is None)):
            raise ValueError(
                "at least one argument must be supplied to specify control")
        if nr is None: nr = 0

        return self._find_control(name, type, kind, id, label, 
                                  is_listcontrol, nr)

    def _find_control(self, name, type, kind, id, label, predicate, nr):
        if (name is not None) and not isstringlike(name):
            raise TypeError("control name must be string-like")
        if (type is not None) and not isstringlike(type):
            raise TypeError("control type must be string-like")
        if (kind is not None) and not isstringlike(kind):
            raise TypeError("control kind must be string-like")
        if (id is not None) and not isstringlike(id):
            raise TypeError("control id must be string-like")
        if (label is not None) and not isstringlike(label):
            raise TypeError("control label must be string-like")
        if (predicate is not None) and not callable(predicate):
            raise TypeError("control predicate must be callable")
        if nr < 0: raise ValueError("control number must be a positive "
                                    "integer")

        orig_nr = nr

        for control in self.controls:
            if name is not None and name != control.name:
                continue
            if type is not None and type != control.type:
                continue
            if kind is not None and not control.is_of_kind(kind):
                continue
            if id is not None and id != control.id:
                continue
            if predicate and not predicate(control):
                continue
            if label:
                for l in control.getLabels():
                    if l.text.find(label) > -1:
                        break
                else:
                    continue
            if nr:
                nr = nr - 1
                continue
            return control

        description = []
        if name is not None: description.append("name '%s'" % name)
        if type is not None: description.append("type '%s'" % type)
        if kind is not None: description.append("kind '%s'" % kind)
        if id is not None: description.append("id '%s'" % id)
        if label is not None: description.append("label '%s'" % label)
        if predicate is not None:
            description.append("predicate %s" % predicate)
        if orig_nr: description.append("nr %d" % orig_nr)
        description = string.join(description, ", ")
        raise ControlNotFoundError("no control matching "+description)

    def _click(self, name, type, id, label, nr, coord, return_type,
               request_class=urllib2.Request):
        try:
            control = self._find_control(
                name, type, "clickable", id, label, None, nr)
        except ControlNotFoundError:
            if ((name is not None) or (type is not None) or (id is not None) or
                (nr != 0)):
                raise
            # no clickable controls, but no control was explicitly requested,
            # so return state without clicking any control
            return self._switch_click(return_type, request_class)
        else:
            return control._click(self, coord, return_type, request_class)

    def _pairs(self):
        """Return sequence of (key, value) pairs suitable for urlencoding."""
        pairs = []
        for control in self.controls:
            pairs.extend(control.pairs())
        return pairs

    def _request_data(self):
        """Return a tuple (url, data, headers)."""
        method = string.upper(self.method)
        #scheme, netloc, path, parameters, query, frag = urlparse.urlparse(self.action)
        parts = urlparse.urlparse(self.action)
        rest, (query, frag) = parts[:-2], parts[-2:]

        if method == "GET":
            if self.enctype != "application/x-www-form-urlencoded":
                raise ValueError(
                    "unknown GET form encoding type '%s'" % self.enctype)
            parts = rest + (urlencode(self._pairs()), "")
            uri = urlparse.urlunparse(parts)
            return uri, None, []
        elif method == "POST":
            parts = rest + (query, "")
            uri = urlparse.urlunparse(parts)
            if self.enctype == "application/x-www-form-urlencoded":
                return (uri, urlencode(self._pairs()),
                        [("Content-type", self.enctype)])
            elif self.enctype == "multipart/form-data":
                data = StringIO()
                http_hdrs = []
                mw = MimeWriter(data, http_hdrs)
                f = mw.startmultipartbody("form-data", add_to_http_hdrs=True,
                                          prefix=0)
                for control in self.controls:
                    control._write_mime_data(mw)
                mw.lastpart()
                return uri, data.getvalue(), http_hdrs
            else:
                raise ValueError(
                    "unknown POST form encoding type '%s'" % self.enctype)
        else:
            raise ValueError("Unknown method '%s'" % method)

    def _switch_click(self, return_type, request_class=urllib2.Request):
        # This is called by HTMLForm and clickable Controls to hide switching
        # on return_type.
        if return_type == "pairs":
            return self._pairs()
        elif return_type == "request_data":
            return self._request_data()
        else:
            req_data = self._request_data()
            req = request_class(req_data[0], req_data[1])
            for key, val in req_data[2]:
                req.add_header(key, val)
            return req
