"""
issafe.py

Check the Google Safe Browsing list to see a website's safety rating.

Created By:
    - Foxlet <http://furcode.tk/>

License:
    GNU General Public License (Version 3)

Docs: https://developers.google.com/safe-browsing/v4/
Test links: https://testsafebrowsing.appspot.com/
"""
from collections import defaultdict
from urllib.parse import urlparse

import requests

import cloudbot
from cloudbot import hook

API_SB = "https://safebrowsing.googleapis.com/v4/threatMatches:find"

THREAT_TYPES = {"MALWARE": "Malware", "SOCIAL_ENGINEERING": "Phishing", "UNWANTED_SOFTWARE": "Unwanted software",
                "POTENTIALLY_HARMFUL_APPLICATION": "Potentially harmful app"}
PLATFORM_TYPES = {"WINDOWS": "Windows", "OSX": "macOS", "LINUX": "Linux",
                  "CHROME": "Chrome", "ANDROID": "Android", "IOS": "iOS"}


@hook.on_start(api_keys=["google_dev_key"])
def load_api(bot):
    global dev_key
    dev_key = bot.config.get("api_keys", {}).get("google_dev_key", None)


@hook.command()
def issafe(text, message):
    """<website> -- Checks the website against Google's Safe Browsing List."""
    if urlparse(text).scheme not in ('https', 'http'):
        return "URL must have http(s) schema"

    request_info = {"client":
                    {"clientId": "CloudBot", "clientVersion": cloudbot.__version__},
                    "threatInfo":
                    {"threatTypes": [*THREAT_TYPES],
                     "platformTypes": [*PLATFORM_TYPES],
                     "threatEntryTypes": ["URL"],
                     "threatEntries": [{"url": text}]
                     }}

    try:
        parsed = requests.post(API_SB, params={"key": dev_key}, headers={"Content-Type": "application/json"},
                               json=request_info, timeout=5)
    except requests.Timeout:
        return "API timed out"
    except:
        message("API request error")
        raise

    try:
        data = parsed.json()
    except:
        message("Invalid response data")
        raise

    if "error" in data:
        return "HTTP {}: {}".format(data["error"]["code"], data["error"]["message"])

    if "matches" not in data:
        return "$(green)No known threats$(c)"
    else:
        # Merge platforms under threat types
        threats = defaultdict(list)

        for d in [{m["threatType"]: m["platformType"]} for m in data["matches"]]:
            for k, v in d.items():
                threats[k].append(PLATFORM_TYPES[v])

        out = []
        for threat_type in threats:
            out.append("[h1]{}:[/h1] {}".format(THREAT_TYPES[threat_type],
                                                ", ".join(threats[threat_type])))
        return " [div] ".join(out)
