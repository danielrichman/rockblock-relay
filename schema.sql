CREATE TABLE messages (
    id serial primary key,
    source bigint not null,
    momsn integer not null,
    transmitted timestamp not null,
    latitude double precision not null,
    longitude double precision not null,
    latlng_cep double precision not null,
    data bytea not null
);

GRANT SELECT, INSERT, UPDATE, DELETE on "messages" to "www-data";
GRANT SELECT, UPDATE ON SEQUENCE "messages_id_seq" to "www-data";
