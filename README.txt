================
The Test Browser
================

The ``zope.testbrowser`` module exposes a ``Browser`` class that
simulates a web browser similar to Mozilla Firefox or IE.

    >>> from zope.testbrowser import Browser
    >>> browser = Browser()
    >>> browser.addHeader('Authorization', 'Basic mgr:mgrpw')

It can send arbitrary headers; this is helpful for setting the language value,
so that your tests format values the way you expect in your tests, if you rely
on zope.i18n locale-based formatting or a similar approach.

    >>> browser.addHeader('Accept-Language', 'en-US')

The browser can `open` web pages:

    >>> browser.open('http://localhost/@@/testbrowser/simple.html')
    >>> browser.url
    'http://localhost/@@/testbrowser/simple.html'

Once you have opened a web page initially, best practice for writing
testbrowser doctests suggests using 'click' to navigate further (as discussed
below), except in unusual circumstances.

Page Contents
-------------

The contents of the current page are available:

    >>> print browser.contents
    <html>
      <head>
        <title>Simple Page</title>
      </head>
      <body>
        <h1>Simple Page</h1>
      </body>
    </html>

Making assertions about page contents is easy.

    >>> '<h1>Simple Page</h1>' in browser.contents
    True

Utilizing the doctest facilities, it also possible to do:

    >>> browser.contents
    '...<h1>Simple Page</h1>...'

Note: Unfortunately, ellipsis (...) cannot be used at the beginning of the
output (this is a limitation of doctest).


Checking for HTML
-----------------

Not all URLs return HTML.  Of course our simple page does:

    >>> browser.open('http://localhost/@@/testbrowser/simple.html')
    >>> browser.isHtml
    True

But if we load an image (or other binary file), we do not get HTML:

    >>> browser.open('http://localhost/@@/testbrowser/zope3logo.gif')
    >>> browser.isHtml
    False


HTML Page Title
----------------

Another useful helper property is the title:

    >>> browser.open('http://localhost/@@/testbrowser/simple.html')
    >>> browser.title
    'Simple Page'

If a page does not provide a title, it is simply ``None``:

    >>> browser.open('http://localhost/@@/testbrowser/notitle.html')
    >>> browser.title

However, if the output is not HTML, then an error will occur trying to access
the title:

    >>> browser.open('http://localhost/@@/testbrowser/zope3logo.gif')
    >>> browser.title
    Traceback (most recent call last):
    ...
    BrowserStateError: not viewing HTML


Headers
-------

As you can see, the `contents` of the browser does not return any HTTP
headers.  The headers are accessible via a separate attribute, which is an
``httplib.HTTPMessage`` instance (httplib is a part of Python's standard
library):

    >>> browser.open('http://localhost/@@/testbrowser/simple.html')
    >>> browser.headers
    <httplib.HTTPMessage instance...>

The headers can be accesed as a string:

    >>> print browser.headers
    Status: 200 Ok
    Content-Length: ...
    Content-Type: text/html;charset=utf-8
    X-Content-Type-Warning: guessed from content
    X-Powered-By: Zope (www.zope.org), Python (www.python.org)

Or as a mapping:

    >>> browser.headers['content-type']
    'text/html;charset=utf-8'


Navigation
----------

If you want to simulate clicking on a link, there is a `click` method.  In the
`navigate.html` file there are several links set up to demonstrate the
capabilities of the `click` method. 

The simplest way to reffer to the link is via the anchor text.  In other words
the text you would see in a browser (text and url searches are substring
searches):

    >>> browser.open('http://localhost/@@/testbrowser/navigate.html')
    >>> browser.contents
    '...<a href="navigate.html?message=By+Link+Text">Link Text</a>...'

    >>> browser.click('Link Text')
    >>> browser.url
    'http://localhost/@@/testbrowser/navigate.html?message=By+Link+Text'
    >>> browser.contents
    '...Message: <em>By Link Text</em>...'

