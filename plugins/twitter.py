import html
import random
import re
from datetime import datetime

import tweepy

from cloudbot import hook
from cloudbot.util import timeformat


STATUS_RE = re.compile(r"(?:(?:www\.twitter\.com|twitter\.com)/(?:[-_a-zA-Z0-9]+)/status/)([0-9]+)", re.I)
TCO_RE = re.compile(r"https?://t\.co/\w+", re.I)


@hook.on_start()
def load_api(bot):
    global tw_api

    consumer_key = bot.config.get("api_keys", {}).get("twitter_consumer_key", None)
    consumer_secret = bot.config.get("api_keys", {}).get("twitter_consumer_secret", None)

    oauth_token = bot.config.get("api_keys", {}).get("twitter_access_token", None)
    oauth_secret = bot.config.get("api_keys", {}).get("twitter_access_secret", None)

    if not all((consumer_key, consumer_secret, oauth_token, oauth_secret)):
        tw_api = None
        return
    else:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(oauth_token, oauth_secret)

        tw_api = tweepy.API(auth)


def get_tweet_by_id(tweet_id):
    try:
        tweet = tw_api.get_status(tweet_id, tweet_mode="extended")
    except tweepy.error.TweepError as e:
        return "Error: {}".format(e.reason[1:-1])

    return tweet


def format_tweet(tweet):
    if isinstance(tweet, str):
        return tweet

    user = tweet.user

    # Format the return the text of the tweet
    text = html.unescape(" ".join(tweet.full_text.split()))

    # Get expanded URLs
    urls = {}
    if tweet.entities.get("urls"):
        for item in tweet.entities["urls"]:
            urls[item["url"]] = item["expanded_url"]

    if "extended_entities" in tweet._json:
        high_bitrate = -1  # mp4 of gif appears to be marked 0
        for item in tweet._json["extended_entities"]["media"]:
            # check for video
            if "video_info" in item:
                for vid in item["video_info"]["variants"]:
                    if vid["content_type"] == "video/mp4" and vid["bitrate"] > high_bitrate:
                        high_bitrate = vid["bitrate"]
                        urls[item["url"]] = vid["url"]
                        continue
            # Did we already set it?
            if not item["url"] in urls:
                urls[item["url"]] = item["media_url_https"]

    while True:
        m = TCO_RE.search(text)
        if not m:
            break
        if m.group() in urls:
            # Expand the URL
            text = TCO_RE.sub(urls[m.group()], text, count=1)
        else:
            # Ignore and move on
            TCO_RE.compile("(?!{}){}".format(m.group(), TCO_RE.pattern))

    verified = "\u2713" if user.verified else ""

    time = timeformat.time_since(tweet.created_at, datetime.utcnow(), simple=True)

    return "{} ({}@{}) [div] {} ago [div] {}".format(user.name, verified, user.screen_name, time, text.strip())


@hook.regex(STATUS_RE)
def twitter_url(match):
    # Find the tweet ID from the URL
    tweet_id = match.group(1)

    # Get the tweet using the tweepy API
    if not tw_api:
        return

    tweet = get_tweet_by_id(tweet_id)
    return format_tweet(tweet)


@hook.command("twitter", "tw", "twatter")
def twitter(text):
    """<url>|<user> [n] -- Gets the tweet at <url> or last/[n]th tweet from <user>"""

    if not tw_api:
        return "This command requires a twitter API key."

    m = STATUS_RE.search(text)
    if m:
        # user is getting a tweet by URL
        tweet = get_tweet_by_id(m.group(1))

    elif re.match(r"\d+$", text):
        # user is getting a tweet by ID
        tweet = get_tweet_by_id(text)

    elif re.match(r'\w{1,15}$', text) or re.match(r'\w{1,15}\s+\d+$', text):
        # user is getting a tweet by name
        if text.find(' ') == -1:
            username = text
            tweet_number = 0
        else:
            username, tweet_number = text.split()
            tweet_number = int(tweet_number) - 1

        if tweet_number > 200:
            return "This command can only find the last \x02200\x02 tweets."

        try:
            # try to get user by username
            user = tw_api.get_user(username)
        except tweepy.error.TweepError as e:
            return "Error: {}".format(e.reason[1:-1])

        # get the users tweets
        user_timeline = tw_api.user_timeline(id=user.id, count=tweet_number + 1, tweet_mode="extended")

        # if the timeline is empty, return an error
        if not user_timeline:
            return "@{} has no tweets.".format(user.screen_name)

        # grab the newest tweet from the users timeline
        try:
            tweet = user_timeline[tweet_number]
        except IndexError:
            tweet_count = len(user_timeline)
            return "@{} only has {} tweets.".format(user.screen_name, tweet_count)

    elif re.match(r'#\w+$', text):
        # user is searching by hashtag
        search = tw_api.search(text, tweet_mode="extended")

        if not search:
            return "No tweets found."

        tweet = random.choice(search)
    else:
        # ???
        return "Invalid Input"

    return format_tweet(tweet)


@hook.command("twuser", "twinfo")
def twuser(text, reply):
    """<user> - Get info on the Twitter user <user>"""

    if not tw_api:
        return

    try:
        # try to get user by username
        user = tw_api.get_user(text)
    except tweepy.error.TweepError as e:
        return "Error: {}".format(e.reason[1:-1])

    verified = "\u2713" if user.verified else ""

    tf = lambda l, s: "[h1]{}:[/h1] {}".format(l, s)

    out = []
    if user.location:
        out.append(tf("Loc", user.location))
    if user.description:
        out.append(tf("Desc", user.description))
    if user.url:
        out.append(tf("URL", user.url))
    out.append(tf("Tweets", user.statuses_count))
    out.append(tf("Followers", user.followers_count))

    return "{}@{} ({}) [div] {}".format(verified, user.screen_name, user.name, " [div] ".join(out))

