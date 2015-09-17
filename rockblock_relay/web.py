import os
from datetime import datetime
import base64
import logging as logging_module

import flask
import psycopg2
from flask import Flask, g, request, render_template
from psycopg2.extras import RealDictCursor

import raven.flask_glue

from .config import config
from . import util, database


app = Flask(__name__)
app.secret_key = os.urandom(16)
auth_decorator = raven.flask_glue.AuthDecorator(desc="RockBLOCK Relay")

app.before_first_request(util.setup_logging)

logger = logging_module.getLogger("rockblock_relay.web")

def connection():
    assert flask.has_request_context()
    if not hasattr(g, '_database'):
        g._database = database.connect()
    return g._database

@app.teardown_appcontext
def close_db_connection(exception):
    if hasattr(g, '_database'):
        try:
            g._database.commit()
        finally:
            g._database.close()


app.jinja_env.filters["plain_or_hex"] = util.plain_or_hex


@app.route('/')
@auth_decorator
def list():
    with database.cursor(connection()) as cur:
        cur.execute("SELECT * FROM messages ORDER BY id")
        messages = cur.fetchall()

    return render_template("home.html", messages=messages)

@app.route('/rockblock-incoming', methods=["POST"])
def rockblock_incoming():
    logger.info("Incoming message: %r", request.form)

    imei = int(request.form["imei"])
    message = {
        "source": config["imei_reverse"].get(imei, "unknown-rockblock"),
        "imei": imei,
        "momsn": int(request.form["momsn"]),
        "transmitted": datetime.strptime(request.form["transmit_time"], "%y-%m-%d %H:%M:%S"),
        "latitude": float(request.form["iridium_latitude"]),
        "longitude": float(request.form["iridium_longitude"]),
        "latlng_cep": float(request.form["iridium_cep"]),
        "data": base64.b16decode(request.form["data"].upper())
    }

    database.insert(connection(), message)

    return "OK"

if __name__ == '__main__':
    util.setup_logging()
    app.run(debug=True, use_reloader=False)