You can also find the link by its URL,

    >>> browser.open('http://localhost/@@/testbrowser/navigate.html')
    >>> browser.contents
    '...<a href="navigate.html?message=By+URL">Using the URL</a>...'

    >>> browser.click(url='?message=By+URL')
    >>> browser.url
    'http://localhost/@@/testbrowser/navigate.html?message=By+URL'
    >>> browser.contents
    '...Message: <em>By URL</em>...'

or its id:

    >>> browser.open('http://localhost/@@/testbrowser/navigate.html')
    >>> browser.contents
    '...<a href="navigate.html?message=By+Id" 
    id="anchorid">By Anchor Id</a>...'

    >>> browser.click(id='anchorid')
    >>> browser.url
    'http://localhost/@@/testbrowser/navigate.html?message=By+Id'
    >>> browser.contents
    '...Message: <em>By Id</em>...'

You thought we were done here? Not so quickly.  The `click` method also
supports image maps, though not by specifying the coordinates, but using the
area's id:

    >>> browser.open('http://localhost/@@/testbrowser/navigate.html')
    >>> browser.click(id='zope3')
    >>> browser.url
    'http://localhost/@@/testbrowser/navigate.html?message=Zope+3+Name'
    >>> browser.contents
    '...Message: <em>Zope 3 Name</em>...'


Other Navigation
----------------

Like in any normal browser, you can reload a page:

    >>> browser.open('http://localhost/@@/testbrowser/simple.html')
    >>> browser.url
    'http://localhost/@@/testbrowser/simple.html'
    >>> browser.reload()
    >>> browser.url
    'http://localhost/@@/testbrowser/simple.html'

You can also go back:

    >>> browser.open('http://localhost/@@/testbrowser/notitle.html')
    >>> browser.url
    'http://localhost/@@/testbrowser/notitle.html'
    >>> browser.goBack()
    >>> browser.url
    'http://localhost/@@/testbrowser/simple.html'


Controls
--------

One of the most important features of the browser is the ability to inspect
and fill in values for the controls of input forms.  To do so, let's first open
a page that has a bunch of controls:

    >>> browser.open('http://localhost/@@/testbrowser/controls.html')

Obtaining a Control
~~~~~~~~~~~~~~~~~~~

You look up browser controls with the 'get' method.  The default first argument
is 'label', and looks up the form on the basis of any associated label.

    >>> browser.get('Text Control')
    <Control name='text-value' type='text'>
    >>> browser.get(label='Text Control') # equivalent
    <Control name='text-value' type='text'>

If you request a control that doesn't exist, the code raises a LookupError:

    >>> browser.get('Does Not Exist')
    Traceback (most recent call last):
    ...
    LookupError: label 'Does Not Exist'

If you request a control with an ambiguous lookup, the code raises an 
AmbiguityError.

    >>> browser.get('Ambiguous Control')
    Traceback (most recent call last):
    ...
    AmbiguityError: label 'Ambiguous Control'

Ambiguous controls may be specified using an index value.  We use the control's
value attribute to show the two controls; this attribute is properly introduced 
below.

    >>> browser.get('Ambiguous Control', index=0)
    <Control name='ambiguous-control-name' type='text'>
    >>> browser.get('Ambiguous Control', index=0).value
    'First'
    >>> browser.get('Ambiguous Control', index=1).value
    'Second'

The label search uses a whitespace-normalized version of the label, and does
a substring search, but case is honored.

    >>> browser.get('Label Needs Whitespace Normalization')
    <Control name='label-needs-normalization' type='text'>
    >>> browser.get('label needs whitespace normalization')
    Traceback (most recent call last):
    ...
    LookupError: label 'label needs whitespace normalization'

