from .util import plain_or_hex, send_mail
from .config import config
from .database import listen

def callback(msg):
    if msg["data"] == b"":
        return

    source = msg["source"]
    data = plain_or_hex(msg["data"])
    body = "\n".join(["RockBLOCK", source, data])

    send_mail("RockBLOCK message", body)

def main():
    listen(callback)

if __name__ == "__main__":
    main()
