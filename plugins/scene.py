"""
scene.py

Provides commands for searching scene releases using pre.corrupt-net.org.

Created By:
    - Ryan Hitchman <https://github.com/rmmh>

Modified By:
    - Luke Rogers <https://github.com/lukeroge>

Converted to pre.corrupt-net.org By:
    - whocares <http://github.com/whocares-openscene>

License:
    GPL v3
"""

import requests
from datetime import datetime
from bs4 import BeautifulSoup

from cloudbot import hook
from cloudbot.util import timeformat


HEADERS = {'Accept-Language': 'en-US'}


@hook.command("pre", "scene")
def pre(text):
    """pre <query> -- searches scene releases using pre.corrupt.org"""

    try:
        request = requests.get("https://pre.corrupt-net.org/search.php", params={"search": text}, headers=HEADERS, timeout=30.0)
        request.raise_for_status()
    except requests.exceptions.HTTPError as e:
        return 'Unable to fetch results: {}'.format(e)

    request.close()
    html = BeautifulSoup(request.text, "lxml")

    cols = html.find_all("td", limit=5)
    if len(cols) < 2 or cols[0].text.strip().startswith("Nothing found"):
        return "No results"

    #section = cols[0].text.strip()
    name = cols[1].text.strip()
    files = cols[2].text.strip().replace("F", " files")
    size = cols[3].text.strip() + "iB"
    date = cols[4].text.strip() + "UTC"

    # parse date/time
    date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S%Z")
    since = timeformat.time_since(date, datetime.utcnow(), simple=True)

    return '{} [div] {} [div] {} [div] {} ({} ago)'.format(name, size, files, date, since)