Multiple labels can refer to the same control (simply because that is possible
in the HTML 4.0 spec).

    >>> browser.get('Multiple labels really')
    <Control name='two-labels' type='text'>
    >>> browser.get('really are possible')
    <Control name='two-labels' type='text'>
    >>> browser.get('really') # OK: ambiguous labels, but not ambiguous control
    <Control name='two-labels' type='text'>

Get also accepts two other arguments, 'name' and 'value'.  Only one of 'label',
'name', and 'value' may be used at a time.

The 'name' keyword searches form field names.

    >>> browser.get(name='text-value')
    <Control name='text-value' type='text'>
    >>> browser.get(name='ambiguous-control-name')
    Traceback (most recent call last):
    ...
    AmbiguityError: name 'ambiguous-control-name'
    >>> browser.get(name='does-not-exist')
    Traceback (most recent call last):
    ...
    LookupError: name 'does-not-exist'
    >>> browser.get(name='ambiguous-control-name', index=1).value
    'Second'

Combining any of 'label', and 'name' raises a ValueError, as does
supplying none of them.

    >>> browser.get(label='Ambiguous Control', name='ambiguous-control-name')
    Traceback (most recent call last):
    ...
    ValueError: Supply one and only one of 'label' and 'name' arguments
    >>> browser.get()
    Traceback (most recent call last):
    ...
    ValueError: Supply one and only one of 'label' and 'name' arguments

Radio and checkbox fields are unusual in that their labels and names may point
to different objects: names point to logical collections of radio buttons or
checkboxes, but labels may only be used for individual choices within the
logical collection.  This means that obtaining a radio button by label gets a
different object than obtaining the radio collection by name.

    >>> browser.get(name='radio-value')
    <ListControl name='radio-value' type='radio'>
    >>> browser.get('Zwei')
    <Subcontrol name='radio-value' type='radio' index=1>

Characteristics of controls and subcontrols are discussed below.

Control Objects
~~~~~~~~~~~~~~~

Controls provide IControl.

    >>> ctrl = browser.get('Text Control')
    >>> ctrl
    <Control name='text-value' type='text'>
    >>> from zope.interface.verify import verifyObject
    >>> from zope.testbrowser import interfaces
    >>> verifyObject(interfaces.IControl, ctrl)
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
These fields have three other attributes:

    >>> ctrl = browser.get('Multiple Select Control')
    >>> ctrl
    <ListControl name='multi-select-value' type='select'>
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    True
    >>> verifyObject(interfaces.IListControl, ctrl)
    True

  - 'options' lists all available value options.

    >>> ctrl.options
    ['1', '2', '3']

  - 'displayOptions' lists all available options by value.

    >>> ctrl.displayOptions
    ['One', 'Two', 'Three']

  - 'displayValue' lets you get and set the displayed values of the control
    of the select box, rather than the actual values.

    >>> ctrl.value
    []
    >>> ctrl.displayValue
    []
    >>> ctrl.displayValue = ['One', 'Two']
    >>> ctrl.displayValue
    ['One', 'Two']
    >>> ctrl.value
    ['1', '2']

Finally, submit controls provide ISubmitControl, and image controls provide
IImageSubmitControl, which extents ISubmitControl.  These both simply add a
'click' method.  For image submit controls, you may also provide a coordinates
argument, which is a tuple of (x, y).  These submit the forms, and are
demonstrated below as we examine each control individually.

Subcontrol Objects
~~~~~~~~~~~~~~~~~~

As introduced briefly above, using labels to obtain elements of a logical
radio button or checkbox collection returns subcontrols, rather than controls.
Manipulating the value of the subcontrols affects the parent control.

    >>> browser.get(name='radio-value').value
    ['2']
    >>> browser.get('Zwei').value
    True
    >>> verifyObject(interfaces.ISubcontrol, browser.get('Zwei'))
    True
    >>> browser.get('Ein').value = True
    >>> browser.get('Ein').value
    True
    >>> browser.get('Zwei').value
    False
    >>> browser.get(name='radio-value').value
    ['1']
    >>> browser.get('Ein').value = False
    >>> browser.get(name='radio-value').value
    []
    >>> browser.get('Zwei').value = True

