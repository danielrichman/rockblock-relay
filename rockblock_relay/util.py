import re
import base64
import textwrap
import email.mime.text
import smtplib

from .config import config

printable_re = re.compile(b"^[\\x20-\\x7E]+$")

def plain_or_hex(s):
    if printable_re.match(s):
        return bytes(s).decode("ascii")
    else:
        return textwrap.fill(base64.b16encode(s).decode("ascii"))

def send_mail(subject, body):
    to = config["email"]
    from_ = "rockblock@magpie.cusf.co.uk"

    message = email.mime.text.MIMEText(body)
    message["From"] = from_
    message["To"] = to
    message["Subject"] = subject

    s = smtplib.SMTP('localhost')
    s.sendmail(from_, [to], message.as_string())
    s.quit()
