"""Searches wikipedia and returns first sentence of article
Scaevolus 2009"""

import re
import requests
from lxml import etree

from cloudbot import hook
from cloudbot.util import formatting


# security
parser = etree.XMLParser(resolve_entities=False, no_network=True)

api_prefix = "https://en.wikipedia.org/w/api.php"
search_url = api_prefix + "?action=opensearch&format=xml"
random_url = api_prefix + "?action=query&format=xml&list=random&rnlimit=1&rnnamespace=0"

paren_re = re.compile('\s*\(.*\)$')
wiki_re = re.compile('wikipedia.org/wiki/([^ ]+)')


@hook.regex(wiki_re)
def wiki_re(match):
    return get_wiki(match.group(1))


@hook.command("wiki", "wikipedia", "w")
def wiki(text):
    """<query> -- Gets first sentence of Wikipedia article on <query>."""
    return get_wiki(text, show_url=True)


def get_wiki(text, show_url=False):
    try:
        request = requests.get(search_url, params={'search': text.strip()})
        request.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        return "Could not get Wikipedia page: {}".format(e)
    x = etree.fromstring(request.text, parser=parser)

    ns = '{http://opensearch.org/searchsuggest2}'
    items = x.findall(ns + 'Section/' + ns + 'Item')

    if not items:
        if x.find('error') is not None:
            return 'Could not get Wikipedia page: %(code)s: %(info)s' % x.find('error').attrib
        else:
            return 'No results found.'

    def extract(item):
        return [item.find(ns + i).text for i in
                ('Text', 'Description', 'Url')]

    title, desc, url = extract(items[0])

    if 'may refer to' in desc:
        title, desc, url = extract(items[1])

    title = paren_re.sub('', title)

    if title.lower() not in desc.lower():
        desc = title + desc

    desc = ' '.join(desc.split())  # remove excess spaces
    desc = formatting.truncate(desc, 350)

    if show_url:
        desc += " [div] [h3]{}[/h3]".format(requests.utils.quote(url, ":/%"))

    return desc
