"""
cryptocurrency.py

A plugin that uses the CoinMarketCap JSON API to get values for cryptocurrencies.

Created By:
    - Luke Rogers <https://github.com/lukeroge>

Special Thanks:
    - https://coinmarketcap-nexuist.rhcloud.com/

License:
    GPL v3
"""
from datetime import datetime
from urllib.parse import quote_plus

import requests

from cloudbot import hook

API_URL = "https://coinmarketcap-nexuist.rhcloud.com/api/{}"
CURRENCY_SIGNS = {
    "usd": "$",
    "eur": "€",
    "cny": "¥",
    "gbp": "£",
    "cad": "$",
    "rub": "₽",
    "hkd": "$",
    "jpy": "¥",
    "aud": "$",
    "brl": "R$",
    "inr": "₹",
    "krw": "₩",
    "mxn": "$",
    "idr": "Rp",
    "chf": "CHF",
    "btc": "฿"  # Thai Baht
#    "btc": "₿"  # official symbol in Unicode (\x20bf)
}


# aliases
@hook.command("bitcoin", "btc", autohelp=False)
def bitcoin(text):
    """ -- Returns current Bitcoin value """
    return crypto_command("btc " + text)


@hook.command("ethereum", "eth", autohelp=False)
def ethereum(text):
    """ -- Returns current Ethereum value """
    return crypto_command("btc " + text)


@hook.command("ethereum_classic", "etc", autohelp=False)
def ethereum_classic(text):
    """ -- Returns current Ethereum Classic value """
    return crypto_command("etc " + text)


@hook.command("litecoin", "ltc", autohelp=False)
def litecoin(text):
    """ -- Returns current Litecoin value """
    return crypto_command("ltc " + text)


@hook.command("nem", "xem", autohelp=False)
def nemcoin(text):
    """ -- Returns current NEM value """
    return crypto_command("xem " + text)


@hook.command("ripple", "xrp", autohelp=False)
def ripple(text):
    """ -- Returns current Ripple value """
    return crypto_command("xrp " + text)


@hook.command("dash", autohelp=False)
def dash(text):
    """ -- Returns current Dash value """
    return crypto_command("dash " + text)


@hook.command("monero", "xmr", autohelp=False)
def monero(text):
    """ -- Returns current Monero value """
    return crypto_command("xmr " + text)


@hook.command("dogecoin", "doge", autohelp=False)
def dogecoin(text):
    """ -- Returns current dogecoin value """
    return crypto_command("doge " + text)


@hook.command("zcash", "zec", autohelp=False)
def zcash(text):
    """ -- Returns current Zcash value """
    return crypto_command("zec " + text)


# main command
@hook.command("crypto", "cryptocurrency")
def crypto_command(text):
    """ <ticker> [currency] -- Returns current value of a cryptocurrency """
    args = text.split()
    ticker = args.pop(0)

    try:
        if not args:
            currency = 'usd'
        else:
            currency = args.pop(0).lower()

        encoded = quote_plus(ticker)
        request = requests.get(API_URL.format(encoded))
        request.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        return "Could not get value: {}".format(e)

    data = request.json()

    if "error" in data:
        return "{}.".format(data['error'])

    updated_time = datetime.fromtimestamp(float(data['timestamp']))
    if (datetime.today() - updated_time).days > 2:
        # the API retains data for old ticker names that are no longer updated
        # in these cases we just return a "not found" message
        return "Currency not found."

    change = float(data['change'])
    if change > 0:
        change_str = "$(green){}%$(c)".format(change)
    elif change < 0:
        change_str = "$(red){}%$(c)".format(change)
    else:
        change_str = "{}%".format(change)

    currency_sign = CURRENCY_SIGNS[currency]

    return "[h1]{}:[/h1] {}{:,.2f} {} [h3]({:,.7f} BTC)[/h3] [div] {} 24hr change".format(data['symbol'].upper(),
                                                                            currency_sign,
                                                                            float(data['price'][currency]),
                                                                            currency.upper(),
                                                                            float(data['price']['btc']),
                                                                            change_str)
