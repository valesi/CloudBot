import codecs
import os
import random

from cloudbot import hook

@hook.on_start()
def load_dogfacts(bot):
    global dogfacts

    with codecs.open(os.path.join(bot.data_dir, "dogfacts.txt"), encoding="utf-8") as f:
        dogfacts = [line.strip() for line in f.readlines() if not line.startswith("//")]


@hook.command(autohelp=False)
def dogs():
    """Dog facts!"""
    return random.choice(dogfacts)
