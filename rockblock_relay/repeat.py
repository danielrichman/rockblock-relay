from .config import config, need_auth
from .database import listen
from .push import push

def callback(message):
    if message["data"] == b"":
        return

    source = message["source"]
    targets = config["repeat"].get(source, [])

    for target in targets:
        push(target, message["data"])

def main():
    need_auth()
    listen(callback)

if __name__ == "__main__":
    main()
