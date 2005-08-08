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

You can also find the link by (1) its URL,

    >>> browser.open('http://localhost/@@/testbrowser/navigate.html')
    >>> browser.contents
    '...<a href="navigate.html?message=By+URL">Using the URL</a>...'

    >>> browser.click(url='?message=By+URL')
    >>> browser.url
    'http://localhost/@@/testbrowser/navigate.html?message=By+URL'
    >>> browser.contents
    '...Message: <em>By URL</em>...'

or (2) its id:

    >>> browser.open('http://localhost/@@/testbrowser/navigate.html')
    >>> browser.contents
    '...<a href="navigate.html?message=By+Id" 
    id="anchorid">By Anchor Id</a>...'

    >>> browser.click(id='anchorid')
    >>> browser.url
    'http://localhost/@@/testbrowser/navigate.html?message=By+Id'
    >>> browser.contents
    '...Message: <em>By Id</em>...'

But there are more interesting cases.  You can also use the `click` method to
submit forms.  You can either use the submit button's value by simply
specifying the text:

    >>> browser.open('http://localhost/@@/testbrowser/navigate.html')
    >>> browser.contents
    '...<input type="submit" name="submit-form" value="Submit" />...'

    >>> browser.click('Submit')
    >>> browser.url
    'http://localhost/@@/testbrowser/navigate.html'
    >>> browser.contents
    '...Message: <em>By Form Submit</em>...'

Alternatively, you can specify the name of the control:

    >>> browser.open('http://localhost/@@/testbrowser/navigate.html')
    >>> browser.click(name='submit-form')
    >>> browser.url
    'http://localhost/@@/testbrowser/navigate.html'
    >>> browser.contents
    '...Message: <em>By Form Submit</em>...'

You thought we were done here? Not so quickly.  The `click` method also
supports image maps, though not by specifying the coordinates, but using the
area's title (or other tag attgributes):

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


Control Mappings
~~~~~~~~~~~~~~~~

You can look up a control's value from a mapping attribute:

    >>> browser.controls['text-value']
    'Some Text'

The key is matched against the value, id and name of the control.  The
`controls` mapping provides other functions too:

  - Asking for existence:

      >>> 'text-value' in browser.controls
      True
      >>> 'foo-value' in browser.controls
      False

  - Getting the value with a default option:

      >>> browser.controls.get('text-value')
      'Some Text'
      >>> browser.controls.get('foo-value', 42)
      42

  - Setting an item to a new value:

    >>> browser.controls['text-value'] = 'Some other Text'
    >>> browser.controls['text-value']
    'Some other Text'

  - Updating a lot of values at once:

    >>> browser.controls['password-value']
    'Password'

    >>> browser.controls.update({'text-value': 'More Text',
    ...                          'password-value': 'pass now'})

    >>> browser.controls['text-value']
    'More Text'
    >>> browser.controls['password-value']
    'pass now'

If we request a control that doesn't exist, an exception is raised.

    >>> browser.controls['does_not_exist']
    Traceback (most recent call last):
    ...
    KeyError: 'does_not_exist'


Control Objects
~~~~~~~~~~~~~~~

But the value of a control is not always everything that there is to know or
that is interesting.  In those cases, one can access the control object.  The
string passed into the function will be matched against the value, id and name
of the control, just as when using the control mapping.

    >>> ctrl = browser.getControl('text-value')
    >>> ctrl
    <Control name='text-value' type='text'>
    >>> ctrl = browser.getControl('text-value-id')
    >>> ctrl
    <Control name='text-value' type='text'>
    >>> ctrl = browser.getControl('More Text')
    >>> ctrl
    <Control name='text-value' type='text'>

If you want to search explicitly by name, value, and/or id, you may also use
keyword arguments 'name', 'text', and 'id'.

    >>> ctrl = browser.getControl(name='text-value')
    >>> ctrl
    <Control name='text-value' type='text'>
    >>> ctrl = browser.getControl(id='text-value-id')
    >>> ctrl
    <Control name='text-value' type='text'>
    >>> ctrl = browser.getControl(text='More Text')
    >>> ctrl
    <Control name='text-value' type='text'>
    >>> ctrl = browser.getControl(
    ...     id='text-value-id', name='text-value', text='More Text')
    >>> ctrl
    <Control name='text-value' type='text'>
    >>> ctrl = browser.getControl(
    ...     id='does not exist', name='does not exist', text='More Text')
    >>> ctrl
    <Control name='text-value' type='text'>

