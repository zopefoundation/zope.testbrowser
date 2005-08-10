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
"""Browser-like functional doctest interfaces

$Id$
"""
__docformat__ = "reStructuredText"

import zope.interface
import zope.schema

class AmbiguityError(Exception):
    pass

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
        description=u"Describes whether this control can hold multiple values.",
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
        # TODO: currently only implemented for select by ClientForm
        title=u"Options",
        description=u"""\
        A list of possible display values for the control.""",
        required=True)

    displayValue = zope.schema.Field(
        # TODO: currently only implemented for select by ClientForm
        title=u"Value",
        description=u"The value of the control, as rendered by the display",
        default=None,
        required=True)

class ISubmitControl(IControl):

    def click():
        "click the submit button"

class IImageSubmitControl(ISubmitControl):

    def click(coord=(1,1,)):
        "click the submit button with optional coordinates"

class ISubcontrol(zope.interface.Interface):
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

    value = zope.schema.Bool(
        title=u"Value",
        description=u"Whether the subcontrol is selected",
        default=None,
        required=True)

class IFormsMapping(zope.interface.common.mapping.IReadMapping):
    """A mapping of all forms in a page."""


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

    def get(label=None, name=None, index=None):
        """Get a control in the page.

        Only one of ``label`` and ``name`` may be provided.  ``label``
        searches form labels (including submit button values, per the HTML 4.0
        spec), and ``name`` searches form field names.

        If no values are found, the code raises a LookupError.

        If ``index`` is None (the default) and more than one field matches the
        search, the code raises an AmbiguityError.  If an index is provided,
        it is used to choose the index from the ambiguous choices.  If the
        index does not exist, the code raises a LookupError.
        """

    def submit(label=None, name=None, index=None, coord=(1,1)):
        """Submit this form.

        The `text`, `id`, and `name` arguments select the submit button to use
        to submit the form.  You may use zero or one of them.

        The control code works identically to 'get' except that searches are
        filtered to find only submit and image controls.
        """
    

class IBrowser(zope.interface.Interface):
    """A Test Web Browser."""

    url = zope.schema.URI(
        title=u"URL",
        description=u"The URL the browser is currently showing.",
        required=True)

    headers = zope.schema.Field(
        title=u"Headers",
        description=u"Heards of the HTTP response; a ``httplib.HTTPMessage``.",
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

    forms = zope.schema.Object(
        title=u"Forms",
        description=(u"A mapping of form elements on the page. The key is "
                     u"actually quiet flexible and searches the id and name "
                     u"of the form element."),
        schema=IFormsMapping,
        required=True)

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

    def click(text=None, url=None, id=None):
        """Click on a link in the page.

        This method opens a new URL that is behind the link. The link itself
        is described by the arguments of the method:

          o ``text`` -- A regular expression trying to match the link's text,
            in other words everything between <a> and </a> or the value of the
            submit button.

          o ``url`` -- The URL the link is going to. This is either the
            ``href`` attribute of an anchor tag or the action of a form.

          o ``id`` -- The id attribute of the anchor tag submit button.
        """

    def get(label=None, name=None, index=None):
        """Get a control in the page.

        Only one of ``label`` and ``name`` may be provided.  ``label``
        searches form labels (including submit button values, per the HTML 4.0
        spec), and ``name`` searches form field names.

        If no values are found, the code raises a LookupError.

        If ``index`` is None (the default) and more than one field matches the
        search, the code raises an AmbiguityError.  If an index is provided,
        it is used to choose the index from the ambiguous choices.  If the
        index does not exist, the code raises a LookupError.
        """
