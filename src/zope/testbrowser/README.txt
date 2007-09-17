Detailed Documentation
======================

Before being of much interest, we need to open a web page.  ``Browser``
instances have a ``base`` attribute that sets the URL from which ``open``ed
URLs are relative.  This lets you target tests at servers running in various,
or even variable locations (like using randomly chosen ports).

    >>> browser = Browser()
    >>> browser.base = 'http://localhost:%s/' % TEST_PORT
    >>> browser.open('index.html')
    >>> browser.url
    'http://localhost:.../index.html'

Once you have opened a web page initially, best practice for writing
testbrowser doctests suggests using 'click' to navigate further (as discussed
below), except in unusual circumstances.

The test browser complies with the IBrowser interface; see
``zope.testbrowser.interfaces`` for full details on the interface.

    >>> import zope.testbrowser.interfaces
    >>> from zope.interface.verify import verifyObject
    >>> zope.testbrowser.interfaces.IBrowser.providedBy(browser)
    True


Page Contents
-------------

The contents of the current page are available:

    >>> browser.contents
    '...<h1>Simple Page</h1>...'

Note: Unfortunately, ellipsis (...) cannot be used at the beginning of the
output (this is a limitation of doctest).

Making assertions about page contents is easy.

    >>> '<h1>Simple Page</h1>' in browser.contents
    True


Checking for HTML
-----------------

Not all URLs return HTML.  Of course our simple page does:

    >>> browser.isHtml
    True

But if we load an image (or other binary file), we do not get HTML:

    >>> browser.open('zope3logo.gif')
    >>> browser.isHtml
    False


HTML Page Title
----------------

Another useful helper property is the title:

    >>> browser.open('index.html')
    >>> browser.title
    'Simple Page'

If a page does not provide a title, it is simply ``None``:

    >>> browser.open('notitle.html')
    >>> browser.title

However, if the output is not HTML, then an error will occur trying to access
the title:

    >>> browser.open('zope3logo.gif')
    >>> browser.title
    Traceback (most recent call last):
    ...
    BrowserStateError: not viewing HTML


Navigation and Link Objects
---------------------------

If you want to simulate clicking on a link, get the link and call its `click`
method.  In the `navigate.html` file there are several links set up to
demonstrate the capabilities of the link objects and their `click` method.

The simplest way to get a link is via the anchor text.  In other words
the text you would see in a browser (text and url searches are substring
searches):

    >>> browser.open('navigate.html')
    >>> browser.contents
    '...<a href="target.html">Link Text</a>...'
    >>> link = browser.getLink('Link Text')
    >>> link
    <Link text='Link Text' url='http://localhost:.../target.html'>

Link objects comply with the ILink interface.

    >>> verifyObject(zope.testbrowser.interfaces.ILink, link)
    True

Links expose several attributes for easy access.

    >>> link.text
    'Link Text'
    >>> link.tag # links can also be image maps.
    'a'
    >>> link.url # normalized to an absolute URL
    'http://localhost:.../target.html'
    >>> link.attrs
    {'href': 'target.html'}

Links can be "clicked" and the browser will navigate to the referenced URL.

    >>> link.click()
    >>> browser.url
    'http://localhost:.../target.html'
    >>> browser.contents
    '...This page is the target of a link...'

When finding a link by its text, whitespace is normalized.

    >>> browser.open('navigate.html')
    >>> browser.contents
    '...> Link Text \n    with     Whitespace\tNormalization (and parens) </...'
    >>> link = browser.getLink('Link Text with Whitespace Normalization '
    ...                        '(and parens)')
    >>> link
    <Link text='Link Text with Whitespace Normalization (and parens)'...>
    >>> link.text
    'Link Text with Whitespace Normalization (and parens)'
    >>> link.click()
    >>> browser.url
    'http://localhost:.../target.html'

