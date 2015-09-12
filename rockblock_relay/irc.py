import time
import threading
import traceback

import irc.client

from .config import config
from .listen import listen
from . import util

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

    def reconnect(self):
        if not self.connection.is_connected():
            # Queue up a retry
            self.connection.execute_delayed(self.reconnection_interval, self.reconnect)

            if self.connection.is_connected():
                self.connection.disconnect(msg)

            try:
                self.connect(self.host, self.port, self.nickname, '', self.nickname)
            except irc.client.ServerConnectionError:
                pass

    def on_connect(self, sock):
        self.connection.execute_delayed(0, self.join)

    def join(self):
        self.connection.join(self.channel)

    def on_disconnect(self, c, e):
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

    def on_pong(self):
        self.last_pong = time.time()

    def check_pong(self):
        delta = time.time() - self.last_pong
        if self.connection.is_connected() and abs(delta) > self.ping_interval * 2:
            self.connection.disconnect("No PONG from server")

    def broadcast(self, msg):
        if self.connection.is_connected():
            self.connection.privmsg(self.channel, msg)


def message_to_line(msg):
    source = config["imei_reverse"].get(msg["imei"], "unknown")
    data = util.plain_or_hex(msg["data"])
    return '{0} @ ~{1},{2}: {3}'.format(source, msg["latitude"], msg["longitude"], data)


kill_everything = threading.Event()

class Thread(threading.Thread):
    def run(self):
        try:
            super(Thread, self).run()
        except:
            traceback.print_exc()
        else:
            print("Clean exit", file=sys.stderr)
        finally:
            kill_everything.set()


def main():
    bot = Bot(**config["irc"])

    def cb(msg):
        if msg["data"] == b"":
            return

        bot.broadcast(message_to_line(msg))

    def listen2():
        listen(cb)

    Thread(target=bot.start, daemon=True).start()
    Thread(target=listen2, daemon=True).start()

    try:
        kill_everything.wait()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
