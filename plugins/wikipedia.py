"""Searches wikipedia and returns first sentence of article
Scaevolus 2009"""

import re
import requests

from cloudbot import hook
from cloudbot.util import formatting


api_url = "https://en.wikipedia.org/w/api.php"

paren_re = re.compile('\s*\(.*\)$')
wiki_re = re.compile('wikipedia.org/wiki/([^\s]+)')


@hook.regex(wiki_re)
def wiki_re(match):
    return wiki(match.group(1), show_url=False)


@hook.command("wiki", "wikipedia", "w", "wik")
def wiki(text, show_url=True):
    """<query> -- Gets first sentence of Wikipedia article on <query>."""
    return get_wiki({"action": "opensearch", "redirects": "resolve", "limit": "2", "search": requests.utils.unquote(text.strip().replace("_", " "))}, show_url=show_url)


@hook.command(autohelp=False)
def wikirand():
    """- Gets a random Wikipedia article."""
    params = {"action": "query", "list": "random", "rnnamespace": "0", "format": "json"}
    try:
        request = requests.get(api_url, params=params)
        request.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        return "Could not get Wikipedia page: {}".format(e)

    return wiki(request.json()["query"]["random"][0]["title"])


def get_wiki(params, show_url=False):
    params["format"] = "json"
    try:
        request = requests.get(api_url, params=params)
        request.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        return "Could not get Wikipedia page: {}".format(e)

    data = request.json()
    if not len(data[1]):
        return 'No results found.'

    idx = 0
    if "may refer to" in data[2][0]:
        idx = 1

    title, snippet, url = data[1][idx], data[2][idx], data[3][idx]

    # remove disambiguation parenthetical from title
    if paren_re.search(title):
        title = paren_re.sub("", title)

    out = snippet if title.lower() in snippet.lower() else title + ": " + snippet

    #snippet = ' '.join(desc.split())  # remove excess spaces
    out = formatting.truncate(out, 350)

    if show_url:
        out += " [div] [h3]{}[/h3]".format(requests.utils.quote(url, safe=":/%"))

    return out