When a link text matches more than one link, by default the first one is
chosen. You can, however, specify the index of the link and thus retrieve a
later matching link:

    >>> browser.open('navigate.html')
    >>> browser.getLink('Link Text')
    <Link text='Link Text' ...>

    >>> browser.getLink('Link Text', index=1)
    <Link text='Link Text with Whitespace Normalization (and parens)' ...>

Note that clicking a link object after its browser page has expired will
generate an error.

    >>> link.click()
    Traceback (most recent call last):
    ...
    ExpiredError

You can also find links by URL,

    >>> browser.open('navigate.html')
    >>> browser.getLink(url='target.html').click()
    >>> browser.url
    'http://localhost:.../target.html'

or its id:

    >>> browser.open('navigate.html')
    >>> browser.contents
    '...<a href="target.html" id="anchorid">By Anchor Id</a>...'

    >>> browser.getLink(id='anchorid').click()
    >>> browser.url
    'http://localhost:.../target.html'

You thought we were done here? Not so quickly.  The `getLink` method also
supports image maps, though not by specifying the coordinates, but using the
area's id:

    >>> browser.open('navigate.html')
    >>> link = browser.getLink(id='zope3')
    >>> link.tag
    'area'
    >>> link.click()
    >>> browser.url
    'http://localhost:.../target.html'

Getting a nonexistent link raises an exception.

    >>> browser.open('navigate.html')
    >>> browser.getLink('This does not exist')
    Traceback (most recent call last):
    ...
    LinkNotFoundError


Other Navigation
----------------

Like in any normal browser, you can reload a page:

    >>> browser.open('index.html')
    >>> browser.url
    'http://localhost:.../index.html'
    >>> browser.reload()
    >>> browser.url
    'http://localhost:.../index.html'

You can also go back:

    >>> browser.open('notitle.html')
    >>> browser.url
    'http://localhost:.../notitle.html'
    >>> browser.goBack()
    >>> browser.url
    'http://localhost:.../index.html'


Controls
--------

One of the most important features of the browser is the ability to inspect
and fill in values for the controls of input forms.  To do so, let's first open
a page that has a bunch of controls:

    >>> browser.open('controls.html')

Obtaining a Control
~~~~~~~~~~~~~~~~~~~

You look up browser controls with the 'getControl' method.  The default first
argument is 'label', and looks up the form on the basis of any associated
label.

    >>> control = browser.getControl('Text Control')
    >>> control
    <Control name='text-value' type='text'>
    >>> browser.getControl(label='Text Control') # equivalent
    <Control name='text-value' type='text'>

If you request a control that doesn't exist, the code raises a LookupError:

    >>> browser.getControl('Does Not Exist')
    Traceback (most recent call last):
    ...
    LookupError: label 'Does Not Exist'

If you request a control with an ambiguous lookup, the code raises an
AmbiguityError.

    >>> browser.getControl('Ambiguous Control')
    Traceback (most recent call last):
    ...
    AmbiguityError: label 'Ambiguous Control'

This is also true if an option in a control is ambiguous in relation to
the control itself.

    >>> browser.getControl('Sub-control Ambiguity')
    Traceback (most recent call last):
    ...
    AmbiguityError: label 'Sub-control Ambiguity'

Ambiguous controls may be specified using an index value.  We use the control's
value attribute to show the two controls; this attribute is properly introduced
below.

    >>> browser.getControl('Ambiguous Control', index=0)
    <Control name='ambiguous-control-name' type='text'>
    >>> browser.getControl('Ambiguous Control', index=0).value
    'First'
    >>> browser.getControl('Ambiguous Control', index=1).value
    'Second'
    >>> browser.getControl('Sub-control Ambiguity', index=0)
    <ListControl name='ambiguous-subcontrol' type='select'>
    >>> browser.getControl('Sub-control Ambiguity', index=1).optionValue
    'ambiguous'

