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
"""Browser-like functional doctest interfaces
"""

import zope.interface
import zope.schema
import zope.interface.common.mapping


__docformat__ = "reStructuredText"


class AlreadyExpiredError(ValueError):
    pass


class ICookies(zope.interface.common.mapping.IExtendedReadMapping,
               zope.interface.common.mapping.IExtendedWriteMapping,
               zope.interface.common.mapping.IMapping):  # NOT copy
    """A mapping of cookies for a given url"""

    url = zope.schema.URI(
        title=u"URL",
        description=u"The URL the mapping is currently exposing.",
        required=True)

    header = zope.schema.TextLine(
        title=u"Header",
        description=u"The current value for the Cookie header for the URL",
        required=True)

    def forURL(url):
        """Returns another ICookies instance for the given URL."""

    def getinfo(name):
        """returns dict of settings for the given cookie name.

        This includes only the following cookie values:

        - name (str)
        - value (str),
        - port (int or None),
        - domain (str),
        - path (str or None),
        - secure (bool), and
        - expires (datetime.datetime with pytz.UTC timezone or None),
        - comment (str or None),
        - commenturl (str or None).

        (Method name is not camelCase because it is intended to feel like an
        extension to the mapping interface, which uses all lower case, e.g.
        iterkeys.)
        """

    def iterinfo(name=None):
        """iterate over the information about all the cookies for the URL.

        Each result is a dictionary as described for ``getinfo``.

        If name is given, iterates over all cookies for given name.

        (Method name is not camelCase because it is intended to feel like an
        extension to the mapping interface, which uses all lower case, e.g.
        iterkeys.)
        """

    def create(name, value,
               domain=None, expires=None, path=None, secure=None, comment=None,
               commenturl=None, port=None):
        """Create a new cookie with the given values.

        If cookie of the same name, domain, and path exists, raises a
        ValueError.

        Expires is a string or a datetime.datetime.  timezone-naive datetimes
        are interpreted as in UTC.  If expires is before now, raises
        AlreadyExpiredError.

        If the domain or path do not generally match the current URL, raises
        ValueError.
        """

    def change(name, value=None, domain=None, expires=None, path=None,
               secure=None, comment=None, commenturl=None, port=None):
        """Change an attribute of an existing cookie.

        If cookie does not exist, raises a KeyError."""

    def clearAll():
        """Clear all cookies for the associated browser, irrespective of URL
        """

    def clearAllSession():
        """Clear session cookies for associated browser, irrespective of URL
        """


