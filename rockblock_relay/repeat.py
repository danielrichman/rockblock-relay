from .config import config, need_auth
from .database import listen
from .push import push
from . import util

def callback(message):
    if message["data"] == b"":
        return

    source = message["source"]
    targets = config["repeat"].get(source, [])
    logger.info("Repeating %s %s to %s", source, util.plain_or_hex(message["data"]), targets)

    for target in targets:
        push(target, message["data"])

def main():
    util.setup_logging()
    need_auth()
    listen(callback)

if __name__ == "__main__":
    main()
