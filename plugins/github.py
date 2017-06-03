import requests

from cloudbot import hook
from cloudbot.util import web, formatting

shortcuts = {
    'origin': 'valesi/CloudBot',
    'upstream': 'edwardslabs/CloudBot',
    'cloudbot': 'CloudBotIRC/CloudBot'
}


@hook.command("ghissue", "issue")
def issue(text):
    """<username|repo> [number] - gets issue [number]'s summary, or the open issue count if no issue is specified"""
    args = text.split()
    repo = args[0] if args[0] not in shortcuts else shortcuts[args[0]]
    issue = args[1] if len(args) > 1 else None

    if issue:
        r = requests.get('https://api.github.com/repos/{}/issues/{}'.format(repo, issue), timeout=10.0)
        j = r.json()

        url = web.try_shorten(j['html_url'], service='git.io')
        number = j['number']
        title = j['title']
        summary = formatting.truncate(j['body'].split('\n')[0], 200)
        if j['state'] == 'open':
            state = '$(green)Opened$(c) by {}'.format(j['user']['login'])
        else:
            state = '$(red)Closed$(c) by {}'.format(j['closed_by']['login'])

        return 'Issue #{} {} [div] {} [div] {} [div] [h3]{}[/h3]'.format(number, state, title, summary, url)
    else:
        r = requests.get('https://api.github.com/repos/{}/issues'.format(repo), timeout=10.0)
        j = r.json()

        count = len(j)
        return '{} has {} open issues.'.format(repo, count if count else "no")

