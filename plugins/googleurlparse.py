import re
from urllib.parse import parse_qs, urlsplit

from cloudbot import hook


URL_RE = re.compile(r'((www\.)?google\.(\w+(\.\w+)?)/url\?[^ ]+)', re.I)


@hook.regex(URL_RE)
def google_url(match):
    return parse_qs(urlsplit(match.group())[3])['url']