class IBrowser(zope.interface.Interface):
    """A Programmatic Web Browser."""

    cookies = zope.schema.Field(
        title=u"Cookies",
        description=(u"An ICookies mapping for the browser's current URL."),
        required=True)

    url = zope.schema.URI(
        title=u"URL",
        description=u"The URL the browser is currently showing.",
        required=True)

    headers = zope.schema.Field(
        title=u"Headers",
        description=(u"Headers of the HTTP response; a "
                     "``httplib.HTTPMessage``."),
        required=True)

    contents = zope.schema.Text(
        title=u"Contents",
        description=u"The complete response body of the HTTP request.",
        required=True)

    isHtml = zope.schema.Bool(
        title=u"Is HTML",
        description=u"Tells whether the output is HTML or not.",
        required=True)

    title = zope.schema.TextLine(
        title=u"Title",
        description=u"Title of the displayed page",
        required=False)

    handleErrors = zope.schema.Bool(
        title=u"Handle Errors",
        description=(u"Describes whether server-side errors will be handled "
                     u"by the publisher. If set to ``False``, the error will "
                     u"progress all the way to the test, which is good for "
                     u"debugging."),
        default=True,
        required=True)

    def addHeader(key, value):
        """Adds a header to each HTTP request.

        Adding additional headers can be useful in many ways, from setting the
        credentials token to specifying the browser identification string.
        """

    def open(url, data=None):
        """Open a URL in the browser.

        The URL must be fully qualified. However, note that the server name
        and port is arbitrary for Zope 3 functional tests, since the request
        is sent to the publisher directly.

        The ``data`` argument describes the data that will be sent as the body
        of the request.
        """

    def reload():
        """Reload the current page.

        Like a browser reload, if the past request included a form submission,
        the form data will be resubmitted."""

    def goBack(count=1):
        """Go back in history by a certain amount of visisted pages.

        The ``count`` argument specifies how far to go back. It is set to 1 by
        default.
        """

    def getLink(text=None, url=None, id=None, index=0):
        """Return an ILink from the page.

        The link is found by the arguments of the method.  One or more may be
        used together.

          o ``text`` -- A regular expression trying to match the link's text,
            in other words everything between <a> and </a> or the value of the
            submit button.

          o ``url`` -- The URL the link is going to. This is either the
            ``href`` attribute of an anchor tag or the action of a form.

          o ``id`` -- The id attribute of the anchor tag submit button.

          o ``index`` -- When there's more than one link that matches the
            text/URL, you can specify which one you want.

        """

    lastRequestSeconds = zope.schema.Field(
        title=u"Seconds to Process Last Request",
        description=(
            u"""Return how many seconds (or fractions) the last request took.

        The values returned have the same resolution as the results from
        ``time.clock``.
        """),
        required=True,
        readonly=True)

    lastRequestPystones = zope.schema.Field(
        title=u"Approximate System-Independent Effort of Last Request "
              u"(Pystones)",
        description=(u"""Return how many pystones the last request took.

        This number is found by multiplying the number of pystones/second at
        which this system benchmarks and the result of ``lastRequestSeconds``.
        """),
        required=True,
        readonly=True)

    def getControl(label=None, name=None, index=None):
        """Get a control from the page.

        Only one of ``label`` and ``name`` may be provided.  ``label``
        searches form labels (including submit button values, per the HTML 4.0
        spec), and ``name`` searches form field names.

        Label value is searched as case-sensitive whole words within
        the labels for each control--that is, a search for 'Add' will match
        'Add a contact' but not 'Address'.  A word is defined as one or more
        alphanumeric characters or the underline.

        If no values are found, the code raises a LookupError.

        If ``index`` is None (the default) and more than one field matches the
        search, the code raises an AmbiguityError.  If an index is provided,
        it is used to choose the index from the ambiguous choices.  If the
        index does not exist, the code raises a LookupError.
        """

    def getForm(id=None, name=None, action=None, index=None):
        """Get a form from the page.

        Zero or one of ``id``, ``name``, and ``action`` may be provided.  If
        none are provided the index alone is used to determine the return
        value.

        If no values are found, the code raises a LookupError.

        If ``index`` is None (the default) and more than one form matches the
        search, the code raises an AmbiguityError.  If an index is provided,
        it is used to choose the index from the ambiguous choices.  If the
        index does not exist, the code raises a LookupError.
        """


class ExpiredError(Exception):
    """The browser page to which this was attached is no longer active"""


class IControl(zope.interface.Interface):
    """A control (input field) of a page."""

    name = zope.schema.TextLine(
        title=u"Name",
        description=u"The name of the control.",
        required=True)

    value = zope.schema.Field(
        title=u"Value",
        description=u"The value of the control",
        default=None,
        required=True)

    type = zope.schema.Choice(
        title=u"Type",
        description=u"The type of the control",
        values=['text', 'password', 'hidden', 'submit', 'checkbox', 'select',
                'radio', 'image', 'file'],
        required=True)

    disabled = zope.schema.Bool(
        title=u"Disabled",
        description=u"Describes whether a control is disabled.",
        default=False,
        required=False)

    multiple = zope.schema.Bool(
        title=u"Multiple",
        description=(
            u"Describes whether this control can hold multiple values."),
        default=False,
        required=False)

    def clear():
        """Clear the value of the control."""