Label searches are against stripped, whitespace-normalized, no-tag versions of
the text. Text applied to searches is also stripped and whitespace normalized.
The search finds results if the text search finds the whole words of your
text in a label.  Thus, for instance, a search for 'Add' will match the label
'Add a Client' but not 'Address'.  Case is honored.

    >>> browser.getControl('Label Needs Whitespace Normalization')
    <Control name='label-needs-normalization' type='text'>
    >>> browser.getControl('label needs whitespace normalization')
    Traceback (most recent call last):
    ...
    LookupError: label 'label needs whitespace normalization'
    >>> browser.getControl(' Label  Needs Whitespace    ')
    <Control name='label-needs-normalization' type='text'>
    >>> browser.getControl('Whitespace')
    <Control name='label-needs-normalization' type='text'>
    >>> browser.getControl('hitespace')
    Traceback (most recent call last):
    ...
    LookupError: label 'hitespace'
    >>> browser.getControl('[non word characters should not confuse]')
    <Control name='non-word-characters' type='text'>

Multiple labels can refer to the same control (simply because that is possible
in the HTML 4.0 spec).

    >>> browser.getControl('Multiple labels really')
    <Control name='two-labels' type='text'>
    >>> browser.getControl('really are possible')
    <Control name='two-labels' type='text'>
    >>> browser.getControl('really') # OK: ambiguous labels, but not ambiguous control
    <Control name='two-labels' type='text'>

A label can be connected with a control using the 'for' attribute and also by
containing a control.

    >>> browser.getControl(
    ...     'Labels can be connected by containing their respective fields')
    <Control name='contained-in-label' type='text'>

Get also accepts one other search argument, 'name'.  Only one of 'label' and
'name' may be used at a time.  The 'name' keyword searches form field names.

    >>> browser.getControl(name='text-value')
    <Control name='text-value' type='text'>
    >>> browser.getControl(name='ambiguous-control-name')
    Traceback (most recent call last):
    ...
    AmbiguityError: name 'ambiguous-control-name'
    >>> browser.getControl(name='does-not-exist')
    Traceback (most recent call last):
    ...
    LookupError: name 'does-not-exist'
    >>> browser.getControl(name='ambiguous-control-name', index=1).value
    'Second'

Combining 'label' and 'name' raises a ValueError, as does supplying neither of
them.

    >>> browser.getControl(label='Ambiguous Control', name='ambiguous-control-name')
    Traceback (most recent call last):
    ...
    ValueError: Supply one and only one of "label" and "name" as arguments
    >>> browser.getControl()
    Traceback (most recent call last):
    ...
    ValueError: Supply one and only one of "label" and "name" as arguments

Radio and checkbox fields are unusual in that their labels and names may point
to different objects: names point to logical collections of radio buttons or
checkboxes, but labels may only be used for individual choices within the
logical collection.  This means that obtaining a radio button by label gets a
different object than obtaining the radio collection by name.  Select options
may also be searched by label.

    >>> browser.getControl(name='radio-value')
    <ListControl name='radio-value' type='radio'>
    >>> browser.getControl('Zwei')
    <ItemControl name='radio-value' type='radio' optionValue='2' selected=True>
    >>> browser.getControl('One')
    <ItemControl name='multi-checkbox-value' type='checkbox' optionValue='1' selected=True>
    >>> browser.getControl('Tres')
    <ItemControl name='single-select-value' type='select' optionValue='3' selected=False>

Characteristics of controls and subcontrols are discussed below.

Control Objects
~~~~~~~~~~~~~~~

Controls provide IControl.

    >>> ctrl = browser.getControl('Text Control')
    >>> ctrl
    <Control name='text-value' type='text'>
    >>> verifyObject(zope.testbrowser.interfaces.IControl, ctrl)
    True

