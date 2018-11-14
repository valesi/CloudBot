import re

import requests

from cloudbot import hook


id_re = re.compile("tt\d+")
imdb_re = re.compile(r'://(imdb.com|www.imdb.com)/.*/?(tt[0-9]+)', re.I)


@hook.on_start()
def on_start(bot):
    global api_key
    api_key = bot.config["api_keys"].get("omdb")


def get_info(reply, params=None, headers=None, show_url=True):
    if api_key:
        params["apikey"] = api_key
    else:
        return

    resp = requests.get("https://www.omdbapi.com/", params=params, headers=headers, timeout=10)
    try:
        resp.raise_for_status()
    except requests.HTTPError as ex:
        reply("Error reaching OMDB API: " + ex.response.status_code)
        raise

    content = resp.json()

    if content.get("Error", None) == "Movie not found!":
        return "Not found."
    elif content["Response"] == "True":
        out = "[h1]{Title}[/h1] ({Year}) ({Genre}): {Plot}"
        if content["Runtime"] != "N/A":
            out += " [div] {Runtime}"
        if content["imdbRating"] != 'N/A' and content["imdbVotes"] != "N/A":
            out += " [div] {imdbRating}/10 ({imdbVotes} votes)"
        if show_url:
            content["URL"] = "http://www.imdb.com/title/{}/".format(content["imdbID"])
            out += " [div] [h3]{URL}[/h3]"

        return out.format(**content)
    else:
        return "Error: {}".format(content["Error"])



@hook.command
def imdb(text, bot, reply):
    """<movie> - gets information about <movie> from IMDb"""
    params = {"i": text} if id_re.match(text) else {'t': text}
    headers = {"User-Agent": bot.user_agent}

    return get_info(reply, params, headers)


@hook.regex(imdb_re)
def imdb_url(match, bot, reply):
    imdb_id = match.group(2)

    params = {"i": imdb_id}
    headers = {"User-Agent": bot.user_agent}

    return get_info(reply, params, headers, show_url=False)
