from zope.testbrowser import interfaces
import re
import simplejson
import telnetlib
import time
import zope.interface
import zope.testbrowser.browser
import ClientForm

PROMPT = re.compile('repl\d?> ')

class Browser(zope.testbrowser.browser.SetattrErrorsMixin):
    zope.interface.implements(interfaces.IBrowser)

    raiseHttpErrors = True
    _counter = 0

    def __init__(self, url=None, host='localhost', port=4242):
        self.timer = zope.testbrowser.browser.PystoneTimer()
        self.init_repl(host, port)
        self._enable_setattr_errors = True

        if url is not None:
            self.open(url)

    def init_repl(self, host, port):
        self.telnet = telnetlib.Telnet(host, port)
        self.telnet.write("""
            var tb_tokens = {};
            var tb_next_token = 0;
            function tb_get_link_by_predicate(predicate, index) {
                var anchors = content.document.getElementsByTagName('a');
                var i=0;
                var found = null;
                if (index == undefined) index = null;
                for (x=0; x < anchors.length; x++) {
                    a = anchors[x];
                    if (!predicate(a)) {
                        continue;
                    }
                    // this anchor matches

                    // if we weren't given an index, but we found more than
                    // one match, we have an ambiguity
                    if (index == null && i > 0) {
                        return 'ambiguity error';
                    }

                    found = x;

                    // if we were given an index and we just found it, stop
                    if (index != null && i == index) {
                        break
                    }
                    i++;
                }
                if (found != null) {
                    tb_tokens[tb_next_token] = anchors[found];
                    return tb_next_token++;
                }
                return false; // link not found
            }

            function tb_get_link_by_text(text, index) {
                return tb_get_link_by_predicate(
                    function (a) {
                        return a.textContent.indexOf(text) == 0;
                    }, index)
            }

            function tb_get_link_by_id(id, index) {
                return tb_get_link_by_predicate(
                    function (a) {
                        return a.id == id;
                    }, index)
            }

            function tb_get_link_by_url(url, index) {
                return tb_get_link_by_predicate(
                    function (a) {
                        return a.href.indexOf(url) == 0;
                    }, index)
            }
            """)

    def execute(self, js):
        if not js.strip():
            return
        self.telnet.write("'MARKER'")
        self.telnet.read_until('MARKER')
        self.expect([PROMPT])
        self.telnet.write(js)
        i, match, text = self.expect([PROMPT])
        result = text.rsplit('\n', 1)
        if len(result) == 1:
            return None
        else:
            return result[0]

    def executeLines(self, js):
        lines = js.split('\n')
        for line in lines:
            self.execute(line)

    def expect(self, res, timeout=1):
        i, match, text = self.telnet.expect([PROMPT], timeout)
        if match is None:
            import pdb;pdb.set_trace()
            raise RuntimeError('unexpected result from MozRepl')
        return i, match, text

    def _changed(self):
        self._counter += 1

    @property
    def url(self):
        return self.execute('content.location')

    def _primePageLoadWait(self):
        # save the current document element to compare against later
        self.execute('tb_prev_document = content.document.documentElement;')

    def _waitForPageLoad(self):
        # wait for the page to load
        while self.execute('content.document.documentElement'
            '.isSameNode(tb_prev_document)') == 'true':
                time.sleep(0.001)

    def open(self, url, data=None):
        assert data is None
        self.start_timer()
        try:
            self._primePageLoadWait()
            self.execute('content.location = ' + simplejson.dumps(url))
            self._waitForPageLoad()
        finally:
            self.stop_timer()
            self._changed()

        # TODO raise non-200 errors

    @property
    def isHtml(self):
        return self.execute('content.document.contentType') == 'text/html'

    @property
    def title(self):
        return self.execute('content.document.title')

    @property
    def contents(self):
        return self.execute('content.document.documentElement.innerHTML')

    @property
    def headers(self):
        raise NotImplementedError

    @apply
    def handleErrors():
        def get(self):
            raise NotImplementedError

        def set(self, value):
            raise NotImplementedError

        return property(get, set)

    def start_timer(self):
        self.timer.start()

    def stop_timer(self):
        self.timer.stop()

    @property
    def lastRequestPystones(self):
        return self.timer.elapsedPystones

    @property
    def lastRequestSeconds(self):
        return self.timer.elapsedSeconds

    def reload(self):
        self.start_timer()
        self._primePageLoadWait()
        self.execute('content.document.location = content.document.location')
        self._waitForPageLoad()
        self.stop_timer()

    def goBack(self, count=1):
        self.start_timer()
        self._primePageLoadWait()
        self.execute('content.back()')
        self._waitForPageLoad()
        self.stop_timer()
        self._changed()

    def addHeader(self, key, value):
        raise NotImplementedError

    def getLink(self, text=None, url=None, id=None, index=None):
        zope.testbrowser.browser.onlyOne((text, url, id), 'text, url, or id')
        js_index = simplejson.dumps(index)
        if text is not None:
            msg = 'text %r' % text
            token = self.execute('tb_get_link_by_text(%s, %s)'
                 % (simplejson.dumps(text), js_index))
        elif url is not None:
            msg = 'url %r' % url
            token = self.execute('tb_get_link_by_text(%s, %s)'
                 % (simplejson.dumps(url), js_index))
        elif id is not None:
            msg = 'id %r' % id
            token = self.execute('tb_get_link_by_id(%s, %s)'
                 % (simplejson.dumps(id), js_index))

        if token == 'false':
            raise ValueError('Link not found: ' + msg)
        if token == 'ambiguity error':
            raise ClientForm.AmbiguityError(msg)

        return Link(token, self)

    def _follow_link(self, token):
        self.execute('tb_follow_link(%s)' % token)

    def getControl(self, label=None, name=None, index=None):
        raise NotImplementedError

    def getForm(self, id=None, name=None, action=None, index=None):
        raise NotImplementedError


