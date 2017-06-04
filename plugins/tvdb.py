import datetime
import requests
from lxml import etree

from cloudbot import hook


# security
parser = etree.XMLParser(resolve_entities=False, no_network=True)

API_URL = "https://thetvdb.com/api/"


@hook.on_start()
def on_start(bot):
    global api_key
    api_key = bot.config.get("api_keys", {}).get("tvdb", None)


# http://thetvdb.com/wiki/index.php/API:GetSeries
def get_series_from_name(text):
    res = {"error": None, "series_id": None, "name": None}

    try:
        params = {"seriesname": text}
        request = requests.get(API_URL + "GetSeries.php", params=params, timeout=10.0)
        request.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as ex:
        res["error"] = "Error getting series: {}".format(ex)
        return res

    series = etree.fromstring(request.content, parser=parser)
    series_id = series.xpath("//seriesid/text()")

    if not series_id:
        res["error"] = "TVDB couldn't find that series"
        return res

    res["series_id"] = series_id[0]

    try:
        res["name"] = series.xpath("//SeriesName/text()")[0]
    except:
        res["name"] = series.xpath("//SeriesName/text()")

    return res



def get_episodes_for_series(series_id):
    res = {"error": None, "status": None, "episodes": None}

    try:
        request = requests.get("{}/{}/series/{}/all/en.xml".format(API_URL, api_key, series_id), timeout=10.0)
        request.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as ex:
        res["error"] = "Error getting episodes: {}".format(ex)
        return res

    series = etree.fromstring(request.content, parser=parser)
    try:
        res["status"] = series.xpath("//Status/text()")[0]
    except:
        res["status"] = series.xpath("//Status/text()")

    res["episodes"] = series.xpath("//Episode")
    return res


def get_episode_info(episode):
    first_aired = episode.findtext("FirstAired")

    try:
        air_date = datetime.date(*list(map(int, first_aired.split("-"))))
    except (ValueError, TypeError):
        return None

    episode_num = "S%02dE%02d" % (int(episode.findtext("SeasonNumber")),
                                  int(episode.findtext("EpisodeNumber")))

    episode_name = episode.findtext("EpisodeName")
    # in the event of an unannounced episode title, users either leave the
    # field out (None) or fill it with TBA
    #if episode_name == "TBA":
    #    episode_name = None

    episode_desc = "{}".format(episode_num)
    if episode_name:
        episode_desc += " - {}".format(episode_name)
    return first_aired, air_date, episode_desc


@hook.command("tv", "tvdb")
def tvdb(text):
    """<series> -- Show next/previous episodes of <series>."""
    if not api_key:
        return "No API key"

    data = get_series_from_name(text)
    if data["error"]:
        return data["error"]

    series_name = data["name"]

    data.update(get_episodes_for_series(data["series_id"]))

    if data["error"]:
        return data["error"]

    status = data["status"]
    episodes = data["episodes"]

    next_eps = []
    today = datetime.datetime.utcnow().date()

    # Don't show status if there's a future episode
    future = False

    for episode in reversed(episodes):
        ep_info = get_episode_info(episode)

        if ep_info is None:
            continue

        (first_aired, air_date, episode_desc) = ep_info

        if air_date > today:
            future = True
            next_eps = ["[h1]Next:[/h1] {} [h3]({})[/h3]".format(episode_desc, first_aired)]
        elif air_date == today:
            next_eps.append("[h1]Today:[/h1] {}".format(episode_desc))
        else:
            next_eps.append("[h1]Previous:[/h1] {} [h3]({})[/h3]".format(episode_desc, first_aired))
            # we're iterating in reverse order with newest episodes last
            # so, as soon as we're past today, break out of loop
            break

    episodes = " [div] ".join(next_eps)

    if not future:
        if status == "Continuing":
            status = "Ongoing"
        episodes = "{} [div] {}".format(status, episodes)

    return "{} [div] {}".format(series_name, episodes)

