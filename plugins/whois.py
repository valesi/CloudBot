"""
whois.py
Provides a command to allow users to look up information on domain names using jsonwhoisapi.com.
https://jsonwhoisapi.com/docs/
"""
import requests
from requests.auth import HTTPBasicAuth

from cloudbot import hook


API_URL = "https://jsonwhoisapi.com/api/v1/whois"


@hook.on_start(api_keys=["jsonwhoisapi_id", "jsonwhoisapi_key"])
def load_key(bot):
    global account_id, api_key
    account_id = bot.config.get("api_keys", {}).get("jsonwhoisapi_id")
    api_key = bot.config.get("api_keys", {}).get("jsonwhoisapi_key")


@hook.command
def whois(text, reply):
    """<domain> -- Does a whois query on <domain>."""
    if not account_id or not api_key:
        return "Missing jsonwhoisapi.com API user/key."

    params = {"identifier": text.lower()}

    auth = HTTPBasicAuth(account_id, api_key)

    try:
        req = requests.get(API_URL, params=params, auth=auth, timeout=10.0)
        req.raise_for_status()
    except Exception as ex:
        reply("Error: {}".format(ex))
        raise

    data = req.json()

    info = [data["name"]]
    info.append("Reg'd" if data["registered"] else "Unreg'd")

    # Remove extra spaces....
    info.append("[h1]Registrar:[/h1] {}".format(data["registrar"]["name"]))

    ts = lambda l, s: "[h1]{}:[/h1] {}".format(l, s[:10] if s else "Unknown")

    info.append(ts("Created", data["created"]))
    info.append(ts("Changed", data["changed"]))
    info.append(ts("Expires", data["expires"]))

    return " [div] ".join(info)
