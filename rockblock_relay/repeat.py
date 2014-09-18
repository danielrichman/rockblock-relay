import base64
import urllib.parse
import http.client
import ssl

from .config import config, need_auth
from .listen import listen

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
        auth = config["auth"][target]
        post = {
            "imei": str(config["imei"][target]),
            "username": auth["username"],
            "password": auth["password"],
            "data": base64.b16encode(message["data"])
        }
        body = urllib.parse.urlencode(post)
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": "text/plain"
        }
        print(body)
        conn = http.client.HTTPSConnection("secure.rock7mobile.com", 443, context=ssl_context)
        conn.request("POST", "/rockblock/MT", body, headers)
        response = conn.getresponse().read()
        if not response.startswith(b"OK"):
            raise SubmitMessageError(response)
        conn.close()

def main():
    listen(callback)

if __name__ == "__main__":
    main()
