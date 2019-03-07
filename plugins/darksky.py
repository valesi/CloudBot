import requests

from collections import defaultdict

from sqlalchemy import Table, Column, String, Float, PrimaryKeyConstraint, and_
from yarl import URL

from cloudbot import hook
from cloudbot.util import database
from .google_maps import query_geocoding_api


table = Table(
    'darksky',
    database.metadata,
    Column('network', String(20)),
    Column('nick', String(24)),
    Column('lat', Float),
    Column('lng', Float),
    Column('formatted', String(32)),
    PrimaryKeyConstraint('network', 'nick')
)

API_BASE_URL = URL('https://api.darksky.net')
FORECAST_URL = 'forecast/{key}/{lat},{lng}'
api_key = None


def to_c(f):
    return (f - 32) * 5.0/9.0


def to_kmh(m):
    conv_factor = 0.621371
    return float(m / conv_factor)


def deg_to_card(d):
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    ix = int((d + 11.25)/22.5)
    return dirs[ix % 16]


@hook.on_start(api_keys=['darksky'])
def on_start(bot):
    global api_key
    api_key = bot.config.get('api_keys', {}).get('darksky')


@hook.on_start()
def load_cache(db):
    global location_cache
    location_cache = defaultdict(dict)
    for row in db.execute(table.select()):
        net = row['network']
        nick = row['nick']
        location_cache[net][nick] = {k: row[k] for k in ('lat', 'lng', 'formatted')}


def get_location(net, nick):
    '''Pulls the location dict from cache for `nick` on `net`'''
    net = net.lower()
    nick = nick.lower()
    if net in location_cache and nick in location_cache[net]:
        return location_cache[net][nick]
    else:
        return


def set_location(db, net, nick, location):
    '''Updates the location for `nick` on `net`'''
    net = net.lower()
    nick = nick.lower()
    if net in location_cache and nick in location_cache[net]:
        db.execute(table.update().values(**location).where(and_(table.c.network == net, table.c.nick == nick)))
        db.commit()
    else:
        db.execute(table.insert().values(network=net, nick=nick, **location))
        db.commit()
    location_cache[net][nick] = location


@hook.command('weather', 'we', 'darksky', autohelp=False)
def darksky_forecast(db, conn, nick, text, reply, notice_doc):
    '''[location] - Gets weather data for [location], remembering the last used location if absent. (Powered by Dark Sky)'''
    if text:
        loc = query_geocoding_api(text)
        if isinstance(loc, str):
            return loc
        loc = loc[0]
        location = {k: loc['geometry']['location'][k] for k in ('lat', 'lng')}
        location['formatted'] = loc['formatted_address']
        set_location(db, conn.name, nick, location)
    else:
        location = get_location(conn.name, nick)
        if location is None:
            notice_doc()
            return

    path_args = {'key': api_key, 'lat': location['lat'], 'lng': location['lng']}

    data = requests.get(API_BASE_URL / FORECAST_URL.format(**path_args), params={'exclude': 'minutely,hourly'}).json()

    currently = data['currently']
    today = data['daily']['data'][0]
    tomorrow = data['daily']['data'][1]

    reply("[h1]{}:[/h1] {}, {:.1f}°C ({:.1f}°F), {:g}%RH, Wind {:.1f}km/h ({:.1f}mph) {}"
          " [div] [h1]Today:[/h1] {}, High {:.1f}°C ({:.1f}°F), Low {:.1f}°C ({:.1f}°F)"
          " [div] [h1]Tomorrow:[/h1] {}, High {:.1f}°C ({:.1f}°F), Low {:.1f}°C ({:.1f}°F)".format(
              location['formatted'],
              currently.get("summary", "").rstrip("."),
              to_c(currently.get("temperature", 1)),
              currently.get("temperature", 0),
              currently.get("humidity") * 100,
              to_kmh(currently.get("windSpeed", 0)), currently.get("windSpeed", 0),
              deg_to_card(currently.get("windBearing")),
              today.get("summary").rstrip("."),
              to_c(today.get("temperatureHigh")), today.get("temperatureHigh"),
              to_c(today.get("temperatureLow")), today.get("temperatureLow"),
              tomorrow.get("summary").rstrip("."),
              to_c(tomorrow.get("temperatureHigh")), tomorrow.get("temperatureHigh"),
              to_c(tomorrow.get("temperatureLow")), tomorrow.get("temperatureLow")))
