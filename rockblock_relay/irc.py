import time
import threading
import traceback
import base64
import binascii
from datetime import datetime
import logging as logging_module

import irc.client

from .config import config
from . import util, database

logger = logging_module.getLogger("rockblock_relay.irc")

class Bot(irc.client.SimpleIRCClient):
    # Based on irc.bot, which is:
    # Copyright (C) 1999-2002  Joel Rosdahl
    # Portions Copyright © 2011-2012 Jason R. Coombs

    def __init__(self, host, port, nickname, channel):
        super(Bot, self).__init__()
        self.manifold._on_connect = self.on_connect

        self.host = host
        self.port = port
        self.reconnection_interval = 60
        self.nickname = nickname
        self.channel = channel
        self.ping_interval = 300
        self.last_pong = time.time()
        self.whois_callbacks = {}

    def reconnect(self):
        if not self.connection.is_connected():
            logger.info("reconnecting")
            # Queue up a retry
            self.connection.execute_delayed(self.reconnection_interval, self.reconnect)

            if self.connection.is_connected():
                self.connection.disconnect(msg)

            try:
                self.connect(self.host, self.port, self.nickname, '', self.nickname)
            except irc.client.ServerConnectionError:
                pass

    def on_connect(self, sock):
        logger.info("connected")
        self.connection.execute_delayed(0, self.join)

    def join(self):
        self.connection.join(self.channel)

    def on_disconnect(self, c, e):
        logger.error("disconnected, will reconnect soon")
        self.whois_callbacks = {}
        self.connection.execute_delayed(self.reconnection_interval, self.reconnect)

    def get_version(self):
        return "Python irc.bot ({version})".format(version=irc.client.VERSION_STRING)

    def on_ctcp(self, c, e):
        nick = e.source.nick
        if e.arguments[0] == "VERSION":
            c.ctcp_reply(nick, "VERSION " + self.get_version())

    def start(self):
        self.reconnect()
        self.connection.set_keepalive(self.ping_interval)
        self.connection.execute_every(self.ping_interval / 10, self.check_pong)
        super(Bot, self).start()

    def on_pong(self, arg1, arg2):
        logger.debug("received pong")
        self.last_pong = time.time()

    def check_pong(self):
        delta = time.time() - self.last_pong
        if self.connection.is_connected() and abs(delta) > self.ping_interval * 2:
            logger.error("Pong timeout, disconnecting")
            self.connection.disconnect("No PONG from server")

    def broadcast(self, msg):
        if self.connection.is_connected():
            logger.info("Broadcast %s", msg)
            for line in msg.splitlines():
                self.connection.privmsg(self.channel, line)

    def on_pubmsg(self, c, e):
        nick = e.source.nick
        message = e.arguments[0]
        binary_prefix = self.nickname + ": binary "
        ascii_prefix = self.nickname + ": push "

        if message.startswith(binary_prefix):
            message = message[len(binary_prefix):].strip().upper()
            try:
                message = base64.b16decode(message)
            except binascii.Error:
                logger.info("Refused binary from nick %s: invalid b16", nick)
                self.broadcast("Invalid b16 data")
                return

        elif message.startswith(ascii_prefix):
            message = message[len(ascii_prefix):].strip()
            try:
                message = message.encode("ascii")
                if not util.is_printable(message):
                    raise ValueError
            except (UnicodeEncodeError, ValueError):
                logger.info("Refused push from nick %s: non-ascii", nick)
                self.broadcast("Non ascii characters: consider using binary mode.")
                return

        else:
            return

        assert isinstance(message, bytes)

        if not (1 <= len(message) <= 149):
            logger.info("Refused push request from nick %s: bad length %s", nick, len(message))
            self.broadcast("Push refused: bad message length")
            return

        row = { 
            "source": "irc",
            "imei": None,
            "momsn": None,
            "transmitted": datetime.utcnow(),
            "latitude": None,
            "longitude": None,
            "latlng_cep": None,
            "data": message
        }   

        def cb(state, channels):
            logger.debug("push callback fired: %r %r", state, channels)

            if hasattr(cb, "once"):
                # this is not an error
                logger.debug("CB: second call")
                return

            cb.once = True

            if state != "ok":
                logger.error("Whois for %s failed", nick)
                self.broadcast("Failed to whois {}".format(nick))
                try:
                    self.whois_callbacks.get(nick, []).remove(cb)
                except ValueError:
                    logger.error("in whois timeout, failed to remove whois cb")
                else:
                    logger.debug("in whois timeout, removed whois cb")
                return

            accept = {"+" + self.channel, "@" + self.channel}
            authed = bool(channels & accept)

            if not authed:
                logger.info("Auth failure: %s, %r", nick, channels)
                self.broadcast("{}: you need voice or op".format(nick))
                return

            logger.info("Push %s %s", nick, util.plain_or_hex(message))
            self.broadcast("{}: enqueued".format(nick))
            with database.connect() as conn:
                database.insert(conn, row)

        self.whois_callbacks.setdefault(nick, []).append(cb)
        self.connection.execute_delayed(10, lambda: cb("timeout", None))
        c.whois([nick])

    def on_whoischannels(self, c, e):
        nick = e.arguments[0]
        callbacks = self.whois_callbacks.pop(nick, [])
        logger.debug("on_whoischannels %s; running %s callbacks", nick, len(callbacks))
        for cb in callbacks:
            cb("ok", set(e.arguments[1].split()))

def message_to_line(msg):
    source = msg["source"]
    data = util.plain_or_hex(msg["data"])
    if data == "":
        data = "<zero byte message / ack>"
    if msg["latitude"] or msg["longitude"]:
        return '{0} @ ~{1},{2}: {3}'.format(source, msg["latitude"], msg["longitude"], data)
    else:
        return '{0}: {1}'.format(source, data)


kill_everything = threading.Event()

class Thread(threading.Thread):
    def run(self):
        try:
            super(Thread, self).run()
        except:
            logger.exception("Thread: uncaught exception")
        else:
            logger.exception("Clean thread exit?")
        finally:
            kill_everything.set()


def main():
    util.setup_logging()
    logging_module.getLogger("irc").setLevel(logging_module.INFO)

    bot = Bot(**config["irc"])

    def cb(msg):
        # we do _not_ filter empty messages here.
        bot.broadcast(message_to_line(msg))

    def listen2():
        database.listen(cb)

    Thread(target=bot.start, daemon=True).start()
    Thread(target=listen2, daemon=True).start()

    try:
        kill_everything.wait()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
