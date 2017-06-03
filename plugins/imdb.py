import re

import requests

from cloudbot import hook


API_URL = "https://www.omdbapi.com/"

id_re = re.compile("tt\d+")
imdb_re = re.compile(r'(.*:)//(imdb.com|www.imdb.com)(:[0-9]+)?(.*)', re.I)


def get_info(bot, params=None, headers=None):
    content = requests.get("https://www.omdbapi.com/", params=params, headers=headers).json()

    if content.get("Error", None) == "Movie not found!":
        return "Not found."
    elif content["Response"] == "True":
        content["URL"] = "http://www.imdb.com/title/{}".format(content["imdbID"])

        out = "[h1]{Title}[h1] ({Year}) ({Genre}): {Plot}"
        if content["Runtime"] != "N/A":
            out += " [div] {Runtime}"
        if content["imdbRating"] != 'N/A' and content["imdbVotes"] != "N/A":
            out += " [div] {imdbRating}/10 ({imdbVotes} votes)"
        out += " [div] [h3]{URL}[/h3]"
        return out.format(**content)
    else:
        return "Error: {}".format(content["Error"])



@hook.command
def imdb(text, bot):
    """imdb <movie> - gets information about <movie> from IMDb"""
    params = {"i": text} if id_re.match(text) else {'t': text}
    headers = {"User-Agent": bot.user_agent}

    return get_info(bot, params, headers)


@hook.regex(imdb_re)
def imdb_url(match, bot):
    imdb_id = match.group(4).split('/')[-1]
    if imdb_id == "":
        imdb_id = match.group(4).split('/')[-2]

    params = {"i": imdb_id}
    headers = {"User-Agent": bot.user_agent}

    return get_info(bot, params, headers)
