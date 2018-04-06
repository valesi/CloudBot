import json
import os
import random

from cloudbot import hook


@hook.onload()
def load_drinks(bot):
    """load the drink recipes"""
    global drinks
    with open(os.path.join(bot.data_dir, "drinks.json")) as json_data:
        drinks = json.load(json_data)


@hook.command()
def drink(text, chan, action):
    """<nick> - makes the user a random cocktail."""
    index = random.randint(0, len(drinks) - 1)
    drink = drinks[index]['title']
    url = drinks[index]['url']
    if drink.endswith(' recipe'):
        drink = drink[:-7]
    contents = drinks[index]['ingredients']
    out = "grabs some"
    for x in contents:
        if x == contents[len(contents) - 1]:
            out += " and {}".format(x)
        else:
            out += " {},".format(x)
    n = "n" if drink.lower()[:1] in ["a", "e", "i", "o", "u"] else ""
    out += " and makes {} a{} $(b){}$(b) [div] [h3]{}[/h3]".format(text, n, drink, url)
    action(out, chan)
