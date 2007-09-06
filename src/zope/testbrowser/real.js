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

function tb_take_screen_shot(out_path) {
    // The `subject` is what we want to take a screen shot of.
    var subject = content.document;
    var canvas = content.document.createElement('canvas');
    canvas.width = subject.width;
    canvas.height = subject.height;

    var ctx = canvas.getContext('2d');
    ctx.drawWindow(content, 0, 0, subject.width, subject.height, 'rgb(0,0,0)');
    tb_save_canvas(canvas, out_path);
}

function tb_save_canvas(canvas, out_path, overwrite) {
    var io = Components.classes['@mozilla.org/network/io-service;1'
        ].getService(Components.interfaces.nsIIOService);
    var source = io.newURI(canvas.toDataURL('image/png', ''), 'UTF8', null);
    var persist = Components.classes[
        '@mozilla.org/embedding/browser/nsWebBrowserPersist;1'
        ].createInstance(Components.interfaces.nsIWebBrowserPersist);
    var file = Components.classes['@mozilla.org/file/local;1'
        ].createInstance(Components.interfaces.nsILocalFile);
    file.initWithPath(out_path);
    persist.saveURI(source, null, null, null, null, file);
}