Checkbox collections behave similarly, as shown below.

Various Controls
~~~~~~~~~~~~~~~~

The various types of controls are demonstrated here. 

  - Text Control

    The text control we already introduced above.

  - Password Control

    >>> ctrl = browser.get('Password Control')
    >>> ctrl
    <Control name='password-value' type='password'>
    >>> verifyObject(interfaces.IControl, ctrl)
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

    >>> ctrl = browser.get(name='hidden-value')
    >>> ctrl
    <Control name='hidden-value' type='hidden'>
    >>> verifyObject(interfaces.IControl, ctrl)
    True
    >>> ctrl.value
    'Hidden'
    >>> ctrl.value = 'More Hidden'
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False
    
  - Text Area Control

    >>> ctrl = browser.get('Text Area Control')
    >>> ctrl
    <Control name='textarea-value' type='textarea'>
    >>> verifyObject(interfaces.IControl, ctrl)
    True
    >>> ctrl.value
    '\n        Text inside\n        area!\n      '
    >>> ctrl.value = 'A lot of\n text.'
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False

  - File Control

    >>> ctrl = browser.get('File Control')
    >>> ctrl
    <Control name='file-value' type='file'>
    >>> verifyObject(interfaces.IControl, ctrl)
    True
    >>> ctrl.value
    >>> import cStringIO
    >>> ctrl.value = cStringIO.StringIO('File contents')
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False

  - Selection Control (Single-Valued)

    >>> ctrl = browser.get('Single Select Control')
    >>> ctrl
    <ListControl name='single-select-value' type='select'>
    >>> verifyObject(interfaces.IListControl, ctrl)
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
    ['One', 'Two', 'Three']
    >>> ctrl.displayValue
    ['Two']
    >>> ctrl.displayValue = ['Three']
    >>> ctrl.displayValue
    ['Three']
    >>> ctrl.value
    ['3']

  - Selection Control (Multi-Valued)

    This was already demonstrated in the introduction to control objects above.

  - Checkbox Control (Single-Valued; Unvalued)

    >>> ctrl = browser.get(name='single-unvalued-checkbox-value')
    >>> ctrl
    <ListControl name='single-unvalued-checkbox-value' type='checkbox'>
    >>> verifyObject(interfaces.IListControl, ctrl)
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
    ...     interfaces.ISubcontrol, browser.get('Single Unvalued Checkbox'))
    True
    >>> browser.get('Single Unvalued Checkbox').value
    False
    >>> ctrl.displayValue = ['Single Unvalued Checkbox']
    >>> ctrl.displayValue
    ['Single Unvalued Checkbox']
    >>> browser.get('Single Unvalued Checkbox').value
    True
    >>> browser.get('Single Unvalued Checkbox').value = False
    >>> browser.get('Single Unvalued Checkbox').value
    False
    >>> ctrl.displayValue
    []

  - Checkbox Control (Single-Valued, Valued)

    >>> ctrl = browser.get(name='single-valued-checkbox-value')
    >>> ctrl
    <ListControl name='single-valued-checkbox-value' type='checkbox'>
    >>> verifyObject(interfaces.IListControl, ctrl)
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
    ...     interfaces.ISubcontrol, browser.get('Single Valued Checkbox'))
    True
    >>> browser.get('Single Valued Checkbox').value
    False
    >>> ctrl.displayValue = ['Single Valued Checkbox']
    >>> ctrl.displayValue
    ['Single Valued Checkbox']
    >>> browser.get('Single Valued Checkbox').value
    True
    >>> browser.get('Single Valued Checkbox').value = False
    >>> browser.get('Single Valued Checkbox').value
    False
    >>> ctrl.displayValue
    []

  - Checkbox Control (Multi-Valued)

    >>> ctrl = browser.get(name='multi-checkbox-value')
    >>> ctrl
    <ListControl name='multi-checkbox-value' type='checkbox'>
    >>> verifyObject(interfaces.IListControl, ctrl)
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
    >>> browser.get('Two').value
    True
    >>> verifyObject(interfaces.ISubcontrol, browser.get('Two'))
    True
    >>> browser.get('Three').value = True
    >>> browser.get('Three').value
    True
    >>> browser.get('Two').value
    True
    >>> ctrl.value
    ['2', '3']
    >>> browser.get('Two').value = False
    >>> ctrl.value
    ['3']
    >>> browser.get('Three').value = False
    >>> ctrl.value
    []

  - Radio Control

    >>> ctrl = browser.get(name='radio-value')
    >>> ctrl
    <ListControl name='radio-value' type='radio'>
    >>> verifyObject(interfaces.IListControl, ctrl)
    True
    >>> ctrl.value
    ['2']
    >>> ctrl.value = []
    >>> ctrl.value
    []
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False
    >>> ctrl.options
    ['1', '2', '3']
    >>> ctrl.displayOptions
    ['Ein', 'Zwei', 'Drei']
    >>> ctrl.displayValue
    []
    >>> ctrl.displayValue = ['Ein']
    >>> ctrl.displayValue
    ['Ein']

  The radio control subcontrols were illustrated above.

  - Image Control

    >>> ctrl = browser.get(name='image-value')
    >>> ctrl
    <ImageControl name='image-value' type='image'>
    >>> verifyObject(interfaces.IImageSubmitControl, ctrl)
    True
    >>> ctrl.value
    ''
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False

  - Submit Control

    >>> ctrl = browser.get(name='submit-value')
    >>> ctrl
    <SubmitControl name='submit-value' type='submit'>
    >>> browser.get('Submit This') # value of submit button is a label
    <SubmitControl name='submit-value' type='submit'>
    >>> browser.get('Standard Submit Control') # label tag is legal
    <SubmitControl name='submit-value' type='submit'>
    >>> browser.get('Submit') # multiple labels, but control is not ambiguous
    <SubmitControl name='submit-value' type='submit'>
    >>> verifyObject(interfaces.ISubmitControl, ctrl)
    True
    >>> ctrl.value
    'Submit This'
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False

