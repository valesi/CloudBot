import re

from lxml.etree import HTMLPullParser
import requests

from cloudbot import hook
from cloudbot.hook import Priority, Action
from cloudbot.util import filesize


ENCODED_CHAR = r"%[A-F0-9]{2}"
PATH_SEG_CHARS = r"[A-Za-z0-9!$&'*-.:;=@_~\u00A0-\U0010FFFD]|" + ENCODED_CHAR
QUERY_CHARS = PATH_SEG_CHARS + r"|/"
FRAG_CHARS = QUERY_CHARS


def no_parens(pattern):
    return r"{0}|\(({0}|[\(\)])*\)".format(pattern)


# This will match any URL, blacklist removed and abstracted to a priority/halting system
url_re = re.compile(
    r"""
    https? # Scheme
    ://
    
    # Username and Password
    (?:
        (?:[^\[\]?/<~#`!@$%^&*()=+}|:";',>{\s]|%[0-9A-F]{2})*
        (?::(?:[^\[\]?/<~#`!@$%^&*()=+}|:";',>{\s]|%[0-9A-F]{2})*)?
        @
    )?
    
    # Domain
    (?:
        # TODO Add support for IDNA hostnames as specified by RFC5891
        (?:
            [\-.0-9A-Za-z]+|  # host
            \d{1,3}(?:\.\d{1,3}){3}|  # IPv4
            \[[A-F0-9]{0,4}(?::[A-F0-9]{0,4}){2,7}\]  # IPv6
        )
        (?<![.,?!\]])  # Invalid end chars
    )
    
    (?::\d*)?  # port
    
    (?:/(?:""" + no_parens(PATH_SEG_CHARS) + r""")*(?<![.,?!\]]))*  # Path segment
    
    (?:\?(?:""" + no_parens(QUERY_CHARS) + r""")*(?<![.,!\]]))?  # Query
    
    (?:\#(?:""" + no_parens(FRAG_CHARS) + r""")*(?<![.,?!\]]))?  # Fragment
    """,
    re.IGNORECASE | re.VERBOSE
)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 Cloudbot/1'
}

MAX_RECV = 1000000


@hook.command("title", "t", autohelp=False)
def title(text, chan, conn):
    """[URL] - Gets the HTML title of [URL], or of the most recent URL in chat history"""
    url = None
    if text:
        url = text
    else:
        for line in reversed(conn.history[chan]):
            match = url_re.search(line[2])
            if match:
                url = match.group()
                break
    return get_title(url)


@hook.regex(url_re, priority=Priority.LOW, action=Action.HALTTYPE, only_no_match=True)
def title_re(match):
    return get_title(match.group())


def get_title(url):
    if not url:
        return

    resp_out = None

    try:
        with requests.get(url, headers=HEADERS, stream=True) as r:
            status = r.status_code

            if r.encoding is not None:
                parser = HTMLPullParser(tag='title')
                found = False
                consumed = 0
                for chunk in r.iter_content(512, decode_unicode=True):
                    consumed += len(chunk)
                    parser.feed(chunk)
                    for _, elem in parser.read_events():
                        parser.close()
                        resp_out = elem.xpath('string()').strip() or 'Empty title'
                        found = True
                        break
                    if found is True:
                        break
                    if consumed >= MAX_RECV:
                        resp_out = 'No title in first {}'.format(filesize.size(MAX_RECV, system=filesize.SA))
                        break
                if resp_out is None:
                    resp_out = 'No title'
            else:
                out = ['[h1]Type:[/h1] {}'.format(r.headers['content-type'])]
                size_out = '[h1]Size:[/h1] '
                size = r.headers.get('content-length')
                if size is not None:
                    size = int(size)
                    size_out += filesize.size(size, system=filesize.SA, roundto=2)
                    # Actual byte count is nice
                    if size >= 1000:
                        size_out += ' [h3]({})[/h3]'.format(size)
                else:
                    size_out += 'Unknown'
                out.append(size_out)
                lmod = r.headers.get('last-modified')
                if lmod:
                    out.append('[h1]Modified:[/h1] {}'.format(lmod))
                resp_out = ' [div] '.join(out)

    except Exception as ex:
        return "Error: {}".format(ex)

    if resp_out is None:
        resp_out = 'No info'

    if status >= 400:
        resp_out = '$(red)({})$(c) [div] {}'.format(status, resp_out)

    return resp_out
