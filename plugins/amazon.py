import re

import requests
from bs4 import BeautifulSoup
from requests import HTTPError

from cloudbot import hook
from cloudbot.util import web, formatting


SEARCH_URL = "https://www.amazon.{}/s/"
PAGE_URL = "https://www.amazon.{}/{}/{}"
DEFAULT_TLD = "com"

AMAZON_RE = re.compile(r'https?://(?:.+\.)?ama?zo?n\.(\w+(?:\.\w+)?)/(?:.*/(?:exec/obidos/ASIN/|o/|gp/product/|(?:(?:[^"\'/]*)/)?dp/|))?(B?[A-Z0-9]{9,10})', re.I)
SHORT_RE = re.compile(r'https?://(a\.co|amzn\.to)/\w+', re.I)


@hook.regex(AMAZON_RE)
def amazon_url(match, reply):
    cc = match.group(1)
    asin = match.group(2)
    return amazon(asin, reply, _parsed=cc)


@hook.regex(SHORT_RE)
def amazon_short_url(match, reply):
    '''Expand redirect from Amazon URL shorteners'''
    try:
        loc = web.expand(match.group(0))
        match = AMAZON_RE.search(loc)
        if match:
            return amazon_url(match, reply)
        else:
            return url + " didn't redirect to an Amazon product"
    except Exception as ex:
        reply('Failed to get redirect: {}'.format(ex))
        raise


@hook.command("amazon", "az", "amzn")
def amazon(text, reply, _parsed=False):
    """<query> -- Searches Amazon for query"""
    headers = {
        'User-Agent': 'Mozilla/5.0 CloudBot/1',
        'Referer': 'https://www.amazon.com/'
    }
    params = {
        'url': 'search-alias',
        'field-keywords': text.strip()
    }

    # if input is from a link parser, we want its TLD
    request = requests.get(SEARCH_URL.format(_parsed if _parsed else DEFAULT_TLD), params=params, headers=headers)

    try:
        request.raise_for_status()
    except HTTPError:
        reply("Amazon API error occurred.")
        raise

    soup = BeautifulSoup(request.text, 'lxml')

    # check if there are any results on the amazon page
    results = soup.find('div', {'id': 'atfResults'})
    if not results:
        return 'Not found.'

    # get all search results
    results = results.find('ul', {'id': 's-results-list-atf'}).find_all('li', {'class': 's-result-item'})

    # loop over all results, as not all results are products
    for result in results:
        item = parse_item(result, _parsed, reply)
        if item:
            return item


def parse_item(item, _parsed, reply):
    asin = item['data-asin']

    # here we use dirty html scraping to get everything we need
    title = item.find('a', {'class': 's-access-detail-page'})
    if not title:
        return None
    out = [formatting.truncate(title.text, 200)]

    # add seller/maker if it isn't already in the title
    try:
        # element immediately after product title div, containing small spans of secondary color
        byline = title.parent.find_next_sibling('div', class_=['a-row', 'a-spacing-none']).find_all('span', class_=['a-size-small', 'a-color-secondary'])
        if byline:
            # first word is 'by' (and translations), so we skip it
            bywords = ''.join([s.text for s in byline[1:]]).split()
            # all words in title in any order
            # (doesn't work with multiple authors. 'and' and commas etc)
            if not all(word.lower() in out[0].lower() for word in bywords):
                out.append(' '.join(bywords))
    except:
        pass

    price= item.find('span', {'class': ['sx-price', 'sx-price-large']})
    if price:
        price = '{}{}.{}'.format(price.find('sup', {'class': 'sx-price-currency'}).text,
                                 price.find('span', {'class': 'sx-price-whole'}).text,
                                 price.find('sup', {'class': 'sx-price-fractional'}).text)
    else:
        price = item.find('span', {'class': ['s-price', 'a-color-price']})
        if price:
            price = price.text
        else:
            price = item.find('span', {'class': ['s-price', 'a-color-base']})
            price = price.text if price else 'No Price'
    out.append(price)

    # use a bit of BS4 and regex to get the ratings
    rating = item.find('i', {'class': 'a-icon-star'})
    if rating:
        # get the rating
        rating = rating.span.text.split()[0].replace(",", ".")
        # get the rating count
        pattern = re.compile(r"(product-reviews|#customerReviews)")
        num_ratings = item.find('a', {'href': pattern}).text.replace(".", ",")
        # format the rating and count into a nice string
        rating_str = "{}/5 ({} ratings)".format(rating, num_ratings)
    else:
        rating_str = "No Ratings"
    out.append(rating_str)

    tags = []
    # tags!
    if item.find('i', {'class': 'a-icon-prime'}):
        tags.append("Prime")
    if item.find('i', {'class': 'sx-bestseller-badge-primary'}):
        tags.append("Bestseller")

    # we use regex because we need to recognise text for this part
    # the other parts detect based on html tags, not text
    if re.search(r"(Kostenlose Lieferung|Livraison gratuite|FREE Shipping|Envío GRATIS"
                 r"|Spedizione gratuita)", item.text, re.I):
        tags.append("Free Shipping")

    # join all the tags into a string
    if tags:
        out.append(", ".join(tags))

    # finally, assemble everything into the final string, and return it!
    out = "[h1]Amazon:[/h1] " + " [div] ".join(out)
    return out if _parsed else out + " [div] [h3]https://www.amazon.com/dp/{}/[/h3]".format(asin)
