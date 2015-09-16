CREATE TABLE messages (
    id serial primary key,
    source text not null,
    imei bigint,
    momsn integer,
    transmitted timestamp not null,
    latitude double precision,
    longitude double precision,
    latlng_cep double precision,
    data bytea not null
);

CREATE FUNCTION messages_insert()
    RETURNS TRIGGER AS
    $$
        BEGIN
            PERFORM pg_notify('messages_insert', NEW.id::text);
            RETURN NULL;
        END
    $$
    LANGUAGE plpgsql;

CREATE TRIGGER messages_insert_trigger
    AFTER INSERT
    ON messages
    FOR EACH ROW EXECUTE PROCEDURE messages_insert();

GRANT SELECT, INSERT ON "messages" TO "www-data";
GRANT SELECT, UPDATE ON SEQUENCE "messages_id_seq" TO "www-data";

-- upgrade sequence:
-- ALTER TABLE messages ALTER imei  DROP NOT NULL
-- ALTER TABLE messages ALTER momsn DROP NOT NULL
-- ALTER TABLE messages ADD source text
-- UPDATE messages SET source = 'abc' WHERE imei = 'def'
-- ALTER TABLE messages ALTER latitude   DROP NOT NULL
-- ALTER TABLE messages ALTER longitude  DROP NOT NULL
-- ALTER TABLE messages ALTER latlng_cep DROP NOT NULL