They have several useful attributes:

  - the name as which the control is known to the form:

    >>> ctrl.name
    'text-value'

  - the value of the control, which may also be set:

    >>> ctrl.value
    'Some Text'
    >>> ctrl.value = 'More Text'
    >>> ctrl.value
    'More Text'

  - the type of the control:

    >>> ctrl.type
    'text'

  - a flag describing whether the control is disabled:

    >>> ctrl.disabled
    False

  - and a flag to tell us whether the control can have multiple values:

    >>> ctrl.multiple
    False

Additionally, controllers for select, radio, and checkbox provide IListControl.
These fields have four other attributes and an additional method:

    >>> ctrl = browser.getControl('Multiple Select Control')
    >>> ctrl
    <ListControl name='multi-select-value' type='select'>
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    True
    >>> verifyObject(zope.testbrowser.interfaces.IListControl, ctrl)
    True

  - 'options' lists all available value options.

    >>> ctrl.options
    ['1', '2', '3']

  - 'displayOptions' lists all available options by label.  The 'label'
    attribute on an option has precedence over its contents, which is why
    our last option is 'Third' in the display.

    >>> ctrl.displayOptions
    ['Un', 'Deux', 'Third']

  - 'displayValue' lets you get and set the displayed values of the control
    of the select box, rather than the actual values.

    >>> ctrl.value
    []
    >>> ctrl.displayValue
    []
    >>> ctrl.displayValue = ['Un', 'Deux']
    >>> ctrl.displayValue
    ['Un', 'Deux']
    >>> ctrl.value
    ['1', '2']

  - 'controls' gives you a list of the subcontrol objects in the control
    (subcontrols are discussed below).

    >>> ctrl.controls
    [<ItemControl name='multi-select-value' type='select' optionValue='1' selected=True>,
     <ItemControl name='multi-select-value' type='select' optionValue='2' selected=True>,
     <ItemControl name='multi-select-value' type='select' optionValue='3' selected=False>]

  - The 'getControl' method lets you get subcontrols by their label or their value.

    >>> ctrl.getControl('Un')
    <ItemControl name='multi-select-value' type='select' optionValue='1' selected=True>
    >>> ctrl.getControl('Deux')
    <ItemControl name='multi-select-value' type='select' optionValue='2' selected=True>
    >>> ctrl.getControl('Trois') # label attribute
    <ItemControl name='multi-select-value' type='select' optionValue='3' selected=False>
    >>> ctrl.getControl('Third') # contents
    <ItemControl name='multi-select-value' type='select' optionValue='3' selected=False>
    >>> browser.getControl('Third') # ambiguous in the browser, so useful
    Traceback (most recent call last):
    ...
    AmbiguityError: label 'Third'

Finally, submit controls provide ISubmitControl, and image controls provide
IImageSubmitControl, which extents ISubmitControl.  These both simply add a
'click' method.  For image submit controls, you may also provide a coordinates
argument, which is a tuple of (x, y).  These submit the forms, and are
demonstrated below as we examine each control individually.

ItemControl Objects
~~~~~~~~~~~~~~~~~~~

As introduced briefly above, using labels to obtain elements of a logical
radio button or checkbox collection returns item controls, which are parents.
Manipulating the value of these controls affects the parent control.

    >>> browser.getControl(name='radio-value').value
    ['2']
    >>> browser.getControl('Zwei').optionValue # read-only.
    '2'
    >>> browser.getControl('Zwei').selected
    True
    >>> verifyObject(zope.testbrowser.interfaces.IItemControl,
    ...     browser.getControl('Zwei'))
    True
    >>> browser.getControl('Ein').selected = True
    >>> browser.getControl('Ein').selected
    True
    >>> browser.getControl('Zwei').selected
    False
    >>> browser.getControl(name='radio-value').value
    ['1']
    >>> browser.getControl('Ein').selected = False
    >>> browser.getControl(name='radio-value').value
    []
    >>> browser.getControl('Zwei').selected = True

Checkbox collections behave similarly, as shown below.

Controls with subcontrols--

Various Controls
~~~~~~~~~~~~~~~~

