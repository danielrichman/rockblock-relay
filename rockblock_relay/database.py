import sys
import select
import psycopg2
import traceback
from psycopg2.extras import RealDictCursor

from .config import config
from .util import send_mail

def connect():
    return psycopg2.connect(dbname=config["database"])

def cursor(conn):
    return conn.cursor(cursor_factory=RealDictCursor)

def listen(callback):
    conn = connect()
    conn.autocommit = True

    cur = cursor(conn)
    cur.execute('LISTEN "messages_insert";')

    while True:
        try:
            select.select([conn], [], [], 600)
        except KeyboardInterrupt:
            break

        conn.poll()

        while conn.notifies:
            notify = conn.notifies.pop()
            id = int(notify.payload)

            cur.execute("SELECT * FROM messages WHERE id = %s", (id, ))
            row = cur.fetchone()

            if row is not None:
                try:
                    callback(row)
                except KeyboardInterrupt:
                    raise
                except SystemExit:
                    raise
                except:
                    print("Exception while handling", id, file=sys.stderr)
                    traceback.print_exc()
                    send_mail("RockBLOCK callback error", traceback.format_exc())
            else:
                print("Failed to get row", id, file=sys.stderr)

def insert(conn, message):
    query = """
    INSERT INTO messages
    (source, imei, momsn, transmitted, latitude, longitude, latlng_cep, data)
    VALUES
    (%(source)s, %(imei)s, %(momsn)s, %(transmitted)s, %(latitude)s,
     %(longitude)s, %(latlng_cep)s, %(data)s)
    """

    with cursor(conn) as cur:
        cur.execute(query, message)

def main():
    listen(print)

if __name__ == "__main__":
    main()
