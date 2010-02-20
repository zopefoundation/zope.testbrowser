import os

import urllib
import urllib2

class ValidatingHandler(urllib2.BaseHandler):

    def http_response(self, request, response):
        check = urllib2.urlopen(
            os.environ.get('ZOPE_TESTBROWSER_VALIDATE',
                           'http://validator.w3.org/check'),
            urllib.urlencode(dict(fragment=response.read())))
        response.seek(0)

        if check.info().get(
            'X-W3C-Validator-Status').lower() != 'valid':
            return self.parent.error(
                'http', request, check, '500', 'Invalid HTML',
                check.info())
            return check

        return response
        
