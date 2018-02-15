import requests
from requests import HTTPError

from cloudbot import hook


def get_data(url, reply, bot, params=None):
    try:
        r = requests.get(url, headers={'User-Agent': bot.user_agent}, params=params)
        r.raise_for_status()
    except HTTPError:
        reply("API error occurred.")
        raise

    return r


@hook.command(autohelp=False)
def cats(reply, bot):
    """- gets a fucking fact about cats."""
    return get_data("https://catfact.ninja/fact", reply, bot).json()["fact"]


@hook.command(autohelp=False)
def catgifs(reply, bot):
    """- gets a fucking cat gif."""
    return "OMG A CAT GIF: " + get_data("http://thecatapi.com/api/images/get", reply, bot, params={"type": "gif"}).url


@hook.command(autohelp=False)
def catpic(reply, bot):
    """- gets a fucking cat pic."""
    return "Kitty! " + get_data("http://thecatapi.com/api/images/get", reply, bot, params={"type": "jpg,png"}).url
