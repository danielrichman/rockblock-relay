CREATE TABLE messages (
    id serial primary key,
    imei bigint not null,
    momsn integer not null,
    transmitted timestamp not null,
    latitude double precision not null,
    longitude double precision not null,
    latlng_cep double precision not null,
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