The various types of controls are demonstrated here.

  - Text Control

    The text control we already introduced above.

  - Password Control

    >>> ctrl = browser.getControl('Password Control')
    >>> ctrl
    <Control name='password-value' type='password'>
    >>> verifyObject(zope.testbrowser.interfaces.IControl, ctrl)
    True
    >>> ctrl.value
    'Password'
    >>> ctrl.value = 'pass now'
    >>> ctrl.value
    'pass now'
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False

  - Hidden Control

    >>> ctrl = browser.getControl(name='hidden-value')
    >>> ctrl
    <Control name='hidden-value' type='hidden'>
    >>> verifyObject(zope.testbrowser.interfaces.IControl, ctrl)
    True
    >>> ctrl.value
    'Hidden'
    >>> ctrl.value = 'More Hidden'
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False

  - Text Area Control

    >>> ctrl = browser.getControl('Text Area Control')
    >>> ctrl
    <Control name='textarea-value' type='textarea'>
    >>> verifyObject(zope.testbrowser.interfaces.IControl, ctrl)
    True
    >>> ctrl.value
    '        Text inside\n        area!\n      '
    >>> ctrl.value = 'A lot of\n text.'
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False

  - File Control

    File controls are used when a form has a file-upload field.
    To specify data, call the add_file method, passing:

    - A file-like object

    - a content type, and

    - a file name

    >>> ctrl = browser.getControl('File Control')
    >>> ctrl
    <Control name='file-value' type='file'>
    >>> verifyObject(zope.testbrowser.interfaces.IControl, ctrl)
    True
    >>> ctrl.value is None
    True
    >>> import cStringIO

    >>> ctrl.add_file(cStringIO.StringIO('File contents'),
    ...               'text/plain', 'test.txt')

    The file control (like the other controls) also knows if it is disabled
    or if it can have multiple values.

    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False

  - Selection Control (Single-Valued)

    >>> ctrl = browser.getControl('Single Select Control')
    >>> ctrl
    <ListControl name='single-select-value' type='select'>
    >>> verifyObject(zope.testbrowser.interfaces.IListControl, ctrl)
    True
    >>> ctrl.value
    ['1']
    >>> ctrl.value = ['2']
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False
    >>> ctrl.options
    ['1', '2', '3']
    >>> ctrl.displayOptions
    ['Uno', 'Dos', 'Third']
    >>> ctrl.displayValue
    ['Dos']
    >>> ctrl.displayValue = ['Tres']
    >>> ctrl.displayValue
    ['Third']
    >>> ctrl.displayValue = ['Dos']
    >>> ctrl.displayValue
    ['Dos']
    >>> ctrl.displayValue = ['Third']
    >>> ctrl.displayValue
    ['Third']
    >>> ctrl.value
    ['3']

  - Selection Control (Multi-Valued)

    This was already demonstrated in the introduction to control objects above.

  - Checkbox Control (Single-Valued; Unvalued)

    >>> ctrl = browser.getControl(name='single-unvalued-checkbox-value')
    >>> ctrl
    <ListControl name='single-unvalued-checkbox-value' type='checkbox'>
    >>> verifyObject(zope.testbrowser.interfaces.IListControl, ctrl)
    True
    >>> ctrl.value
    True
    >>> ctrl.value = False
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    True
    >>> ctrl.options
    [True]
    >>> ctrl.displayOptions
    ['Single Unvalued Checkbox']
    >>> ctrl.displayValue
    []
    >>> verifyObject(
    ...     zope.testbrowser.interfaces.IItemControl,
    ...     browser.getControl('Single Unvalued Checkbox'))
    True
    >>> browser.getControl('Single Unvalued Checkbox').optionValue
    'on'
    >>> browser.getControl('Single Unvalued Checkbox').selected
    False
    >>> ctrl.displayValue = ['Single Unvalued Checkbox']
    >>> ctrl.displayValue
    ['Single Unvalued Checkbox']
    >>> browser.getControl('Single Unvalued Checkbox').selected
    True
    >>> browser.getControl('Single Unvalued Checkbox').selected = False
    >>> browser.getControl('Single Unvalued Checkbox').selected
    False
    >>> ctrl.displayValue
    []
    >>> browser.getControl(
    ...     name='single-disabled-unvalued-checkbox-value').disabled
    True

  - Checkbox Control (Single-Valued, Valued)

    >>> ctrl = browser.getControl(name='single-valued-checkbox-value')
    >>> ctrl
    <ListControl name='single-valued-checkbox-value' type='checkbox'>
    >>> verifyObject(zope.testbrowser.interfaces.IListControl, ctrl)
    True
    >>> ctrl.value
    ['1']
    >>> ctrl.value = []
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    True
    >>> ctrl.options
    ['1']
    >>> ctrl.displayOptions
    ['Single Valued Checkbox']
    >>> ctrl.displayValue
    []
    >>> verifyObject(
    ...     zope.testbrowser.interfaces.IItemControl,
    ...     browser.getControl('Single Valued Checkbox'))
    True
    >>> browser.getControl('Single Valued Checkbox').selected
    False
    >>> browser.getControl('Single Valued Checkbox').optionValue
    '1'
    >>> ctrl.displayValue = ['Single Valued Checkbox']
    >>> ctrl.displayValue
    ['Single Valued Checkbox']
    >>> browser.getControl('Single Valued Checkbox').selected
    True
    >>> browser.getControl('Single Valued Checkbox').selected = False
    >>> browser.getControl('Single Valued Checkbox').selected
    False
    >>> ctrl.displayValue
    []

  - Checkbox Control (Multi-Valued)

    >>> ctrl = browser.getControl(name='multi-checkbox-value')
    >>> ctrl
    <ListControl name='multi-checkbox-value' type='checkbox'>
    >>> verifyObject(zope.testbrowser.interfaces.IListControl, ctrl)
    True
    >>> ctrl.value
    ['1', '3']
    >>> ctrl.value = ['1', '2']
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    True
    >>> ctrl.options
    ['1', '2', '3']
    >>> ctrl.displayOptions
    ['One', 'Two', 'Three']
    >>> ctrl.displayValue
    ['One', 'Two']
    >>> ctrl.displayValue = ['Two']
    >>> ctrl.value
    ['2']
    >>> browser.getControl('Two').optionValue
    '2'
    >>> browser.getControl('Two').selected
    True
    >>> verifyObject(zope.testbrowser.interfaces.IItemControl,
    ...     browser.getControl('Two'))
    True
    >>> browser.getControl('Three').selected = True
    >>> browser.getControl('Three').selected
    True
    >>> browser.getControl('Two').selected
    True
    >>> ctrl.value
    ['2', '3']
    >>> browser.getControl('Two').selected = False
    >>> ctrl.value
    ['3']
    >>> browser.getControl('Three').selected = False
    >>> ctrl.value
    []

  - Radio Control

    This is how you get a radio button based control:

    >>> ctrl = browser.getControl(name='radio-value')

    This shows the existing value of the control, as it was in the
    HTML received from the server:

    >>> ctrl.value
    ['2']

    We can then unselect it:

    >>> ctrl.value = []
    >>> ctrl.value
    []

    We can also reselect it:

    >>> ctrl.value = ['2']
    >>> ctrl.value
    ['2']

    displayValue shows the text the user would see next to the
    control:

    >>> ctrl.displayValue
    ['Zwei']

    This is just unit testing:

    >>> ctrl
    <ListControl name='radio-value' type='radio'>
    >>> verifyObject(zope.testbrowser.interfaces.IListControl, ctrl)
    True
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False
    >>> ctrl.options
    ['1', '2', '3']
    >>> ctrl.displayOptions
    ['Ein', 'Zwei', 'Drei']
    >>> ctrl.displayValue = ['Ein']
    >>> ctrl.value
    ['1']
    >>> ctrl.displayValue
    ['Ein']

    The radio control subcontrols were illustrated above.

  - Image Control

    >>> ctrl = browser.getControl(name='image-value')
    >>> ctrl
    <ImageControl name='image-value' type='image'>
    >>> verifyObject(zope.testbrowser.interfaces.IImageSubmitControl, ctrl)
    True
    >>> ctrl.value
    ''
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False

  - Submit Control

    >>> ctrl = browser.getControl(name='submit-value')
    >>> ctrl
    <SubmitControl name='submit-value' type='submit'>
    >>> browser.getControl('Submit This') # value of submit button is a label
    <SubmitControl name='submit-value' type='submit'>
    >>> browser.getControl('Standard Submit Control') # label tag is legal
    <SubmitControl name='submit-value' type='submit'>
    >>> browser.getControl('Submit') # multiple labels, but same control
    <SubmitControl name='submit-value' type='submit'>
    >>> verifyObject(zope.testbrowser.interfaces.ISubmitControl, ctrl)
    True
    >>> ctrl.value
    'Submit This'
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False

