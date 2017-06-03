import requests

from cloudbot import hook
from cloudbot.util import web, formatting


HEADERS = {
    "Accept": "application/vnd.github.v3+json"
}

shortcuts = {
    'origin': 'valesi/CloudBot',
    'upstream': 'edwardslabs/CloudBot',
    'cloudbot': 'CloudBotIRC/CloudBot'
}


def get_data(url, headers=HEADERS):
    try:
        return (True, requests.get(url, headers=headers, timeout=10.0).json())
    except Exception as ex:
        return (False, "API Error: {}".format(ex))


@hook.command("ghissue", "issue")
def issue(text):
    """<username|repo> [number] - gets issue [number]'s summary, or the open issue count if no issue is specified"""
    args = text.split()
    repo = args[0] if args[0] not in shortcuts else shortcuts[args[0]]
    issue = args[1] if len(args) > 1 else None

    if issue:
        ret, data = get_data('https://api.github.com/repos/{}/issues/{}'.format(repo, issue))
        if not ret:
            return data

        url = web.try_shorten(data['html_url'], service='git.io')
        number = data['number']
        title = data['title']
        summary = formatting.truncate(data['body'].split('\n')[0], 200)
        if data['state'] == 'open':
            state = '$(green)Opened$(c) by {}'.format(data['user']['login'])
        else:
            state = '$(red)Closed$(c) by {}'.format(data['closed_by']['login'])

        return 'Issue #{} {} [div] {} [div] {} [div] [h3]{}[/h3]'.format(number, state, title, summary, url)
    else:
        ret, data = get_data('https://api.github.com/repos/{}/issues'.format(repo))
        if not ret:
            return data

        return '{} has {} open issues.'.format(repo, len(data) if data else "no")

