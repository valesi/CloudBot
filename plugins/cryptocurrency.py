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

import requests

from cloudbot import hook


CMC_API_URL = "https://api.coinmarketcap.com/v1/ticker/"
BA_API_URL = "https://apiv2.bitcoinaverage.com/indices/global/ticker/{}{}"
GDAX_API_URL = "https://api.gdax.com/products/{}-USD/ticker"


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
#    "btc": "₿"  # official symbol in Unicode (\u20bf)
}


def format_output(coin, currency, price, change=None, avg_change=False, to_btc=None):
    price = float(price)
    out = []

    if currency.lower() in CURRENCY_SIGNS:
        out.append("{}{:,.2f}".format(CURRENCY_SIGNS[currency.lower()], price))
    else:
        out.append("{:,.2f} {}".format(price, currency.upper()))

    if change:
        change = float(change)
        if change > 0:
            change_str = "$(green){}%$(c)".format(change)
        elif change < 0:
            change_str = "$(red){}%$(c)".format(change)
        else:
            change_str = "{}%".format(change)
        out.append("{} 24hr{}".format(change_str.format(change), " avg" if avg_change else ""))

    if to_btc is not None:  # Could be 0.0
        out.append("{:,.7f} BTC".format(float(to_btc)))

    return "[h1]{}:[/h1] ".format(coin) + " [div] ".join(out)


@hook.command("btcavg")
def bitcoin_average(text):
    """<coin> [currency] -- Gets the price of <coin> against [currency], defaulting to USD"""
    args = text.upper().split()
    coin = args.pop(0)

    currency = args.pop(0) if args else "USD"

    try:
        response = requests.get(BA_API_URL.format(coin, currency))
        response.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        if "for symbol is not valid for url" in str(e):
            return "Invalid symbol: " + coin + currency
        else:
            return "Could not get value: {}".format(e)

    data = response.json()

    return format_output(coin, currency, data["last"], data["changes"]["percent"]["day"], True)


@hook.command("cryptocurrency", "cmc", "crypto")
def coinmarketcap(text):
    """<ticker> [currency] -- Returns current value of a cryptocurrency. [currency] defaults to USD."""
    args = text.lower().split()
    coin = args.pop(0)

    currency = args.pop(0) if args else "usd"
    params = {}
    if currency is not "usd":
        params["convert"] = currency.upper()

    try:
        response = requests.get(CMC_API_URL, params=params)
        response.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        return "Could not get value: {}".format(e)

    data = response.json()

    if "error" in data:
        return data["error"]

    # Find the symbol
    for ccoin in data:
        if ccoin["symbol"] == coin.upper() or ccoin["id"] == coin:
            if "price_{}".format(currency) not in ccoin:
                return "Cannot convert to currency: " + currency
            return format_output(ccoin["symbol"], currency, ccoin["price_{}".format(currency)], ccoin["percent_change_24h"],
                                 to_btc=float(ccoin["price_btc"]))

    return "Coin not found"



@hook.command()
def gdax(text):
    """[coin] -- Gets the current GDAX USD price for <coin>."""
    coin = text.upper() if text else "BTC"

    try:
        response = requests.get(GDAX_API_URL.format(coin))
        response.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        return "Could not get value: {}".format(e)

    data = response.json()

    if "message" in data:
        return data["message"]

    return format_output(coin, "USD", data["price"])


# aliases
@hook.command("bitcoin", "btc", autohelp=False)
def bitcoin(text):
    """ -- Returns current Bitcoin value """
    return bitcoin_average("btc " + text)


@hook.command("bitcoincash", "bch", autohelp=False)
def bitcoincash(text):
    """ -- Returns current Bitcoin Cash value """
    return coinmarketcap("bch " + text)


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