Using Submitting Controls
~~~~~~~~~~~~~~~~~~~~~~~~~

Both, the submit and image type, should be clickable and submit the form:

    >>> browser.get('Text Control').value = 'Other Text'
    >>> browser.get('Submit').click()
    >>> print browser.contents
    <html>
    ...
    <em>Other Text</em>
    <input type="text" name="text-value" id="text-value" value="Some Text" />
    ...
    <em>Submit This</em>
    <input type="submit" name="submit-value" id="submit-value" value="Submit This" />
    ...
    </html>

And also with the image value:

    >>> browser.open('http://localhost/@@/testbrowser/controls.html')
    >>> browser.get('Text Control').value = 'Other Text'
    >>> browser.get(name='image-value').click()
    >>> print browser.contents
    <html>
    ...
    <em>Other Text</em>
    <input type="text" name="text-value" id="text-value" value="Some Text" />
    ...
    <em>1</em>
    <em>1</em>
    <input type="image" name="image-value" id="image-value"
           src="zope3logo.gif" />
    ...
    </html>

But when sending an image, you can also specify the coordinate you clicked:

    >>> browser.open('http://localhost/@@/testbrowser/controls.html')
    >>> browser.get(name='image-value').click((50,25))
    >>> print browser.contents
    <html>
    ...
    <em>50</em>
    <em>25</em>
    <input type="image" name="image-value" id="image-value"
           src="zope3logo.gif" />
    ...
    </html>

Forms
-----

