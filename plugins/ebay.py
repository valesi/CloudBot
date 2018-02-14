"""
ebay.py

Provides a command and URL parser for viewing eBay products.
"""

import requests
import re

from bs4 import BeautifulSoup

from cloudbot import hook


BASE_URL = 'http://www.ebay.{}/itm/{}'
SEARCH_URL = 'http://www.ebay.com/sch/i.html'
ebay_re = re.compile(r"\.ebay\.(\w+(?:\.\w+)?)/(?:.*)?/(\d+)", re.I)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1',
    'Referer': 'http://www.ebay.com/'
}

# Max 1600
IMAGE_WIDTH = 1600


def get_info(cc, item_id, show_url=False):
    """ Finds auction info and returns a formatted string """
    r = requests.get(BASE_URL.format(cc, item_id), headers=HEADERS)

    if not r.status_code == 200:
        return "Failed to get auction details"

    body = BeautifulSoup(r.text).body
    r.close()
    i = {}

    title = body.h1
    try:
        title.span.decompose()
    except:
        pass
    # Kill extra whitespace
    i["title"] = " ".join(title.text.split())
    out = ["[h1]eBay:[/h1] {title}"]

    # Bid
    bid_price = body.find(id="prcIsum_bidPrice")
    if bid_price:
        i["bid_price"] = bid_price.text.strip()
        bid = "[h1]Bid:[/h1] {bid_price}"
        foreign_price = body.find(id="convbidPrice")
        try:
            foreign_price.span.decompose()
        except:
            pass
        if foreign_price:
            i["bid_foreign_price"] = foreign_price.text.strip()
            bid += " ({bid_foreign_price})"
        out.append(bid)

    buy = None
    # Discount Buy
    sale_price = body.find(id="mm-saleDscPrc")
    if sale_price:
        i["buy_price"] = sale_price.text.strip()
        buy = "[h1]Buy:[/h1] {buy_price} ($(red)Sale$(c))"
    # Buy
    buy_price = body.find(id="prcIsum")
    if buy_price:
        i["buy_price"] = buy_price.text.strip()
        buy = "[h1]Buy:[/h1] {buy_price}"
    if buy:
        foreign_price = body.find(id="convbinPrice")
        try:
            foreign_price.span.decompose()
        except:
            pass
        if foreign_price:
            i["buy_foreign_price"] = foreign_price.text.strip()
            buy += " ({buy_foreign_price})"
        # Best offer
        if body.find(id="boBtn_btn"):
            buy += " ($(green)OBO$(c))"
        out.append(buy)

    # Time left
    time_left = body.find(id="vi-cdown_timeLeft")
    if time_left:
        i["time_left"] = time_left.text.strip()
        out.append("[h1]Ends:[/h1] {time_left}")

    # Free shipping (not sure if this is useful)
    #shipping = body.find(id="fshippingCost")
    #if shipping:
    #    if shipping.text.strip().lower() == "free":
            # TODO get free shipping countries
    #        out += " ^ \x0304Ship:\x0F FREE (USA)"
    #    else:
    #        i["ship_cost"] = " ".join(shipping.text.split())
    #        out += " ^ \x0304Ship:\x0F {ship_cost}"

    # Condition
    cond = body.find(id="vi-itm-cond")
    i["cond"] = cond.text.strip()
    out.append("[h1]Cond:[/h1] {cond}")

    # Image
    image = body.find(id="icImg")
    if image and image["src"]:
        i["image"] = image["src"]
        # 2 types of images are found: "$_##.jpg" and "s-l500.jpg". Get bigger image
        m = re.search(r".*l(\d+)\.jpg", image["src"], re.I)
        if m:
            i["image"] = image["src"].replace(m.group(1), str(IMAGE_WIDTH))
        else:
            m = re.search(r"\$_(\d\d)\.jpg", image["src"], re.I)
            if m:
                # "$_57.jpg" appears to be largest image
                i["image"] = image["src"].replace(m.group(1), "57")
        # If m wasn't a match, maybe use src="viEnlargeImgLayer_img_ctr"
        out.append("[h1]Img:[/h1] {image}")

    ## Clean up
    # Remove cents if price is whole dollar etc
    for price in ['bid_price', 'buy_price', 'bid_foreign_price', 'buy_foreign_price', 'ship_cost']:
        try:
            i[price] = i[price].replace(".00", "")
        except:
            pass

    if show_url:
        out.append("[h3]{}".format(BASE_URL.format(cc, item_id)))

    # Kill any and all details' surrounding whitespace
    for k, v in i.items():
        i[k] = v.strip()

    return " [div] ".join(out).format(**i)


@hook.regex(ebay_re)
def ebay_url(match):
    cc = match.group(1)
    auction_id = match.group(2)

    return get_info(cc, auction_id)


@hook.command()
def ebay(text):
    """<product> - searches eBay for <product>"""
    if text.isdigit():
        return get_info('com', text, show_url=True)

    search = ' '.join(text.split())

    params = {'_nkw': search}

    r = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=10.0)

    if not r.text:
        return 'Search failed. Hmmm.'

    soup = BeautifulSoup(r.text)
    listing = soup.find('ul', {'id': 'ListViewInner'})

    for tag in listing or []:
        if tag.name == 'li':
            return get_info('com', tag['listingid'], show_url=True)
    return 'Nothing?'
