drop table observation_tables;
drop table observations;
drop table sequence_hashes;
drop table sample_counts;

create table observation_tables(
    table_id varchar(64), 
    study_id integer,
    ref varchar(64),
    trim varchar(16),
    similarity float(24),
    primary key (table_id, study_id, ref, trim, similarity)
);

create table observations (
    table_id varchar(64),
    study_sample varchar(64),
    observation varchar(64),
    count float(24)
);

create table sequence_hashes (
    seq_hash char(32),
    sequence varchar(1024)
);

create table sample_counts (
    study_sample varchar(64),
    seq_hash char(32),
    count integer
); 
