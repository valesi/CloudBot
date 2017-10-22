# Plugin by GhettoWizard and Scaevolus

from lxml import html

import requests

from cloudbot import hook

@hook.command("e", "etymology")
def etymology(text):
    """<word> - retrieves the etymology of <word> (via etymonline.com)
    :type text: str
    """

    url = 'http://www.etymonline.com/search'

    response = requests.get(url, params={"q": text})
    if response.status_code != requests.codes.ok:
        return "Error reaching etymonline.com: {}".format(response.status_code)

    h = html.fromstring(response.text)

    etym = h.xpath('//h1')

    if not etym:
        return 'No etymology found for {} :('.format(text)

    etym = etym[0].text_content()
    text = h.xpath('//section')[0].text_content()
    url = h.xpath('//a')[1].attrib['href']

    # Strip ellipsis
    if text.endswith(" …"):
        text = text[:-2]

    out = '[h1]{}:[/h1] {}'.format(" ".join(etym.split()), " ".join(text.split()))

    if len(out) > 400:
        out = out[:out.rfind(' ', 0, 400)] + ' ...'

    return "{} [div] [h3]http://www.etymonline.com{}[/h3]".format(out, url)