Using Submitting Controls
~~~~~~~~~~~~~~~~~~~~~~~~~

Both the submit and image type should be clickable and submit the form:

    >>> browser.getControl('Text Control').value = 'Other Text'
    >>> browser.getControl('Submit').click()
    >>> browser.contents
    "...'text-value': ['Other Text']..."

Note that if you click a submit object after the associated page has expired,
you will get an error.

    >>> browser.open('controls.html')
    >>> ctrl = browser.getControl('Submit')
    >>> ctrl.click()
    >>> ctrl.click()
    Traceback (most recent call last):
    ...
    ExpiredError

All the above also holds true for the image control:

    >>> browser.open('controls.html')
    >>> browser.getControl('Text Control').value = 'Other Text'
    >>> browser.getControl(name='image-value').click()
    >>> browser.contents
    "...'text-value': ['Other Text']..."

    >>> browser.open('controls.html')
    >>> ctrl = browser.getControl(name='image-value')
    >>> ctrl.click()
    >>> ctrl.click()
    Traceback (most recent call last):
    ...
    ExpiredError

But when sending an image, you can also specify the coordinate you clicked:

    >>> browser.open('controls.html')
    >>> browser.getControl(name='image-value').click((50,25))
    >>> browser.contents
    "...'image-value.x': ['50']...'image-value.y': ['25']..."

