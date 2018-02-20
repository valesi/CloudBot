"""
newegg.py

Provides a command and URL parser for viewing newegg products.

Created By:
    - Luke Rogers <https://github.com/lukeroge>

License:
    GPL v3
"""

import json
import re

import requests

from cloudbot import hook
from cloudbot.util import formatting, web

# CONSTANTS

ITEM_URL = "https://www.newegg.com/Product/Product.aspx?Item={}"

API_PRODUCT = "https://www.ows.newegg.{}/Products.egg/{}"
API_SEARCH = "https://www.ows.newegg.com/Search.egg/Advanced"

NEWEGG_RE = re.compile(r"(?:(?:www\.newegg\.(com|ca))(?:/global/(?:\w+))?/Product/Product\.aspx\?Item=)([-_a-zA-Z0-9]+)", re.I)

CURRENCY = {"com": "USD", "ca": "CAD"}


# OTHER FUNCTIONS

def format_item(tld, item, show_url=True):
    """ takes a newegg API item object and returns a description """
    additional = item['Additional']
    item = item['Basic']

    start = "[h1]Newegg:[/h1] {} [div] ".format(formatting.truncate(item["Title"], 160))

    out = []

    if item["FinalPrice"] == item["OriginalPrice"] or not item["OriginalPrice"]:
        price = "$(b){}$(b)".format(item["FinalPrice"])
    else:
        price = "$(b){FinalPrice}$(b), was {OriginalPrice}".format(**item)
    out.append("{}{}".format(CURRENCY[tld], price))

    # format the rating nicely if it exists
    if item["ReviewSummary"]["TotalReviews"]:
        out.append("{}/5 ({} ratings)".format(item["ReviewSummary"]["Rating"], item["ReviewSummary"]["TotalReviews"]))

    tags = []

    if not item["Instock"]:
        tags.append("$(red)Out Of Stock$(c)")
    if item["IsFreeShipping"]:
        tags.append("Free Shipping")
    if item.get("IsPremierItem"):
        tags.append("Premier")
    if item["IsFeaturedItem"]:
        tags.append("Featured")
    if additional["IsShellShockerItem"]:
        tags.append("$(b)SHELL SHOCKER$(b)")
    if tags:
        out.append(", ".join(tags))

    if show_url:
        out.append("[h3]{}[/h3]".format(ITEM_URL.format(tld, item["NeweggItemNumber"])))

    return start + " [div] ".join(out)


# HOOK FUNCTIONS

@hook.regex(NEWEGG_RE)
def newegg_url(match):
    tld = match.group(1)
    item_id = match.group(2)

    try:
        item = requests.get(API_PRODUCT.format(tld, item_id)).json()
        return format_item(tld, item, show_url=False)
    except Exception as ex:
        return "Failed to get info: " + str(ex)


# @hook.command()
def newegg(text, admin_log, reply):
    """<item name> - searches newegg.com for <item name>"""

    # form the search request
    request = {
        "Keyword": text,
        "Sort": "FEATURED"
    }

    # submit the search request
    try:
        request = requests.post(
            API_SEARCH,
            data=json.dumps(request).encode('utf-8'),
            headers=HEADERS
        )
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        return "Unable to find product: {}".format(e)

    r = request.json()

    if not request.ok:
        if r.get("Message"):
            msg = "{ExceptionMessage}\n{ExceptionType}\n{StackTrace}".format(**r).replace("\r", "")
            url = web.paste(msg)
            admin_log("Newegg API Error: {ExceptionType}: {url}".format(url=url, **r))
            return "Newegg Error: {Message} (\x02{code}\x02)".format(code=request.status_code, **r)
        else:
            reply("Unknown error occurred.")
            request.raise_for_status()
            return

    # get the first result
    if r["ProductListItems"]:
        return format_item("com", r["ProductListItems"][0])
    else:
        return "No results found."
