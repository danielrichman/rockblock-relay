import select
import psycopg2
from psycopg2.extras import RealDictCursor

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

            callback(row)

def main():
    listen(print)

if __name__ == "__main__":
    main()
