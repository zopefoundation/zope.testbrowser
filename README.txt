================
The Test Browser
================

The ``zope.testbrowser`` module exposes a ``Browser`` class that
simulates a web browser similar to Mozilla Firefox or IE.

    >>> from zope.testbrowser import Browser
    >>> browser = Browser()
    >>> browser.addHeader('Authorization', 'Basic mgr:mgrpw')

The browser can `open` web pages:

   >>> browser.open('http://localhost/@@/testbrowser/simple.html')
   >>> browser.url
   'http://localhost/@@/testbrowser/simple.html'


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
output.


Checking for HTML
-----------------

Not all URLs return HTML. Of course our simple page does:

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
headers. The headers are accessible via a separate attribute, which is an
``httplib.HTTPMessage`` instance:

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

If you want to simulate clicking on a link, there is a `click` method. In the
`navigate.html` file there are several links set up to demonstrate the
capabilities of the `click` method. 

    >>> browser.open('http://localhost/@@/testbrowser/navigate.html')

The simplest is to access the link by the text value that is linked, in other
words the linked text you would see in a browser:

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

But there are more interesting cases. You can also use the `click` method to
submit forms. You can either use the submit button's value by simply
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

You thought we were done here? Not so quickly. The `click` method also
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
and fill in values for the controls of input forms. To do so, let's first open
a page that has a bunch of controls:

    >>> browser.open('http://localhost/@@/testbrowser/controls.html')


Control Mappings
~~~~~~~~~~~~~~~~

You can look up a control's value from a mapping attribute:

    >>> browser.controls['text-value']
    'Some Text'

The key is matched against the value, id and name of the control. The
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
that is interesting. In those cases, one can access the control object:

    >>> ctrl = browser.getControl('text-value')
    >>> ctrl
    <Control name='text-value' type='text'>

The string passed into the function will be matched against the value, id and
name of the control, just as when using the controll mapping. The control has
several useful attributes:

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

  - there is a flag to tell us whether the control can have multiple values:

    >>> ctrl.multiple
    False

  - and finally there is an attribute that provides all available value
    options. This is of course not sensible for a text input control and thus
    not available:

    >>> ctrl.options
    Traceback (most recent call last):
    ...    
    AttributeError: options


Various Controls
~~~~~~~~~~~~~~~~

There are various types of controls. They are demonstrated here. 

  - Text Control

    The text control we already introduced above.

  - Password Control

    >>> ctrl = browser.getControl('password-value')
    >>> ctrl
    <Control name='password-value' type='password'>
    >>> ctrl.value
    'pass now'
    >>> ctrl.value = 'Password'
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False
    >>> ctrl.options
    Traceback (most recent call last):
    ...    
    AttributeError: options

  - Hidden Control

    >>> ctrl = browser.getControl('hidden-value')
    >>> ctrl
    <Control name='hidden-value' type='hidden'>
    >>> ctrl.value
    'Hidden'
    >>> ctrl.value = 'More Hidden'
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False
    >>> ctrl.options
    Traceback (most recent call last):
    ...    
    AttributeError: options
    
  - Text Area Control

    >>> ctrl = browser.getControl('textarea-value')
    >>> ctrl
    <Control name='textarea-value' type='textarea'>
    >>> ctrl.value
    '\n        Text inside\n        area!\n      '
    >>> ctrl.value = 'A lot of\n text.'
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False
    >>> ctrl.options
    Traceback (most recent call last):
    ...    
    AttributeError: options

  - File Control

    >>> ctrl = browser.getControl('file-value')
    >>> ctrl
    <Control name='file-value' type='file'>
    >>> ctrl.value
    >>> import cStringIO
    >>> ctrl.value = cStringIO.StringIO('File contents')
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False
    >>> ctrl.options
    Traceback (most recent call last):
    ...    
    AttributeError: options

  - Selection Control (Single-Valued)

    >>> ctrl = browser.getControl('single-select-value')
    >>> ctrl
    <Control name='single-select-value' type='select'>
    >>> ctrl.value
    ['1']
    >>> ctrl.value = ['2']
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False
    >>> ctrl.options
    ['1', '2', '3']

  - Selection Control (Multi-Valued)

    >>> ctrl = browser.getControl('multi-select-value')
    >>> ctrl
    <Control name='multi-select-value' type='select'>
    >>> ctrl.value
    []
    >>> ctrl.value = ['1', '2']
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    True
    >>> ctrl.options
    ['1', '2', '3']

  - Checkbox Control (Single-Valued; Unvalued)

    >>> ctrl = browser.getControl('single-unvalued-checkbox-value')
    >>> ctrl
    <Control name='single-unvalued-checkbox-value' type='checkbox'>
    >>> ctrl.value
    True
    >>> ctrl.value = False
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    True
    >>> ctrl.options
    [True]

  - Checkbox Control (Single-Valued, Valued)

    >>> ctrl = browser.getControl('single-valued-checkbox-value')
    >>> ctrl
    <Control name='single-valued-checkbox-value' type='checkbox'>
    >>> ctrl.value
    ['1']
    >>> ctrl.value = []
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    True
    >>> ctrl.options
    ['1']

  - Checkbox Control (Multi-Valued)

    >>> ctrl = browser.getControl('multi-checkbox-value')
    >>> ctrl
    <Control name='multi-checkbox-value' type='checkbox'>
    >>> ctrl.value
    ['1', '3']
    >>> ctrl.value = ['1', '2']
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    True
    >>> ctrl.options
    ['1', '2', '3']

  - Image Control

    >>> ctrl = browser.getControl('image-value')
    >>> ctrl
    <Control name='image-value' type='image'>
    >>> ctrl.value
    ''
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False
    >>> ctrl.options
    Traceback (most recent call last):
    ...    
    AttributeError: options

  - Submit Control

    >>> ctrl = browser.getControl('submit-value')
    >>> ctrl
    <Control name='submit-value' type='submit'>
    >>> ctrl.value
    'Submit'
    >>> ctrl.disabled
    False
    >>> ctrl.multiple
    False
    >>> ctrl.options
    Traceback (most recent call last):
    ...    
    AttributeError: options


Using Submitting Controls
~~~~~~~~~~~~~~~~~~~~~~~~~

Both, the submit and image type, should be clickable and submit the form:

    >>> browser.controls['text-value'] = 'Other Text'
    >>> browser.click('Submit')
    >>> print browser.contents
    <html>
    ...
    <em>Other Text</em>
    <input type="text" name="text-value" value="Some Text" />
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
    <input type="text" name="text-value" value="Some Text" />
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

Besides those attributes, you have also a couple of methods. Like for the
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

Okay, that's it about forms. Now let me show you briefly that looking up forms
is sometimes important. In the `forms.html` template, we have three forms all
having a text control named `text-value`. Now, if I use the browser's
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

I can every only get to the first form, making the others unreachable. But
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
publisher. For debugging purposes, however, it can be very useful to see the
original exception caused by the application. In those cases you can set the
``handleErrors`` property of the browser to ``False``. It is defaulted to
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
