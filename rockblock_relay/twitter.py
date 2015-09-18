import logging as logging_module

import tweepy

from .util import is_printable, setup_logging
from .config import config, need_auth
from .database import listen

logger = logging_module.getLogger("rockblock_relay.twitter")

def callback(msg):
    prefix = b"tweet "
    message = bytes(msg["data"])

    if not message.startswith(prefix):
        return

    if msg["source"] == "irc":
        logger.error("Tweet rejected: not a rockblock")
        return

    if not is_printable(message):
        logger.error("Tweet rejected: not printable")
        return

    message = message.decode("ascii")
    args = {"status": message}
    if msg["latitude"] is not None and msg["longitude"] is not None:
        args["lat"] = msg["latitude"]
        args["lon"] = msg["longitude"]
        args["display_coordinates"] = True

    logger.info("Tweeting %r", args)

    creds = config["auth"]["twitter"]
    auth = tweepy.OAuthHandler(creds["consumer_key"], creds["consumer_secret"])
    auth.secure = True
    auth.set_access_token(creds["access_token"], creds["access_token_secret"])
    api = tweepy.API(auth)
    api.update_status(**args)

def main():
    setup_logging()
    need_auth()
    listen(callback)

if __name__ == "__main__":
    main()
