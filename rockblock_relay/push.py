import sys
import argparse
import base64
import urllib.parse
import http.client
import ssl

from .config import config, need_auth
from .listen import listen

ssl_context = ssl.create_default_context()
# XXX TLSv1 connections seem to fail!
ssl_context.options |= ssl.OP_NO_TLSv1
ssl_context.options &= ~ssl.OP_NO_SSLv3

class SubmitMessageError(Exception): pass

def push(target, data):
    need_auth()
    auth = config["auth"][target]
    post = {
        "imei": str(config["imei"][target]),
        "username": auth["username"],
        "password": auth["password"],
        "data": base64.b16encode(data)
    }
    body = urllib.parse.urlencode(post)
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "text/plain"
    }
    conn = http.client.HTTPSConnection("secure.rock7mobile.com", 443, context=ssl_context)
    conn.request("POST", "/rockblock/MT", body, headers)
    response = conn.getresponse().read()
    if not response.startswith(b"OK"):
        raise SubmitMessageError(response)
    conn.close()


parser = argparse.ArgumentParser(description='CLI message push')
parser.add_argument('target', metavar='TARGET',
                    help="Destination (name, not IMEI; IMEI is looked up in config)")
parser.add_argument('-x', '--hex', dest='hex', action='store_true', default=False,
                    help="Should the data be interpreted as b16 (default: plain)")
parser.add_argument('data', metavar='DATA')

def main():
    need_auth()

    args = parser.parse_args()

    if args.hex:
        data = base64.b16decode(args.data.upper())
    else:
        data = args.data.encode("ascii")

    push(args.target, data)

if __name__ == "__main__":
    main()
