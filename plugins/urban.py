import random

import requests

from cloudbot import hook
from cloudbot.util import formatting


base_url = "https://api.urbandictionary.com/v0"
define_url = base_url + "/define"
random_url = base_url + "/random"


@hook.command("urban", "u", "ud", autohelp=False)
def urban(text):
    """<phrase> [id] -- Looks up <phrase> on the Urban Dictionary"""

    headers = {
        "Referer": "http://m.urbandictionary.com"
    }

    if text:
        # clean and split the input
        parts = text.split()

        # if the last word is a number, set the ID to that number
        if parts[-1].isdigit():
            id_num = int(parts[-1])
            # remove the ID from the input string
            del parts[-1]
            text = " ".join(parts)
        else:
            id_num = 1

        # fetch the definitions
        try:
            params = {"term": text}
            request = requests.get(define_url, params=params, headers=headers)
            request.raise_for_status()
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
            reply("Could not get definition: {}".format(e))
            raise

        page = request.json()

        if page['result_type'] == 'no_results':
            return 'Not found.'
    else:
        # get a random definition!
        try:
            request = requests.get(random_url, headers=headers)
            request.raise_for_status()
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
            reply("Could not get definition: {}".format(e))
            raise

        page = request.json()
        id_num = None

    definitions = page['list']

    if id_num:
        # try getting the requested definition
        try:
            definition = definitions[id_num - 1]

        except IndexError:
            return 'Not found.'

        url = definition['permalink']

        output = "[h3]({}/{})[/h3]".format(id_num, len(definitions))

    else:
        definition = random.choice(definitions)

        name = definition['word']
        url = definition['permalink']
        output = "[h1]{}:[/h1]".format(name)

    def_text = " ".join(definition['definition'].split())  # remove excess spaces
    def_text = formatting.truncate(def_text, 300)

    return "{} {} [div] [h3]{}[/h3]".format(output, def_text, url)
