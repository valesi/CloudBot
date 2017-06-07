from datetime import datetime
import re
import random
import asyncio
import functools
import urllib.parse

import requests
from html.parser import HTMLParser

from cloudbot import hook
from cloudbot.util import timeformat, formatting


reddit_re = re.compile(r'.*(((www\.)?reddit\.com/r|redd\.it)[^ ]+)[/.\?]', re.I)

base_url = "https://reddit.com/r/{}/.json"
short_url = "https://redd.it/{}"


def format_output(item, show_url=False):
    """ takes a reddit post and returns a formatted string """
    item["title"] = formatting.truncate(item["title"], 200)
    item["link"] = short_url.format(item["id"])

    # Fix some URLs
    if not item["is_self"] and item["url"]:
        if "imgur.com/" in item["url"]:
            # Force TLS for imgur
            if item["url"].startswith("http://"):
                item["url"] = item["url"].replace("http://", "https://")
            # Use .gifv links
            if item["url"].endswith(".gif"):
                item["url"] += "v"
        # Fix i.reddituploads.com crap ("&amp;" in URL)
        if "i.reddituploads.com/" in item["url"]:
            # Get i.redditmedia.com preview (first one is full size)
            item["url"] = item["preview"]["images"][0]["source"]["url"]
        # Unescape since reddit gives links for HTML
        item["url"] = HTMLParser().unescape(item["url"])

    raw_time = datetime.fromtimestamp(int(item["created_utc"]))
    item["timesince"] = timeformat.time_since(raw_time, count=1, simple=True)

    item["comments"] = formatting.pluralize(item["num_comments"], 'comment').replace(",", "")
    item["points"] = formatting.pluralize(item["score"], 'point').replace(",", "")

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
        item["gilded"] = formatting.pluralize(item["gilded"], 'gild')
        out.append("$(yellow){gilded}$(c)")

    return "[h1]Reddit:[/h1] " + " [div] ".join(out).format(**item)


@hook.regex(reddit_re)
def reddit_url(match, bot):
    url = match.group(1)
    if "redd.it" in url:
        url = "https://" + url
        response = requests.get(url)
        url = response.url + ".json"
    if not urllib.parse.urlparse(url).scheme:
        url = "https://" + url + ".json"

    # the reddit API gets grumpy if we don't include headers
    headers = {'User-Agent': bot.user_agent}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return "HTTP {}".format(r.status_code)
    data = r.json()
    if type(data) == list:
        item = data[0]["data"]["children"][0]["data"]
    elif type(data) == dict:
        #item = data["data"]["children"][random.randint(0,9)]["data"]
        return

    return format_output(item)


@asyncio.coroutine
@hook.command(autohelp=False)
def reddit(text, bot, loop):
    """<subreddit> [n] - gets a random post from <subreddit>, or gets the [n]th post in the subreddit"""
    id_num = None
    headers = {'User-Agent': bot.user_agent}

    if text:
        # clean and split the input
        parts = text.lower().strip().split()

        # find the requested post number (if any)
        if len(parts) > 1:
            url = base_url.format(parts[0].strip())
            try:
                id_num = int(parts[1]) - 1
            except ValueError:
                return "Invalid post number."
        else:
            url = base_url.format(parts[0].strip())
    else:
        url = "https://reddit.com/.json"

    try:
        # Again, identify with Reddit using an User Agent, otherwise get a 429
        inquiry = yield from loop.run_in_executor(None, functools.partial(requests.get, url, headers=headers))
        if inquiry.status_code != 200:
            return "r/{} either does not exist or is private.".format(text)
        data = inquiry.json()
    except Exception as e:
        return "Error: " + str(e)
    data = data["data"]["children"]

    # get the requested/random post
    if id_num is not None:
        try:
            item = data[id_num]["data"]
        except IndexError:
            length = len(data)
            return "Invalid post number. Number must be between 1 and {}.".format(length)
    else:
        item = random.choice(data)["data"]

    return format_output(item, show_url=True)