You may not use both the default argument and any of the other named arguments.

    >>> ctrl = browser.getControl('text-value', name='text-value')
    Traceback (most recent call last):
    ...    
    ValueError: ...

Controls provide IControl.

    >>> from zope.interface.verify import verifyObject
    >>> from zope.testbrowser import interfaces
    >>> verifyObject(interfaces.IControl, ctrl)
    True

They have several useful attributes:

  - the name as which the control is known to the form:

    >>> ctrl.name
    'text-value'

  - the value of the control; this attribute can also be set, of course:

    >>> ctrl.value
    'More Text'
    >>> ctrl.value = 'Some Text'

  - the type of the control:

    >>> ctrl.type
    'text'

  - a flag describing whether the control is disabled:

    >>> ctrl.disabled
    False

  - and there is a flag to tell us whether the control can have multiple
    values:

    >>> ctrl.multiple
    False

Additionally, controllers for select, radio, and checkbox provide IListControl.
These fields have three other attributes (at least in theory--see below):

    >>> ctrl = browser.getControl('multi-select-value')
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

Unfortunately, radio fields and checkbox fields do not yet implement
displayOptions and displayValue, although we hope to support them eventually
(i.e., basing off of label tags).

Various Controls
~~~~~~~~~~~~~~~~

There are various types of controls.  They are demonstrated here. 

  - Text Control

    The text control we already introduced above.

  - Password Control

    >>> ctrl = browser.getControl('password-value')
    >>> ctrl
    <Control name='password-value' type='password'>
    >>> verifyObject(interfaces.IControl, ctrl)
    True
    >>> ctrl.value
    'pass now'
    >>> ctrl.value = 'Password'
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False

  - Hidden Control

    >>> ctrl = browser.getControl('hidden-value')
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

    >>> ctrl = browser.getControl('textarea-value')
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

    >>> ctrl = browser.getControl('file-value')
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

    >>> ctrl = browser.getControl('single-select-value')
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

    >>> ctrl = browser.getControl('single-unvalued-checkbox-value')
    >>> ctrl
    <ListControl name='single-unvalued-checkbox-value' type='checkbox'>
    >>> interfaces.IListControl.providedBy(ctrl)
    True
    >>> verifyObject(interfaces.IControl, ctrl) # IListControl when implemented
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
    >>> ctrl.displayOptions # we wish this would work!
    Traceback (most recent call last):
    ...    
    NotImplementedError: ...
    >>> ctrl.displayValue # we wish this would work!
    Traceback (most recent call last):
    ...    
    NotImplementedError: ...
    >>> ctrl.displayValue = ['One'] # we wish this would work!
    Traceback (most recent call last):
    ...    
    NotImplementedError: ...

  - Checkbox Control (Single-Valued, Valued)

    >>> ctrl = browser.getControl('single-valued-checkbox-value')
    >>> ctrl
    <ListControl name='single-valued-checkbox-value' type='checkbox'>
    >>> interfaces.IListControl.providedBy(ctrl)
    True
    >>> verifyObject(interfaces.IControl, ctrl) # IListControl when implemented
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
    >>> ctrl.displayOptions # we wish this would work!
    Traceback (most recent call last):
    ...    
    NotImplementedError: ...
    >>> ctrl.displayValue # we wish this would work!
    Traceback (most recent call last):
    ...    
    NotImplementedError: ...
    >>> ctrl.displayValue = ['One'] # we wish this would work!
    Traceback (most recent call last):
    ...    
    NotImplementedError: ...

  - Checkbox Control (Multi-Valued)

    >>> ctrl = browser.getControl('multi-checkbox-value')
    >>> ctrl
    <ListControl name='multi-checkbox-value' type='checkbox'>
    >>> interfaces.IListControl.providedBy(ctrl)
    True
    >>> verifyObject(interfaces.IControl, ctrl) # IListControl when implemented
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
    >>> ctrl.displayOptions # we wish this would work!
    Traceback (most recent call last):
    ...    
    NotImplementedError: ...
    >>> ctrl.displayValue # we wish this would work!
    Traceback (most recent call last):
    ...    
    NotImplementedError: ...
    >>> ctrl.displayValue = ['One'] # we wish this would work!
    Traceback (most recent call last):
    ...    
    NotImplementedError: ...

  - Radio Control

    >>> ctrl = browser.getControl('radio-value')
    >>> ctrl
    <ListControl name='radio-value' type='radio'>
    >>> interfaces.IListControl.providedBy(ctrl)
    True
    >>> verifyObject(interfaces.IControl, ctrl) # IListControl when implemented
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
    >>> ctrl.displayOptions # we wish this would work!
    Traceback (most recent call last):
    ...    
    NotImplementedError: ...
    >>> ctrl.displayValue # we wish this would work!
    Traceback (most recent call last):
    ...    
    NotImplementedError: ...
    >>> ctrl.displayValue = ['One'] # we wish this would work!
    Traceback (most recent call last):
    ...    
    NotImplementedError: ...

  - Image Control

    >>> ctrl = browser.getControl('image-value')
    >>> ctrl
    <Control name='image-value' type='image'>
    >>> verifyObject(interfaces.IControl, ctrl)
    True
    >>> ctrl.value
    ''
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False

  - Submit Control

    >>> ctrl = browser.getControl('submit-value')
    >>> ctrl
    <Control name='submit-value' type='submit'>
    >>> verifyObject(interfaces.IControl, ctrl)
    True
    >>> ctrl.value
    'Submit'
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False


