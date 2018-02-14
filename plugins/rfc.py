import re
import requests

from bs4 import BeautifulSoup
from cloudbot import hook


rfc_re = re.compile(r"https?://(?:tools\.ietf\.org/\w+/|www\.rfc-editor\.org/\w+/)rfc(\d+){,4}")
BASE_URL = "https://tools.ietf.org/html/rfc{}"


def get_info(rfc_id, show_url=False):
    url = BASE_URL.format(rfc_id)

    # Only request first 10 KiB
    headers={"Range": "bytes=0-10240"}
    try:
        req = requests.get(url, headers=headers, timeout=5.0, stream=True)
        req.raise_for_status()
    except Exception as ex:
        return "Error reaching {}: {}".format(url, ex)

    soup = BeautifulSoup(req.text, "lxml")
    date = "N/A"

    for line in soup.body.pre.text[:2000].split('\n'):
        # Assuming Date is right-justified and ends with 4 year digits
        if len(line) > 64 and line[-4:].isdigit():
            date = line[-20:].strip()
            break

    out = []
    out.append(soup.title.text.split(" - ", 1)[1].strip())
    out.append("[h1]Date:[/h1] " + date)
    if show_url:
        out.append("[h3]{}[/h3]".format(url))
    return " [div] ".join(out)


@hook.regex(rfc_re)
def rfc_re(match):
    return get_info(match.group(1))


@hook.command()
def rfc(text):
    """<number> - Gets the title, publish date, and link to IEFT RFCs."""
    if not text.isdigit():
        return "Invalid RFC number"

    return get_info(text, show_url=True)

