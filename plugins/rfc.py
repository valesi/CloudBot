import re
import requests

from bs4 import BeautifulSoup
from cloudbot import hook


rfc_re = re.compile(r"https?://(?:tools\.ietf\.org/\w+/|www\.rfc-editor\.org/\w+/)rfc(\d+){,4}")
BASE_URL = "https://tools.ietf.org/html/rfc{}"


def get_info(rfc_id, show_url=False):
    # Fetch the first 2001 bytes
    url = BASE_URL.format(rfc_id)

    # Only request first 10 KiB
    headers={"Range": "bytes=0-10240"}
    try:
        req = requests.get(url, headers=headers, timeout=5.0, stream=True)
    except Exception as ex:
        return "Error reaching IETF site: {}".format(ex)

    if not req.ok:
        return "tools.ietf.org returned HTTP {}".format(req.status_code)

    soup = BeautifulSoup(req.text, "lxml")
    title = soup.title.text.strip().split(" - ", 1)[1]
    date = "N/A"
    pre = soup.body.pre
    # Not \r\n... First 1000 characters
    for line in pre.text[:1000].split('\n'):
        print("line: {}".format(line))
        if len(line) > 64 and line[-4:].isdigit():
            date = line[-20:].strip()
            break

    out = "{} [div] [h1]Date:[/h1] {}".format(title, date)
    if show_url:
        out += " [div] [h3]{}[/h3]".format(url)
    return out


@hook.regex(rfc_re)
def rfc_re(match):
    return get_info(match.group(1))


@hook.command()
def rfc(text):
    """<number> - Gets the title and a link to an RFC"""
    if not text.isdigit():
        return "Invalid RFC number"

    return get_info(text, show_url=True)

