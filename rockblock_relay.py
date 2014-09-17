from datetime import datetime
from flask import Flask, g, request
import psycopg2
from psycopg2.extras import RealDictCursor
import raven.flask_glue

app = Flask(__name__)
auth_decorator = AuthDecorator(desc="Rockblock Relay")

def connection():
    assert flask.has_request_context()
    if not hasattr(g, '_database'):
        g._database = psycopg2.connect(app.config["POSTGRES"])
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

@app.route('/')
@auth_decorator
def list():
    return 'Hello World!'

@app.route('/rockblock-incoming')
def rockblock_incoming():
    query = """
    INSERT INTO messages
    (source, momsn, transmitted, latitude, longitude, latlng_cep, data)
    VALUES
    (%(imei)s, %(momsn)s, %(transmitted)s, %(latitude)s, %(longitude)s
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

if __name__ == '__main__':
    app.run()
