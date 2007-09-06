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
