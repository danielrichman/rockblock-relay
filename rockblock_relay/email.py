import sys
import email.mime.text
import email.utils
import smtplib

from .util import plain_or_hex
from .config import config
from .listen import listen

def callback(msg):
    if msg["data"] == b"":
        return

    source = config["imei_reverse"].get(msg["imei"], "unknown")
    data = plain_or_hex(msg["data"])
    body = "\n".join(["RockBLOCK", source, data])

    to = config["email"]
    from_ = "rockblock@magpie.cusf.co.uk"

    message = email.mime.text.MIMEText(body)
    message["From"] = from_
    message["To"] = to
    message["Subject"] = "RockBLOCK Alert"

    s = smtplib.SMTP('localhost')
    s.sendmail(from_, [to], message.as_string())
    s.quit()

def main():
    if "email" not in config:
        raise ValueError("Email not configured")

    listen(callback)

if __name__ == "__main__":
    main()
