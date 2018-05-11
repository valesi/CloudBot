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

    response = requests.get('https://www.etymonline.com/search', params={"q": text})

    try:
        response.raise_for_status()
    except HTTPError as e:
        reply("Error reaching etymonline.com: {}".format(e.response.status_code))
        raise

    soup = BeautifulSoup(response.text, "lxml")

    result = soup.find('a', class_=re.compile("word--.+"))

    if not result:
        return 'No etymology found'

    title = result.div.p.text.strip()
    etym = result.div.section.text.strip()
    url = result['href']

    # Strip ellipsis
    if etym.endswith(" …"):
        etym = etym[:-2]

    out = '[h1]{}:[/h1] {}'.format(title, etym)

    if len(out) > 400:
        out = out[:out.rfind(' ', 0, 400)] + ' ...'

    return "{} [div] [h3]http://www.etymonline.com{}[/h3]".format(out, url)