class IListControl(IControl):
    """A radio button, checkbox, or select control"""

    options = zope.schema.List(
        title=u"Options",
        description=u"""\
        A list of possible values for the control.""",
        required=True)

    displayOptions = zope.schema.List(
        # TODO: currently only implemented for select
        title=u"Options",
        description=u"""\
        A list of possible display values for the control.""",
        required=True)

    displayValue = zope.schema.Field(
        # TODO: currently only implemented for select
        title=u"Value",
        description=u"The value of the control, as rendered by the display",
        default=None,
        required=True)

    def getControl(label=None, value=None, index=None):
        """return subcontrol for given label or value, disambiguated by index
        if given.  Label value is searched as case-sensitive whole words within
        the labels for each item--that is, a search for 'Add' will match
        'Add a contact' but not 'Address'.  A word is defined as one or more
        alphanumeric characters or the underline."""

    controls = zope.interface.Attribute(
        """a list of subcontrols for the control.  mutating list has no effect
        on control (although subcontrols may be changed as usual).""")


class ISubmitControl(IControl):

    def click():
        "click the submit button"


class IImageSubmitControl(ISubmitControl):

    def click(coord=(1, 1)):
        "click the submit button with optional coordinates"


class IItemControl(zope.interface.Interface):
    """a radio button or checkbox within a larger multiple-choice control"""

    control = zope.schema.Object(
        title=u"Control",
        description=(u"The parent control element."),
        schema=IControl,
        required=True)

    disabled = zope.schema.Bool(
        title=u"Disabled",
        description=u"Describes whether a subcontrol is disabled.",
        default=False,
        required=False)

    selected = zope.schema.Bool(
        title=u"Selected",
        description=u"Whether the subcontrol is selected",
        default=None,
        required=True)

    optionValue = zope.schema.TextLine(
        title=u"Value",
        description=u"The value of the subcontrol",
        default=None,
        required=False)


class ILink(zope.interface.Interface):

    def click():
        """click the link, going to the URL referenced"""

    url = zope.schema.TextLine(
        title=u"URL",
        description=u"The normalized URL of the link",
        required=False)

    attrs = zope.schema.Dict(
        title=u'Attributes',
        description=u'The attributes of the link tag',
        required=False)

    text = zope.schema.TextLine(
        title=u'Text',
        description=u'The contained text of the link',
        required=False)

    tag = zope.schema.TextLine(
        title=u'Tag',
        description=u'The tag name of the link (a or area, typically)',
        required=True)


class IForm(zope.interface.Interface):
    """An HTML form of the page."""

    action = zope.schema.TextLine(
        title=u"Action",
        description=u"The action (or URI) that is opened upon submittance.",
        required=True)

    method = zope.schema.Choice(
        title=u"Method",
        description=u"The method used to submit the form.",
        values=['post', 'get', 'put'],
        required=True)

    enctype = zope.schema.TextLine(
        title=u"Encoding Type",
        description=u"The type of encoding used to encode the form data.",
        required=True)

    name = zope.schema.TextLine(
        title=u"Name",
        description=u"The value of the `name` attribute in the form tag, "
                    u"if specified.",
        required=True)

    id = zope.schema.TextLine(
        title=u"Id",
        description=u"The value of the `id` attribute in the form tag, "
                    u"if specified.",
        required=True)

    def getControl(label=None, name=None, index=None):
        """Get a control in the page.

        Only one of ``label`` and ``name`` may be provided.  ``label``
        searches form labels (including submit button values, per the HTML 4.0
        spec), and ``name`` searches form field names.

        Label value is searched as case-sensitive whole words within
        the labels for each control--that is, a search for 'Add' will match
        'Add a contact' but not 'Address'.  A word is defined as one or more
        alphanumeric characters or the underline.

        If no values are found, the code raises a LookupError.

        If ``index`` is None (the default) and more than one field matches the
        search, the code raises an AmbiguityError.  If an index is provided,
        it is used to choose the index from the ambiguous choices.  If the
        index does not exist, the code raises a LookupError.
        """

    def submit(label=None, name=None, index=None, coord=(1, 1)):
        """Submit this form.

        The `label`, `name`, and `index` arguments select the submit button to
        use to submit the form.  You may label or name, with index to
        disambiguate.

        Label value is searched as case-sensitive whole words within
        the labels for each control--that is, a search for 'Add' will match
        'Add a contact' but not 'Address'.  A word is defined as one or more
        alphanumeric characters or the underline.

        The control code works identically to 'get' except that searches are
        filtered to find only submit and image controls.
        """
