"""
Etymology plugin

Authors:
    - GhettoWizard
    - Scaevolus
    - linuxdaemon <linuxdaemon@snoonet.org>
"""
import re

import requests
from bs4 import BeautifulSoup
from requests import HTTPError

from cloudbot import hook


@hook.command("e", "etymology")
def etymology(text, reply):
    """<word> - retrieves the etymology of <word>
    :type text: str
    """

    url = 'http://www.etymonline.com/search'

    response = requests.get(url, params={"term": text})

    try:
        response.raise_for_status()
    except HTTPError as e:
        reply("Error reaching etymonline.com: {}".format(e.response.status_code))
        raise

    if response.status_code != requests.codes.ok:
        return "Error reaching etymonline.com: {}".format(response.status_code)

    soup = BeautifulSoup(response.text, "lxml")

    block = soup.find('div', class_=re.compile("word--.+"))

    if not block:
        return 'No etymology found for {} :('.format(text)

    etym = ' '.join(e.text for e in block.div)

    etym = ' '.join(etym.splitlines())

    # Strip ellipsis
    if text.endswith(" …"):
        text = text[:-2]

    out = '[h1]{}:[/h1] {}'.format(" ".join(etym.split()), " ".join(text.split()))

    if len(out) > 400:
        out = out[:out.rfind(' ', 0, 400)] + ' ...'

    return "{} [div] [h3]http://www.etymonline.com{}[/h3]".format(out, url)
