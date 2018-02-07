import json
import re

import requests
from lxml import html

from cloudbot import hook

speedtest_re = re.compile(r'https?://(?:\w+)\.speedtest\.net/(?:my-)?result/(d?/?[0-9]+)', re.I)
base_url = "http://www.speedtest.net/result/{}"


@hook.regex(speedtest_re)
def speedtest_url(match, bot):
    test_id = match.group(1)
    url = base_url.format(test_id)

    request = requests.get(url)
    request.raise_for_status()

    # Disgusting regex hack to get data from JS literal
    reg = re.search(r'window\.OOKLA\.INIT_DATA={"result":([^}]+})', request.text)
    data = json.loads(reg.group(1))

    out = []
    out.append("[h1]DL:[/h1] {0:.2f} Mbps".format(float(data["download"])/1000))
    out.append("[h1]UL:[/h1] {0:.2f} Mbps".format(float(data["upload"])/1000))
    out.append("[h1]Ping:[/h1] {}ms".format(data["latency"]))
    out.append("[h1]ISP:[/h1] {}".format(data["isp_name"]))
    out.append("[h1]Server:[/h1] {} [h3]({}, {})[/h3]".format(data["sponsor_name"], data["server_name"], data["country_code"]))

    return " [div] ".join(out)

