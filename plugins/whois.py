"""
whois.py
Provides a command to allow users to look up information on domain names.
"""

import pythonwhois
from contextlib import suppress

from cloudbot import hook


@hook.command
def whois(text):
    """<domain> -- Does a whois query on <domain>."""
    domain = text.lower()

    try:
        data = pythonwhois.get_whois(domain, normalized=True)
    except pythonwhois.shared.WhoisException:
        return "Invalid input."
    info = []

    # We suppress errors here because different domains provide different data fields
    with suppress(KeyError):
        info.append("[h1]Registrar:[/h1] {}".format(data["registrar"][0]))

    with suppress(KeyError):
        info.append("[h1]Registered:[/h1] {}".format(data["creation_date"][0].strftime("%Y-%m-%d")))

    with suppress(KeyError):
        info.append("[h1]Expires:[/h1] {}".format(data["expiration_date"][0].strftime("%Y-%m-%d")))

    info_text = " [div] ".join(info)
    return "{} [div] {}".format(domain, info_text)