class Link(zope.testbrowser.browser.SetattrErrorsMixin):
    zope.interface.implements(interfaces.ILink)

    def __init__(self, token, browser):
        self.token = token
        self.browser = browser
        self._browser_counter = self.browser._counter
        self._enable_setattr_errors = True

    def click(self):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        self.browser._start_timer()
        self.browser._follow_link(self.token)
        self.browser._stop_timer()
        self.browser._changed()

    @property
    def url(self):
        return self.browser.execute('tb_tokens[%s].href' % self.token)

    @property
    def text(self):
        return self.browser.execute('tb_tokens[%s].textContent' % self.token)

    @property
    def tag(self):
        raise NotImplementedError

    @property
    def attrs(self):
        raise NotImplementedError

    def __repr__(self):
        return "<%s text=%r url=%r>" % (
            self.__class__.__name__, self.text, self.url)

    def _follow_link(self, token):
        self.execute('tb_follow_link(%s)' % token)

    def getControl(self, label=None, name=None, index=None):
        raise NotImplementedError

    def getForm(self, id=None, name=None, action=None, index=None):
        raise NotImplementedError


class Link(zope.testbrowser.browser.SetattrErrorsMixin):
    zope.interface.implements(interfaces.ILink)

    def __init__(self, token, browser):
        self.token = token
        self.browser = browser
        self._browser_counter = self.browser._counter
        self._enable_setattr_errors = True

    def click(self):
        if self._browser_counter != self.browser._counter:
            raise interfaces.ExpiredError
        self.browser._start_timer()
        self.browser._follow_link(self.token)
        self.browser._stop_timer()
        self.browser._changed()

    @property
    def url(self):
        return self.browser.execute('tb_tokens[%s].href' % self.token)

    @property
    def text(self):
        return self.browser.execute('tb_tokens[%s].textContent' % self.token)

    @property
    def tag(self):
        raise NotImplementedError

    @property
    def attrs(self):
        raise NotImplementedError

    def __repr__(self):
        return "<%s text=%r url=%r>" % (
            self.__class__.__name__, self.text, self.url)
