from .config import config, need_auth
from .listen import listen
from .push import push

def callback(message):
    if message["data"] == b"":
        return

    source = message["imei"]
    if source not in config["imei_reverse"]:
        return

    source = config["imei_reverse"][source]
    targets = config["repeat"].get(source, [])

    for target in targets:
        push(target, message["data"])

def main():
    need_auth()
    listen(callback)

if __name__ == "__main__":
    main()
