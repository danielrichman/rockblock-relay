import sys
import select
import psycopg2
import traceback
from psycopg2.extras import RealDictCursor

from .util import send_mail

def listen(callback):
    conn = psycopg2.connect(dbname='rockblock-relay')
    conn.autocommit = True

    cur = conn.cursor(cursor_factory=RealDictCursor)
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


def main():
    listen(print)

if __name__ == "__main__":
    main()
