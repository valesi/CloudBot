from googlefinance import getQuotes
from cloudbot import hook


@hook.on_start()
def on_start(bot):
    pass


@hook.command()
def stock(text):
    """<symbol> -- gets stock information"""
    sym = text.upper()

    try:
        quote = getQuotes(sym)[0]
    except requests.exceptions.HTTPError as e:
        return "Could not get stock data: {}".format(e)

    if not quote:
        return "No data"

    return "[h1]{StockSymbol}[/h1] [div] ${LastTradePrice}".format(**quote)
