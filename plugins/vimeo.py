from cloudbot import hook
from cloudbot.util import http, timeformat


@hook.regex(r'vimeo.com/([0-9]+)')
def vimeo_url(match):
    """vimeo <url> -- returns information on the Vimeo video at <url>"""
    info = http.get_json('https://vimeo.com/api/v2/video/{}.json'.format(match.group(1)))

    if info:
        info[0]["duration"] = timeformat.format_time(info[0]["duration"])
        info[0]["stats_number_of_likes"] = format(
            info[0]["stats_number_of_likes"], ",d")
        info[0]["stats_number_of_plays"] = format(
            info[0]["stats_number_of_plays"], ",d")
        return ("[h1]Vimeo:[/h1] {title} [div] {user_name} [div] {duration} [div] "
                "{upload_date} [div] "
                "[h1]Likes:[/h1] {stats_number_of_likes} [div] "
                "[h1]Plays:[/h1] {stats_number_of_plays}".format(**info[0]))
