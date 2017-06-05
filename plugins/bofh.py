import codecs
import os
import random

from cloudbot import hook


@hook.on_start()
def load_lines(bot):
    """
    :type bot: cloudbot.bot.Cloudbot
    """
    global bofh
    with codecs.open(os.path.join(bot.data_dir, "bofh.txt"), encoding="utf-8") as f:
        bofh = [line.strip() for line in f.readlines() if not line.startswith("//")]


@hook.command(autohelp=False)
def bofh():
    """The wise words of the Bachelor Operator From Hell"""
    return random.choice(bofh)

