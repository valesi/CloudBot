import re

import requests
from bs4 import BeautifulSoup

from cloudbot import hook
from cloudbot.util import web, formatting

# CONSTANTS

steam_re = re.compile('.*://store.steampowered.com/app/([0-9]+)', re.I)

API_URL = "https://store.steampowered.com/api/appdetails/"
STORE_URL = "https://store.steampowered.com/app/{}/"


# OTHER FUNCTIONS

def format_game(app_id, show_url=True):
    """
    Takes a Steam Store app ID and returns a formatted string with data about that app ID
    :type app_id: string
    :return: string
    """
    params = {'appids': app_id}

    try:
        request = requests.get(API_URL, params=params, timeout=15)
        request.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        return "Could not get game info: {}".format(e)

    data = request.json()
    game = data[app_id]["data"]

    # basic info
    out = ["{} [h3]({})[/h3]".format(game['name'], game['release_date']['date'])]

    # genres
    try:
        genres = ", ".join([g['description'] for g in game['genres']])
        out.append(genres)
    except KeyError:
        # some things have no genre
        pass

    # pricing
    if game['is_free']:
        out.append("\x02Free\x02")
    elif game.get("price_overview"):
        price = game['price_overview']

        price_now = "{}\x02{}\x02".format(price['currency'], price['final_formatted'])

        if price['final'] == price['initial']:
            out.append(price_now)
        else:
            out.append("{} ($(green)-{}%$(c) from {})".format(price_now, price['discount_percent'], price['initial_formatted']))
    # else: game has no pricing, it's probably not released yet

    out.append(formatting.truncate(game['short_description'], 250))

    if show_url:
        out.append("[h3]{}[/h3]".format(STORE_URL.format(game['steam_appid'])))

    return "[h1]Steam:[/h1] " + " [div] ".join(out)


# HOOK FUNCTIONS

@hook.command()
def steam(text, reply):
    """<query> - Search for specified game/trailer/DLC"""
    params = {'term': text}

    try:
        request = requests.get("https://store.steampowered.com/search/", params=params)
        request.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        reply("Could not get game info: {}".format(e))
        raise

    soup = BeautifulSoup(request.text, from_encoding="utf-8")
    result = soup.find('a', {'class': 'search_result_row'})

    if not result:
        return "No game found."

    app_id = result['data-ds-appid']
    return format_game(app_id)


@hook.regex(steam_re)
def steam_url(match):
    app_id = match.group(1)
    return format_game(app_id, show_url=False)
