import re
import time

import isodate
import requests

from cloudbot import hook
from cloudbot.util import timeformat
from cloudbot.util.formatting import pluralize_auto


youtube_re = re.compile(r'(?:youtube.*?(?:v=|/v/)|youtu\.be/|yooouuutuuube.*?id=)([-_a-zA-Z0-9]+)', re.I)

api_url = 'https://www.googleapis.com/youtube/v3/'

video_parts = ["snippet", "contentDetails", "statistics", "liveStreamingDetails"]
playlist_parts = ["snippet", "contentDetails", "status"]

err_no_api = "The YouTube API is off in the Google Developers Console."


@hook.on_start()
def load_key(bot):
    global dev_key
    dev_key = bot.config.get("api_keys", {}).get("google_dev_key", None)


@hook.regex(youtube_re)
def youtube_url(match):
    return get_video_description(match.group(1))


def get_video_description(video_id, show_url=False):
    json = requests.get(api_url + "videos", params={"id": video_id, "key": dev_key, "part": ",".join(video_parts)}).json()

    if json.get('error'):
        if json['error']['code'] == 403:
            return err_no_api
        else:
            return

    data = json['items'][0]
    snippet = data['snippet']
    content_details = data['contentDetails']

    start = '[h1]YT:[/h1] '
    out = []

    if show_url:
        out.append('[h3]https://youtu.be/{}[/h3]'.format(video_id))

    out.append(snippet['title'])

    if 'duration' not in content_details:
        return start + ' [div] '.join(out)

    if 'contentRating' in content_details:
        out.append('$(red)NSFW$(c)')

    out.append(snippet['channelTitle'])

    if "live" in snippet['liveBroadcastContent']:
        out.append("$(red)LIVE$(c)")
        #livestream_details = data['liveStreamingDetails']
    else:
        length = isodate.parse_duration(content_details.get('duration'))
        out.append(timeformat.format_time(int(length.total_seconds()), simple=True))

    upload_time = time.strptime(snippet.get('publishedAt'), "%Y-%m-%dT%H:%M:%S.000Z")
    out.append(time.strftime("%Y-%m-%d", upload_time))

    # Some videos/channels don't give this info??
    if 'statistics' in data:
        statistics = data['statistics']
    else:
        return start + ' [div] '.join(out)

    if statistics.get('viewCount'):
        views = int(statistics.get('viewCount'))
        out.append(u'{:,} views'.format(views))  # Eye \U0001f441

    if statistics.get('likeCount'):
        likes = u'{:,} $(green)\u25b2$(c)'.format(int(statistics.get('likeCount')))  # Thumbs up: \U0001F44D
        dislikes = u'{:,} $(red)\u25bc$(c)'.format(int(statistics.get('dislikeCount')))  # Down: \U0001F44E
        out.append('{} {}'.format(likes, dislikes))

    return start + ' [div] '.join(out)


@hook.command("youtube", "you", "yt", "y")
def youtube(text):
    """<query> - Returns the first YouTube search result for <query>."""
    if not dev_key:
        return "This command requires a Google Developers Console API key."

    json = requests.get(api_url + "search", params={"part": "id", "maxResults": "1", "q": text, "key": dev_key, "type": "video"}).json()

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
    """<query> - Gets the total run time of the first YouTube search result for <query>."""
    if not dev_key:
        return "This command requires a Google Developers Console API key."

    json = requests.get(api_url + "search", params={"q": text, "key": dev_key, "type": "video"}).json()

    if json.get('error'):
        if json['error']['code'] == 403:
            return err_no_api
        else:
            return 'Error performing search.'

    if json['pageInfo']['totalResults'] == 0:
        return 'No results found.'

    video_id = json['items'][0]['id']['videoId']
    json = requests.get(api_url + "videos", params={"id": video_id, "key": dev_key, "part": ",".join(video_parts)}).json()

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
    json = requests.get(api_url + "playlists", params={"id": location, "key": dev_key, "part": ",".join(playlist_parts)}).json()

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
