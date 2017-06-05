import re
import time

import isodate
import requests

from cloudbot import hook
from cloudbot.util import timeformat
from cloudbot.util.formatting import pluralize


youtube_re = re.compile(r'(?:youtube.*?(?:v=|/v/)|youtu\.be/|yooouuutuuube.*?id=)([-_a-zA-Z0-9]+)', re.I)

base_url = 'https://www.googleapis.com/youtube/v3/'
api_url = base_url + 'videos?part=contentDetails%2C+snippet%2C+statistics&id={}&key={}'
search_api_url = base_url + 'search?part=id&maxResults=1'
playlist_api_url = base_url + 'playlists?part=snippet%2CcontentDetails%2Cstatus'
video_url = "http://youtu.be/%s"
err_no_api = "The YouTube API is off in the Google Developers Console."


def get_video_description(video_id, show_url=False):
    json = requests.get(api_url.format(video_id, dev_key)).json()

    if json.get('error'):
        if json['error']['code'] == 403:
            return err_no_api
        else:
            return

    data = json['items']
    snippet = data[0]['snippet']
    statistics = data[0]['statistics']
    content_details = data[0]['contentDetails']

    out = '[h1]YT:[/h1]'

    if show_url:
        out += ' [h3]https://youtu.be/{}[/h3] [div]'.format(video_id)

    out += ' {}'.format(snippet['title'])

    if 'duration' not in content_details:
        return out

    if 'contentRating' in content_details:
        out += ' [div] $(red)NSFW$(c)'

    uploader = snippet['channelTitle']
    out += ' [div] {}'.format(uploader)

    length = isodate.parse_duration(content_details.get('duration'))
    out += ' [div] {}'.format(timeformat.format_time(int(length.total_seconds()), simple=True))

    upload_time = time.strptime(snippet.get('publishedAt'), "%Y-%m-%dT%H:%M:%S.000Z")
    out += ' [div] {}'.format(time.strftime("%Y-%m-%d", upload_time))

    # Some videos/channels don't give this info??
    if 'statistics' in data[0]:
        statistics = data[0]['statistics']
    else:
        return out

    if statistics.get('viewCount'):
        views = int(statistics.get('viewCount'))
        out += u' [div] {:,} views'.format(views)  # Eye \U0001f441

    if statistics.get('likeCount'):
        likes = u'{:,} $(green)\u25b2$(c)'.format(int(statistics.get('likeCount')))  # Thumbs up: \U0001F44D
        dislikes = u'{:,} $(red)\u25bc$(c)'.format(int(statistics.get('dislikeCount')))  # Down: \U0001F44E
        out += ' [div] {} {}'.format(likes, dislikes)

    return out


@hook.on_start()
def load_key(bot):
    global dev_key
    dev_key = bot.config.get("api_keys", {}).get("google_dev_key", None)


@hook.regex(youtube_re)
def youtube_url(match):
    return get_video_description(match.group(1))


@hook.command("youtube", "you", "yt", "y")
def youtube(text):
    """youtube <query> -- Returns the first YouTube search result for <query>."""
    if not dev_key:
        return "This command requires a Google Developers Console API key."

    json = requests.get(search_api_url, params={"q": text, "key": dev_key, "type": "video"}).json()

    if json.get('error'):
        if json['error']['code'] == 403:
            return err_no_api
        else:
            return 'Error performing search.'

    if json['pageInfo']['totalResults'] == 0:
        return 'No results found.'
    
    video_id = json['items'][0]['id']['videoId']

    return get_video_description(video_id, show_url=True)


@hook.command("youtime", "ytime")
def youtime(text):
    """youtime <query> -- Gets the total run time of the first YouTube search result for <query>."""
    if not dev_key:
        return "This command requires a Google Developers Console API key."

    json = requests.get(search_api_url, params={"q": text, "key": dev_key, "type": "video"}).json()

    if json.get('error'):
        if json['error']['code'] == 403:
            return err_no_api
        else:
            return 'Error performing search.'

    if json['pageInfo']['totalResults'] == 0:
        return 'No results found.'

    video_id = json['items'][0]['id']['videoId']
    json = requests.get(api_url.format(video_id, dev_key)).json()

    if json.get('error'):
        return
    data = json['items']
    snippet = data[0]['snippet']
    content_details = data[0]['contentDetails']
    statistics = data[0]['statistics']

    if not content_details.get('duration'):
        return

    length = isodate.parse_duration(content_details['duration'])
    l_sec = int(length.total_seconds())
    views = int(statistics['viewCount'])
    total = int(l_sec * views)

    length_text = timeformat.format_time(l_sec, simple=True)
    total_text = timeformat.format_time(total, accuracy=8)

    return '{}: [h1]Length:[/h1] {} [div] [h1]Views:[/h1] {:,} [div] [h1]Total run time:[/h1] {}'.format(snippet['title'], length_text, views,
                                            total_text)


ytpl_re = re.compile(r'(.*:)//(www.youtube.com/playlist|youtube.com/playlist)(:[0-9]+)?(.*)', re.I)


@hook.regex(ytpl_re)
def ytplaylist_url(match):
    location = match.group(4).split("=")[-1]
    json = requests.get(playlist_api_url, params={"id": location, "key": dev_key}).json()

    if json.get('error'):
        if json['error']['code'] == 403:
            return err_no_api
        else:
            return 'Error looking up playlist.'

    data = json['items']
    snippet = data[0]['snippet']
    content_details = data[0]['contentDetails']

    title = snippet['title']
    author = snippet['channelTitle']
    num_videos = int(content_details['itemCount'])
    count_videos = '{:,} video{}'.format(num_videos, "s"[num_videos == 1:])
    return "{} [div] {} [div] {}".format(title, count_videos, author)