Using Submitting Controls
~~~~~~~~~~~~~~~~~~~~~~~~~

Both, the submit and image type, should be clickable and submit the form:

    >>> browser.controls['text-value'] = 'Other Text'
    >>> browser.click('Submit')
    >>> print browser.contents
    <html>
    ...
    <em>Other Text</em>
    <input type="text" name="text-value" id="text-value-id" value="Some Text" />
    ...
    <em>Submit</em>
    <input type="submit" name="submit-value" value="Submit" />
    ...
    </html>

And also with the image value:

    >>> browser.open('http://localhost/@@/testbrowser/controls.html')
    >>> browser.controls['text-value'] = 'Other Text'
    >>> browser.click(name='image-value')
    >>> print browser.contents
    <html>
    ...
    <em>Other Text</em>
    <input type="text" name="text-value" id="text-value-id" value="Some Text" />
    ...
    <em>1</em>
    <em>1</em>
    <input type="image" name="image-value" src="zope3logo.gif" />
    ...
    </html>

But when sending an image, you can also specify the coordinate you clicked:

    >>> browser.open('http://localhost/@@/testbrowser/controls.html')
    >>> browser.click(name='image-value', coord=(50,25))
    >>> print browser.contents
    <html>
    ...
    <em>50</em>
    <em>25</em>
    <input type="image" name="image-value" src="zope3logo.gif" />
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

  - The controls for this specific form are also available:

    >>> form.controls
    <zope.testbrowser.browser.ControlsMapping object at ...>
    >>> form.controls['text-value']
    'First Text'

Besides those attributes, you have also a couple of methods.  Like for the
browser, you can get control objects

    >>> form.getControl('text-value')
    <Control name='text-value' type='text'>

and submit the form:

    >>> form.submit('Submit')
    >>> print browser.contents
    <html>
    ...
    <em>First Text</em>
    ...
    </html>

Okay, that's it about forms.  Now let me show you briefly that looking up forms
is sometimes important.  In the `forms.html` template, we have three forms all
having a text control named `text-value`.  Now, if I use the browser's
`controls` attribute and `click` method,

    >>> browser.controls['text-value']
    'First Text'
    >>> browser.click('Submit')
    >>> print browser.contents
    <html>
    ...
    <em>First Text</em>
    ...
    </html>

I can every only get to the first form, making the others unreachable.  But
with the `forms` mapping I can get to the second and third form as well:

    >>> form = browser.forms['2']
    >>> form.controls['text-value']
    'Second Text'
    >>> form.submit('Submit')
    >>> browser.contents
    '...<em>Second Text</em>...'

The `forms` mapping also supports the check for containment

    >>> 'three' in browser.forms
    True

and retrievel with optional default value:

    >>> browser.forms.get('2')
    <zope.testbrowser.browser.Form object at ...>
    >>> browser.forms.get('invalid', 42)
    42


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
