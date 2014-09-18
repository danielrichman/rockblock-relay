import re
import base64
import textwrap

printable_re = re.compile(b"^[\\x20-\\x7E]+$")

def plain_or_hex(s):
    if printable_re.match(s):
        return bytes(s).decode("ascii")
    else:
        return textwrap.fill(base64.b16encode(s).decode("ascii"))
