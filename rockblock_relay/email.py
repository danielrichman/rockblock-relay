import logging as logging_module

from .util import plain_or_hex, send_mail, setup_logging
from .config import config
from .database import listen

logger = logging_module.getLogger("rockblock_relay.email")

def callback(msg):
    if msg["data"] == b"":
        return

    source = msg["source"]
    data = plain_or_hex(msg["data"])
    body = "\n".join(["RockBLOCK", source, data])

    logger.info("Sending mail for message %s %s", source, data)
    send_mail("RockBLOCK message", body)

def main():
    setup_logging()
    listen(callback)

if __name__ == "__main__":
    main()
