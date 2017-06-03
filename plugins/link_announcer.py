import requests
import re
from bs4 import BeautifulSoup
from contextlib import closing
from cloudbot import hook

# This will match any URL except the patterns defined in blacklist.
blacklist_re = '.*(ebay\.(?:\w+(?:\.\w+)?)|reddit\.com|redd\.it|youtube\.com|youtu\.be|spotify\.com|twitter\.com|twitch\.tv|ama?zo?n\.(?:\w+(?:\.\w+)?)|xkcd\.com|steamcommunity\.com|steampowered\.com|newegg\.com|soundcloud\.com|speedtest\.net|vimeo\.com).*'
url_re = re.compile('(?!{})http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+~]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'.format(blacklist_re), re.I)

opt_out = []

traditional = [
    (1024 ** 5, 'PiB'),
    (1024 ** 4, 'TiB'),
    (1024 ** 3, 'GiB'),
    (1024 ** 2, 'MiB'),
    (1024 ** 1, 'KiB'),
    (1024 ** 0, 'B'),
]

HEADERS = {
    'Accept-Language': 'en-US,en;q=0.5',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36'
}


def bytesto(bytes, system = traditional):
    """ converts bytes to something """
    bytes = int(bytes)
    for factor, suffix in system:
        if bytes >= factor:
            break
    amount = int(bytes/factor)
    return str(amount) + suffix


@hook.command("title", "t", autohelp=False)
def title(text, chan, conn):
    """[URL] - Gets the HTML title of [URL], or of the lastest URL in chat history"""
    url = None
    if text:
        match = url_re.search(text)
        if not match:
            return
        url = match.group()
    else:
        for line in conn.history[chan].__reversed__():
            match = url_re.search(item[2])
            if match:
                url = match.group()
                break
    return get_title(url) if url else None


@hook.regex(url_re)
def title_re(match, chan, conn):
    if chan in opt_out:
        return
    url = match.group()
    if re.search(blacklist_re, url):
        return

    return get_title(url)


def get_title(url):
    try:
        with closing(requests.get(url, headers=HEADERS, stream=True, timeout=5)) as r:
            if not r.encoding:
                r.close()
                content = r.headers['content-type']
                size = bytesto(r.headers['content-length'])
                return "[h1]Content Type:[/h1] {} [div] [h1]Size:[/h1] {}".format(content, size)
            # Sites advertising ISO-8859-1 are often lying
            if r.encoding == 'ISO-8859-1':
                r.encoding = "utf-8"
            content = r.raw.read(1000000+1, decode_content=True)
            if len(content) > 1000000:
                r.close()
                return
            html = BeautifulSoup(content)
            r.close()
            return " ".join(html.title.text.strip().splitlines())
    except ReadTimeout as ex:
        return "Error: Connection timeout"
