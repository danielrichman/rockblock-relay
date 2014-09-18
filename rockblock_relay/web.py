import os
from datetime import datetime
import re
import base64
import textwrap

import flask
import psycopg2
from flask import Flask, g, request, render_template
from psycopg2.extras import RealDictCursor

import raven.flask_glue

from .config import config


app = Flask(__name__)
app.secret_key = os.urandom(16)
auth_decorator = raven.flask_glue.AuthDecorator(desc="Rockblock Relay")


def connection():
    assert flask.has_request_context()
    if not hasattr(g, '_database'):
        g._database = psycopg2.connect(dbname=config["database"])
    return g._database

def cursor():
    return connection().cursor(cursor_factory=RealDictCursor)

@app.teardown_appcontext
def close_db_connection(exception):
    if hasattr(g, '_database'):
        try:
            g._database.commit()
        finally:
            g._database.close()

printable_re = re.compile(b"^[\\x20-\\x7E]+$")

@app.template_filter('plain_or_hex')
def plain_or_hex(s):
    if printable_re.match(s):
        return bytes(s).decode("ascii")
    else:
        return textwrap.fill(base64.b16encode(s).decode("ascii"))

@app.route('/')
@auth_decorator
def list():
    with cursor() as cur:
        cur.execute("SELECT * FROM messages ORDER BY id")
        messages = cur.fetchall()

    return render_template("home.html", messages=messages)

@app.route('/rockblock-incoming', methods=["POST"])
def rockblock_incoming():
    query = """
    INSERT INTO messages
    (source, momsn, transmitted, latitude, longitude, latlng_cep, data)
    VALUES
    (%(source)s, %(momsn)s, %(transmitted)s, %(latitude)s, %(longitude)s,
     %(latlng_cep)s, %(data)s)
    """

    args = {
        "source": int(request.form["imei"]),
        "momsn": int(request.form["momsn"]),
        "transmitted": datetime.strptime(request.form["transmit_time"], "%y-%m-%d %H:%M:%S"),
        "latitude": float(request.form["iridium_latitude"]),
        "longitude": float(request.form["iridium_longitude"]),
        "latlng_cep": float(request.form["iridium_cep"]),
        "data": base64.b16decode(request.form["data"].upper())
    }

    with cursor() as cur:
        cur.execute(query, args)

    return "OK"

if __name__ == '__main__':
    app.run()
