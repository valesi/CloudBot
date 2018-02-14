import re

import requests
from bs4 import BeautifulSoup

from cloudbot import hook

xkcd_re = re.compile(r'(?:.*:)//(?:www\.xkcd\.com|xkcd\.com)(.*)', re.I)
months = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August',
          9: 'September', 10: 'October', 11: 'November', 12: 'December'}


def xkcd_info(xkcd_id, url=False):
    """ takes an XKCD entry ID and returns a formatted string """
    data = requests.get("https://www.xkcd.com/{}/info.0.json".format(xkcd_id)).json()
    date = "{}-{}-{}".format(data['year'], int(data['month']), data['day'])
    url = "https://xkcd.com/$(b){}$(b)/ ".format(xkcd_id) if url else ""
    return "$(b){}$(b): {}[h3]({})[/h3]".format(data['title'], url, date)


def xkcd_search(term):
    p = { "query": term }
    request = requests.get("https://relevantxkcd.appspot.com/process?action=xkcd", params=p)
    results = request.text.splitlines()[2:]
    xkcds = []
    for r in results[:3]:
        xid = r.split(' ')[0]
        xkcds.append(xkcd_info(xid, url=True))
    return " [div] ".join(xkcds)


@hook.regex(xkcd_re)
def xkcd_url(match):
    xkcd_id = match.group(1).split(" ")[0].split("/")[1]
    return xkcd_info(xkcd_id)


@hook.command()
def xkcd(text):
    """[search] - Get a random comic, otherwise search for xkcd comic matching [search]"""
    # Pull a random comic
    if not text:
        # Get latest number
        request = requests.get("https://xkcd.com/info.0.json")
        data = request.json()
        request.close()
        return xkcd_info(str(random.randint(1, data['num'])), url=True)
    else:
        # Latest (0/-1)
        if text in ["0", "-1"]:
            request = requests.get("https://xkcd.com/info.0.json")
            data = request.json()
            request.close()
            return xkcd_info(str(data['num']), url=True)
    if text.isdigit():
        if text == "404":
            return "404 Not Found [div] https://www.xkcd.com/404/"
        return xkcd_info(text, url=True)
    # Search
    return xkcd_search(text)