Forms
-----

Because pages can have multiple forms with like-named controls, it is sometimes
necessary to access forms by name or id.  The browser's `forms` attribute can
be used to do so.  The key value is the form's name or id.  If more than one
form has the same name or id, the first one will be returned.

    >>> browser.open('forms.html')
    >>> form = browser.getForm(name='one')

Form instances conform to the IForm interface.

    >>> verifyObject(zope.testbrowser.interfaces.IForm, form)
    True

The form exposes several attributes related to forms:

  - The name of the form:

    >>> form.name
    'one'

  - The id of the form:

    >>> form.id
    '1'

  - The action (target URL) when the form is submitted:

    >>> form.action
    'http://localhost:.../forms.html'

  - The method (HTTP verb) used to transmit the form data:

    >>> form.method
    'POST'

  - The encoding type of the form data:

    >>> form.enctype
    'application/x-www-form-urlencoded'

Besides those attributes, you have also a couple of methods.  Like for the
browser, you can get control objects, but limited to the current form...

    >>> form.getControl(name='text-value')
    <Control name='text-value' type='text'>

...and submit the form.

    >>> form.submit('Submit')
    >>> browser.contents
    "...'text-value': ['First Text']..."

Submitting also works without specifying a control, as shown below, which is
it's primary reason for existing in competition with the control submission
discussed above.