Because pages can have multiple forms with like-named controls, it is sometimes
neccesary to access forms by name or id.  The browser's `forms` attribute can
be used to do so.  The key value is the form's name or id.  If more than one 
form has the same name or id, the first one will be returned.

    >>> browser.open('http://localhost/@@/testbrowser/forms.html')
    >>> form = browser.forms['one']

The form exposes several attributes related to forms:

  - The name of the form:

    >>> form.name
    'one'

  - The id of the form:

    >>> form.id
    '1'
    
  - The action (target URL) when the form is submitted:

    >>> form.action
    'http://localhost/@@/testbrowser/forms.html'

  - The method (HTTP verb) used to transmit the form data:

    >>> form.method
    'POST'

  - The encoding type of the form data:

    >>> form.enctype
    'multipart/form-data'

Besides those attributes, you have also a couple of methods.  Like for the
browser, you can get control objects, but limited to the current form...

    >>> form.get(name='text-value')
    <Control name='text-value' type='text'>

...and submit the form.

    >>> form.submit('Submit')
    >>> print browser.contents
    <html>
    ...
    <em>First Text</em>
    ...
    </html>

Submitting also works without specifying a control, as shown below, which is
it's primary reason for existing in competition with the control submission
discussed above.

Now let me show you briefly that looking up forms is sometimes important.  In
the `forms.html` template, we have four forms all having a text control named
`text-value`.  Now, if I use the browser's `get` method,

    >>> browser.get(name='text-value')
    Traceback (most recent call last):
    ...
    AmbiguityError: name 'text-value'
    >>> browser.get('Text Control')
    Traceback (most recent call last):
    ...
    AmbiguityError: label 'Text Control'

I'll always get an ambiguous form field.  I can use the index argument, or
with the `forms` mapping I can disambiguate by searching only within a given
form:

    >>> form = browser.forms['2']
    >>> form.get(name='text-value').value
    'Second Text'
    >>> form.submit('Submit')
    >>> browser.contents
    '...<em>Second Text</em>...'
    >>> form = browser.forms['2']
    >>> form.get('Submit').click()
    >>> browser.contents
    '...<em>Second Text</em>...'
    >>> browser.forms['3'].get('Text Control').value
    'Third Text'

The `forms` mapping also supports the check for containment

    >>> 'three' in browser.forms
    True

and retrievel with optional default value:

    >>> browser.forms.get('2')
    <zope.testbrowser.browser.Form object at ...>
    >>> browser.forms.get('invalid', 42)
    42

The last form on the page does not have a name, an id, or a submit button.
Working with it is still easy, thanks to a values attribute that guarantees
order.  (Forms without submit buttons are sometimes useful for JavaScript.)

    >>> form = browser.forms.values()[3]
    >>> form.submit()
    >>> browser.contents
    '...<em>Fourth Text</em>...'

Other mapping attributes for the forms collection remain unimplemented.
If useful, contributors implementing these would be welcome.

    >>> browser.forms.items()
    Traceback (most recent call last):
    ...
    AttributeError: 'FormsMapping' object has no attribute 'items'
    >>> browser.forms.keys()
    Traceback (most recent call last):
    ...
    AttributeError: 'FormsMapping' object has no attribute 'keys'

Handling Errors
---------------

A very useful feature of the publisher is the automatic graceful handling of
application errors, such as invalid URLs:

    >>> browser.open('http://localhost/invalid')
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 404: Not Found

Note that the above error was thrown by ``urllib2`` and not by the
publisher.  For debugging purposes, however, it can be very useful to see the
original exception caused by the application.  In those cases you can set the
``handleErrors`` property of the browser to ``False``.  It is defaulted to
``True``:

    >>> browser.handleErrors
    True

So when we tell the publisher not to handle the errors,    

    >>> browser.handleErrors = False

we get a different, Zope internal error:

    >>> browser.open('http://localhost/invalid')
    Traceback (most recent call last):
    ...
    NotFound: Object: <zope.app.folder.folder.Folder object at ...>, 
              name: u'invalid'
