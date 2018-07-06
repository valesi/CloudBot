import html
import random
import re
from datetime import datetime

import requests
from yarl import URL

from cloudbot import hook
from cloudbot.util import timeformat, formatting

reddit_re = re.compile(
    r"""
    https? # Scheme
    ://

    # Domain
    (?:
        redd\.it|
        (?:www\.|old\.)?reddit\.com/r
    )

    (?:/(?:[A-Za-z0-9!$&-.:;=@_~\u00A0-\u10FFFD]|%[A-F0-9]{2})*)*  # Path

    (?:\?(?:[A-Za-z0-9!$&-;=@_~\u00A0-\u10FFFD]|%[A-F0-9]{2})*)?  # Query
    """,
    re.IGNORECASE | re.VERBOSE
)

base_url = "https://reddit.com/r/{}"
short_url = "https://redd.it/{}"


def api_request(url, bot):
    """
    :type url: yarl.URL
    :type bot: cloudbot.bot.CloudBot
    """
    url = url.with_query("").with_scheme("https") / ".json"
    r = requests.get(str(url), headers={'User-Agent': bot.user_agent})
    r.raise_for_status()
    return r.json()


def format_output(item, show_url=False):
    """ takes a reddit post and returns a formatted string """
    item["title"] = html.unescape(formatting.truncate(item["title"], 200))
    item["link"] = short_url.format(item["id"])

    # Fix some URLs
    if not item["is_self"] and item["url"]:
        # Use .gifv links for imgur
        if "imgur.com/" in item["url"] and item["url"].endswith(".gif"):
            item["url"] += "v"
        # Fix i.reddituploads.com crap ("&amp;" in URL)
        if "i.reddituploads.com/" in item["url"]:
            # Get i.redditmedia.com preview (first one is full size)
            item["url"] = item["preview"]["images"][0]["source"]["url"]
        # Unescape since reddit gives links for HTML
        item["url"] = html.unescape(item["url"])

    raw_time = datetime.fromtimestamp(int(item["created_utc"]))
    item["timesince"] = timeformat.time_since(raw_time, count=1, simple=True)

    item["comments"] = formatting.pluralize_auto(item["num_comments"], 'comment').replace(",", "")
    item["points"] = formatting.pluralize_auto(item["score"], 'point').replace(",", "")

    out = []

    if show_url and item["link"]:
        out.append("[h3]{link}[/h3]")

    out.append("{title}")

    if not item["is_self"]:
        out.append("{url}")
    if item["over_18"]:
        out.append("$(red)NSFW$(c)")

    out.extend(["/r/{subreddit}", "/u/{author}", "{timesince} ago", "{points}", "{comments}"])

    if item["gilded"]:
        item["gilded"] = formatting.pluralize_auto(item["gilded"], 'gild')
        out.append("$(yellow){gilded}$(c)")

    return "[h1]Reddit:[/h1] " + " [div] ".join(out).format(**item)


@hook.regex(reddit_re, singlethread=True)
def reddit_url(match, bot):
    url = match.group()
    url = URL(url).with_scheme("https")

    if url.host.endswith("redd.it"):
        response = requests.get(url, headers={'User-Agent': bot.user_agent})
        if response.status_code != requests.codes.ok:
            return "HTTP {}".format(response.status_code)
        url = URL(response.url).with_scheme("https")

    data = api_request(url, bot)
    if isinstance(data, list):
        item = data[0]["data"]["children"][0]["data"]
    #elif isinstance(data, dict):
        #item = data["data"]["children"][random.randint(0,9)]["data"]
        #return

    return format_output(item)


@hook.command(autohelp=False, singlethread=True)
def reddit(text, bot, reply):
    """[subreddit] [n] - gets a random post from <subreddit>, or gets the [n]th post in the subreddit"""
    id_num = None

    if text:
        # clean and split the input
        parts = text.lower().strip().split()
        url = base_url.format(parts.pop(0).strip())

        # find the requested post number (if any)
        if parts:
            try:
                id_num = int(parts[0]) - 1
            except ValueError:
                return "Invalid post number."
    else:
        url = "https://reddit.com"

    try:
        data = api_request(URL(url), bot)
    except Exception as e:
        reply("Error: " + str(e))
        raise

    data = data["data"]["children"]

    # get the requested/random post
    if id_num is not None:
        try:
            item = data[id_num]
        except IndexError:
            length = len(data)
            return "Invalid post number. Number must be between 1 and {}.".format(length)
    else:
        item = random.choice(data)

    return format_output(item["data"], show_url=True)