Now let me show you briefly that looking up forms is sometimes important.  In
the `forms.html` template, we have four forms all having a text control named
`text-value`.  Now, if I use the browser's `get` method,

    >>> browser.open('forms.html')
    >>> browser.getControl(name='text-value')
    Traceback (most recent call last):
    ...
    AmbiguityError: name 'text-value'
    >>> browser.getControl('Text Control')
    Traceback (most recent call last):
    ...
    AmbiguityError: label 'Text Control'

I'll always get an ambiguous form field.  I can use the index argument, or
with the `getForm` method I can disambiguate by searching only within a given
form:

    >>> form = browser.getForm('2')
    >>> form.getControl(name='text-value').value
    'Second Text'
    >>> form.submit('Submit')
    >>> browser.contents
    "...'text-value': ['Second Text']..."
    >>> browser.open('forms.html')
    >>> form = browser.getForm('2')
    >>> form.getControl('Submit').click()
    >>> browser.contents
    "...'text-value': ['Second Text']..."
    >>> browser.open('forms.html')
    >>> browser.getForm('3').getControl('Text Control').value
    'Third Text'

The last form on the page does not have a name, an id, or a submit button.
Working with it is still easy, thanks to a index attribute that guarantees
order.  (Forms without submit buttons are sometimes useful for JavaScript.)

    >>> form = browser.getForm(index=3)
    >>> form.submit()
    >>> browser.contents
    "...'text-value': ['Fourth Text']..."

If a form is requested that does not exists, an exception will be raised.

    >>> browser.open('forms.html')
    >>> form = browser.getForm('does-not-exist')
    Traceback (most recent call last):
    LookupError

If the HTML page contains only one form, no arguments to `getForm` are
needed:

    >>> browser.open('oneform.html')
    >>> browser.getForm()
    <zope.testbrowser...Form object at ...>

If the HTML page contains more than one form, `index` is needed to
disambiguate if no other arguments are provided:

    >>> browser.open('forms.html')
    >>> browser.getForm()
    Traceback (most recent call last):
    ValueError: if no other arguments are given, index is required.


Performance Testing
-------------------

Browser objects keep up with how much time each request takes.  This can be
used to ensure a particular request's performance is within a tolerable range.
Be very careful using raw seconds, cross-machine differences can be huge,
pystones is usually a better choice.

    >>> browser.open('index.html')
    >>> browser.lastRequestSeconds < 10 # really big number for safety
    True
    >>> browser.lastRequestPystones < 10000 # really big number for safety
    True


Hand-Holding
------------

Instances of the various objects ensure that users don't set incorrect
instance attributes accidentally.

    >>> browser.nonexistant = None
    Traceback (most recent call last):
    ...
    AttributeError: 'Browser' object has no attribute 'nonexistant'

    >>> form.nonexistant = None
    Traceback (most recent call last):
    ...
    AttributeError: 'Form' object has no attribute 'nonexistant'

    >>> control.nonexistant = None
    Traceback (most recent call last):
    ...
    AttributeError: 'Control' object has no attribute 'nonexistant'

    >>> link.nonexistant = None
    Traceback (most recent call last):
    ...
    AttributeError: 'Link' object has no attribute 'nonexistant'


Fixed Bugs
----------

This section includes tests for bugs that were found and then fixed that don't
fit into the more documentation-centric sections above.

Spaces in URL
~~~~~~~~~~~~~

When URLs have spaces in them, they're handled correctly (before the bug was
fixed, you'd get "ValueError: too many values to unpack"):

    >>> browser.open('navigate.html')
    >>> browser.getLink('Spaces in the URL').click()

.goBack() Truncation
~~~~~~~~~~~~~~~~~~~~

The .goBack() method used to truncate the .contents.

    >>> browser.open('navigate.html')
    >>> actual_length = len(browser.contents)

    >>> browser.open('navigate.html')
    >>> browser.open('index.html')
    >>> browser.goBack()
    >>> len(browser.contents) == actual_length
    True
