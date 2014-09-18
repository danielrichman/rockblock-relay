import base64
import urllib.parse
import http.client
import ssl

from .config import config, need_auth
from .listen import listen
from .push import push

need_auth()

ssl_context = ssl.create_default_context()
# XXX TLSv1 connections seem to fail!
ssl_context.options |= ssl.OP_NO_TLSv1
ssl_context.options &= ~ssl.OP_NO_SSLv3

class SubmitMessageError(Exception): pass

def callback(message):
    source = message["imei"]
    if source not in config["imei_reverse"]:
        return

    source = config["imei_reverse"][source]
    targets = config["repeat"].get(source, [])

    for target in targets:
        push(target, message["data"])

def main():
    listen(callback)

if __name__ == "__main__":
    main()
