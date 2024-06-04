--
-- PostgreSQL database dump
--

-- Dumped from database version 13.9
-- Dumped by pg_dump version 13.9

-- SET statement_timeout = 0;
-- SET lock_timeout = 0;
-- SET idle_in_transaction_session_timeout = 0;
-- SET client_encoding = 'UTF8';
-- SET standard_conforming_strings = on;
-- SELECT pg_catalog.set_config('search_path', '', false);
-- SET check_function_bodies = false;
-- SET xmloption = content;
-- SET client_min_messages = warning;
-- SET row_security = off;

--
-- Name: qiita; Type: SCHEMA; Schema: -
--

CREATE SCHEMA qiita;



--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner:
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: archive_upsert(integer, character varying, character varying); Type: FUNCTION; Schema: public
--

CREATE OR REPLACE FUNCTION public.archive_upsert(amsi integer, af character varying, afv character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    LOOP
        -- first try to update the key
        UPDATE qiita.archive_feature_value SET archive_feature_value = afv WHERE archive_merging_scheme_id = amsi AND archive_feature = af;
        IF found THEN
            RETURN;
        END IF;
        -- not there, so try to insert the key
        -- if someone else inserts the same key concurrently,
        -- we could get a unique-key failure
        BEGIN
            INSERT INTO qiita.archive_feature_value (archive_merging_scheme_id, archive_feature, archive_feature_value) VALUES (amsi, af, afv);
            RETURN;
        EXCEPTION WHEN unique_violation THEN
            -- Do nothing, and loop to try the UPDATE again.
        END;
    END LOOP;
END;
$$;



--
-- Name: isnumeric(text); Type: FUNCTION; Schema: public
--

CREATE OR REPLACE FUNCTION public.isnumeric(text) RETURNS boolean
    LANGUAGE plpgsql IMMUTABLE STRICT
    AS $_$
DECLARE x NUMERIC;
BEGIN
    x = $1::NUMERIC;
    RETURN TRUE;
EXCEPTION WHEN others THEN
    RETURN FALSE;
END;
$_$;



SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: parent_artifact; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.parent_artifact (
    artifact_id bigint NOT NULL,
    parent_id bigint NOT NULL
);



--
-- Name: artifact_ancestry(bigint); Type: FUNCTION; Schema: qiita
--

CREATE OR REPLACE FUNCTION qiita.artifact_ancestry(a_id bigint) RETURNS SETOF qiita.parent_artifact
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF EXISTS(SELECT * FROM qiita.parent_artifact WHERE artifact_id = a_id) THEN
        RETURN QUERY WITH RECURSIVE root AS (
            SELECT artifact_id, parent_id
            FROM qiita.parent_artifact
            WHERE artifact_id = a_id
          UNION
            SELECT p.artifact_id, p.parent_id
            FROM qiita.parent_artifact p
            JOIN root r ON (r.parent_id = p.artifact_id)
        )
        SELECT DISTINCT artifact_id, parent_id
            FROM root;
    END IF;
END
$$;



--
-- Name: artifact_descendants(bigint); Type: FUNCTION; Schema: qiita
--

CREATE OR REPLACE FUNCTION qiita.artifact_descendants(a_id bigint) RETURNS SETOF qiita.parent_artifact
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF EXISTS(SELECT * FROM qiita.parent_artifact WHERE parent_id = a_id) THEN
        RETURN QUERY WITH RECURSIVE root AS (
            SELECT artifact_id, parent_id
            FROM qiita.parent_artifact
            WHERE parent_id = a_id
          UNION
            SELECT p.artifact_id, p.parent_id
            FROM qiita.parent_artifact p
            JOIN root r ON (r.artifact_id = p.parent_id)
        )
        SELECT DISTINCT artifact_id, parent_id
            FROM root;
    END IF;
END
$$;



--
-- Name: artifact_descendants_with_jobs(bigint); Type: FUNCTION; Schema: qiita
--

CREATE OR REPLACE FUNCTION qiita.artifact_descendants_with_jobs(a_id bigint) RETURNS TABLE(processing_job_id uuid, input_id bigint, output_id bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF EXISTS(SELECT * FROM qiita.artifact WHERE artifact_id = a_id) THEN
        RETURN QUERY WITH RECURSIVE root AS (
          SELECT qiita.artifact_processing_job.processing_job_id AS processing_job_id,
                 qiita.artifact_processing_job.artifact_id AS input_id,
                 qiita.artifact_output_processing_job.artifact_id AS output_id
            FROM qiita.artifact_processing_job
            LEFT JOIN qiita.artifact_output_processing_job USING (processing_job_id)
            WHERE qiita.artifact_processing_job.artifact_id = a_id
          UNION
            SELECT apj.processing_job_id AS processing_job_id,
                   apj.artifact_id AS input_id,
                   aopj.artifact_id AS output_id
              FROM qiita.artifact_processing_job apj
              LEFT JOIN qiita.artifact_output_processing_job aopj USING (processing_job_id)
              JOIN root r ON (r.output_id = apj.artifact_id)
        )
        SELECT DISTINCT root.processing_job_id, root.input_id, root.output_id
            FROM root
            WHERE root.output_id IS NOT NULL
            ORDER BY root.input_id ASC, root.output_id ASC;
    END IF;
END
$$;



--
-- Name: bioms_from_preparation_artifacts(bigint); Type: FUNCTION; Schema: qiita
--

CREATE OR REPLACE FUNCTION qiita.bioms_from_preparation_artifacts(prep_id bigint) RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
  artifacts TEXT := NULL;
BEGIN
  SELECT array_to_string(array_agg(artifact_id), ',') INTO artifacts
  FROM qiita.preparation_artifact
  LEFT JOIN qiita.artifact USING (artifact_id)
  LEFT JOIN qiita.artifact_type USING (artifact_type_id)
  LEFT JOIN qiita.software_command USING (command_id)
  LEFT JOIN qiita.software USING (software_id)
  LEFT JOIN qiita.visibility USING (visibility_id)
  WHERE
    prep_template_id = prep_id AND
    artifact_type = 'BIOM' AND
    NOT deprecated AND
    visibility != 'archived';
  RETURN artifacts;
END
$$;



--
-- Name: check_collection_access(); Type: FUNCTION; Schema: qiita
--

CREATE OR REPLACE FUNCTION qiita.check_collection_access() RETURNS trigger
    LANGUAGE plpgsql STABLE
    AS $$
    BEGIN
        IF NOT EXISTS (
           SELECT aj.* FROM  qiita.analysis_job aj
           LEFT JOIN qiita.collection_analysis ca
           ON aj.analysis_id = ca.analysis_id
           WHERE aj.job_id = NEW.job_id and ca.collection_id = NEW.collection_id
         ) THEN
        	RAISE EXCEPTION 'Jobs inserted that do not belong to collection' USING ERRCODE = 'unique_violation';
        	RETURN OLD;
        ELSE
        	RETURN NEW;
        END IF;
        RETURN NULL;
    END;
    $$;



--
-- Name: find_artifact_roots(bigint); Type: FUNCTION; Schema: qiita
--

CREATE OR REPLACE FUNCTION qiita.find_artifact_roots(a_id bigint) RETURNS SETOF bigint
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF EXISTS(SELECT * FROM qiita.parent_artifact WHERE artifact_id = a_id) THEN
        RETURN QUERY WITH RECURSIVE root AS (
            SELECT artifact_id, parent_id
            FROM qiita.parent_artifact
            WHERE artifact_id = a_id
          UNION
            SELECT p.artifact_id, p.parent_id
            FROM qiita.parent_artifact p
            JOIN root r ON (r.parent_id = p.artifact_id)
        )
        SELECT DISTINCT parent_id
            FROM root
            WHERE parent_id NOT IN (SELECT artifact_id
                                    FROM qiita.parent_artifact);
    ELSE
        RETURN QUERY SELECT a_id;
    END IF;
END
$$;



--
-- Name: parent_processing_job; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.parent_processing_job (
    parent_id uuid NOT NULL,
    child_id uuid NOT NULL
);



--
-- Name: get_processing_workflow_edges(bigint); Type: FUNCTION; Schema: qiita
--

CREATE OR REPLACE FUNCTION qiita.get_processing_workflow_edges(wf_id bigint) RETURNS SETOF qiita.parent_processing_job
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY WITH RECURSIVE edges AS (
        SELECT parent_id, child_id
        FROM qiita.parent_processing_job
        WHERE parent_id IN (SELECT processing_job_id
                            FROM qiita.processing_job_workflow_root
                            WHERE processing_job_workflow_id = wf_id)
      UNION
          SELECT p.parent_id, p.child_id
        FROM qiita.parent_processing_job p
            JOIN edges e ON (e.child_id = p.parent_id)
    )
    SELECT DISTINCT parent_id, child_id
        FROM edges;
END
$$;



--
-- Name: get_processing_workflow_roots(uuid); Type: FUNCTION; Schema: qiita
--

CREATE OR REPLACE FUNCTION qiita.get_processing_workflow_roots(job_id uuid) RETURNS SETOF uuid
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF EXISTS(SELECT * FROM qiita.processing_job_workflow_root WHERE processing_job_id = job_id) THEN
        RETURN QUERY SELECT job_id;
    ELSE
        RETURN QUERY WITH RECURSIVE root AS (
            SELECT child_id, parent_id
            FROM qiita.parent_processing_job
            WHERE child_id = job_id
          UNION
            SELECT p.child_id, p.parent_id
            FROM qiita.parent_processing_job p
            JOIN root r ON (r.parent_id = p.child_id)
        )
        SELECT DISTINCT parent_id
            FROM root
            WHERE parent_id NOT IN (SELECT child_id FROM qiita.parent_processing_job);
    END IF;
END
$$;



--
-- Name: json_object_set_key(json, text, anyelement); Type: FUNCTION; Schema: qiita
--

CREATE OR REPLACE FUNCTION qiita.json_object_set_key(json json, key_to_set text, value_to_set anyelement) RETURNS json
    LANGUAGE sql IMMUTABLE STRICT
    AS $$
SELECT concat('{', string_agg(to_json("key") || ':' || "value", ','), '}')::json
  FROM (SELECT *
          FROM json_each("json")
         WHERE "key" <> "key_to_set"
         UNION ALL
        SELECT "key_to_set", to_json("value_to_set")) AS "fields"
$$;




CREATE TABLE qiita.analysis (
    analysis_id bigint NOT NULL,
    email character varying NOT NULL,
    name character varying NOT NULL,
    description character varying NOT NULL,
    pmid character varying,
    "timestamp" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    dflt boolean DEFAULT false NOT NULL,
    logging_id bigint,
    slurm_reservation character varying DEFAULT ''::character varying NOT NULL
);


--
-- Name: TABLE analysis; Type: COMMENT; Schema: qiita
--

COMMENT ON TABLE qiita.analysis IS 'hHolds analysis information';


--
-- Name: COLUMN analysis.analysis_id; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.analysis.analysis_id IS 'Unique identifier for analysis';


--
-- Name: COLUMN analysis.email; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.analysis.email IS 'Email for user who owns the analysis';


--
-- Name: COLUMN analysis.name; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.analysis.name IS 'Name of the analysis';


--
-- Name: COLUMN analysis.pmid; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.analysis.pmid IS 'PMID of paper from the analysis';


--
-- Name: analysis_analysis_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.analysis_analysis_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: analysis_analysis_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.analysis_analysis_id_seq OWNED BY qiita.analysis.analysis_id;


--
-- Name: analysis_artifact; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.analysis_artifact (
    analysis_id bigint NOT NULL,
    artifact_id bigint NOT NULL
);


--
-- Name: analysis_filepath; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.analysis_filepath (
    analysis_id bigint NOT NULL,
    filepath_id bigint NOT NULL,
    data_type_id bigint
);



--
-- Name: TABLE analysis_filepath; Type: COMMENT; Schema: qiita
--

COMMENT ON TABLE qiita.analysis_filepath IS 'Stores link between analysis and the data file used for the analysis.';


--
-- Name: analysis_portal; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.analysis_portal (
    analysis_id bigint NOT NULL,
    portal_type_id bigint NOT NULL
);



--
-- Name: TABLE analysis_portal; Type: COMMENT; Schema: qiita
--

COMMENT ON TABLE qiita.analysis_portal IS 'Controls what analyses are visible on what portals';


--
-- Name: analysis_processing_job; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.analysis_processing_job (
    analysis_id bigint NOT NULL,
    processing_job_id uuid NOT NULL
);



--
-- Name: analysis_sample; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.analysis_sample (
    analysis_id bigint NOT NULL,
    sample_id character varying NOT NULL,
    artifact_id bigint NOT NULL
);



--
-- Name: analysis_users; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.analysis_users (
    analysis_id bigint NOT NULL,
    email character varying NOT NULL
);



--
-- Name: TABLE analysis_users; Type: COMMENT; Schema: qiita
--

COMMENT ON TABLE qiita.analysis_users IS 'Links analyses to the users they are shared with';


--
-- Name: archive_feature_value; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.archive_feature_value (
    archive_merging_scheme_id bigint NOT NULL,
    archive_feature character varying NOT NULL,
    archive_feature_value character varying NOT NULL
);



--
-- Name: archive_merging_scheme; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.archive_merging_scheme (
    archive_merging_scheme_id bigint NOT NULL,
    archive_merging_scheme character varying NOT NULL
);



--
-- Name: archive_merging_scheme_archive_merging_scheme_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.archive_merging_scheme_archive_merging_scheme_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: archive_merging_scheme_archive_merging_scheme_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.archive_merging_scheme_archive_merging_scheme_id_seq OWNED BY qiita.archive_merging_scheme.archive_merging_scheme_id;


--
-- Name: artifact; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.artifact (
    artifact_id bigint NOT NULL,
    generated_timestamp timestamp without time zone NOT NULL,
    command_id bigint,
    command_parameters json,
    visibility_id bigint NOT NULL,
    artifact_type_id integer,
    data_type_id bigint NOT NULL,
    submitted_to_vamps boolean DEFAULT false NOT NULL,
    name character varying DEFAULT 'noname'::character varying NOT NULL,
    archive_data jsonb
);



--
-- Name: TABLE artifact; Type: COMMENT; Schema: qiita
--

COMMENT ON TABLE qiita.artifact IS 'Represents data in the system';


--
-- Name: COLUMN artifact.visibility_id; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.artifact.visibility_id IS 'If the artifact is sandbox, awaiting_for_approval, private or public';


--
-- Name: artifact_artifact_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.artifact_artifact_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: artifact_artifact_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.artifact_artifact_id_seq OWNED BY qiita.artifact.artifact_id;


--
-- Name: artifact_filepath; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.artifact_filepath (
    artifact_id bigint NOT NULL,
    filepath_id bigint NOT NULL
);



--
-- Name: artifact_output_processing_job; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.artifact_output_processing_job (
    artifact_id bigint NOT NULL,
    processing_job_id uuid NOT NULL,
    command_output_id bigint NOT NULL
);



--
-- Name: artifact_processing_job; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.artifact_processing_job (
    artifact_id bigint NOT NULL,
    processing_job_id uuid NOT NULL
);



--
-- Name: artifact_type; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.artifact_type (
    artifact_type_id bigint NOT NULL,
    artifact_type character varying NOT NULL,
    description character varying,
    can_be_submitted_to_ebi boolean DEFAULT false NOT NULL,
    can_be_submitted_to_vamps boolean DEFAULT false NOT NULL,
    is_user_uploadable boolean DEFAULT false
);



--
-- Name: TABLE artifact_type; Type: COMMENT; Schema: qiita
--

COMMENT ON TABLE qiita.artifact_type IS 'Type of file (FASTA, FASTQ, SPECTRA, etc)';


--
-- Name: artifact_type_filepath_type; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.artifact_type_filepath_type (
    artifact_type_id bigint NOT NULL,
    filepath_type_id bigint NOT NULL,
    required boolean DEFAULT true NOT NULL
);



--
-- Name: checksum_algorithm; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.checksum_algorithm (
    checksum_algorithm_id bigint NOT NULL,
    name character varying NOT NULL
);



--
-- Name: checksum_algorithm_checksum_algorithm_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.checksum_algorithm_checksum_algorithm_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: checksum_algorithm_checksum_algorithm_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.checksum_algorithm_checksum_algorithm_id_seq OWNED BY qiita.checksum_algorithm.checksum_algorithm_id;


--
-- Name: column_controlled_vocabularies; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.column_controlled_vocabularies (
    controlled_vocab_id bigint NOT NULL,
    column_name character varying NOT NULL
);



--
-- Name: TABLE column_controlled_vocabularies; Type: COMMENT; Schema: qiita
--

COMMENT ON TABLE qiita.column_controlled_vocabularies IS 'Table relates a column with a controlled vocabulary.';


--
-- Name: column_controlled_vocabularies_controlled_vocab_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.column_controlled_vocabularies_controlled_vocab_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: column_controlled_vocabularies_controlled_vocab_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.column_controlled_vocabularies_controlled_vocab_id_seq OWNED BY qiita.column_controlled_vocabularies.controlled_vocab_id;


--
-- Name: column_ontology; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.column_ontology (
    column_name character varying NOT NULL,
    ontology_short_name character varying NOT NULL,
    bioportal_id integer NOT NULL,
    ontology_branch_id character varying
);



--
-- Name: TABLE column_ontology; Type: COMMENT; Schema: qiita
--

COMMENT ON TABLE qiita.column_ontology IS 'This table relates a column with an ontology.';


--
-- Name: command_output; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.command_output (
    command_output_id bigint NOT NULL,
    name character varying NOT NULL,
    command_id bigint NOT NULL,
    artifact_type_id bigint NOT NULL,
    check_biom_merge boolean DEFAULT false NOT NULL
);



--
-- Name: command_output_command_output_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.command_output_command_output_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: command_output_command_output_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.command_output_command_output_id_seq OWNED BY qiita.command_output.command_output_id;


--
-- Name: command_parameter; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.command_parameter (
    command_id bigint NOT NULL,
    parameter_name character varying NOT NULL,
    parameter_type character varying NOT NULL,
    required boolean NOT NULL,
    default_value character varying,
    command_parameter_id bigint NOT NULL,
    name_order integer,
    check_biom_merge boolean DEFAULT false NOT NULL
);



--
-- Name: command_parameter_command_parameter_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.command_parameter_command_parameter_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: command_parameter_command_parameter_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.command_parameter_command_parameter_id_seq OWNED BY qiita.command_parameter.command_parameter_id;


--
-- Name: controlled_vocab; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.controlled_vocab (
    controlled_vocab_id bigint NOT NULL,
    controlled_vocab character varying NOT NULL
);



--
-- Name: controlled_vocab_controlled_vocab_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.controlled_vocab_controlled_vocab_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: controlled_vocab_controlled_vocab_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.controlled_vocab_controlled_vocab_id_seq OWNED BY qiita.controlled_vocab.controlled_vocab_id;


--
-- Name: controlled_vocab_values; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.controlled_vocab_values (
    vocab_value_id bigint NOT NULL,
    controlled_vocab_id bigint NOT NULL,
    term character varying NOT NULL,
    order_by character varying NOT NULL,
    default_item character varying
);



--
-- Name: controlled_vocab_values_vocab_value_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.controlled_vocab_values_vocab_value_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: controlled_vocab_values_vocab_value_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.controlled_vocab_values_vocab_value_id_seq OWNED BY qiita.controlled_vocab_values.vocab_value_id;


--
-- Name: data_directory; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.data_directory (
    data_directory_id bigint NOT NULL,
    data_type character varying NOT NULL,
    mountpoint character varying NOT NULL,
    subdirectory boolean DEFAULT false NOT NULL,
    active boolean NOT NULL
);



--
-- Name: data_directory_data_directory_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.data_directory_data_directory_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: data_directory_data_directory_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.data_directory_data_directory_id_seq OWNED BY qiita.data_directory.data_directory_id;


--
-- Name: data_type; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.data_type (
    data_type_id bigint NOT NULL,
    data_type character varying NOT NULL
);



--
-- Name: COLUMN data_type.data_type; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.data_type.data_type IS 'Data type (16S, metabolome, etc) the job will use';


--
-- Name: data_type_data_type_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.data_type_data_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: data_type_data_type_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.data_type_data_type_id_seq OWNED BY qiita.data_type.data_type_id;


--
-- Name: default_parameter_set; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.default_parameter_set (
    default_parameter_set_id bigint NOT NULL,
    command_id bigint NOT NULL,
    parameter_set_name character varying NOT NULL,
    parameter_set json NOT NULL
);



--
-- Name: default_parameter_set_default_parameter_set_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.default_parameter_set_default_parameter_set_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: default_parameter_set_default_parameter_set_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.default_parameter_set_default_parameter_set_id_seq OWNED BY qiita.default_parameter_set.default_parameter_set_id;


--
-- Name: default_workflow; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.default_workflow (
    default_workflow_id bigint NOT NULL,
    name character varying NOT NULL,
    active boolean DEFAULT true,
    description text,
    artifact_type_id bigint DEFAULT 3 NOT NULL,
    parameters jsonb DEFAULT '{"prep": {}, "sample": {}}'::jsonb NOT NULL
);



--
-- Name: default_workflow_data_type; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.default_workflow_data_type (
    default_workflow_id bigint NOT NULL,
    data_type_id bigint NOT NULL
);



--
-- Name: default_workflow_default_workflow_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.default_workflow_default_workflow_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: default_workflow_default_workflow_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.default_workflow_default_workflow_id_seq OWNED BY qiita.default_workflow.default_workflow_id;


--
-- Name: default_workflow_edge; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.default_workflow_edge (
    default_workflow_edge_id bigint NOT NULL,
    parent_id bigint NOT NULL,
    child_id bigint NOT NULL
);



--
-- Name: default_workflow_edge_connections; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.default_workflow_edge_connections (
    default_workflow_edge_id bigint NOT NULL,
    parent_output_id bigint NOT NULL,
    child_input_id bigint NOT NULL
);



--
-- Name: default_workflow_edge_default_workflow_edge_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.default_workflow_edge_default_workflow_edge_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: default_workflow_edge_default_workflow_edge_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.default_workflow_edge_default_workflow_edge_id_seq OWNED BY qiita.default_workflow_edge.default_workflow_edge_id;


--
-- Name: default_workflow_node; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.default_workflow_node (
    default_workflow_node_id bigint NOT NULL,
    default_workflow_id bigint NOT NULL,
    default_parameter_set_id bigint NOT NULL
);



--
-- Name: default_workflow_node_default_workflow_node_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.default_workflow_node_default_workflow_node_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: default_workflow_node_default_workflow_node_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.default_workflow_node_default_workflow_node_id_seq OWNED BY qiita.default_workflow_node.default_workflow_node_id;


--
-- Name: download_link; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.download_link (
    jti character varying(32) NOT NULL,
    jwt text NOT NULL,
    exp timestamp without time zone NOT NULL
);



--
-- Name: ebi_run_accession; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.ebi_run_accession (
    sample_id character varying NOT NULL,
    ebi_run_accession character varying NOT NULL,
    artifact_id bigint NOT NULL
);



--
-- Name: environmental_package; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.environmental_package (
    environmental_package_name character varying NOT NULL,
    metadata_table character varying NOT NULL
);



--
-- Name: COLUMN environmental_package.environmental_package_name; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.environmental_package.environmental_package_name IS 'The name of the environmental package';


--
-- Name: COLUMN environmental_package.metadata_table; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.environmental_package.metadata_table IS 'Contains the name of the table that contains the pre-defined metadata columns for the environmental package';


--
-- Name: filepath; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.filepath (
    filepath_id bigint NOT NULL,
    filepath character varying NOT NULL,
    filepath_type_id bigint NOT NULL,
    checksum character varying NOT NULL,
    checksum_algorithm_id bigint NOT NULL,
    data_directory_id bigint NOT NULL,
    fp_size bigint DEFAULT 0 NOT NULL
);



--
-- Name: filepath_data_directory_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.filepath_data_directory_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: filepath_data_directory_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.filepath_data_directory_id_seq OWNED BY qiita.filepath.data_directory_id;


--
-- Name: filepath_filepath_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.filepath_filepath_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: filepath_filepath_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.filepath_filepath_id_seq OWNED BY qiita.filepath.filepath_id;


--
-- Name: filepath_type; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.filepath_type (
    filepath_type_id bigint NOT NULL,
    filepath_type character varying
);



--
-- Name: filepath_type_filepath_type_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.filepath_type_filepath_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: filepath_type_filepath_type_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.filepath_type_filepath_type_id_seq OWNED BY qiita.filepath_type.filepath_type_id;


--
-- Name: filetype_filetype_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.filetype_filetype_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: filetype_filetype_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.filetype_filetype_id_seq OWNED BY qiita.artifact_type.artifact_type_id;


--
-- Name: investigation; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.investigation (
    investigation_id bigint NOT NULL,
    investigation_name character varying NOT NULL,
    investigation_description character varying NOT NULL,
    contact_person_id bigint
);



--
-- Name: TABLE investigation; Type: COMMENT; Schema: qiita
--

COMMENT ON TABLE qiita.investigation IS 'Overarching investigation information.An investigation comprises one or more individual studies.';


--
-- Name: COLUMN investigation.investigation_description; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.investigation.investigation_description IS 'Describes the overarching goal of the investigation';


--
-- Name: investigation_investigation_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.investigation_investigation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: investigation_investigation_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.investigation_investigation_id_seq OWNED BY qiita.investigation.investigation_id;


--
-- Name: investigation_study; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.investigation_study (
    investigation_id bigint NOT NULL,
    study_id bigint NOT NULL
);



--
-- Name: logging; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.logging (
    logging_id bigint NOT NULL,
    "time" timestamp without time zone NOT NULL,
    severity_id integer NOT NULL,
    msg character varying NOT NULL,
    information character varying
);



--
-- Name: COLUMN logging."time"; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.logging."time" IS 'Time the error was thrown';


--
-- Name: COLUMN logging.msg; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.logging.msg IS 'Error message thrown';


--
-- Name: COLUMN logging.information; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.logging.information IS 'Other applicable information (depending on error)';


--
-- Name: logging_logging_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.logging_logging_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: logging_logging_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.logging_logging_id_seq OWNED BY qiita.logging.logging_id;


--
-- Name: message; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.message (
    message_id bigint NOT NULL,
    message character varying NOT NULL,
    message_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expiration timestamp without time zone
);



--
-- Name: message_message_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.message_message_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: message_message_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.message_message_id_seq OWNED BY qiita.message.message_id;


--
-- Name: message_user; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.message_user (
    email character varying NOT NULL,
    message_id bigint NOT NULL,
    read boolean DEFAULT false NOT NULL
);



--
-- Name: COLUMN message_user.read; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.message_user.read IS 'Whether the message has been read or not.';


--
-- Name: mixs_field_description; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.mixs_field_description (
    column_name character varying NOT NULL,
    data_type character varying NOT NULL,
    desc_or_value character varying NOT NULL,
    definition character varying NOT NULL,
    min_length integer,
    active integer NOT NULL
);



--
-- Name: oauth_identifiers; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.oauth_identifiers (
    client_id character varying(50) NOT NULL,
    client_secret character varying(255)
);



--
-- Name: oauth_software; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.oauth_software (
    software_id bigint NOT NULL,
    client_id character varying NOT NULL
);



--
-- Name: ontology; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.ontology (
    ontology_id bigint NOT NULL,
    ontology character varying NOT NULL,
    fully_loaded boolean NOT NULL,
    fullname character varying,
    query_url character varying,
    source_url character varying,
    definition text,
    load_date date NOT NULL
);



--
-- Name: parameter_artifact_type; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.parameter_artifact_type (
    command_parameter_id bigint NOT NULL,
    artifact_type_id bigint NOT NULL
);



--
-- Name: parameter_artifact_type_command_parameter_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.parameter_artifact_type_command_parameter_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: parameter_artifact_type_command_parameter_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.parameter_artifact_type_command_parameter_id_seq OWNED BY qiita.parameter_artifact_type.command_parameter_id;


--
-- Name: per_study_tags; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.per_study_tags (
    study_id bigint NOT NULL,
    study_tag character varying NOT NULL
);



--
-- Name: portal_type; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.portal_type (
    portal_type_id bigint NOT NULL,
    portal character varying NOT NULL,
    portal_description character varying NOT NULL
);



--
-- Name: TABLE portal_type; Type: COMMENT; Schema: qiita
--

COMMENT ON TABLE qiita.portal_type IS 'What portals are available to show a study in';


--
-- Name: portal_type_portal_type_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.portal_type_portal_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: portal_type_portal_type_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.portal_type_portal_type_id_seq OWNED BY qiita.portal_type.portal_type_id;


--
-- Name: prep_1; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.prep_1 (
    sample_id character varying NOT NULL,
    sample_values jsonb
);



--
-- Name: prep_2; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.prep_2 (
    sample_id character varying NOT NULL,
    sample_values jsonb
);



--
-- Name: prep_template; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.prep_template (
    prep_template_id bigint NOT NULL,
    data_type_id bigint NOT NULL,
    preprocessing_status character varying DEFAULT 'not_preprocessed'::character varying NOT NULL,
    investigation_type character varying,
    artifact_id bigint,
    name character varying DEFAULT 'Default Name'::character varying NOT NULL,
    deprecated boolean DEFAULT false,
    creation_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    modification_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    creation_job_id uuid
);



--
-- Name: COLUMN prep_template.investigation_type; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.prep_template.investigation_type IS 'The investigation type (e.g., one of the values from EBI`s set of known types)';


--
-- Name: prep_template_filepath; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.prep_template_filepath (
    prep_template_id bigint NOT NULL,
    filepath_id bigint NOT NULL
);



--
-- Name: prep_template_prep_template_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.prep_template_prep_template_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: prep_template_prep_template_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.prep_template_prep_template_id_seq OWNED BY qiita.prep_template.prep_template_id;


--
-- Name: prep_template_processing_job; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.prep_template_processing_job (
    prep_template_id bigint NOT NULL,
    processing_job_id uuid NOT NULL
);



--
-- Name: prep_template_sample; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.prep_template_sample (
    prep_template_id bigint NOT NULL,
    sample_id character varying NOT NULL,
    ebi_experiment_accession character varying
);



--
-- Name: COLUMN prep_template_sample.prep_template_id; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.prep_template_sample.prep_template_id IS 'The prep template identifier';


--
-- Name: preparation_artifact; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.preparation_artifact (
    prep_template_id bigint NOT NULL,
    artifact_id bigint NOT NULL
);



--
-- Name: processing_job; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.processing_job (
    processing_job_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    email character varying NOT NULL,
    command_id bigint NOT NULL,
    command_parameters json NOT NULL,
    processing_job_status_id bigint NOT NULL,
    logging_id bigint,
    heartbeat timestamp without time zone,
    step character varying,
    pending json,
    hidden boolean DEFAULT false,
    external_job_id character varying
);



--
-- Name: COLUMN processing_job.email; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.processing_job.email IS 'The user that launched the job';


--
-- Name: COLUMN processing_job.command_id; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.processing_job.command_id IS 'The command launched';


--
-- Name: COLUMN processing_job.command_parameters; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.processing_job.command_parameters IS 'The parameters used in the command';


--
-- Name: COLUMN processing_job.logging_id; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.processing_job.logging_id IS 'In case of failure, point to the log entry that holds more information about the error';


--
-- Name: COLUMN processing_job.heartbeat; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.processing_job.heartbeat IS 'The last heartbeat received by this job';


--
-- Name: COLUMN processing_job.external_job_id; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.processing_job.external_job_id IS 'Store an external job ID (e.g. Torque job ID) associated this Qiita job.';


--
-- Name: processing_job_resource_allocation; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.processing_job_resource_allocation (
    name character varying NOT NULL,
    description character varying,
    job_type character varying NOT NULL,
    allocation character varying
);



--
-- Name: processing_job_status; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.processing_job_status (
    processing_job_status_id bigint NOT NULL,
    processing_job_status character varying NOT NULL,
    processing_job_status_description character varying NOT NULL
);



--
-- Name: processing_job_status_processing_job_status_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.processing_job_status_processing_job_status_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: processing_job_status_processing_job_status_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.processing_job_status_processing_job_status_id_seq OWNED BY qiita.processing_job_status.processing_job_status_id;


--
-- Name: processing_job_validator; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.processing_job_validator (
    processing_job_id uuid NOT NULL,
    validator_id uuid NOT NULL,
    artifact_info json
);



--
-- Name: processing_job_workflow; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.processing_job_workflow (
    processing_job_workflow_id bigint NOT NULL,
    email character varying NOT NULL,
    name character varying
);



--
-- Name: processing_job_workflow_processing_job_workflow_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.processing_job_workflow_processing_job_workflow_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: processing_job_workflow_processing_job_workflow_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.processing_job_workflow_processing_job_workflow_id_seq OWNED BY qiita.processing_job_workflow.processing_job_workflow_id;


--
-- Name: processing_job_workflow_root; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.processing_job_workflow_root (
    processing_job_workflow_id bigint NOT NULL,
    processing_job_id uuid NOT NULL
);



--
-- Name: publication; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.publication (
    doi character varying NOT NULL,
    pubmed_id character varying
);



--
-- Name: qiita_user; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.qiita_user (
    email character varying NOT NULL,
    user_level_id integer DEFAULT 5 NOT NULL,
    password character varying NOT NULL,
    name character varying,
    affiliation character varying,
    address character varying,
    phone character varying,
    user_verify_code character varying,
    pass_reset_code character varying,
    pass_reset_timestamp timestamp without time zone,
    receive_processing_job_emails boolean DEFAULT false,
    social_orcid character varying,
    social_researchgate character varying,
    social_googlescholar character varying
);



--
-- Name: TABLE qiita_user; Type: COMMENT; Schema: qiita
--

COMMENT ON TABLE qiita.qiita_user IS 'Holds all user information';


--
-- Name: COLUMN qiita_user.user_level_id; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.qiita_user.user_level_id IS 'user level';


--
-- Name: COLUMN qiita_user.user_verify_code; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.qiita_user.user_verify_code IS 'Code for initial user email verification';


--
-- Name: COLUMN qiita_user.pass_reset_code; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.qiita_user.pass_reset_code IS 'Randomly generated code for password reset';


--
-- Name: COLUMN qiita_user.pass_reset_timestamp; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.qiita_user.pass_reset_timestamp IS 'Time the reset code was generated';


--
-- Name: reference; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.reference (
    reference_id bigint NOT NULL,
    reference_name character varying NOT NULL,
    reference_version character varying,
    sequence_filepath bigint NOT NULL,
    taxonomy_filepath bigint,
    tree_filepath bigint
);



--
-- Name: reference_reference_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.reference_reference_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: reference_reference_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.reference_reference_id_seq OWNED BY qiita.reference.reference_id;


--
-- Name: restrictions; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.restrictions (
    table_name character varying,
    name character varying,
    valid_values character varying[]
);



--
-- Name: sample_1; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.sample_1 (
    sample_id character varying NOT NULL,
    sample_values jsonb
);



--
-- Name: sample_template_filepath; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.sample_template_filepath (
    study_id bigint NOT NULL,
    filepath_id bigint NOT NULL
);



--
-- Name: severity; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.severity (
    severity_id integer NOT NULL,
    severity character varying NOT NULL
);



--
-- Name: severity_severity_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.severity_severity_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: severity_severity_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.severity_severity_id_seq OWNED BY qiita.severity.severity_id;


--
-- Name: software; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.software (
    software_id bigint NOT NULL,
    name character varying NOT NULL,
    version character varying NOT NULL,
    description character varying NOT NULL,
    environment_script character varying NOT NULL,
    start_script character varying NOT NULL,
    software_type_id bigint NOT NULL,
    active boolean DEFAULT false NOT NULL,
    deprecated boolean DEFAULT false
);



--
-- Name: software_artifact_type; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.software_artifact_type (
    software_id bigint NOT NULL,
    artifact_type_id bigint NOT NULL
);



--
-- Name: TABLE software_artifact_type; Type: COMMENT; Schema: qiita
--

COMMENT ON TABLE qiita.software_artifact_type IS 'In case that the software is of type "type plugin", it holds the artifact types that such software can validate and generate the summary.';


--
-- Name: software_command; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.software_command (
    command_id bigint NOT NULL,
    name character varying NOT NULL,
    software_id bigint NOT NULL,
    description character varying NOT NULL,
    active boolean DEFAULT true NOT NULL,
    is_analysis boolean DEFAULT false NOT NULL,
    ignore_parent_command boolean DEFAULT false NOT NULL,
    post_processing_cmd character varying
);



--
-- Name: COLUMN software_command.post_processing_cmd; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.software_command.post_processing_cmd IS 'Store information on additional post-processing steps for merged BIOMs, if any.';


--
-- Name: software_command_command_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.software_command_command_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: software_command_command_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.software_command_command_id_seq OWNED BY qiita.software_command.command_id;


--
-- Name: software_publication; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.software_publication (
    software_id bigint NOT NULL,
    publication_doi character varying NOT NULL
);



--
-- Name: software_software_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.software_software_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: software_software_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.software_software_id_seq OWNED BY qiita.software.software_id;


--
-- Name: software_type; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.software_type (
    software_type_id bigint NOT NULL,
    software_type character varying NOT NULL,
    description character varying NOT NULL
);



--
-- Name: software_type_software_type_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.software_type_software_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: software_type_software_type_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.software_type_software_type_id_seq OWNED BY qiita.software_type.software_type_id;


--
-- Name: stats_daily; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.stats_daily (
    stats jsonb NOT NULL,
    stats_timestamp timestamp without time zone NOT NULL
);



--
-- Name: study; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.study (
    study_id bigint NOT NULL,
    email character varying NOT NULL,
    first_contact timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    funding character varying,
    timeseries_type_id bigint NOT NULL,
    lab_person_id bigint,
    metadata_complete boolean NOT NULL,
    mixs_compliant boolean NOT NULL,
    most_recent_contact timestamp without time zone,
    principal_investigator_id bigint NOT NULL,
    reprocess boolean NOT NULL,
    spatial_series boolean,
    study_title character varying NOT NULL,
    study_alias character varying NOT NULL,
    study_description text NOT NULL,
    study_abstract text NOT NULL,
    vamps_id character varying,
    ebi_study_accession character varying,
    public_raw_download boolean DEFAULT false,
    notes text DEFAULT ''::text NOT NULL,
    autoloaded boolean DEFAULT false NOT NULL
);



--
-- Name: COLUMN study.study_id; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.study.study_id IS 'Unique name for study';


--
-- Name: COLUMN study.email; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.study.email IS 'Email of study owner';


--
-- Name: COLUMN study.timeseries_type_id; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.study.timeseries_type_id IS 'What type of timeseries this study is (or is not)
Controlled Vocabulary';


--
-- Name: study_artifact; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.study_artifact (
    study_id bigint NOT NULL,
    artifact_id bigint NOT NULL
);



--
-- Name: study_environmental_package; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.study_environmental_package (
    study_id bigint NOT NULL,
    environmental_package_name character varying NOT NULL
);



--
-- Name: TABLE study_environmental_package; Type: COMMENT; Schema: qiita
--

COMMENT ON TABLE qiita.study_environmental_package IS 'Holds the 1 to many relationship between the study and the environmental_package';


--
-- Name: study_person; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.study_person (
    study_person_id bigint NOT NULL,
    name character varying NOT NULL,
    email character varying NOT NULL,
    affiliation character varying NOT NULL,
    address character varying(100),
    phone character varying
);



--
-- Name: TABLE study_person; Type: COMMENT; Schema: qiita
--

COMMENT ON TABLE qiita.study_person IS 'Contact information for the various people involved in a study';


--
-- Name: COLUMN study_person.affiliation; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.study_person.affiliation IS 'The institution with which this person is affiliated';


--
-- Name: study_person_study_person_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.study_person_study_person_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: study_person_study_person_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.study_person_study_person_id_seq OWNED BY qiita.study_person.study_person_id;


--
-- Name: study_portal; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.study_portal (
    study_id bigint NOT NULL,
    portal_type_id bigint NOT NULL
);



--
-- Name: TABLE study_portal; Type: COMMENT; Schema: qiita
--

COMMENT ON TABLE qiita.study_portal IS 'Controls what studies are visible on what portals';


--
-- Name: study_prep_template; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.study_prep_template (
    study_id bigint NOT NULL,
    prep_template_id bigint NOT NULL
);



--
-- Name: TABLE study_prep_template; Type: COMMENT; Schema: qiita
--

COMMENT ON TABLE qiita.study_prep_template IS 'links study to its prep templates';


--
-- Name: study_publication; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.study_publication (
    study_id bigint NOT NULL,
    publication character varying NOT NULL,
    is_doi boolean
);



--
-- Name: study_sample; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.study_sample (
    sample_id character varying NOT NULL,
    study_id bigint NOT NULL,
    ebi_sample_accession character varying,
    biosample_accession character varying
);



--
-- Name: TABLE study_sample; Type: COMMENT; Schema: qiita
--

COMMENT ON TABLE qiita.study_sample IS 'Required info for each sample. One row is one sample.';


--
-- Name: visibility; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.visibility (
    visibility_id bigint NOT NULL,
    visibility character varying NOT NULL,
    visibility_description character varying NOT NULL
);



--
-- Name: study_status_study_status_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.study_status_study_status_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: study_status_study_status_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.study_status_study_status_id_seq OWNED BY qiita.visibility.visibility_id;


--
-- Name: study_study_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.study_study_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: study_study_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.study_study_id_seq OWNED BY qiita.study.study_id;


--
-- Name: study_tags; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.study_tags (
    email character varying NOT NULL,
    study_tag character varying NOT NULL
);



--
-- Name: study_users; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.study_users (
    study_id bigint NOT NULL,
    email character varying NOT NULL
);



--
-- Name: TABLE study_users; Type: COMMENT; Schema: qiita
--

COMMENT ON TABLE qiita.study_users IS 'Links shared studies to users they are shared with';


--
-- Name: term; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.term (
    term_id bigint NOT NULL,
    ontology_id bigint NOT NULL,
    old_term_id bigint,
    term character varying NOT NULL,
    identifier character varying,
    definition character varying,
    namespace character varying,
    is_obsolete boolean DEFAULT false,
    is_root_term boolean,
    is_leaf boolean,
    user_defined boolean DEFAULT false NOT NULL
);



--
-- Name: COLUMN term.old_term_id; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.term.old_term_id IS 'Identifier used in the old system, we are keeping this for consistency';


--
-- Name: COLUMN term.user_defined; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.term.user_defined IS 'Whether or not this term was defined by a user';


--
-- Name: term_term_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.term_term_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: term_term_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.term_term_id_seq OWNED BY qiita.term.term_id;


--
-- Name: timeseries_type; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.timeseries_type (
    timeseries_type_id bigint NOT NULL,
    timeseries_type character varying NOT NULL,
    intervention_type character varying DEFAULT 'None'::character varying NOT NULL
);



--
-- Name: timeseries_type_timeseries_type_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.timeseries_type_timeseries_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: timeseries_type_timeseries_type_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.timeseries_type_timeseries_type_id_seq OWNED BY qiita.timeseries_type.timeseries_type_id;


--
-- Name: user_level; Type: TABLE; Schema: qiita
--

CREATE TABLE qiita.user_level (
    user_level_id integer NOT NULL,
    name character varying NOT NULL,
    description text NOT NULL,
    slurm_parameters character varying DEFAULT '--nice=10000'::character varying NOT NULL
);



--
-- Name: TABLE user_level; Type: COMMENT; Schema: qiita
--

COMMENT ON TABLE qiita.user_level IS 'Holds available user levels';


--
-- Name: COLUMN user_level.name; Type: COMMENT; Schema: qiita
--

COMMENT ON COLUMN qiita.user_level.name IS 'One of the user levels (admin, user, guest, etc)';


--
-- Name: user_level_user_level_id_seq; Type: SEQUENCE; Schema: qiita
--

CREATE SEQUENCE qiita.user_level_user_level_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: user_level_user_level_id_seq; Type: SEQUENCE OWNED BY; Schema: qiita
--

ALTER SEQUENCE qiita.user_level_user_level_id_seq OWNED BY qiita.user_level.user_level_id;


--
-- Name: analysis analysis_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis ALTER COLUMN analysis_id SET DEFAULT nextval('qiita.analysis_analysis_id_seq'::regclass);


--
-- Name: archive_merging_scheme archive_merging_scheme_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.archive_merging_scheme ALTER COLUMN archive_merging_scheme_id SET DEFAULT nextval('qiita.archive_merging_scheme_archive_merging_scheme_id_seq'::regclass);


--
-- Name: artifact artifact_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact ALTER COLUMN artifact_id SET DEFAULT nextval('qiita.artifact_artifact_id_seq'::regclass);


--
-- Name: artifact_type artifact_type_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact_type ALTER COLUMN artifact_type_id SET DEFAULT nextval('qiita.filetype_filetype_id_seq'::regclass);


--
-- Name: checksum_algorithm checksum_algorithm_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.checksum_algorithm ALTER COLUMN checksum_algorithm_id SET DEFAULT nextval('qiita.checksum_algorithm_checksum_algorithm_id_seq'::regclass);


--
-- Name: column_controlled_vocabularies controlled_vocab_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.column_controlled_vocabularies ALTER COLUMN controlled_vocab_id SET DEFAULT nextval('qiita.column_controlled_vocabularies_controlled_vocab_id_seq'::regclass);


--
-- Name: command_output command_output_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.command_output ALTER COLUMN command_output_id SET DEFAULT nextval('qiita.command_output_command_output_id_seq'::regclass);


--
-- Name: command_parameter command_parameter_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.command_parameter ALTER COLUMN command_parameter_id SET DEFAULT nextval('qiita.command_parameter_command_parameter_id_seq'::regclass);


--
-- Name: controlled_vocab controlled_vocab_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.controlled_vocab ALTER COLUMN controlled_vocab_id SET DEFAULT nextval('qiita.controlled_vocab_controlled_vocab_id_seq'::regclass);


--
-- Name: controlled_vocab_values vocab_value_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.controlled_vocab_values ALTER COLUMN vocab_value_id SET DEFAULT nextval('qiita.controlled_vocab_values_vocab_value_id_seq'::regclass);


--
-- Name: data_directory data_directory_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.data_directory ALTER COLUMN data_directory_id SET DEFAULT nextval('qiita.data_directory_data_directory_id_seq'::regclass);


--
-- Name: data_type data_type_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.data_type ALTER COLUMN data_type_id SET DEFAULT nextval('qiita.data_type_data_type_id_seq'::regclass);


--
-- Name: default_parameter_set default_parameter_set_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_parameter_set ALTER COLUMN default_parameter_set_id SET DEFAULT nextval('qiita.default_parameter_set_default_parameter_set_id_seq'::regclass);


--
-- Name: default_workflow default_workflow_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_workflow ALTER COLUMN default_workflow_id SET DEFAULT nextval('qiita.default_workflow_default_workflow_id_seq'::regclass);


--
-- Name: default_workflow_edge default_workflow_edge_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_workflow_edge ALTER COLUMN default_workflow_edge_id SET DEFAULT nextval('qiita.default_workflow_edge_default_workflow_edge_id_seq'::regclass);


--
-- Name: default_workflow_node default_workflow_node_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_workflow_node ALTER COLUMN default_workflow_node_id SET DEFAULT nextval('qiita.default_workflow_node_default_workflow_node_id_seq'::regclass);


--
-- Name: filepath filepath_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.filepath ALTER COLUMN filepath_id SET DEFAULT nextval('qiita.filepath_filepath_id_seq'::regclass);


--
-- Name: filepath data_directory_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.filepath ALTER COLUMN data_directory_id SET DEFAULT nextval('qiita.filepath_data_directory_id_seq'::regclass);


--
-- Name: filepath_type filepath_type_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.filepath_type ALTER COLUMN filepath_type_id SET DEFAULT nextval('qiita.filepath_type_filepath_type_id_seq'::regclass);


--
-- Name: investigation investigation_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.investigation ALTER COLUMN investigation_id SET DEFAULT nextval('qiita.investigation_investigation_id_seq'::regclass);


--
-- Name: logging logging_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.logging ALTER COLUMN logging_id SET DEFAULT nextval('qiita.logging_logging_id_seq'::regclass);


--
-- Name: message message_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.message ALTER COLUMN message_id SET DEFAULT nextval('qiita.message_message_id_seq'::regclass);


--
-- Name: parameter_artifact_type command_parameter_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.parameter_artifact_type ALTER COLUMN command_parameter_id SET DEFAULT nextval('qiita.parameter_artifact_type_command_parameter_id_seq'::regclass);


--
-- Name: portal_type portal_type_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.portal_type ALTER COLUMN portal_type_id SET DEFAULT nextval('qiita.portal_type_portal_type_id_seq'::regclass);


--
-- Name: prep_template prep_template_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.prep_template ALTER COLUMN prep_template_id SET DEFAULT nextval('qiita.prep_template_prep_template_id_seq'::regclass);


--
-- Name: processing_job_status processing_job_status_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.processing_job_status ALTER COLUMN processing_job_status_id SET DEFAULT nextval('qiita.processing_job_status_processing_job_status_id_seq'::regclass);


--
-- Name: processing_job_workflow processing_job_workflow_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.processing_job_workflow ALTER COLUMN processing_job_workflow_id SET DEFAULT nextval('qiita.processing_job_workflow_processing_job_workflow_id_seq'::regclass);


--
-- Name: reference reference_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.reference ALTER COLUMN reference_id SET DEFAULT nextval('qiita.reference_reference_id_seq'::regclass);


--
-- Name: severity severity_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.severity ALTER COLUMN severity_id SET DEFAULT nextval('qiita.severity_severity_id_seq'::regclass);


--
-- Name: software software_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.software ALTER COLUMN software_id SET DEFAULT nextval('qiita.software_software_id_seq'::regclass);


--
-- Name: software_command command_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.software_command ALTER COLUMN command_id SET DEFAULT nextval('qiita.software_command_command_id_seq'::regclass);


--
-- Name: software_type software_type_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.software_type ALTER COLUMN software_type_id SET DEFAULT nextval('qiita.software_type_software_type_id_seq'::regclass);


--
-- Name: study study_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.study ALTER COLUMN study_id SET DEFAULT nextval('qiita.study_study_id_seq'::regclass);


--
-- Name: study_person study_person_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_person ALTER COLUMN study_person_id SET DEFAULT nextval('qiita.study_person_study_person_id_seq'::regclass);


--
-- Name: term term_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.term ALTER COLUMN term_id SET DEFAULT nextval('qiita.term_term_id_seq'::regclass);


--
-- Name: timeseries_type timeseries_type_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.timeseries_type ALTER COLUMN timeseries_type_id SET DEFAULT nextval('qiita.timeseries_type_timeseries_type_id_seq'::regclass);


--
-- Name: user_level user_level_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.user_level ALTER COLUMN user_level_id SET DEFAULT nextval('qiita.user_level_user_level_id_seq'::regclass);


--
-- Name: visibility visibility_id; Type: DEFAULT; Schema: qiita
--

ALTER TABLE ONLY qiita.visibility ALTER COLUMN visibility_id SET DEFAULT nextval('qiita.study_status_study_status_id_seq'::regclass);


--
-- Name: default_workflow_data_type default_workflow_data_type_pkey; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_workflow_data_type
    ADD CONSTRAINT default_workflow_data_type_pkey PRIMARY KEY (default_workflow_id, data_type_id);


--
-- Name: download_link download_link_pkey; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.download_link
    ADD CONSTRAINT download_link_pkey PRIMARY KEY (jti);


--
-- Name: analysis_artifact idx_analysis_artifact_0; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_artifact
    ADD CONSTRAINT idx_analysis_artifact_0 PRIMARY KEY (analysis_id, artifact_id);


--
-- Name: analysis_filepath idx_analysis_filepath_1; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_filepath
    ADD CONSTRAINT idx_analysis_filepath_1 PRIMARY KEY (analysis_id, filepath_id);


--
-- Name: analysis_processing_job idx_analysis_processing_job; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_processing_job
    ADD CONSTRAINT idx_analysis_processing_job PRIMARY KEY (analysis_id, processing_job_id);


--
-- Name: analysis_users idx_analysis_users; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_users
    ADD CONSTRAINT idx_analysis_users PRIMARY KEY (analysis_id, email);


--
-- Name: archive_feature_value idx_archive_feature_value; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.archive_feature_value
    ADD CONSTRAINT idx_archive_feature_value PRIMARY KEY (archive_merging_scheme_id, archive_feature);


--
-- Name: artifact_filepath idx_artifact_filepath; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact_filepath
    ADD CONSTRAINT idx_artifact_filepath PRIMARY KEY (artifact_id, filepath_id);


--
-- Name: artifact_processing_job idx_artifact_processing_job; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact_processing_job
    ADD CONSTRAINT idx_artifact_processing_job PRIMARY KEY (artifact_id, processing_job_id);


--
-- Name: artifact_type_filepath_type idx_artifact_type_filepath_type; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact_type_filepath_type
    ADD CONSTRAINT idx_artifact_type_filepath_type PRIMARY KEY (artifact_type_id, filepath_type_id);


--
-- Name: checksum_algorithm idx_checksum_algorithm; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.checksum_algorithm
    ADD CONSTRAINT idx_checksum_algorithm UNIQUE (name);


--
-- Name: column_controlled_vocabularies idx_column_controlled_vocabularies; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.column_controlled_vocabularies
    ADD CONSTRAINT idx_column_controlled_vocabularies PRIMARY KEY (controlled_vocab_id, column_name);


--
-- Name: column_ontology idx_column_ontology; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.column_ontology
    ADD CONSTRAINT idx_column_ontology PRIMARY KEY (column_name, ontology_short_name);


--
-- Name: command_output idx_command_output; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.command_output
    ADD CONSTRAINT idx_command_output UNIQUE (name, command_id);


--
-- Name: command_parameter idx_command_parameter_0; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.command_parameter
    ADD CONSTRAINT idx_command_parameter_0 UNIQUE (command_id, parameter_name);


--
-- Name: prep_template_sample idx_common_prep_info; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.prep_template_sample
    ADD CONSTRAINT idx_common_prep_info PRIMARY KEY (prep_template_id, sample_id);


--
-- Name: data_type idx_data_type; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.data_type
    ADD CONSTRAINT idx_data_type UNIQUE (data_type);


--
-- Name: default_parameter_set idx_default_parameter_set_0; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_parameter_set
    ADD CONSTRAINT idx_default_parameter_set_0 UNIQUE (command_id, parameter_set_name);


--
-- Name: default_workflow_edge_connections idx_default_workflow_edge_connections; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_workflow_edge_connections
    ADD CONSTRAINT idx_default_workflow_edge_connections PRIMARY KEY (default_workflow_edge_id, parent_output_id, child_input_id);


--
-- Name: filepath_type idx_filepath_type; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.filepath_type
    ADD CONSTRAINT idx_filepath_type UNIQUE (filepath_type);


--
-- Name: artifact_type idx_filetype; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact_type
    ADD CONSTRAINT idx_filetype UNIQUE (artifact_type);


--
-- Name: investigation_study idx_investigation_study; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.investigation_study
    ADD CONSTRAINT idx_investigation_study PRIMARY KEY (investigation_id, study_id);


--
-- Name: message_user idx_message_user; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.message_user
    ADD CONSTRAINT idx_message_user PRIMARY KEY (email, message_id);


--
-- Name: oauth_software idx_oauth_software; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.oauth_software
    ADD CONSTRAINT idx_oauth_software PRIMARY KEY (software_id, client_id);


--
-- Name: ontology idx_ontology; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.ontology
    ADD CONSTRAINT idx_ontology UNIQUE (ontology);


--
-- Name: parameter_artifact_type idx_parameter_artifact_type; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.parameter_artifact_type
    ADD CONSTRAINT idx_parameter_artifact_type PRIMARY KEY (command_parameter_id, artifact_type_id);


--
-- Name: parent_artifact idx_parent_artifact; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.parent_artifact
    ADD CONSTRAINT idx_parent_artifact PRIMARY KEY (artifact_id, parent_id);


--
-- Name: parent_processing_job idx_parent_processing_job; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.parent_processing_job
    ADD CONSTRAINT idx_parent_processing_job PRIMARY KEY (parent_id, child_id);


--
-- Name: prep_template_filepath idx_prep_template_filepath; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.prep_template_filepath
    ADD CONSTRAINT idx_prep_template_filepath PRIMARY KEY (prep_template_id, filepath_id);


--
-- Name: prep_template_processing_job idx_prep_template_processing_job; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.prep_template_processing_job
    ADD CONSTRAINT idx_prep_template_processing_job PRIMARY KEY (prep_template_id, processing_job_id);


--
-- Name: processing_job_validator idx_processing_job_validator; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.processing_job_validator
    ADD CONSTRAINT idx_processing_job_validator PRIMARY KEY (processing_job_id, validator_id);


--
-- Name: processing_job_workflow_root idx_processing_job_workflow_root_0; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.processing_job_workflow_root
    ADD CONSTRAINT idx_processing_job_workflow_root_0 PRIMARY KEY (processing_job_workflow_id, processing_job_id);


--
-- Name: study_sample idx_required_sample_info_1; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_sample
    ADD CONSTRAINT idx_required_sample_info_1 PRIMARY KEY (sample_id);


--
-- Name: sample_template_filepath idx_sample_template_filepath; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.sample_template_filepath
    ADD CONSTRAINT idx_sample_template_filepath PRIMARY KEY (study_id, filepath_id);


--
-- Name: severity idx_severity; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.severity
    ADD CONSTRAINT idx_severity UNIQUE (severity);


--
-- Name: software_artifact_type idx_software_artifact_type; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.software_artifact_type
    ADD CONSTRAINT idx_software_artifact_type PRIMARY KEY (software_id, artifact_type_id);


--
-- Name: software_publication idx_software_publication_0; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.software_publication
    ADD CONSTRAINT idx_software_publication_0 PRIMARY KEY (software_id, publication_doi);


--
-- Name: study_artifact idx_study_artifact; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_artifact
    ADD CONSTRAINT idx_study_artifact PRIMARY KEY (study_id, artifact_id);


--
-- Name: study_person idx_study_person; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_person
    ADD CONSTRAINT idx_study_person UNIQUE (name, affiliation);


--
-- Name: study_prep_template idx_study_prep_template; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_prep_template
    ADD CONSTRAINT idx_study_prep_template PRIMARY KEY (study_id, prep_template_id);


--
-- Name: visibility idx_study_status; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.visibility
    ADD CONSTRAINT idx_study_status UNIQUE (visibility);


--
-- Name: study_users idx_study_users; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_users
    ADD CONSTRAINT idx_study_users PRIMARY KEY (study_id, email);


--
-- Name: timeseries_type idx_timeseries_type; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.timeseries_type
    ADD CONSTRAINT idx_timeseries_type UNIQUE (timeseries_type, intervention_type);


--
-- Name: user_level idx_user_level; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.user_level
    ADD CONSTRAINT idx_user_level UNIQUE (name);


--
-- Name: analysis pk_analysis; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis
    ADD CONSTRAINT pk_analysis PRIMARY KEY (analysis_id);


--
-- Name: analysis_portal pk_analysis_portal; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_portal
    ADD CONSTRAINT pk_analysis_portal PRIMARY KEY (analysis_id, portal_type_id);


--
-- Name: analysis_sample pk_analysis_sample; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_sample
    ADD CONSTRAINT pk_analysis_sample PRIMARY KEY (analysis_id, artifact_id, sample_id);


--
-- Name: artifact pk_artifact; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact
    ADD CONSTRAINT pk_artifact PRIMARY KEY (artifact_id);


--
-- Name: checksum_algorithm pk_checksum_algorithm; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.checksum_algorithm
    ADD CONSTRAINT pk_checksum_algorithm PRIMARY KEY (checksum_algorithm_id);


--
-- Name: command_output pk_command_output; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.command_output
    ADD CONSTRAINT pk_command_output PRIMARY KEY (command_output_id);


--
-- Name: command_parameter pk_command_parameter; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.command_parameter
    ADD CONSTRAINT pk_command_parameter PRIMARY KEY (command_parameter_id);


--
-- Name: controlled_vocab_values pk_controlled_vocab_values; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.controlled_vocab_values
    ADD CONSTRAINT pk_controlled_vocab_values PRIMARY KEY (vocab_value_id);


--
-- Name: controlled_vocab pk_controlled_vocabularies; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.controlled_vocab
    ADD CONSTRAINT pk_controlled_vocabularies PRIMARY KEY (controlled_vocab_id);


--
-- Name: data_directory pk_data_directory; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.data_directory
    ADD CONSTRAINT pk_data_directory PRIMARY KEY (data_directory_id);


--
-- Name: data_type pk_data_type; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.data_type
    ADD CONSTRAINT pk_data_type PRIMARY KEY (data_type_id);


--
-- Name: default_parameter_set pk_default_parameter_set; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_parameter_set
    ADD CONSTRAINT pk_default_parameter_set PRIMARY KEY (default_parameter_set_id);


--
-- Name: default_workflow pk_default_workflow; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_workflow
    ADD CONSTRAINT pk_default_workflow PRIMARY KEY (default_workflow_id);


--
-- Name: default_workflow_node pk_default_workflow_command; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_workflow_node
    ADD CONSTRAINT pk_default_workflow_command PRIMARY KEY (default_workflow_node_id);


--
-- Name: default_workflow_edge pk_default_workflow_edge; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_workflow_edge
    ADD CONSTRAINT pk_default_workflow_edge PRIMARY KEY (default_workflow_edge_id);


--
-- Name: environmental_package pk_environmental_package; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.environmental_package
    ADD CONSTRAINT pk_environmental_package PRIMARY KEY (environmental_package_name);


--
-- Name: filepath pk_filepath; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.filepath
    ADD CONSTRAINT pk_filepath PRIMARY KEY (filepath_id);


--
-- Name: filepath_type pk_filepath_type; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.filepath_type
    ADD CONSTRAINT pk_filepath_type PRIMARY KEY (filepath_type_id);


--
-- Name: artifact_type pk_filetype; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact_type
    ADD CONSTRAINT pk_filetype PRIMARY KEY (artifact_type_id);


--
-- Name: investigation pk_investigation; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.investigation
    ADD CONSTRAINT pk_investigation PRIMARY KEY (investigation_id);


--
-- Name: prep_1 pk_jsonb_prep_1; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.prep_1
    ADD CONSTRAINT pk_jsonb_prep_1 PRIMARY KEY (sample_id);


--
-- Name: prep_2 pk_jsonb_prep_2; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.prep_2
    ADD CONSTRAINT pk_jsonb_prep_2 PRIMARY KEY (sample_id);


--
-- Name: sample_1 pk_jsonb_sample_1; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.sample_1
    ADD CONSTRAINT pk_jsonb_sample_1 PRIMARY KEY (sample_id);


--
-- Name: logging pk_logging; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.logging
    ADD CONSTRAINT pk_logging PRIMARY KEY (logging_id);


--
-- Name: archive_merging_scheme pk_merging_scheme; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.archive_merging_scheme
    ADD CONSTRAINT pk_merging_scheme PRIMARY KEY (archive_merging_scheme_id);


--
-- Name: message pk_message; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.message
    ADD CONSTRAINT pk_message PRIMARY KEY (message_id);


--
-- Name: mixs_field_description pk_mixs_field_description; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.mixs_field_description
    ADD CONSTRAINT pk_mixs_field_description PRIMARY KEY (column_name);


--
-- Name: oauth_identifiers pk_oauth2; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.oauth_identifiers
    ADD CONSTRAINT pk_oauth2 PRIMARY KEY (client_id);


--
-- Name: ontology pk_ontology; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.ontology
    ADD CONSTRAINT pk_ontology PRIMARY KEY (ontology_id);


--
-- Name: per_study_tags pk_per_study_tags; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.per_study_tags
    ADD CONSTRAINT pk_per_study_tags PRIMARY KEY (study_tag, study_id);


--
-- Name: portal_type pk_portal_type; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.portal_type
    ADD CONSTRAINT pk_portal_type PRIMARY KEY (portal_type_id);


--
-- Name: prep_template pk_prep_template; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.prep_template
    ADD CONSTRAINT pk_prep_template PRIMARY KEY (prep_template_id);


--
-- Name: processing_job pk_processing_job; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.processing_job
    ADD CONSTRAINT pk_processing_job PRIMARY KEY (processing_job_id);


--
-- Name: processing_job_status pk_processing_job_status; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.processing_job_status
    ADD CONSTRAINT pk_processing_job_status PRIMARY KEY (processing_job_status_id);


--
-- Name: processing_job_workflow pk_processing_job_workflow; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.processing_job_workflow
    ADD CONSTRAINT pk_processing_job_workflow PRIMARY KEY (processing_job_workflow_id);


--
-- Name: publication pk_publication; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.publication
    ADD CONSTRAINT pk_publication PRIMARY KEY (doi);


--
-- Name: reference pk_reference; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.reference
    ADD CONSTRAINT pk_reference PRIMARY KEY (reference_id);


--
-- Name: severity pk_severity; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.severity
    ADD CONSTRAINT pk_severity PRIMARY KEY (severity_id);


--
-- Name: software pk_software; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.software
    ADD CONSTRAINT pk_software PRIMARY KEY (software_id);


--
-- Name: software_command pk_software_command; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.software_command
    ADD CONSTRAINT pk_software_command PRIMARY KEY (command_id);


--
-- Name: software_type pk_software_type; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.software_type
    ADD CONSTRAINT pk_software_type PRIMARY KEY (software_type_id);


--
-- Name: study pk_study; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study
    ADD CONSTRAINT pk_study PRIMARY KEY (study_id);


--
-- Name: study_environmental_package pk_study_environmental_package; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_environmental_package
    ADD CONSTRAINT pk_study_environmental_package PRIMARY KEY (study_id, environmental_package_name);


--
-- Name: study_person pk_study_person; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_person
    ADD CONSTRAINT pk_study_person PRIMARY KEY (study_person_id);


--
-- Name: study_portal pk_study_portal; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_portal
    ADD CONSTRAINT pk_study_portal PRIMARY KEY (study_id, portal_type_id);


--
-- Name: visibility pk_study_status; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.visibility
    ADD CONSTRAINT pk_study_status PRIMARY KEY (visibility_id);


--
-- Name: study_tags pk_study_tags; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_tags
    ADD CONSTRAINT pk_study_tags PRIMARY KEY (study_tag);


--
-- Name: term pk_term; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.term
    ADD CONSTRAINT pk_term PRIMARY KEY (term_id);


--
-- Name: timeseries_type pk_timeseries_type; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.timeseries_type
    ADD CONSTRAINT pk_timeseries_type PRIMARY KEY (timeseries_type_id);


--
-- Name: qiita_user pk_user; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.qiita_user
    ADD CONSTRAINT pk_user PRIMARY KEY (email);


--
-- Name: user_level pk_user_level; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.user_level
    ADD CONSTRAINT pk_user_level PRIMARY KEY (user_level_id);


--
-- Name: preparation_artifact preparation_artifact_pkey; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.preparation_artifact
    ADD CONSTRAINT preparation_artifact_pkey PRIMARY KEY (prep_template_id, artifact_id);


--
-- Name: processing_job_resource_allocation processing_job_resource_allocation_pkey; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.processing_job_resource_allocation
    ADD CONSTRAINT processing_job_resource_allocation_pkey PRIMARY KEY (name, job_type);


--
-- Name: study unique_study_title; Type: CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study
    ADD CONSTRAINT unique_study_title UNIQUE (study_title);


--
-- Name: idx_analysis_0; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_analysis_0 ON qiita.analysis USING btree (logging_id);


--
-- Name: idx_analysis_artifact_analysis; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_analysis_artifact_analysis ON qiita.analysis_artifact USING btree (analysis_id);


--
-- Name: idx_analysis_artifact_artifact; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_analysis_artifact_artifact ON qiita.analysis_artifact USING btree (artifact_id);


--
-- Name: idx_analysis_email; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_analysis_email ON qiita.analysis USING btree (email);


--
-- Name: idx_analysis_filepath; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_analysis_filepath ON qiita.analysis_filepath USING btree (analysis_id);


--
-- Name: idx_analysis_filepath_0; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_analysis_filepath_0 ON qiita.analysis_filepath USING btree (filepath_id);


--
-- Name: idx_analysis_filepath_2; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_analysis_filepath_2 ON qiita.analysis_filepath USING btree (data_type_id);


--
-- Name: idx_analysis_portal; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_analysis_portal ON qiita.analysis_portal USING btree (analysis_id);


--
-- Name: idx_analysis_portal_0; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_analysis_portal_0 ON qiita.analysis_portal USING btree (portal_type_id);


--
-- Name: idx_analysis_processing_job_analysis; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_analysis_processing_job_analysis ON qiita.analysis_processing_job USING btree (analysis_id);


--
-- Name: idx_analysis_processing_job_pj; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_analysis_processing_job_pj ON qiita.analysis_processing_job USING btree (processing_job_id);


--
-- Name: idx_analysis_sample; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_analysis_sample ON qiita.analysis_sample USING btree (analysis_id);


--
-- Name: idx_analysis_sample_1; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_analysis_sample_1 ON qiita.analysis_sample USING btree (sample_id);


--
-- Name: idx_analysis_sample_artifact_id; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_analysis_sample_artifact_id ON qiita.analysis_sample USING btree (artifact_id);


--
-- Name: idx_analysis_users_analysis; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_analysis_users_analysis ON qiita.analysis_users USING btree (analysis_id);


--
-- Name: idx_analysis_users_email; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_analysis_users_email ON qiita.analysis_users USING btree (email);


--
-- Name: idx_archive_feature_value_0; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_archive_feature_value_0 ON qiita.archive_feature_value USING btree (archive_merging_scheme_id);


--
-- Name: idx_artifact; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_artifact ON qiita.artifact USING btree (command_id);


--
-- Name: idx_artifact_0; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_artifact_0 ON qiita.artifact USING btree (visibility_id);


--
-- Name: idx_artifact_1; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_artifact_1 ON qiita.artifact USING btree (artifact_type_id);


--
-- Name: idx_artifact_2; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_artifact_2 ON qiita.artifact USING btree (data_type_id);


--
-- Name: idx_artifact_filepath_artifact; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_artifact_filepath_artifact ON qiita.artifact_filepath USING btree (artifact_id);


--
-- Name: idx_artifact_filepath_filepath; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_artifact_filepath_filepath ON qiita.artifact_filepath USING btree (filepath_id);


--
-- Name: idx_artifact_output_processing_job_artifact; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_artifact_output_processing_job_artifact ON qiita.artifact_output_processing_job USING btree (artifact_id);


--
-- Name: idx_artifact_output_processing_job_cmd; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_artifact_output_processing_job_cmd ON qiita.artifact_output_processing_job USING btree (command_output_id);


--
-- Name: idx_artifact_output_processing_job_job; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_artifact_output_processing_job_job ON qiita.artifact_output_processing_job USING btree (processing_job_id);


--
-- Name: idx_artifact_processing_job_artifact; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_artifact_processing_job_artifact ON qiita.artifact_processing_job USING btree (artifact_id);


--
-- Name: idx_artifact_processing_job_job; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_artifact_processing_job_job ON qiita.artifact_processing_job USING btree (processing_job_id);


--
-- Name: idx_artifact_type_filepath_type_at; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_artifact_type_filepath_type_at ON qiita.artifact_type_filepath_type USING btree (artifact_type_id);


--
-- Name: idx_artifact_type_filepath_type_ft; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_artifact_type_filepath_type_ft ON qiita.artifact_type_filepath_type USING btree (filepath_type_id);


--
-- Name: idx_column_controlled_vocabularies_0; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_column_controlled_vocabularies_0 ON qiita.column_controlled_vocabularies USING btree (column_name);


--
-- Name: idx_column_controlled_vocabularies_1; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_column_controlled_vocabularies_1 ON qiita.column_controlled_vocabularies USING btree (controlled_vocab_id);


--
-- Name: idx_column_ontology_0; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_column_ontology_0 ON qiita.column_ontology USING btree (column_name);


--
-- Name: idx_command_output_cmd_id; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_command_output_cmd_id ON qiita.command_output USING btree (command_id);


--
-- Name: idx_command_output_type_id; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_command_output_type_id ON qiita.command_output USING btree (artifact_type_id);


--
-- Name: idx_command_parameter; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_command_parameter ON qiita.command_parameter USING btree (command_id);


--
-- Name: idx_common_prep_info_0; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_common_prep_info_0 ON qiita.prep_template_sample USING btree (sample_id);


--
-- Name: idx_common_prep_info_1; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_common_prep_info_1 ON qiita.prep_template_sample USING btree (prep_template_id);


--
-- Name: idx_controlled_vocab_values; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_controlled_vocab_values ON qiita.controlled_vocab_values USING btree (controlled_vocab_id);


--
-- Name: idx_default_parameter_set; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_default_parameter_set ON qiita.default_parameter_set USING btree (command_id);


--
-- Name: idx_default_workflow_command_dflt_param_id; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_default_workflow_command_dflt_param_id ON qiita.default_workflow_node USING btree (default_parameter_set_id);


--
-- Name: idx_default_workflow_command_dflt_wf_id; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_default_workflow_command_dflt_wf_id ON qiita.default_workflow_node USING btree (default_workflow_id);


--
-- Name: idx_default_workflow_edge_child; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_default_workflow_edge_child ON qiita.default_workflow_edge USING btree (child_id);


--
-- Name: idx_default_workflow_edge_connections_child; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_default_workflow_edge_connections_child ON qiita.default_workflow_edge_connections USING btree (child_input_id);


--
-- Name: idx_default_workflow_edge_connections_edge; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_default_workflow_edge_connections_edge ON qiita.default_workflow_edge_connections USING btree (default_workflow_edge_id);


--
-- Name: idx_default_workflow_edge_connections_parent; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_default_workflow_edge_connections_parent ON qiita.default_workflow_edge_connections USING btree (parent_output_id);


--
-- Name: idx_default_workflow_edge_parent; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_default_workflow_edge_parent ON qiita.default_workflow_edge USING btree (parent_id);


--
-- Name: idx_download_link_exp; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_download_link_exp ON qiita.download_link USING btree (exp);


--
-- Name: idx_ebi_run_accession_artifact_id; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_ebi_run_accession_artifact_id ON qiita.ebi_run_accession USING btree (artifact_id);


--
-- Name: idx_ebi_run_accession_sid; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_ebi_run_accession_sid ON qiita.ebi_run_accession USING btree (sample_id);


--
-- Name: idx_filepath; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_filepath ON qiita.filepath USING btree (filepath_type_id);


--
-- Name: idx_filepath_0; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_filepath_0 ON qiita.filepath USING btree (data_directory_id);


--
-- Name: idx_investigation; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_investigation ON qiita.investigation USING btree (contact_person_id);


--
-- Name: idx_investigation_study_investigation; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_investigation_study_investigation ON qiita.investigation_study USING btree (investigation_id);


--
-- Name: idx_investigation_study_study; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_investigation_study_study ON qiita.investigation_study USING btree (study_id);


--
-- Name: idx_logging_0; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_logging_0 ON qiita.logging USING btree (severity_id);


--
-- Name: idx_message_user_0; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_message_user_0 ON qiita.message_user USING btree (message_id);


--
-- Name: idx_message_user_1; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_message_user_1 ON qiita.message_user USING btree (email);


--
-- Name: idx_oauth_software_client; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_oauth_software_client ON qiita.oauth_software USING btree (client_id);


--
-- Name: idx_oauth_software_software; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_oauth_software_software ON qiita.oauth_software USING btree (software_id);


--
-- Name: idx_parameter_artifact_type_param_id; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_parameter_artifact_type_param_id ON qiita.parameter_artifact_type USING btree (command_parameter_id);


--
-- Name: idx_parameter_artifact_type_type_id; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_parameter_artifact_type_type_id ON qiita.parameter_artifact_type USING btree (artifact_type_id);


--
-- Name: idx_parent_artifact_artifact; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_parent_artifact_artifact ON qiita.parent_artifact USING btree (artifact_id);


--
-- Name: idx_parent_artifact_parent; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_parent_artifact_parent ON qiita.parent_artifact USING btree (parent_id);


--
-- Name: idx_parent_processing_job_child; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_parent_processing_job_child ON qiita.parent_processing_job USING btree (child_id);


--
-- Name: idx_parent_processing_job_parent; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_parent_processing_job_parent ON qiita.parent_processing_job USING btree (parent_id);


--
-- Name: idx_prep_template; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_prep_template ON qiita.prep_template USING btree (data_type_id);


--
-- Name: idx_prep_template_artifact_id; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_prep_template_artifact_id ON qiita.prep_template USING btree (artifact_id);


--
-- Name: idx_prep_template_processing_job_job; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_prep_template_processing_job_job ON qiita.prep_template_processing_job USING btree (processing_job_id);


--
-- Name: idx_prep_template_processing_job_pt_id; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_prep_template_processing_job_pt_id ON qiita.prep_template_processing_job USING btree (prep_template_id);


--
-- Name: idx_preparation_artifact_prep_template_id; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_preparation_artifact_prep_template_id ON qiita.preparation_artifact USING btree (prep_template_id);


--
-- Name: idx_processing_job_command_id; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_processing_job_command_id ON qiita.processing_job USING btree (command_id);


--
-- Name: idx_processing_job_email; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_processing_job_email ON qiita.processing_job USING btree (email);


--
-- Name: idx_processing_job_logging; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_processing_job_logging ON qiita.processing_job USING btree (logging_id);


--
-- Name: idx_processing_job_status_id; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_processing_job_status_id ON qiita.processing_job USING btree (processing_job_status_id);


--
-- Name: idx_processing_job_validator_0; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_processing_job_validator_0 ON qiita.processing_job_validator USING btree (processing_job_id);


--
-- Name: idx_processing_job_validator_1; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_processing_job_validator_1 ON qiita.processing_job_validator USING btree (validator_id);


--
-- Name: idx_processing_job_workflow; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_processing_job_workflow ON qiita.processing_job_workflow USING btree (email);


--
-- Name: idx_processing_job_workflow_root_job; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_processing_job_workflow_root_job ON qiita.processing_job_workflow_root USING btree (processing_job_id);


--
-- Name: idx_processing_job_workflow_root_wf; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_processing_job_workflow_root_wf ON qiita.processing_job_workflow_root USING btree (processing_job_workflow_id);


--
-- Name: idx_reference; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_reference ON qiita.reference USING btree (sequence_filepath);


--
-- Name: idx_reference_0; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_reference_0 ON qiita.reference USING btree (taxonomy_filepath);


--
-- Name: idx_reference_1; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_reference_1 ON qiita.reference USING btree (tree_filepath);


--
-- Name: idx_required_prep_info_2; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_required_prep_info_2 ON qiita.prep_template_sample USING btree (sample_id);


--
-- Name: idx_required_sample_info; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_required_sample_info ON qiita.study_sample USING btree (study_id);


--
-- Name: idx_software_artifact_type_artifact; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_software_artifact_type_artifact ON qiita.software_artifact_type USING btree (artifact_type_id);


--
-- Name: idx_software_artifact_type_software; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_software_artifact_type_software ON qiita.software_artifact_type USING btree (software_id);


--
-- Name: idx_software_command; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_software_command ON qiita.software_command USING btree (software_id);


--
-- Name: idx_software_publication_publication; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_software_publication_publication ON qiita.software_publication USING btree (publication_doi);


--
-- Name: idx_software_publication_software; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_software_publication_software ON qiita.software_publication USING btree (software_id);


--
-- Name: idx_software_type; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_software_type ON qiita.software USING btree (software_type_id);


--
-- Name: idx_study; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_study ON qiita.study USING btree (email);


--
-- Name: idx_study_2; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_study_2 ON qiita.study USING btree (lab_person_id);


--
-- Name: idx_study_3; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_study_3 ON qiita.study USING btree (principal_investigator_id);


--
-- Name: idx_study_4; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_study_4 ON qiita.study USING btree (timeseries_type_id);


--
-- Name: idx_study_artifact_artifact; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_study_artifact_artifact ON qiita.study_artifact USING btree (artifact_id);


--
-- Name: idx_study_artifact_study; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_study_artifact_study ON qiita.study_artifact USING btree (study_id);


--
-- Name: idx_study_environmental_package; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_study_environmental_package ON qiita.study_environmental_package USING btree (study_id);


--
-- Name: idx_study_environmental_package_0; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_study_environmental_package_0 ON qiita.study_environmental_package USING btree (environmental_package_name);


--
-- Name: idx_study_portal; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_study_portal ON qiita.study_portal USING btree (study_id);


--
-- Name: idx_study_portal_0; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_study_portal_0 ON qiita.study_portal USING btree (portal_type_id);


--
-- Name: idx_study_prep_template_0; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_study_prep_template_0 ON qiita.study_prep_template USING btree (study_id);


--
-- Name: idx_study_prep_template_1; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_study_prep_template_1 ON qiita.study_prep_template USING btree (prep_template_id);


--
-- Name: idx_study_publication_doi; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_study_publication_doi ON qiita.study_publication USING btree (publication);


--
-- Name: idx_study_publication_study; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_study_publication_study ON qiita.study_publication USING btree (study_id);


--
-- Name: idx_study_users_0; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_study_users_0 ON qiita.study_users USING btree (study_id);


--
-- Name: idx_study_users_1; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_study_users_1 ON qiita.study_users USING btree (email);


--
-- Name: idx_term; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_term ON qiita.term USING btree (ontology_id);


--
-- Name: idx_user; Type: INDEX; Schema: qiita
--

CREATE INDEX idx_user ON qiita.qiita_user USING btree (user_level_id);


--
-- Name: analysis_artifact fk_analysis_artifact_analysis; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_artifact
    ADD CONSTRAINT fk_analysis_artifact_analysis FOREIGN KEY (analysis_id) REFERENCES qiita.analysis(analysis_id);


--
-- Name: analysis_artifact fk_analysis_artifact_artifact; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_artifact
    ADD CONSTRAINT fk_analysis_artifact_artifact FOREIGN KEY (artifact_id) REFERENCES qiita.artifact(artifact_id);


--
-- Name: analysis_filepath fk_analysis_filepath; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_filepath
    ADD CONSTRAINT fk_analysis_filepath FOREIGN KEY (analysis_id) REFERENCES qiita.analysis(analysis_id);


--
-- Name: analysis_filepath fk_analysis_filepath_0; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_filepath
    ADD CONSTRAINT fk_analysis_filepath_0 FOREIGN KEY (filepath_id) REFERENCES qiita.filepath(filepath_id);


--
-- Name: analysis_filepath fk_analysis_filepath_1; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_filepath
    ADD CONSTRAINT fk_analysis_filepath_1 FOREIGN KEY (data_type_id) REFERENCES qiita.data_type(data_type_id);


--
-- Name: analysis fk_analysis_logging; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis
    ADD CONSTRAINT fk_analysis_logging FOREIGN KEY (logging_id) REFERENCES qiita.logging(logging_id);


--
-- Name: analysis_portal fk_analysis_portal; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_portal
    ADD CONSTRAINT fk_analysis_portal FOREIGN KEY (analysis_id) REFERENCES qiita.analysis(analysis_id);


--
-- Name: analysis_portal fk_analysis_portal_0; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_portal
    ADD CONSTRAINT fk_analysis_portal_0 FOREIGN KEY (portal_type_id) REFERENCES qiita.portal_type(portal_type_id);


--
-- Name: analysis_processing_job fk_analysis_processing_job; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_processing_job
    ADD CONSTRAINT fk_analysis_processing_job FOREIGN KEY (analysis_id) REFERENCES qiita.analysis(analysis_id);


--
-- Name: analysis_processing_job fk_analysis_processing_job_pj; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_processing_job
    ADD CONSTRAINT fk_analysis_processing_job_pj FOREIGN KEY (processing_job_id) REFERENCES qiita.processing_job(processing_job_id);


--
-- Name: analysis_sample fk_analysis_sample; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_sample
    ADD CONSTRAINT fk_analysis_sample FOREIGN KEY (sample_id) REFERENCES qiita.study_sample(sample_id) ON UPDATE CASCADE;


--
-- Name: analysis_sample fk_analysis_sample_analysis; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_sample
    ADD CONSTRAINT fk_analysis_sample_analysis FOREIGN KEY (analysis_id) REFERENCES qiita.analysis(analysis_id);


--
-- Name: analysis_sample fk_analysis_sample_artifact; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_sample
    ADD CONSTRAINT fk_analysis_sample_artifact FOREIGN KEY (artifact_id) REFERENCES qiita.artifact(artifact_id);


--
-- Name: analysis fk_analysis_user; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis
    ADD CONSTRAINT fk_analysis_user FOREIGN KEY (email) REFERENCES qiita.qiita_user(email) ON UPDATE CASCADE;


--
-- Name: analysis_users fk_analysis_users_analysis; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_users
    ADD CONSTRAINT fk_analysis_users_analysis FOREIGN KEY (analysis_id) REFERENCES qiita.analysis(analysis_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: analysis_users fk_analysis_users_user; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.analysis_users
    ADD CONSTRAINT fk_analysis_users_user FOREIGN KEY (email) REFERENCES qiita.qiita_user(email) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: archive_feature_value fk_archive_feature_value; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.archive_feature_value
    ADD CONSTRAINT fk_archive_feature_value FOREIGN KEY (archive_merging_scheme_id) REFERENCES qiita.archive_merging_scheme(archive_merging_scheme_id);


--
-- Name: artifact fk_artifact_data_type; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact
    ADD CONSTRAINT fk_artifact_data_type FOREIGN KEY (data_type_id) REFERENCES qiita.data_type(data_type_id);


--
-- Name: artifact_filepath fk_artifact_filepath_artifact; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact_filepath
    ADD CONSTRAINT fk_artifact_filepath_artifact FOREIGN KEY (artifact_id) REFERENCES qiita.artifact(artifact_id);


--
-- Name: artifact_filepath fk_artifact_filepath_filepath; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact_filepath
    ADD CONSTRAINT fk_artifact_filepath_filepath FOREIGN KEY (filepath_id) REFERENCES qiita.filepath(filepath_id);


--
-- Name: preparation_artifact fk_artifact_id; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.preparation_artifact
    ADD CONSTRAINT fk_artifact_id FOREIGN KEY (artifact_id) REFERENCES qiita.artifact(artifact_id);


--
-- Name: artifact_output_processing_job fk_artifact_output_processing_job_artifact; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact_output_processing_job
    ADD CONSTRAINT fk_artifact_output_processing_job_artifact FOREIGN KEY (artifact_id) REFERENCES qiita.artifact(artifact_id);


--
-- Name: artifact_output_processing_job fk_artifact_output_processing_job_cmd; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact_output_processing_job
    ADD CONSTRAINT fk_artifact_output_processing_job_cmd FOREIGN KEY (command_output_id) REFERENCES qiita.command_output(command_output_id);


--
-- Name: artifact_output_processing_job fk_artifact_output_processing_job_job; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact_output_processing_job
    ADD CONSTRAINT fk_artifact_output_processing_job_job FOREIGN KEY (processing_job_id) REFERENCES qiita.processing_job(processing_job_id);


--
-- Name: artifact_processing_job fk_artifact_processing_job; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact_processing_job
    ADD CONSTRAINT fk_artifact_processing_job FOREIGN KEY (artifact_id) REFERENCES qiita.artifact(artifact_id);


--
-- Name: artifact_processing_job fk_artifact_processing_job_0; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact_processing_job
    ADD CONSTRAINT fk_artifact_processing_job_0 FOREIGN KEY (processing_job_id) REFERENCES qiita.processing_job(processing_job_id);


--
-- Name: artifact fk_artifact_software_command; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact
    ADD CONSTRAINT fk_artifact_software_command FOREIGN KEY (command_id) REFERENCES qiita.software_command(command_id);


--
-- Name: artifact fk_artifact_type; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact
    ADD CONSTRAINT fk_artifact_type FOREIGN KEY (artifact_type_id) REFERENCES qiita.artifact_type(artifact_type_id);


--
-- Name: artifact_type_filepath_type fk_artifact_type_filepath_type_at; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact_type_filepath_type
    ADD CONSTRAINT fk_artifact_type_filepath_type_at FOREIGN KEY (artifact_type_id) REFERENCES qiita.artifact_type(artifact_type_id);


--
-- Name: artifact_type_filepath_type fk_artifact_type_filepath_type_ft; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact_type_filepath_type
    ADD CONSTRAINT fk_artifact_type_filepath_type_ft FOREIGN KEY (filepath_type_id) REFERENCES qiita.filepath_type(filepath_type_id);


--
-- Name: default_workflow fk_artifact_type_id; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_workflow
    ADD CONSTRAINT fk_artifact_type_id FOREIGN KEY (artifact_type_id) REFERENCES qiita.artifact_type(artifact_type_id) ON UPDATE CASCADE;


--
-- Name: artifact fk_artifact_visibility; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.artifact
    ADD CONSTRAINT fk_artifact_visibility FOREIGN KEY (visibility_id) REFERENCES qiita.visibility(visibility_id);


--
-- Name: column_controlled_vocabularies fk_column_controlled_vocab2; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.column_controlled_vocabularies
    ADD CONSTRAINT fk_column_controlled_vocab2 FOREIGN KEY (controlled_vocab_id) REFERENCES qiita.controlled_vocab(controlled_vocab_id);


--
-- Name: column_controlled_vocabularies fk_column_controlled_vocabularies; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.column_controlled_vocabularies
    ADD CONSTRAINT fk_column_controlled_vocabularies FOREIGN KEY (column_name) REFERENCES qiita.mixs_field_description(column_name);


--
-- Name: column_ontology fk_column_ontology; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.column_ontology
    ADD CONSTRAINT fk_column_ontology FOREIGN KEY (column_name) REFERENCES qiita.mixs_field_description(column_name);


--
-- Name: command_output fk_command_output; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.command_output
    ADD CONSTRAINT fk_command_output FOREIGN KEY (command_id) REFERENCES qiita.software_command(command_id);


--
-- Name: command_output fk_command_output_0; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.command_output
    ADD CONSTRAINT fk_command_output_0 FOREIGN KEY (artifact_type_id) REFERENCES qiita.artifact_type(artifact_type_id);


--
-- Name: command_parameter fk_command_parameter; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.command_parameter
    ADD CONSTRAINT fk_command_parameter FOREIGN KEY (command_id) REFERENCES qiita.software_command(command_id);


--
-- Name: prep_template_sample fk_common_prep_info; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.prep_template_sample
    ADD CONSTRAINT fk_common_prep_info FOREIGN KEY (sample_id) REFERENCES qiita.study_sample(sample_id) ON UPDATE CASCADE;


--
-- Name: controlled_vocab_values fk_controlled_vocab_values; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.controlled_vocab_values
    ADD CONSTRAINT fk_controlled_vocab_values FOREIGN KEY (controlled_vocab_id) REFERENCES qiita.controlled_vocab(controlled_vocab_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: default_workflow_data_type fk_data_type_id; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_workflow_data_type
    ADD CONSTRAINT fk_data_type_id FOREIGN KEY (data_type_id) REFERENCES qiita.data_type(data_type_id);


--
-- Name: default_parameter_set fk_default_parameter_set; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_parameter_set
    ADD CONSTRAINT fk_default_parameter_set FOREIGN KEY (command_id) REFERENCES qiita.software_command(command_id);


--
-- Name: default_workflow_node fk_default_workflow_command_0; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_workflow_node
    ADD CONSTRAINT fk_default_workflow_command_0 FOREIGN KEY (default_parameter_set_id) REFERENCES qiita.default_parameter_set(default_parameter_set_id);


--
-- Name: default_workflow_node fk_default_workflow_command_1; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_workflow_node
    ADD CONSTRAINT fk_default_workflow_command_1 FOREIGN KEY (default_workflow_id) REFERENCES qiita.default_workflow(default_workflow_id);


--
-- Name: default_workflow_edge fk_default_workflow_edge; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_workflow_edge
    ADD CONSTRAINT fk_default_workflow_edge FOREIGN KEY (parent_id) REFERENCES qiita.default_workflow_node(default_workflow_node_id);


--
-- Name: default_workflow_edge fk_default_workflow_edge_0; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_workflow_edge
    ADD CONSTRAINT fk_default_workflow_edge_0 FOREIGN KEY (child_id) REFERENCES qiita.default_workflow_node(default_workflow_node_id);


--
-- Name: default_workflow_edge_connections fk_default_workflow_edge_connections; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_workflow_edge_connections
    ADD CONSTRAINT fk_default_workflow_edge_connections FOREIGN KEY (parent_output_id) REFERENCES qiita.command_output(command_output_id);


--
-- Name: default_workflow_edge_connections fk_default_workflow_edge_connections_0; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_workflow_edge_connections
    ADD CONSTRAINT fk_default_workflow_edge_connections_0 FOREIGN KEY (child_input_id) REFERENCES qiita.command_parameter(command_parameter_id);


--
-- Name: default_workflow_edge_connections fk_default_workflow_edge_connections_1; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_workflow_edge_connections
    ADD CONSTRAINT fk_default_workflow_edge_connections_1 FOREIGN KEY (default_workflow_edge_id) REFERENCES qiita.default_workflow_edge(default_workflow_edge_id);


--
-- Name: default_workflow_data_type fk_default_workflow_id; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.default_workflow_data_type
    ADD CONSTRAINT fk_default_workflow_id FOREIGN KEY (default_workflow_id) REFERENCES qiita.default_workflow(default_workflow_id);


--
-- Name: ebi_run_accession fk_ebi_run_accesion_artifact; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.ebi_run_accession
    ADD CONSTRAINT fk_ebi_run_accesion_artifact FOREIGN KEY (artifact_id) REFERENCES qiita.artifact(artifact_id);


--
-- Name: ebi_run_accession fk_ebi_run_accession; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.ebi_run_accession
    ADD CONSTRAINT fk_ebi_run_accession FOREIGN KEY (sample_id) REFERENCES qiita.study_sample(sample_id);


--
-- Name: study_tags fk_email; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_tags
    ADD CONSTRAINT fk_email FOREIGN KEY (email) REFERENCES qiita.qiita_user(email);


--
-- Name: filepath fk_filepath; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.filepath
    ADD CONSTRAINT fk_filepath FOREIGN KEY (filepath_type_id) REFERENCES qiita.filepath_type(filepath_type_id);


--
-- Name: filepath fk_filepath_0; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.filepath
    ADD CONSTRAINT fk_filepath_0 FOREIGN KEY (checksum_algorithm_id) REFERENCES qiita.checksum_algorithm(checksum_algorithm_id);


--
-- Name: filepath fk_filepath_data_directory; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.filepath
    ADD CONSTRAINT fk_filepath_data_directory FOREIGN KEY (data_directory_id) REFERENCES qiita.data_directory(data_directory_id) ON UPDATE RESTRICT ON DELETE RESTRICT;


--
-- Name: prep_template_filepath fk_filepath_id; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.prep_template_filepath
    ADD CONSTRAINT fk_filepath_id FOREIGN KEY (filepath_id) REFERENCES qiita.filepath(filepath_id);


--
-- Name: sample_template_filepath fk_filepath_id; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.sample_template_filepath
    ADD CONSTRAINT fk_filepath_id FOREIGN KEY (filepath_id) REFERENCES qiita.filepath(filepath_id);


--
-- Name: investigation_study fk_investigation_study; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.investigation_study
    ADD CONSTRAINT fk_investigation_study FOREIGN KEY (investigation_id) REFERENCES qiita.investigation(investigation_id);


--
-- Name: investigation fk_investigation_study_person; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.investigation
    ADD CONSTRAINT fk_investigation_study_person FOREIGN KEY (contact_person_id) REFERENCES qiita.study_person(study_person_id);


--
-- Name: investigation_study fk_investigation_study_study; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.investigation_study
    ADD CONSTRAINT fk_investigation_study_study FOREIGN KEY (study_id) REFERENCES qiita.study(study_id);


--
-- Name: logging fk_logging_severity; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.logging
    ADD CONSTRAINT fk_logging_severity FOREIGN KEY (severity_id) REFERENCES qiita.severity(severity_id);


--
-- Name: message_user fk_message_user; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.message_user
    ADD CONSTRAINT fk_message_user FOREIGN KEY (message_id) REFERENCES qiita.message(message_id);


--
-- Name: message_user fk_message_user_0; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.message_user
    ADD CONSTRAINT fk_message_user_0 FOREIGN KEY (email) REFERENCES qiita.qiita_user(email) ON UPDATE CASCADE;


--
-- Name: oauth_software fk_oauth_software; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.oauth_software
    ADD CONSTRAINT fk_oauth_software FOREIGN KEY (client_id) REFERENCES qiita.oauth_identifiers(client_id);


--
-- Name: oauth_software fk_oauth_software_software; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.oauth_software
    ADD CONSTRAINT fk_oauth_software_software FOREIGN KEY (software_id) REFERENCES qiita.software(software_id);


--
-- Name: parameter_artifact_type fk_parameter_artifact_type; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.parameter_artifact_type
    ADD CONSTRAINT fk_parameter_artifact_type FOREIGN KEY (command_parameter_id) REFERENCES qiita.command_parameter(command_parameter_id);


--
-- Name: parameter_artifact_type fk_parameter_artifact_type_0; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.parameter_artifact_type
    ADD CONSTRAINT fk_parameter_artifact_type_0 FOREIGN KEY (artifact_type_id) REFERENCES qiita.artifact_type(artifact_type_id);


--
-- Name: parent_artifact fk_parent_artifact_artifact; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.parent_artifact
    ADD CONSTRAINT fk_parent_artifact_artifact FOREIGN KEY (artifact_id) REFERENCES qiita.artifact(artifact_id);


--
-- Name: parent_artifact fk_parent_artifact_parent; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.parent_artifact
    ADD CONSTRAINT fk_parent_artifact_parent FOREIGN KEY (parent_id) REFERENCES qiita.artifact(artifact_id);


--
-- Name: parent_processing_job fk_parent_processing_job_child; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.parent_processing_job
    ADD CONSTRAINT fk_parent_processing_job_child FOREIGN KEY (child_id) REFERENCES qiita.processing_job(processing_job_id);


--
-- Name: parent_processing_job fk_parent_processing_job_parent; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.parent_processing_job
    ADD CONSTRAINT fk_parent_processing_job_parent FOREIGN KEY (parent_id) REFERENCES qiita.processing_job(processing_job_id);


--
-- Name: prep_template_sample fk_prep_template; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.prep_template_sample
    ADD CONSTRAINT fk_prep_template FOREIGN KEY (prep_template_id) REFERENCES qiita.prep_template(prep_template_id);


--
-- Name: prep_template fk_prep_template_artifact; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.prep_template
    ADD CONSTRAINT fk_prep_template_artifact FOREIGN KEY (artifact_id) REFERENCES qiita.artifact(artifact_id);


--
-- Name: prep_template fk_prep_template_data_type; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.prep_template
    ADD CONSTRAINT fk_prep_template_data_type FOREIGN KEY (data_type_id) REFERENCES qiita.data_type(data_type_id);


--
-- Name: prep_template_filepath fk_prep_template_id; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.prep_template_filepath
    ADD CONSTRAINT fk_prep_template_id FOREIGN KEY (prep_template_id) REFERENCES qiita.prep_template(prep_template_id);


--
-- Name: preparation_artifact fk_prep_template_id; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.preparation_artifact
    ADD CONSTRAINT fk_prep_template_id FOREIGN KEY (prep_template_id) REFERENCES qiita.prep_template(prep_template_id);


--
-- Name: prep_template_processing_job fk_prep_template_processing_job_job; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.prep_template_processing_job
    ADD CONSTRAINT fk_prep_template_processing_job_job FOREIGN KEY (processing_job_id) REFERENCES qiita.processing_job(processing_job_id);


--
-- Name: prep_template_processing_job fk_prep_template_processing_job_pt; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.prep_template_processing_job
    ADD CONSTRAINT fk_prep_template_processing_job_pt FOREIGN KEY (prep_template_id) REFERENCES qiita.prep_template(prep_template_id);


--
-- Name: processing_job fk_processing_job; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.processing_job
    ADD CONSTRAINT fk_processing_job FOREIGN KEY (command_id) REFERENCES qiita.software_command(command_id);


--
-- Name: processing_job fk_processing_job_logging; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.processing_job
    ADD CONSTRAINT fk_processing_job_logging FOREIGN KEY (logging_id) REFERENCES qiita.logging(logging_id);


--
-- Name: processing_job fk_processing_job_qiita_user; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.processing_job
    ADD CONSTRAINT fk_processing_job_qiita_user FOREIGN KEY (email) REFERENCES qiita.qiita_user(email) ON UPDATE CASCADE;


--
-- Name: processing_job fk_processing_job_status; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.processing_job
    ADD CONSTRAINT fk_processing_job_status FOREIGN KEY (processing_job_status_id) REFERENCES qiita.processing_job_status(processing_job_status_id);


--
-- Name: processing_job_validator fk_processing_job_validator_c; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.processing_job_validator
    ADD CONSTRAINT fk_processing_job_validator_c FOREIGN KEY (validator_id) REFERENCES qiita.processing_job(processing_job_id);


--
-- Name: processing_job_validator fk_processing_job_validator_p; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.processing_job_validator
    ADD CONSTRAINT fk_processing_job_validator_p FOREIGN KEY (processing_job_id) REFERENCES qiita.processing_job(processing_job_id);


--
-- Name: processing_job_workflow fk_processing_job_workflow; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.processing_job_workflow
    ADD CONSTRAINT fk_processing_job_workflow FOREIGN KEY (email) REFERENCES qiita.qiita_user(email) ON UPDATE CASCADE;


--
-- Name: processing_job_workflow_root fk_processing_job_workflow_root_job; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.processing_job_workflow_root
    ADD CONSTRAINT fk_processing_job_workflow_root_job FOREIGN KEY (processing_job_workflow_id) REFERENCES qiita.processing_job_workflow(processing_job_workflow_id);


--
-- Name: processing_job_workflow_root fk_processing_job_workflow_root_wf; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.processing_job_workflow_root
    ADD CONSTRAINT fk_processing_job_workflow_root_wf FOREIGN KEY (processing_job_id) REFERENCES qiita.processing_job(processing_job_id);


--
-- Name: reference fk_reference_sequence_filepath; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.reference
    ADD CONSTRAINT fk_reference_sequence_filepath FOREIGN KEY (sequence_filepath) REFERENCES qiita.filepath(filepath_id);


--
-- Name: reference fk_reference_taxonomy_filepath; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.reference
    ADD CONSTRAINT fk_reference_taxonomy_filepath FOREIGN KEY (taxonomy_filepath) REFERENCES qiita.filepath(filepath_id);


--
-- Name: reference fk_reference_tree_filepath; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.reference
    ADD CONSTRAINT fk_reference_tree_filepath FOREIGN KEY (tree_filepath) REFERENCES qiita.filepath(filepath_id);


--
-- Name: study_sample fk_required_sample_info_study; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_sample
    ADD CONSTRAINT fk_required_sample_info_study FOREIGN KEY (study_id) REFERENCES qiita.study(study_id);


--
-- Name: software_artifact_type fk_software_artifact_type_at; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.software_artifact_type
    ADD CONSTRAINT fk_software_artifact_type_at FOREIGN KEY (artifact_type_id) REFERENCES qiita.artifact_type(artifact_type_id);


--
-- Name: software_artifact_type fk_software_artifact_type_sw; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.software_artifact_type
    ADD CONSTRAINT fk_software_artifact_type_sw FOREIGN KEY (software_id) REFERENCES qiita.software(software_id);


--
-- Name: software_command fk_software_command_software; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.software_command
    ADD CONSTRAINT fk_software_command_software FOREIGN KEY (software_id) REFERENCES qiita.software(software_id);


--
-- Name: software_publication fk_software_publication; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.software_publication
    ADD CONSTRAINT fk_software_publication FOREIGN KEY (software_id) REFERENCES qiita.software(software_id);


--
-- Name: software_publication fk_software_publication_0; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.software_publication
    ADD CONSTRAINT fk_software_publication_0 FOREIGN KEY (publication_doi) REFERENCES qiita.publication(doi);


--
-- Name: software fk_software_software_type; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.software
    ADD CONSTRAINT fk_software_software_type FOREIGN KEY (software_type_id) REFERENCES qiita.software_type(software_type_id);


--
-- Name: study_artifact fk_study_artifact_artifact; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_artifact
    ADD CONSTRAINT fk_study_artifact_artifact FOREIGN KEY (artifact_id) REFERENCES qiita.artifact(artifact_id);


--
-- Name: study_artifact fk_study_artifact_study; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_artifact
    ADD CONSTRAINT fk_study_artifact_study FOREIGN KEY (study_id) REFERENCES qiita.study(study_id);


--
-- Name: study_environmental_package fk_study_environmental_package; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_environmental_package
    ADD CONSTRAINT fk_study_environmental_package FOREIGN KEY (study_id) REFERENCES qiita.study(study_id);


--
-- Name: study_environmental_package fk_study_environmental_package_0; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_environmental_package
    ADD CONSTRAINT fk_study_environmental_package_0 FOREIGN KEY (environmental_package_name) REFERENCES qiita.environmental_package(environmental_package_name);


--
-- Name: sample_template_filepath fk_study_id; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.sample_template_filepath
    ADD CONSTRAINT fk_study_id FOREIGN KEY (study_id) REFERENCES qiita.study(study_id);


--
-- Name: per_study_tags fk_study_id; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.per_study_tags
    ADD CONSTRAINT fk_study_id FOREIGN KEY (study_id) REFERENCES qiita.study(study_id);


--
-- Name: study_portal fk_study_portal; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_portal
    ADD CONSTRAINT fk_study_portal FOREIGN KEY (study_id) REFERENCES qiita.study(study_id);


--
-- Name: study_portal fk_study_portal_0; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_portal
    ADD CONSTRAINT fk_study_portal_0 FOREIGN KEY (portal_type_id) REFERENCES qiita.portal_type(portal_type_id);


--
-- Name: study_prep_template fk_study_prep_template_pt; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_prep_template
    ADD CONSTRAINT fk_study_prep_template_pt FOREIGN KEY (prep_template_id) REFERENCES qiita.prep_template(prep_template_id);


--
-- Name: study_prep_template fk_study_prep_template_study; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_prep_template
    ADD CONSTRAINT fk_study_prep_template_study FOREIGN KEY (study_id) REFERENCES qiita.study(study_id);


--
-- Name: study fk_study_study_lab_person; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study
    ADD CONSTRAINT fk_study_study_lab_person FOREIGN KEY (lab_person_id) REFERENCES qiita.study_person(study_person_id);


--
-- Name: study fk_study_study_pi_person; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study
    ADD CONSTRAINT fk_study_study_pi_person FOREIGN KEY (principal_investigator_id) REFERENCES qiita.study_person(study_person_id);


--
-- Name: per_study_tags fk_study_tags; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.per_study_tags
    ADD CONSTRAINT fk_study_tags FOREIGN KEY (study_tag) REFERENCES qiita.study_tags(study_tag);


--
-- Name: study fk_study_timeseries_type; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study
    ADD CONSTRAINT fk_study_timeseries_type FOREIGN KEY (timeseries_type_id) REFERENCES qiita.timeseries_type(timeseries_type_id);


--
-- Name: study fk_study_user; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study
    ADD CONSTRAINT fk_study_user FOREIGN KEY (email) REFERENCES qiita.qiita_user(email) ON UPDATE CASCADE;


--
-- Name: study_users fk_study_users_study; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_users
    ADD CONSTRAINT fk_study_users_study FOREIGN KEY (study_id) REFERENCES qiita.study(study_id);


--
-- Name: study_users fk_study_users_user; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.study_users
    ADD CONSTRAINT fk_study_users_user FOREIGN KEY (email) REFERENCES qiita.qiita_user(email) ON UPDATE CASCADE;


--
-- Name: term fk_term_ontology; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.term
    ADD CONSTRAINT fk_term_ontology FOREIGN KEY (ontology_id) REFERENCES qiita.ontology(ontology_id);


--
-- Name: qiita_user fk_user_user_level; Type: FK CONSTRAINT; Schema: qiita
--

ALTER TABLE ONLY qiita.qiita_user
    ADD CONSTRAINT fk_user_user_level FOREIGN KEY (user_level_id) REFERENCES qiita.user_level(user_level_id) ON UPDATE RESTRICT;


--
-- PostgreSQL database dump complete
--
