import urllib.parse

import requests
import requests.exceptions
from bs4 import BeautifulSoup

from cloudbot import hook


@hook.command("down", "offline", "up")
def down(bot, text):
    """<url> - checks if <url> is online or offline
    :type text: str
    """

    if "://" not in text:
        text = 'http://' + text

    #text = 'http://' + urllib.parse.urlparse(text).netloc
    up = False

    try:
        r = requests.get(text, headers={"user-agent":bot.user_agent}, timeout=10.0)
        if r.status_code == requests.codes.ok:
            up = True
        else:
            reason = r.status_code
    except requests.exceptions.HTTPError:
        reason = "HTTP error"
    except ConnectionError:
        reason = "connection error"
    except requests.exceptions.SSLError as ex:
        reason = "TLS error"
    except requests.exceptions.TooManyRedirects:
        reason = "too many redirects"
    except requests.exceptions.Timeout:
        reason = "timeout after 10s"

    if up:
        return text + " looks $(green)up$(c) from here"
    else:
        return "{} looks $(red)down$(c) from here: {}".format(text, reason)


@hook.command()
def isup(text):
    """<url> - uses isup.me to check if <url> is online or offline
    :type text: str
    """
    url = text.strip()

    # slightly overcomplicated, esoteric URL parsing
    scheme, auth, path, query, fragment = urllib.parse.urlsplit(url)

    domain = auth or path

    try:
        response = requests.get('http://isup.me/' + domain)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        return "Failed to get status."
    if response.status_code != requests.codes.ok:
        return "Failed to get status."

    soup = BeautifulSoup(response.text, 'lxml')

    content = soup.find('div').text.strip()

    if "not just you" in content:
        return "It's not just you. {} looks $(red)down$(c)".format(url)
    elif "is up" in content:
        return "It's just you. {} is $(green)up$(c)".format(url)
    else:
        return "Huh? That doesn't look like a site on the interweb."
