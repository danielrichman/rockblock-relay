import re
import base64
import textwrap
import email.mime.text
import smtplib
import logging
import logging.handlers

from .config import config

printable_re = re.compile(b"^[\\x20-\\x7E]+$")

def is_printable(s):
    return printable_re.match(s)

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
    message["To"] = ", ".join(to)
    message["Subject"] = subject

    s = smtplib.SMTP('localhost')
    s.sendmail(from_, to, message.as_string())
    s.quit()

_format_email = \
"""%(levelname)s from logger %(name)s (thread %(threadName)s)

Time:       %(asctime)s
Location:   %(pathname)s:%(lineno)d
Module:     %(module)s
Function:   %(funcName)s

%(message)s"""

_format_string = \
"[%(asctime)s] %(levelname)s %(name)s %(threadName)s: %(message)s"

def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    fmtr = logging.Formatter(_format_string)

    handler = logging.StreamHandler() # stderr
    handler.setFormatter(fmtr)
    handler.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)

    to = config["email"]
    from_ = "rockblock@magpie.cusf.co.uk"

    handler = logging.handlers.SMTPHandler(
            "localhost", from_, to, "RockBLOCK logger")
    handler.setLevel(logging.ERROR)
    handler.setFormatter(logging.Formatter(_format_email))
    root_logger.addHandler(handler)
