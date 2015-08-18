-- Aug 3, 2015
-- Adds tables for storing messages and messaging information

CREATE TABLE qiita.message (
    message_id           bigserial  NOT NULL,
    message              varchar  NOT NULL,
    message_time         timestamp DEFAULT current_timestamp NOT NULL,
    expiration           timestamp,
    CONSTRAINT pk_message PRIMARY KEY ( message_id )
 );

CREATE TABLE qiita.message_user (
    email                varchar  NOT NULL,
    message_id           bigint  NOT NULL,
    read                 bool DEFAULT 'false' NOT NULL,
    CONSTRAINT idx_message_user PRIMARY KEY ( email, message_id )
 );

CREATE INDEX idx_message_user_0 ON qiita.message_user ( message_id );

CREATE INDEX idx_message_user_1 ON qiita.message_user ( email );

COMMENT ON COLUMN qiita.message_user.read IS 'Whether the message has been read or not.';

ALTER TABLE qiita.message_user ADD CONSTRAINT fk_message_user FOREIGN KEY ( message_id ) REFERENCES qiita.message( message_id );

ALTER TABLE qiita.message_user ADD CONSTRAINT fk_message_user_0 FOREIGN KEY ( email ) REFERENCES qiita.qiita_user( email );
