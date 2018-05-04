import re
from contextlib import closing

import requests
from bs4 import BeautifulSoup

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
    try:
        with closing(requests.get(url, headers=HEADERS, stream=True, timeout=10)) as r:
            r.raise_for_status()
            if not r.encoding:
                content = r.headers['content-type']
                size = filesize.size(int(r.headers['content-length']), system=filesize.si)
                return "[h1]Content Type:[/h1] {} [div] [h1]Size:[/h1] {}".format(content, size)

            content = r.raw.read(MAX_RECV + 1, decode_content=True)
            # Sites advertising ISO-8859-1 are often lying
            if r.encoding == 'ISO-8859-1':
                r.encoding = "utf-8"
            encoding = r.encoding

        if len(content) > MAX_RECV:
            return

        html = BeautifulSoup(content, "lxml", from_encoding=encoding)

        if html.title:
            return " ".join(html.title.text.strip().splitlines())
        else:
            return "No title"
    except Exception as ex:
        return "Error: {}".format(ex)
