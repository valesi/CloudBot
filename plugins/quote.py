import random
from collections import defaultdict
from threading import RLock

from sqlalchemy import Table, Column, String
from sqlalchemy.exc import SQLAlchemyError

from cloudbot import hook
from cloudbot.util import database
from cloudbot.util.pager import paginated_list

search_pages = defaultdict(dict)

added_responses = ['Bam!', 'Bang!', 'Shazam!', 'Ding!', 'Dong!', 'Kapow!', 'Oh snap!', 'Wham!', 'lol', 'Nailed it!', 'hahaha']

table = Table(
    'grab',
    database.metadata,
    Column('name', String),
    Column('time', String),
    Column('quote', String),
    Column('chan', String)
)

grab_cache = {}
grab_locks = defaultdict(dict)
grab_locks_lock = RLock()
cache_lock = RLock()


@hook.on_start()
def load_cache(db):
    """
    :type db: sqlalchemy.orm.Session
    """
    with cache_lock:
        grab_cache.clear()
        for row in db.execute(table.select().order_by(table.c.time)):
            name = row["name"].lower()
            quote = row["quote"]
            chan = row["chan"]
            grab_cache.setdefault(chan, {}).setdefault(name, []).append(quote)


@hook.command("morequote", "qm", "moregrab", autohelp=False)
def moregrab(text, chan, conn):
    """[page] - if a search has lots of results the results are pagintated. If the most recent search is paginated the pages are stored for retreival. If no argument is given the next page will be returned else a page number can be specified."""
    pages = search_pages[conn.name].get(chan)
    if not pages:
        return "There are no pages to show."

    if text:
        try:
            index = int(text)
        except ValueError:
            return "Please specify an integer value."

        page = pages[index - 1]
        if page is None:
            return "Please specify a valid page number between 1 and {}.".format(len(pages))
        else:
            return page
    else:
        page = pages.next()
        if page is not None:
            return page
        else:
            return "All pages have been shown. You can specify a page number or do a new search."


def check_grabs(name, quote, chan):
    try:
        if quote in grab_cache[chan][name.lower()]:
            return True
        else:
            return False
    except KeyError:
        return False


def grab_add(nick, time, msg, chan, db):
    # Adds a quote to the grab table
    db.execute(table.insert().values(name=nick, time=time, quote=msg, chan=chan))
    db.commit()
    load_cache(db)


def get_latest_line(conn, chan, nick):
    for name, timestamp, msg in reversed(conn.history[chan]):
        if nick.casefold() == name.casefold():
            return name, timestamp, msg

    return None, None, None


@hook.command("quoteadd", "qadd", "qa", "grab")
def grab(text, nick, chan, db, conn, reply):
    """<nick> - grabs the last message from the specified nick and adds it to the quote database"""
    if text.lower() == nick.lower():
        return "Think you're hot shit, eh?"

    with grab_locks_lock:
        grab_lock = grab_locks[conn.name.casefold()].setdefault(chan.casefold(), RLock())

    with grab_lock:
        name, timestamp, msg = get_latest_line(conn, chan, text)
        if not msg:
            return "I couldn't find anything from {} in recent history.".format(text)

        if check_grabs(text.casefold(), msg, chan):
            return "I already have that quote from {} in the database".format(text)

        try:
            grab_add(name.casefold(), timestamp, msg, chan, db)
        except SQLAlchemyError:
            reply("Failed to add quote to db.")
            raise

        if check_grabs(name.casefold(), msg, chan):
            return random.choice(added_responses)
        else:
            return "Uhh the quote wasn't added for some reason."


def format_grab(name, quote):
    # add zero-width space to nicks to avoid highlighting people with printed grabs
    name = "{}{}{}".format(name[0], u"\u200B", name[1:])
    if quote.startswith("\x01ACTION") or quote.startswith("*"):
        quote = quote.replace("\x01ACTION", "").replace("\x01", "")
        return "* {}{}".format(name, quote)
    else:
        return "<{}> {}".format(name, quote)



@hook.command("lquote", "lq", "lastgrab", "lgrab")
def lastgrab(text, chan, message):
    """<nick> - prints the last grabbed quote from <nick>."""
    try:
        with cache_lock:
            lgrab = grab_cache[chan][text.lower()][-1]
    except (KeyError, IndexError):
        return "<{}> has never been quoted.".format(text)
    if lgrab:
        quote = lgrab
        message(format_grab(text, quote), chan)


@hook.command("q", "rquote", "quoterandom", "grabrandom", "grabr", autohelp=False)
def grabrandom(text, chan, message):
    """[nick] - grabs a random quote from the database"""
    with cache_lock:
        try:
            chan_grabs = grab_cache[chan]
        except KeyError:
            return "I couldn't find any quotes in {}.".format(chan)

        matching_quotes = []

        if text:
            for nick in text.split():
                try:
                    quotes = chan_grabs[nick.lower()]
                except LookupError:
                    message("{} is boring and has never been quoted in here".format(name))
                else:
                    matching_quotes.extend((nick, quote) for quote in quotes)
        else:
            matching_quotes.extend(
                (name, quote) for name, quotes in chan_grabs.items() for quote in quotes
            )

    if not matching_quotes:
        return "I couldn't find any quotes in {}.".format(chan)

    name, quote_text = random.choice(matching_quotes)

    message(format_grab(name, quote_text))


@hook.command("quotesearch", "quotes", "qs", "grabsearch", "grabs", autohelp=False)
def grabsearch(text, chan, conn, triggered_prefix):
    """[text] - matches [text] against nicks or quote strings in the database"""
    result = []
    lower_text = text.lower()
    with cache_lock:
        try:
            chan_grabs = grab_cache[chan]
        except LookupError:
            return "I couldn't find any quotes in {}.".format(chan)

        try:
            quotes = chan_grabs[lower_text]
        except KeyError:
            pass
        else:
            result.extend((text, quote) for quote in quotes)

        for name, quotes in chan_grabs.items():
            if name != lower_text:
                result.extend((name, quote) for quote in quotes if lower_text in quote.lower())

    if not result:
        return "I couldn't find any matches for {}.".format(text)

    grabs = []
    for name, quote in result:
        if lower_text == name:
            name = text

        grabs.append(format_grab(name, quote))

    pager = paginated_list(grabs)
    search_pages[conn.name][chan] = pager
    page = pager.next()
    if len(pager) > 1:
        page[-1] += " {}qm".format(triggered_prefix)

    return page
