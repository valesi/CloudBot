import re
import urllib.parse

import requests
from lxml import etree
from requests import HTTPError

from cloudbot import hook
from cloudbot.util import web


# security
parser = etree.XMLParser(resolve_entities=False, no_network=True)

api_url = 'https://api.wolframalpha.com/v2/query'
query_url = 'https://www.wolframalpha.com/input/?i={}'

show_pods = {'Input': True, 'Result': True, 'UnitConversion': True, 'AdditionalConversion': True}


@hook.on_start()
def on_start(bot):
    global api_key
    api_key = bot.config.get("api_keys", {}).get("wolframalpha", None)


@hook.command("wolframalpha", "wa", "conv", "convert")
def wolframalpha(text, message):
    """<query> -- Computes <query> using Wolfram Alpha."""
    if not api_key:
        return "Missing API key"

    params = {
        'input': text,
        'format': "plaintext",
        'appid': api_key
    }
    request = requests.get(api_url, params=params)
    url = query_url.format(urllib.parse.quote_plus(text))

    try:
        request.raise_for_status()
    except HTTPError as e:
        message("Error getting query: {}".format(e.response.status_code))
        raise

    if request.status_code != requests.codes.ok:
        return "WA error: {} [div] {}".format(request.status_code, url)

    result = etree.fromstring(request.content, parser=parser)

    pod_texts = {}
    for pod in result.xpath("//pod"):
        primary = "primary" in pod.attrib.keys()
        pid = pod.attrib["id"]
        title = pod.attrib["title"]
        # Ignore pods we don't care about
        if not primary and (not pid in list(show_pods) or not show_pods[pid]):
            # Sometimes Result will have a different id
            if not title in list(show_pods) or not show_pods[title]:
                continue

        results = []
        # Format subpods
        #for subpod in pod.xpath('subpod/plaintext/text()'):
        for subpod in pod.xpath('subpod'):
            podinfo = "[h2]{}[/h2] ".format(subpod.attrib['title']) if subpod.attrib['title'] else ""

            podresults = []
            for subinfo in subpod.xpath('plaintext/text()'):
                # Itemize units (separate lines)
                values = []
                for item in subinfo.split('\n'):
                    # Format "key | value"
                    item = re.sub(r"^([\w\s]+)\s+\|\s+", "[h4]\\1:[/h4] ", item)
                    # Replace inner '|' (eg weather forecast)
                    item = re.sub(r"(\))\s+\|\s+", "\\1 [h2]-[/h2] ", item)
                    # Colorize "(extra info)", preceeded with whitespace
                    item = re.sub(r"\s+(\([^()]+\))", " [h3]\\1[/h3]", item)
                    # Remove extra spaces
                    item = re.sub(r'\s{2,}', ' ', item)
                    # Add
                    values.append(item.strip())
                # Put 'em back together
                subinfo = " [div] ".join(values)
                if subinfo:
                    podresults.append(subinfo)

            podinfo += ''.join(podresults)
            results.append(podinfo)


        if results:
            info = " [div] ".join(results)
            if pid == "Input":
                # Strip verbose "Input interp/info"
                title = title.replace(" interpretation", "").replace(" information", "")
                # Strip open/closing parentheses around input
            if pid in ["AdditionalConversion", "UnitConversion"]:
                # Reduce verbosity (just print "Conversions")
                title = "C" + title[title.index("conv") + 1:]
            title = "[h1]{}[/h1] ".format(title)
            pod_texts[pid] = title + info

    # NOTHING??
    if not pod_texts:
        return "WA ain't found shit! [div] " + url

    # Sometimes input will be the only pod from filtering
    if "Input" in pod_texts and len(pod_texts) == 1:
        return "Extra info filtered [div] " + url

    # get the URL for a user to view this query in a browser
    try:
        short_url = " [div] [h1]Web[/h1] " + web.shorten(url)
    except:
        short_url = None
    if short_url:
        pod_texts['Input'] += short_url

    # Append input to result
    if "Input" in pod_texts and "Result" in pod_texts:
        pod_texts['Result'] = "{} [div] {}".format(pod_texts['Result'], pod_texts['Input'])
        del pod_texts['Input']

    # Print result/input first
    if "Input" in pod_texts:
        message(pod_texts['Input'])
        del pod_texts['Input']
    if "Result" in pod_texts:
        message(pod_texts['Result'])
        del pod_texts['Result']

    # Print remaining info
    for key in pod_texts:
        message(pod_texts[key])

