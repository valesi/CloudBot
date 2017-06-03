import asyncio
from collections import deque

from sqlalchemy import Table, Column, UniqueConstraint, String

from cloudbot import hook, event
from cloudbot.util import database


table = Table(
    "regex_chans",
    database.metadata,
    Column("connection", String),
    Column("channel", String),
    Column("status", String),
    UniqueConstraint("connection", "channel")
)

# Default value.
# If True, all channels without a setting will have regex enabled
# If False, all channels without a setting will have regex disabled
default_enabled = True

QUEUE_MAX_LEN = 10
events = {}

plugin_whitelist = ["factoids"]


@hook.on_start()
def load_cache(db):
    """
    :type db: sqlalchemy.orm.Session
    """
    global status_cache
    status_cache = {}
    for row in db.execute(table.select()):
        conn = row["connection"]
        chan = row["channel"]
        status = row["status"]
        status_cache[(conn, chan)] = status


def set_status(db, conn, chan, status):
    """
    :type db: sqlalchemy.orm.Session
    :type conn: str
    :type chan: str
    :type status: str
    """
    if (conn, chan) in status_cache:
        # if we have a set value, update
        db.execute(
            table.update().values(status=status).where(table.c.connection == conn).where(table.c.channel == chan))
    else:
        # otherwise, insert
        db.execute(table.insert().values(connection=conn, channel=chan, status=status))
    db.commit()
    load_cache(db)


def delete_status(db, conn, chan):
    db.execute(table.delete().where(table.c.connection == conn).where(table.c.channel == chan))
    db.commit()
    load_cache(db)


def store_event(event):
    global events
    if (event.conn.name, event.chan) in events:
        events[(event.conn.name, event.chan)].appendleft(event)
    else:
        events[(event.conn.name, event.chan)] = deque([event], QUEUE_MAX_LEN)


def get_event(conn_name, chan, index=0):
    """Returns the suppressed event at index"""
    if (conn_name, chan) in events:
        return events[(conn_name, chan)][index]


def check_solicit_index(conn_name, chan, text):
    """Check if .get <text> is a number, otherwise it's a direct regex command"""
    if text:
        try:
            index = int(text)
        except:
            # NaN: Direct regex command
            return (None, None)
    else:
        index = 0

    # Allow both negative and positive syntax
    if index < 0:
        index *= -1
    if (conn_name, chan) in events:
        if index >= len(events[(conn_name, chan)]):
            return (False, "Out of bounds. Max index: {}".format(len(events[(conn_name, chan)]) - 1))
        return (True, index)
    else:
        return (False, None)


@hook.command("get", autohelp=False)
def solicit(bot, conn, text, chan, nick, user):
    """[index] - Gets suppressed event at count [index] from most recent 0, defaulting to last"""
    if text:
        ret, value = check_solicit_index(conn.name, chan, text)
        if ret is None:
            # Run a new event directly with the force flag
            e = event.Event(bot=bot, conn=conn, content=text, event_type=event.EventType.message, channel=chan, nick=nick, user=user, force=True)
            asyncio.async(bot.process(e), loop=bot.loop)


@hook.sieve()
def sieve_regex(bot, event, _hook):
    prefix = event.conn.config.get("command_prefix")

    if _hook.type == "regex" and event.chan.startswith("#"):
        if _hook.plugin.title not in plugin_whitelist:
            if event.force:
                bot.logger.info("Force run regex: {}".format(event.match.group()))
                return event
            status = status_cache.get((event.conn.name, event.chan))
            if status != "ENABLED" and (status == "DISABLED" or not default_enabled):
                # Allow sed/correction with command prefix
                if _hook.plugin.title == "correction":
                    return event if event.match.group().startswith(prefix) else None
                bot.logger.info("[{}] Denying {} from {}. Storing in queue.".format(event.conn.name, _hook.function_name, event.chan))
                store_event(event)
                return
            bot.logger.info("[{}] Allowing {} to {}".format(event.conn.name, _hook.function_name, event.chan))
    elif _hook.type == "command" and _hook.function_name == "solicit":
        # Don't allow recursive .get .get .get ...
        if event.text.startswith(prefix + event.triggered_command):
            return
        # TODO get last regex of user if text is user?
        ret, value = check_solicit_index(event.conn.name, event.chan, event.text)
        # number: valid index
        if ret:
            return get_event(event.conn.name, event.chan, value)
        # number: invalid index
        elif ret is False:
            if value:
                event.message(value)
            return
        # ret is None: NaN: direct regex command (force flag) passes through solicit()

    return event


@hook.command(autohelp=False, permissions=["botcontrol"])
def enableregex(text, db, conn, chan, nick, message, notice):
    text = text.lower()
    if not text:
        channel = chan
    elif text.startswith("#"):
        channel = text
    else:
        channel = "#{}".format(text)

    message("Enabling regex matching in " + channel)
    set_status(db, conn.name, channel, "ENABLED")


@hook.command(autohelp=False, permissions=["botcontrol"])
def disableregex(text, db, conn, chan, nick, message, notice):
    text = text.lower()
    if not text:
        channel = chan
    elif text.startswith("#"):
        channel = text
    else:
        channel = "#{}".format(text)

    message("Disabling regex matching in " + channel)
    set_status(db, conn.name, channel, "DISABLED")


@hook.command(autohelp=False, permissions=["botcontrol"])
def resetregex(text, db, conn, chan, nick, message, notice):
    text = text.lower()
    if not text:
        channel = chan
    elif text.startswith("#"):
        channel = text
    else:
        channel = "#{}".format(text)

    message("Resetting regex matching in " + channel)
    delete_status(db, conn.name, channel)


@hook.command(autohelp=False, permissions=["botcontrol"])
def regexstatus(text, conn, chan):
    text = text.lower()
    if not text:
        channel = chan
    elif text.startswith("#"):
        channel = text
    else:
        channel = "#{}".format(text)
    status = status_cache.get((conn.name, chan))
    if not status:
        status = "ENABLED" if default_enabled else "DISABLED"
    return "Regex status for {}: {}".format(channel, status)


@hook.command(autohelp=False, permissions=["botcontrol"])
def listregex(conn):
    values = []
    for (conn_name, chan), status in status_cache.items():
        if conn_name != conn.name:
            continue
        values.append("{}: {}".format(chan, status))
    return ", ".join(values) if values else "No overrides. Default: {}".format("enabled" if default_enabled else "disabled")
