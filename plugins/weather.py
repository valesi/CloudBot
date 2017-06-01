import requests

from sqlalchemy import Table, Column, PrimaryKeyConstraint, String
from cloudbot import hook
from cloudbot.util import database


# Define database table
table = Table(
    "weather",
    database.metadata,
    Column('nick', String),
    Column('loc', String),
    PrimaryKeyConstraint('nick')
)

location_api = "https://autocomplete.wunderground.com/aq"
forecast_api = "https://api.wunderground.com/api/{}/forecast/geolookup/conditions/q/zmw:{}.json"


def find_location(location):
    """
    Takes a location as a string, and returns a dict of data
    :param location: string
    :return: dict
    """
    params = {"query": location}

    json = requests.get(location_api, params=params).json()

    if len(json["RESULTS"]) > 0:
        return json["RESULTS"][0]["zmw"]
    else:
        return None


def load_cache(db):
    global location_cache
    location_cache = []
    for row in db.execute(table.select()):
        nick = row["nick"]
        location = row["loc"]
        location_cache.append((nick,location))


def add_location(nick, location, db):
    test = dict(location_cache)
    location = str(location)
    if nick.lower() in test:
        db.execute(table.update().values(loc=location.lower()).where(table.c.nick == nick.lower()))
        db.commit()
        load_cache(db)
    else:
        db.execute(table.insert().values(nick=nick.lower(), loc=location.lower()))
        db.commit()
        load_cache(db)


@hook.on_start
def on_start(bot, db):
    """ Loads API keys """
    global wunder_key
    wunder_key = bot.config.get("api_keys", {}).get("wunderground", None)
    load_cache(db)


def get_location(nick):
    """looks in location_cache for a saved location"""
    location = [row[1] for row in location_cache if nick.lower() == row[0]]
    if not location:
        return
    else:
        return location[0]


@hook.command("weather", "we", autohelp=False)
def weather(text, reply, db, nick, notice):
    """weather <location> -- Gets weather data for <location>. First use requires location then the bot remembers it."""
    if not wunder_key:
        return "This command requires a Weather Underground API key."

    location = None

    if not text:
        location = get_location(nick)
        if not location:
            notice(weather.__doc__)
            return
    else:
        location = find_location(text)
        if location:
            add_location(nick, location, db)
        else:
            return "Location not found :/"

    url = forecast_api.format(wunder_key, location)
    response = requests.get(url).json()

    if response['response'].get('error'):
        return "{}".format(response['response']['error']['description'])

    forecast_today = response["forecast"]["simpleforecast"]["forecastday"][0]
    forecast_tomorrow = response["forecast"]["simpleforecast"]["forecastday"][1]

    # put all the stuff we want to use in a dictionary for easy formatting of the output
    weather_data = {
        "place": response['current_observation']['display_location']['full'],
        "conditions": response['current_observation']['weather'],
        "temp_f": response['current_observation']['temp_f'],
        "temp_c": response['current_observation']['temp_c'],
        "humidity": response['current_observation']['relative_humidity'],
        "wind_kph": response['current_observation']['wind_kph'],
        "wind_mph": response['current_observation']['wind_mph'],
        "wind_direction": response['current_observation']['wind_dir'],
        "today_conditions": forecast_today['conditions'],
        "today_high_f": forecast_today['high']['fahrenheit'],
        "today_high_c": forecast_today['high']['celsius'],
        "today_low_f": forecast_today['low']['fahrenheit'],
        "today_low_c": forecast_today['low']['celsius'],
        "tomorrow_conditions": forecast_tomorrow['conditions'],
        "tomorrow_high_f": forecast_tomorrow['high']['fahrenheit'],
        "tomorrow_high_c": forecast_tomorrow['high']['celsius'],
        "tomorrow_low_f": forecast_tomorrow['low']['fahrenheit'],
        "tomorrow_low_c": forecast_tomorrow['low']['celsius']
    }

    reply("{place}: {conditions}, {temp_f}F/{temp_c}C, {humidity}, "
          "Wind: {wind_mph}MPH/{wind_kph}KPH {wind_direction}, \x02Today:\x02 {today_conditions}, "
          "High: {today_high_f}F/{today_high_c}C, Low: {today_low_f}F/{today_low_c}C. "
          "\x02Tomorrow:\x02 {tomorrow_conditions}, High: {tomorrow_high_f}F/{tomorrow_high_c}C, "
          "Low: {tomorrow_low_f}F/{tomorrow_low_c}C".format(**weather_data))
