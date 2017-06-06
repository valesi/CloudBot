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


CMC_API_URL = "https://coinmarketcap-nexuist.rhcloud.com/api/{}"
BA_API_URL = "https://api.bitcoinaverage.com/indices/global/ticker/{}{}"

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


def format_output(coin, currency, price, change, avg_change=False, to_btc=None):
    out = ["[h1]{}:[/h1] ".format(coin)]

    if currency.lower() in CURRENCY_SIGNS:
        out[0] = out[0] + "{}{:,.2f}".format(CURRENCY_SIGNS[currency.lower()], price)
    else:
        out[0] = out[0] + "{:,.2f} {}".format(float(price), currency.upper())

    change = float(change)
    if change > 0:
        change_str = "$(green){}%$(c)".format(change)
    elif change < 0:
        change_str = "$(red){}%$(c)".format(change)
    else:
        change_str = "{}%".format(change)
    out.append("{} 24hr {}change".format(change_str.format(change), "average " if avg_change else ""))

    if to_btc is not None:  # Could be 0.0
        out.append("{:,.7f} BTC".format(float(to_btc)))

    return " [div] ".join(out)


@hook.command("btca")
def bitcoin_average(text):
    """<coin> [currency] -- Gets the price of <coin> against [currency], defaulting to USD"""
    args = text.upper().split()
    coin = args.pop(0)

    currency = args.pop(0) if args else "USD"

    try:
        request = requests.get(BA_API_URL.format(coin, currency))
        request.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        if "for symbol is not valid for url" in str(e):
            return "Invalid symbol: " + coin + currency
        else:
            return "Could not get value: {}".format(e)

    data = request.json()

    return format_output(coin, currency, data["last"], data["changes"]["percent"]["day"])


@hook.command("crypto", "cryptocurrency")
def coinmarketcap(text):
    """<ticker> [currency] -- Returns current value of a cryptocurrency. [currency] defaults to USD."""
    args = text.lower().split()
    coin = args.pop(0)

    currency = args.pop(0) if args else "usd"

    try:
        request = requests.get(CMC_API_URL.format(quote_plus(coin)))
        request.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        return "Could not get value: {}".format(e)

    data = request.json()

    if "error" in data:
        return "{}.".format(data['error'])

    if currency not in data['price']:
        return "Currencies supported: {}".format(", ".join(list(data['price'])).upper())

    updated_time = datetime.fromtimestamp(float(data['timestamp']))
    if (datetime.today() - updated_time).days > 2:
        # the API retains data for old ticker names that are no longer updated
        # in these cases we just return a "not found" message
        return "{} ticker info outdated".format(ticker.upper())

    data = request.json()

    return format_output(data["symbol"].upper(), currency, data["price"][currency], data["change"], avg_change=True, to_btc=data["price"]["btc"])


# aliases
@hook.command("bitcoin", "btc", autohelp=False)
def bitcoin(text):
    """ -- Returns current Bitcoin value """
    return bitcoin_average("btc " + text)


@hook.command("ethereum", "eth", autohelp=False)
def ethereum(text):
    """ -- Returns current Ethereum value """
    return bitcoin_average("eth " + text)


@hook.command("ethereum_classic", "etc", autohelp=False)
def ethereum_classic(text):
    """ -- Returns current Ethereum Classic value """
    return coinmarketcap("etc " + text)


@hook.command("litecoin", "ltc", autohelp=False)
def litecoin(text):
    """ -- Returns current Litecoin value """
    return bitcoin_average("ltc " + text)


@hook.command("nem", "xem", autohelp=False)
def nemcoin(text):
    """ -- Returns current NEM value """
    return coinmarketcap("xem " + text)


@hook.command("ripple", "xrp", autohelp=False)
def ripple(text):
    """ -- Returns current Ripple value """
    return coinmarketcap("xrp " + text)


@hook.command("dash", autohelp=False)
def dash(text):
    """ -- Returns current Dash value """
    return coinmarketcap("dash " + text)


@hook.command("monero", "xmr", autohelp=False)
def monero(text):
    """ -- Returns current Monero value """
    return coinmarketcap("xmr " + text)


@hook.command("dogecoin", "doge", autohelp=False)
def dogecoin(text):
    """ -- Returns current dogecoin value """
    return coinmarketcap("doge " + text)


@hook.command("zcash", "zec", autohelp=False)
def zcash(text):
    """ -- Returns current Zcash value """
    return bitcoin_average("zec " + text)

