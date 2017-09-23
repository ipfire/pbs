--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

--
-- Name: arches_binary; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE arches_binary AS ENUM (
    'Y',
    'N'
);


ALTER TYPE arches_binary OWNER TO pakfire;

--
-- Name: builders_arches_enabled; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE builders_arches_enabled AS ENUM (
    'Y',
    'N'
);


ALTER TYPE builders_arches_enabled OWNER TO pakfire;

--
-- Name: builders_build_release; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE builders_build_release AS ENUM (
    'Y',
    'N'
);


ALTER TYPE builders_build_release OWNER TO pakfire;

--
-- Name: builders_build_scratch; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE builders_build_scratch AS ENUM (
    'Y',
    'N'
);


ALTER TYPE builders_build_scratch OWNER TO pakfire;

--
-- Name: builders_build_test; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE builders_build_test AS ENUM (
    'Y',
    'N'
);


ALTER TYPE builders_build_test OWNER TO pakfire;

--
-- Name: builders_deleted; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE builders_deleted AS ENUM (
    'Y',
    'N'
);


ALTER TYPE builders_deleted OWNER TO pakfire;

--
-- Name: builders_disabled; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE builders_disabled AS ENUM (
    'Y',
    'N'
);


ALTER TYPE builders_disabled OWNER TO pakfire;

--
-- Name: builders_history_action; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE builders_history_action AS ENUM (
    'created',
    'enabled',
    'disabled',
    'deleted'
);


ALTER TYPE builders_history_action OWNER TO pakfire;

--
-- Name: builders_overload; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE builders_overload AS ENUM (
    'Y',
    'N'
);


ALTER TYPE builders_overload OWNER TO pakfire;

--
-- Name: builders_status; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE builders_status AS ENUM (
    'enabled',
    'disabled',
    'deleted'
);


ALTER TYPE builders_status OWNER TO pakfire;

--
-- Name: builds_auto_move; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE builds_auto_move AS ENUM (
    'N',
    'Y'
);


ALTER TYPE builds_auto_move OWNER TO pakfire;

--
-- Name: builds_bugs_updates_error; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE builds_bugs_updates_error AS ENUM (
    'N',
    'Y'
);


ALTER TYPE builds_bugs_updates_error OWNER TO pakfire;

--
-- Name: builds_history_action; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE builds_history_action AS ENUM (
    'created',
    'bug_added',
    'bug_removed'
);


ALTER TYPE builds_history_action OWNER TO pakfire;

--
-- Name: builds_public; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE builds_public AS ENUM (
    'Y',
    'N'
);


ALTER TYPE builds_public OWNER TO pakfire;

--
-- Name: builds_severity; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE builds_severity AS ENUM (
    'security update',
    'bugfix update',
    'enhancement',
    'new package'
);


ALTER TYPE builds_severity OWNER TO pakfire;

--
-- Name: builds_state; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE builds_state AS ENUM (
    'building',
    'testing',
    'stable',
    'obsolete',
    'broken'
);


ALTER TYPE builds_state OWNER TO pakfire;

--
-- Name: builds_type; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE builds_type AS ENUM (
    'release',
    'scratch'
);


ALTER TYPE builds_type OWNER TO pakfire;

--
-- Name: filelists_config; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE filelists_config AS ENUM (
    'Y',
    'N'
);


ALTER TYPE filelists_config OWNER TO pakfire;

--
-- Name: jobs_history_action; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE jobs_history_action AS ENUM (
    'created',
    'state_change',
    'reset',
    'schedule_rebuild',
    'schedule_test_job'
);


ALTER TYPE jobs_history_action OWNER TO pakfire;

--
-- Name: jobs_history_state; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE jobs_history_state AS ENUM (
    'new',
    'pending',
    'running',
    'finished',
    'dispatching',
    'uploading',
    'failed',
    'temporary_failed',
    'dependency_error',
    'aborted',
    'download_error',
    'deleted'
);


ALTER TYPE jobs_history_state OWNER TO pakfire;

--
-- Name: jobs_state; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE jobs_state AS ENUM (
    'new',
    'pending',
    'running',
    'finished',
    'dispatching',
    'uploading',
    'failed',
    'aborted',
    'temporary_failed',
    'dependency_error',
    'download_error',
    'deleted'
);


ALTER TYPE jobs_state OWNER TO pakfire;

--
-- Name: jobs_type; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE jobs_type AS ENUM (
    'build',
    'test'
);


ALTER TYPE jobs_type OWNER TO pakfire;

--
-- Name: mirrors_check_status; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE mirrors_check_status AS ENUM (
    'UNKNOWN',
    'UP',
    'DOWN'
);


ALTER TYPE mirrors_check_status OWNER TO pakfire;

--
-- Name: mirrors_history_action; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE mirrors_history_action AS ENUM (
    'created',
    'enabled',
    'disabled',
    'deleted'
);


ALTER TYPE mirrors_history_action OWNER TO pakfire;

--
-- Name: mirrors_status; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE mirrors_status AS ENUM (
    'enabled',
    'disabled',
    'deleted'
);


ALTER TYPE mirrors_status OWNER TO pakfire;

--
-- Name: packages_deps_type; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE packages_deps_type AS ENUM (
    'requires',
    'prerequires',
    'provides',
    'conflicts',
    'obsoletes',
    'suggests',
    'recommends'
);


ALTER TYPE packages_deps_type OWNER TO pakfire;

--
-- Name: packages_properties_critical_path; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE packages_properties_critical_path AS ENUM (
    'N',
    'Y'
);


ALTER TYPE packages_properties_critical_path OWNER TO pakfire;

--
-- Name: packages_type; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE packages_type AS ENUM (
    'source',
    'binary'
);


ALTER TYPE packages_type OWNER TO pakfire;

--
-- Name: repositories_aux_status; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE repositories_aux_status AS ENUM (
    'enabled',
    'disabled'
);


ALTER TYPE repositories_aux_status OWNER TO pakfire;

--
-- Name: repositories_enabled_for_builds; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE repositories_enabled_for_builds AS ENUM (
    'N',
    'Y'
);


ALTER TYPE repositories_enabled_for_builds OWNER TO pakfire;

--
-- Name: repositories_history_action; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE repositories_history_action AS ENUM (
    'added',
    'removed',
    'moved'
);


ALTER TYPE repositories_history_action OWNER TO pakfire;

--
-- Name: repositories_mirrored; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE repositories_mirrored AS ENUM (
    'N',
    'Y'
);


ALTER TYPE repositories_mirrored OWNER TO pakfire;

--
-- Name: repositories_type; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE repositories_type AS ENUM (
    'testing',
    'unstable',
    'stable'
);


ALTER TYPE repositories_type OWNER TO pakfire;

--
-- Name: sources_commits_state; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE sources_commits_state AS ENUM (
    'pending',
    'running',
    'finished',
    'failed'
);


ALTER TYPE sources_commits_state OWNER TO pakfire;

--
-- Name: uploads_finished; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE uploads_finished AS ENUM (
    'N',
    'Y'
);


ALTER TYPE uploads_finished OWNER TO pakfire;

--
-- Name: users_activated; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE users_activated AS ENUM (
    'Y',
    'N'
);


ALTER TYPE users_activated OWNER TO pakfire;

--
-- Name: users_deleted; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE users_deleted AS ENUM (
    'Y',
    'N'
);


ALTER TYPE users_deleted OWNER TO pakfire;

--
-- Name: users_emails_primary; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE users_emails_primary AS ENUM (
    'N',
    'Y'
);


ALTER TYPE users_emails_primary OWNER TO pakfire;

--
-- Name: users_permissions_create_scratch_builds; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE users_permissions_create_scratch_builds AS ENUM (
    'Y',
    'N'
);


ALTER TYPE users_permissions_create_scratch_builds OWNER TO pakfire;

--
-- Name: users_permissions_maintain_builders; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE users_permissions_maintain_builders AS ENUM (
    'N',
    'Y'
);


ALTER TYPE users_permissions_maintain_builders OWNER TO pakfire;

--
-- Name: users_permissions_manage_critical_path; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE users_permissions_manage_critical_path AS ENUM (
    'N',
    'Y'
);


ALTER TYPE users_permissions_manage_critical_path OWNER TO pakfire;

--
-- Name: users_permissions_manage_mirrors; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE users_permissions_manage_mirrors AS ENUM (
    'N',
    'Y'
);


ALTER TYPE users_permissions_manage_mirrors OWNER TO pakfire;

--
-- Name: users_permissions_vote; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE users_permissions_vote AS ENUM (
    'N',
    'Y'
);


ALTER TYPE users_permissions_vote OWNER TO pakfire;

--
-- Name: users_state; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE users_state AS ENUM (
    'user',
    'tester',
    'admin'
);


ALTER TYPE users_state OWNER TO pakfire;

--
-- Name: on_update_current_timestamp_sources(); Type: FUNCTION; Schema: public; Owner: pakfire
--

CREATE FUNCTION on_update_current_timestamp_sources() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
   NEW.updated = now();
   RETURN NEW;
END;
$$;


ALTER FUNCTION public.on_update_current_timestamp_sources() OWNER TO pakfire;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: arches; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE arches (
    id integer NOT NULL,
    name character varying(32) NOT NULL,
    prio bigint DEFAULT 0::bigint NOT NULL,
    "binary" arches_binary DEFAULT 'Y'::arches_binary NOT NULL,
    platform character varying(8)
);


ALTER TABLE arches OWNER TO pakfire;

--
-- Name: arches_compat; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE arches_compat (
    host_arch character varying(8) NOT NULL,
    build_arch character varying(8) NOT NULL
);


ALTER TABLE arches_compat OWNER TO pakfire;

--
-- Name: builders; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE builders (
    id bigint NOT NULL,
    name character varying(255) NOT NULL,
    passphrase character varying(255),
    description text,
    status builders_status DEFAULT 'disabled'::builders_status NOT NULL,
    disabled builders_disabled DEFAULT 'Y'::builders_disabled NOT NULL,
    loadavg character varying(32) DEFAULT '0'::character varying NOT NULL,
    arches character varying(128),
    build_release builders_build_release DEFAULT 'N'::builders_build_release NOT NULL,
    build_scratch builders_build_scratch DEFAULT 'N'::builders_build_scratch NOT NULL,
    build_test builders_build_test DEFAULT 'N'::builders_build_test NOT NULL,
    max_jobs bigint DEFAULT 1::bigint NOT NULL,
    pakfire_version character varying(32),
    os_name character varying(64),
    cpu_model character varying(255),
    cpu_count smallint DEFAULT 1::smallint NOT NULL,
    cpu_arch character varying(8),
    cpu_bogomips double precision,
    memory numeric DEFAULT 0::numeric NOT NULL,
    overload builders_overload DEFAULT 'N'::builders_overload NOT NULL,
    free_space numeric DEFAULT 0::numeric NOT NULL,
    host_key_id character varying(64),
    deleted builders_deleted DEFAULT 'N'::builders_deleted NOT NULL,
    time_created timestamp with time zone NOT NULL,
    time_updated timestamp with time zone,
    time_keepalive timestamp with time zone,
    loadavg1 double precision,
    loadavg5 double precision,
    loadavg15 double precision,
    mem_total numeric,
    mem_free numeric,
    swap_total numeric,
    swap_free numeric,
    space_free numeric
);


ALTER TABLE builders OWNER TO pakfire;

--
-- Name: arches_builders; Type: VIEW; Schema: public; Owner: pakfire
--

CREATE VIEW arches_builders AS
 SELECT arches_compat.build_arch AS arch,
    builders.id AS builder_id
   FROM (arches_compat
     LEFT JOIN builders ON (((arches_compat.host_arch)::text = (builders.cpu_arch)::text)));


ALTER TABLE arches_builders OWNER TO pakfire;

--
-- Name: arches_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE arches_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE arches_id_seq OWNER TO pakfire;

--
-- Name: arches_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE arches_id_seq OWNED BY arches.id;


--
-- Name: builders_arches; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE builders_arches (
    id bigint NOT NULL,
    builder_id bigint NOT NULL,
    arch_id bigint NOT NULL,
    enabled builders_arches_enabled DEFAULT 'Y'::builders_arches_enabled NOT NULL
);


ALTER TABLE builders_arches OWNER TO pakfire;

--
-- Name: builders_arches_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE builders_arches_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE builders_arches_id_seq OWNER TO pakfire;

--
-- Name: builders_arches_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE builders_arches_id_seq OWNED BY builders_arches.id;


--
-- Name: builders_history; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE builders_history (
    id bigint NOT NULL,
    builder_id bigint NOT NULL,
    action builders_history_action NOT NULL,
    user_id bigint,
    "time" timestamp with time zone NOT NULL
);


ALTER TABLE builders_history OWNER TO pakfire;

--
-- Name: builders_history_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE builders_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE builders_history_id_seq OWNER TO pakfire;

--
-- Name: builders_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE builders_history_id_seq OWNED BY builders_history.id;


--
-- Name: builders_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE builders_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE builders_id_seq OWNER TO pakfire;

--
-- Name: builders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE builders_id_seq OWNED BY builders.id;


--
-- Name: jobs; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE jobs (
    id bigint NOT NULL,
    uuid character varying(40) NOT NULL,
    type jobs_type DEFAULT 'build'::jobs_type NOT NULL,
    build_id bigint NOT NULL,
    state jobs_state DEFAULT 'new'::jobs_state NOT NULL,
    arch_id bigint NOT NULL,
    time_created timestamp with time zone NOT NULL,
    time_started timestamp with time zone,
    time_finished timestamp with time zone,
    start_not_before timestamp with time zone,
    builder_id bigint,
    tries bigint DEFAULT 0::bigint NOT NULL,
    aborted_state smallint DEFAULT 0::smallint NOT NULL,
    message text
);


ALTER TABLE jobs OWNER TO pakfire;

--
-- Name: jobs_active; Type: VIEW; Schema: public; Owner: pakfire
--

CREATE VIEW jobs_active AS
 SELECT jobs.id,
    jobs.uuid,
    jobs.type,
    jobs.build_id,
    jobs.state,
    jobs.arch_id,
    jobs.time_created,
    jobs.time_started,
    jobs.time_finished,
    jobs.start_not_before,
    jobs.builder_id,
    jobs.tries,
    jobs.aborted_state,
    jobs.message
   FROM jobs
  WHERE (jobs.state = ANY (ARRAY['dispatching'::jobs_state, 'running'::jobs_state, 'uploading'::jobs_state]))
  ORDER BY jobs.time_started;


ALTER TABLE jobs_active OWNER TO pakfire;

--
-- Name: builders_ready; Type: VIEW; Schema: public; Owner: pakfire
--

CREATE VIEW builders_ready AS
 SELECT builders.id AS builder_id,
    builders.cpu_arch AS builder_arch,
    builders.build_release,
    builders.build_scratch,
    builders.build_test
   FROM builders
  WHERE (((builders.status = 'enabled'::builders_status) AND (builders.time_keepalive >= (now() - '00:05:00'::interval))) AND (builders.max_jobs > ( SELECT count(0) AS count
           FROM jobs_active
          WHERE (jobs_active.builder_id = builders.id))))
  ORDER BY ( SELECT count(0) AS count
           FROM jobs_active
          WHERE (jobs_active.builder_id = builders.id)), builders.cpu_bogomips DESC;


ALTER TABLE builders_ready OWNER TO pakfire;

--
-- Name: builds; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE builds (
    id bigint NOT NULL,
    uuid character varying(40) NOT NULL,
    pkg_id bigint NOT NULL,
    type builds_type DEFAULT 'release'::builds_type NOT NULL,
    state builds_state DEFAULT 'building'::builds_state NOT NULL,
    severity builds_severity,
    message text,
    time_created timestamp with time zone NOT NULL,
    update_year bigint,
    update_num bigint,
    depends_on bigint,
    distro_id bigint NOT NULL,
    owner_id bigint,
    public builds_public DEFAULT 'Y'::builds_public NOT NULL,
    priority bigint DEFAULT 0::bigint NOT NULL,
    auto_move builds_auto_move DEFAULT 'N'::builds_auto_move NOT NULL
);


ALTER TABLE builds OWNER TO pakfire;

--
-- Name: builds_bugs; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE builds_bugs (
    id bigint NOT NULL,
    build_id bigint NOT NULL,
    bug_id bigint NOT NULL
);


ALTER TABLE builds_bugs OWNER TO pakfire;

--
-- Name: builds_bugs_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE builds_bugs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE builds_bugs_id_seq OWNER TO pakfire;

--
-- Name: builds_bugs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE builds_bugs_id_seq OWNED BY builds_bugs.id;


--
-- Name: builds_bugs_updates; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE builds_bugs_updates (
    id bigint NOT NULL,
    bug_id bigint NOT NULL,
    status character varying(32),
    resolution character varying(32),
    comment text,
    "time" timestamp with time zone NOT NULL,
    error builds_bugs_updates_error DEFAULT 'N'::builds_bugs_updates_error NOT NULL,
    error_msg text
);


ALTER TABLE builds_bugs_updates OWNER TO pakfire;

--
-- Name: builds_bugs_updates_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE builds_bugs_updates_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE builds_bugs_updates_id_seq OWNER TO pakfire;

--
-- Name: builds_bugs_updates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE builds_bugs_updates_id_seq OWNED BY builds_bugs_updates.id;


--
-- Name: builds_comments; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE builds_comments (
    id bigint NOT NULL,
    build_id bigint NOT NULL,
    user_id bigint NOT NULL,
    text text NOT NULL,
    credit smallint NOT NULL,
    time_created timestamp with time zone NOT NULL,
    time_updated timestamp with time zone
);


ALTER TABLE builds_comments OWNER TO pakfire;

--
-- Name: builds_comments_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE builds_comments_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE builds_comments_id_seq OWNER TO pakfire;

--
-- Name: builds_comments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE builds_comments_id_seq OWNED BY builds_comments.id;


--
-- Name: builds_history; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE builds_history (
    id bigint NOT NULL,
    build_id bigint NOT NULL,
    action builds_history_action NOT NULL,
    user_id bigint,
    "time" timestamp with time zone NOT NULL,
    bug_id bigint
);


ALTER TABLE builds_history OWNER TO pakfire;

--
-- Name: builds_history_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE builds_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE builds_history_id_seq OWNER TO pakfire;

--
-- Name: builds_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE builds_history_id_seq OWNED BY builds_history.id;


--
-- Name: builds_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE builds_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE builds_id_seq OWNER TO pakfire;

--
-- Name: builds_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE builds_id_seq OWNED BY builds.id;


--
-- Name: packages; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE packages (
    id bigint NOT NULL,
    name character varying(128) NOT NULL,
    epoch bigint NOT NULL,
    version character varying(128) NOT NULL,
    release character varying(32) NOT NULL,
    type packages_type NOT NULL,
    arch smallint NOT NULL,
    groups character varying(1024) NOT NULL,
    maintainer character varying(128) NOT NULL,
    license character varying(128) NOT NULL,
    url character varying(1024) NOT NULL,
    summary text NOT NULL,
    description text NOT NULL,
    size bigint NOT NULL,
    supported_arches character varying(64),
    uuid character varying(40) NOT NULL,
    commit_id bigint,
    build_id character varying(40) NOT NULL,
    build_host character varying(128) NOT NULL,
    build_time timestamp with time zone NOT NULL,
    path character varying(255) NOT NULL,
    filesize bigint NOT NULL,
    hash_sha512 character varying(140) NOT NULL
);


ALTER TABLE packages OWNER TO pakfire;

--
-- Name: repositories_builds; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE repositories_builds (
    id bigint NOT NULL,
    repo_id bigint NOT NULL,
    build_id bigint NOT NULL,
    time_added timestamp with time zone NOT NULL
);


ALTER TABLE repositories_builds OWNER TO pakfire;

--
-- Name: builds_latest; Type: VIEW; Schema: public; Owner: pakfire
--

CREATE VIEW builds_latest AS
 SELECT builds.id AS build_id,
    builds.type AS build_type,
    builds.state AS build_state,
    packages.name AS package_name,
    builds.public
   FROM (builds
     LEFT JOIN packages ON ((builds.pkg_id = packages.id)))
  WHERE ((builds.id IN ( SELECT repositories_builds.build_id
           FROM repositories_builds)) OR ((builds.time_created >= ( SELECT builds_1.time_created
           FROM ((builds builds_1
             LEFT JOIN repositories_builds ON ((builds_1.id = repositories_builds.build_id)))
             LEFT JOIN packages p ON ((builds_1.pkg_id = p.id)))
          WHERE ((p.name)::text = (packages.name)::text)
          ORDER BY builds_1.time_created
         LIMIT 1)) AND (builds.state <> ALL (ARRAY['obsolete'::builds_state, 'broken'::builds_state]))));


ALTER TABLE builds_latest OWNER TO pakfire;

--
-- Name: builds_times; Type: VIEW; Schema: public; Owner: pakfire
--

CREATE VIEW builds_times AS
 SELECT builds.id AS build_id,
    arches.name AS arch,
    arches.platform,
    jobs.type AS job_type,
    (jobs.time_finished - jobs.time_started) AS duration
   FROM (((jobs
     LEFT JOIN builds ON ((jobs.build_id = builds.id)))
     LEFT JOIN packages ON ((builds.pkg_id = packages.id)))
     LEFT JOIN arches ON ((jobs.arch_id = arches.id)))
  WHERE (jobs.state = 'finished'::jobs_state);


ALTER TABLE builds_times OWNER TO pakfire;

--
-- Name: builds_watchers; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE builds_watchers (
    id bigint NOT NULL,
    build_id bigint NOT NULL,
    user_id bigint NOT NULL
);


ALTER TABLE builds_watchers OWNER TO pakfire;

--
-- Name: builds_watchers_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE builds_watchers_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE builds_watchers_id_seq OWNER TO pakfire;

--
-- Name: builds_watchers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE builds_watchers_id_seq OWNED BY builds_watchers.id;


--
-- Name: distributions; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE distributions (
    id bigint NOT NULL,
    name character varying(64) NOT NULL,
    sname character varying(64) NOT NULL,
    slogan character varying(255) NOT NULL,
    description text,
    vendor character varying(64) NOT NULL,
    contact character varying(128),
    tag character varying(4) NOT NULL
);


ALTER TABLE distributions OWNER TO pakfire;

--
-- Name: distributions_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE distributions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE distributions_id_seq OWNER TO pakfire;

--
-- Name: distributions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE distributions_id_seq OWNED BY distributions.id;


--
-- Name: distro_arches; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE distro_arches (
    id bigint NOT NULL,
    distro_id bigint NOT NULL,
    arch_id bigint NOT NULL
);


ALTER TABLE distro_arches OWNER TO pakfire;

--
-- Name: distro_arches_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE distro_arches_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE distro_arches_id_seq OWNER TO pakfire;

--
-- Name: distro_arches_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE distro_arches_id_seq OWNED BY distro_arches.id;


--
-- Name: filelists; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE filelists (
    pkg_id bigint NOT NULL,
    name character varying(256) NOT NULL,
    size bigint NOT NULL,
    hash_sha512 character varying(130),
    type smallint NOT NULL,
    config filelists_config NOT NULL,
    mode bigint NOT NULL,
    "user" character varying(16) NOT NULL,
    "group" character varying(16) NOT NULL,
    mtime timestamp with time zone NOT NULL,
    capabilities character varying(64)
);


ALTER TABLE filelists OWNER TO pakfire;

--
-- Name: images_types; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE images_types (
    id bigint NOT NULL,
    type character varying(12) NOT NULL
);


ALTER TABLE images_types OWNER TO pakfire;

--
-- Name: images_types_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE images_types_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE images_types_id_seq OWNER TO pakfire;

--
-- Name: images_types_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE images_types_id_seq OWNED BY images_types.id;


--
-- Name: jobs_buildroots; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE jobs_buildroots (
    job_id bigint NOT NULL,
    tries smallint NOT NULL,
    pkg_uuid character varying(40) NOT NULL,
    pkg_name character varying(1024) NOT NULL
);


ALTER TABLE jobs_buildroots OWNER TO pakfire;

--
-- Name: jobs_history; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE jobs_history (
    job_id bigint NOT NULL,
    action jobs_history_action NOT NULL,
    state jobs_history_state,
    user_id bigint,
    "time" timestamp with time zone NOT NULL,
    builder_id bigint,
    test_job_id bigint
);


ALTER TABLE jobs_history OWNER TO pakfire;

--
-- Name: jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE jobs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE jobs_id_seq OWNER TO pakfire;

--
-- Name: jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE jobs_id_seq OWNED BY jobs.id;


--
-- Name: jobs_packages; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE jobs_packages (
    id bigint NOT NULL,
    job_id bigint NOT NULL,
    pkg_id bigint NOT NULL
);


ALTER TABLE jobs_packages OWNER TO pakfire;

--
-- Name: jobs_packages_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE jobs_packages_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE jobs_packages_id_seq OWNER TO pakfire;

--
-- Name: jobs_packages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE jobs_packages_id_seq OWNED BY jobs_packages.id;


--
-- Name: jobs_queue; Type: VIEW; Schema: public; Owner: pakfire
--

CREATE VIEW jobs_queue AS
 SELECT jobs.id,
    arches.name AS arch,
    ( SELECT builders_ready.builder_id
           FROM builders_ready
          WHERE (builders_ready.builder_id IN ( SELECT arches_builders.builder_id
                   FROM arches_builders
                  WHERE (((arches_builders.arch)::text = (arches.name)::text) AND
                        CASE
                            WHEN ((builds.type = 'release'::builds_type) AND (jobs.type = 'build'::jobs_type)) THEN (builders_ready.build_release = 'Y'::builders_build_release)
                            WHEN ((builds.type = 'scratch'::builds_type) AND (jobs.type = 'build'::jobs_type)) THEN (builders_ready.build_scratch = 'Y'::builders_build_scratch)
                            WHEN (jobs.type = 'test'::jobs_type) THEN (builders_ready.build_test = 'Y'::builders_build_test)
                            ELSE NULL::boolean
                        END)))
         LIMIT 1) AS designated_builder_id
   FROM ((jobs
     LEFT JOIN arches ON ((jobs.arch_id = arches.id)))
     LEFT JOIN builds ON ((jobs.build_id = builds.id)))
  WHERE ((jobs.state = ANY (ARRAY['pending'::jobs_state, 'new'::jobs_state])) AND ((jobs.start_not_before IS NULL) OR (jobs.start_not_before <= now())))
  ORDER BY
        CASE
            WHEN (jobs.type = 'build'::jobs_type) THEN 0
            WHEN (jobs.type = 'test'::jobs_type) THEN 1
            ELSE NULL::integer
        END, builds.priority DESC, jobs.tries, jobs.time_created;


ALTER TABLE jobs_queue OWNER TO pakfire;

--
-- Name: jobs_repos; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE jobs_repos (
    job_id bigint NOT NULL,
    repo_id bigint NOT NULL
);


ALTER TABLE jobs_repos OWNER TO pakfire;

--
-- Name: jobs_waiting; Type: VIEW; Schema: public; Owner: pakfire
--

CREATE VIEW jobs_waiting AS
 SELECT jobs_queue.id,
    (now() - jobs.time_created) AS time_waiting
   FROM (jobs_queue
     LEFT JOIN jobs ON ((jobs_queue.id = jobs.id)))
  WHERE (jobs.start_not_before IS NULL)
UNION
 SELECT jobs_queue.id,
    (now() - jobs.start_not_before) AS time_waiting
   FROM (jobs_queue
     LEFT JOIN jobs ON ((jobs_queue.id = jobs.id)))
  WHERE (jobs.start_not_before IS NOT NULL);


ALTER TABLE jobs_waiting OWNER TO pakfire;

--
-- Name: keys; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE keys (
    id bigint NOT NULL,
    fingerprint character varying(64) NOT NULL,
    uids character varying(255) NOT NULL,
    data text NOT NULL
);


ALTER TABLE keys OWNER TO pakfire;

--
-- Name: keys_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE keys_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE keys_id_seq OWNER TO pakfire;

--
-- Name: keys_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE keys_id_seq OWNED BY keys.id;


--
-- Name: keys_subkeys; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE keys_subkeys (
    id bigint NOT NULL,
    key_id bigint NOT NULL,
    fingerprint character varying(64) NOT NULL,
    time_created timestamp with time zone NOT NULL,
    time_expires timestamp with time zone,
    algo character varying(16)
);


ALTER TABLE keys_subkeys OWNER TO pakfire;

--
-- Name: keys_subkeys_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE keys_subkeys_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE keys_subkeys_id_seq OWNER TO pakfire;

--
-- Name: keys_subkeys_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE keys_subkeys_id_seq OWNED BY keys_subkeys.id;


--
-- Name: logfiles; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE logfiles (
    id bigint NOT NULL,
    job_id bigint NOT NULL,
    path character varying(255) NOT NULL,
    filesize bigint NOT NULL,
    hash_sha512 character varying(140) NOT NULL
);


ALTER TABLE logfiles OWNER TO pakfire;

--
-- Name: logfiles_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE logfiles_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE logfiles_id_seq OWNER TO pakfire;

--
-- Name: logfiles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE logfiles_id_seq OWNED BY logfiles.id;


--
-- Name: mirrors; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE mirrors (
    id bigint NOT NULL,
    hostname character varying(128) NOT NULL,
    path character varying(128) NOT NULL,
    owner character varying(128),
    contact character varying(128),
    status mirrors_status DEFAULT 'disabled'::mirrors_status NOT NULL,
    check_status mirrors_check_status DEFAULT 'UNKNOWN'::mirrors_check_status NOT NULL,
    last_check timestamp with time zone
);


ALTER TABLE mirrors OWNER TO pakfire;

--
-- Name: mirrors_history; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE mirrors_history (
    id bigint NOT NULL,
    mirror_id bigint NOT NULL,
    action mirrors_history_action NOT NULL,
    user_id bigint,
    "time" timestamp with time zone NOT NULL
);


ALTER TABLE mirrors_history OWNER TO pakfire;

--
-- Name: mirrors_history_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE mirrors_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE mirrors_history_id_seq OWNER TO pakfire;

--
-- Name: mirrors_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE mirrors_history_id_seq OWNED BY mirrors_history.id;


--
-- Name: mirrors_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE mirrors_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE mirrors_id_seq OWNER TO pakfire;

--
-- Name: mirrors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE mirrors_id_seq OWNED BY mirrors.id;


--
-- Name: packages_deps; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE packages_deps (
    pkg_id bigint NOT NULL,
    type packages_deps_type NOT NULL,
    what character varying(1024) NOT NULL
);


ALTER TABLE packages_deps OWNER TO pakfire;

--
-- Name: packages_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE packages_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE packages_id_seq OWNER TO pakfire;

--
-- Name: packages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE packages_id_seq OWNED BY packages.id;


--
-- Name: packages_properties; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE packages_properties (
    id bigint NOT NULL,
    name character varying(128) NOT NULL,
    critical_path packages_properties_critical_path DEFAULT 'N'::packages_properties_critical_path NOT NULL,
    priority smallint DEFAULT 0::smallint NOT NULL
);


ALTER TABLE packages_properties OWNER TO pakfire;

--
-- Name: packages_properties_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE packages_properties_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE packages_properties_id_seq OWNER TO pakfire;

--
-- Name: packages_properties_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE packages_properties_id_seq OWNED BY packages_properties.id;


--
-- Name: queue_delete; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE queue_delete (
    id bigint NOT NULL,
    path character varying(1024) NOT NULL
);


ALTER TABLE queue_delete OWNER TO pakfire;

--
-- Name: queue_delete_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE queue_delete_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE queue_delete_id_seq OWNER TO pakfire;

--
-- Name: queue_delete_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE queue_delete_id_seq OWNED BY queue_delete.id;


--
-- Name: repositories; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE repositories (
    id bigint NOT NULL,
    name character varying(64) NOT NULL,
    type repositories_type DEFAULT 'testing'::repositories_type NOT NULL,
    description text NOT NULL,
    distro_id bigint NOT NULL,
    parent_id bigint,
    key_id bigint,
    mirrored repositories_mirrored DEFAULT 'N'::repositories_mirrored NOT NULL,
    enabled_for_builds repositories_enabled_for_builds DEFAULT 'N'::repositories_enabled_for_builds NOT NULL,
    score_needed bigint DEFAULT 0::bigint NOT NULL,
    last_update timestamp with time zone,
    time_min bigint DEFAULT 0::bigint NOT NULL,
    time_max bigint DEFAULT 0::bigint NOT NULL,
    update_started timestamp with time zone,
    update_ended timestamp with time zone
);


ALTER TABLE repositories OWNER TO pakfire;

--
-- Name: repositories_aux; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE repositories_aux (
    id bigint NOT NULL,
    name character varying(32) NOT NULL,
    description text,
    url character varying(128) NOT NULL,
    distro_id bigint NOT NULL,
    status repositories_aux_status DEFAULT 'disabled'::repositories_aux_status NOT NULL
);


ALTER TABLE repositories_aux OWNER TO pakfire;

--
-- Name: repositories_aux_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE repositories_aux_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE repositories_aux_id_seq OWNER TO pakfire;

--
-- Name: repositories_aux_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE repositories_aux_id_seq OWNED BY repositories_aux.id;


--
-- Name: repositories_builds_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE repositories_builds_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE repositories_builds_id_seq OWNER TO pakfire;

--
-- Name: repositories_builds_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE repositories_builds_id_seq OWNED BY repositories_builds.id;


--
-- Name: repositories_history; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE repositories_history (
    build_id bigint NOT NULL,
    action repositories_history_action NOT NULL,
    from_repo_id bigint,
    to_repo_id bigint,
    user_id bigint,
    "time" timestamp with time zone NOT NULL
);


ALTER TABLE repositories_history OWNER TO pakfire;

--
-- Name: repositories_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE repositories_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE repositories_id_seq OWNER TO pakfire;

--
-- Name: repositories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE repositories_id_seq OWNED BY repositories.id;


--
-- Name: sessions; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE sessions (
    session_id character varying(64) NOT NULL,
    user_id bigint NOT NULL,
    impersonated_user_id bigint,
    creation_time timestamp with time zone,
    valid_until timestamp with time zone,
    from_address character varying(255)
);


ALTER TABLE sessions OWNER TO pakfire;

--
-- Name: settings; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE settings (
    k character varying(255) NOT NULL,
    v character varying(1024) NOT NULL
);


ALTER TABLE settings OWNER TO pakfire;

--
-- Name: slogans; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE slogans (
    id bigint NOT NULL,
    message character varying(64) NOT NULL
);


ALTER TABLE slogans OWNER TO pakfire;

--
-- Name: slogans_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE slogans_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE slogans_id_seq OWNER TO pakfire;

--
-- Name: slogans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE slogans_id_seq OWNED BY slogans.id;


--
-- Name: sources; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE sources (
    id bigint NOT NULL,
    name character varying(128) NOT NULL,
    identifier character varying(128) NOT NULL,
    url character varying(1024) NOT NULL,
    gitweb character varying(255),
    revision character varying(40) NOT NULL,
    branch character varying(32) NOT NULL,
    updated timestamp with time zone,
    distro_id bigint NOT NULL
);


ALTER TABLE sources OWNER TO pakfire;

--
-- Name: sources_commits; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE sources_commits (
    id bigint NOT NULL,
    source_id bigint NOT NULL,
    revision character varying(40) NOT NULL,
    author character varying(1024) NOT NULL,
    committer character varying(1024) NOT NULL,
    subject character varying(1024) NOT NULL,
    body text NOT NULL,
    date timestamp with time zone NOT NULL,
    state sources_commits_state DEFAULT 'pending'::sources_commits_state NOT NULL
);


ALTER TABLE sources_commits OWNER TO pakfire;

--
-- Name: sources_commits_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE sources_commits_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE sources_commits_id_seq OWNER TO pakfire;

--
-- Name: sources_commits_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE sources_commits_id_seq OWNED BY sources_commits.id;


--
-- Name: sources_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE sources_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE sources_id_seq OWNER TO pakfire;

--
-- Name: sources_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE sources_id_seq OWNED BY sources.id;


--
-- Name: uploads; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE uploads (
    id bigint NOT NULL,
    uuid character varying(40) NOT NULL,
    user_id bigint,
    builder_id bigint,
    filename character varying(1024) NOT NULL,
    hash character varying(40) NOT NULL,
    size bigint NOT NULL,
    progress bigint DEFAULT 0::bigint NOT NULL,
    finished uploads_finished DEFAULT 'N'::uploads_finished NOT NULL,
    time_started timestamp with time zone DEFAULT now() NOT NULL,
    time_finished timestamp with time zone
);


ALTER TABLE uploads OWNER TO pakfire;

--
-- Name: uploads_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE uploads_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE uploads_id_seq OWNER TO pakfire;

--
-- Name: uploads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE uploads_id_seq OWNED BY uploads.id;


--
-- Name: user_messages; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE user_messages (
    id bigint NOT NULL,
    frm character varying(255) NOT NULL,
    "to" character varying(2048) NOT NULL,
    subject character varying(1024) NOT NULL,
    text text NOT NULL,
    time_added timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE user_messages OWNER TO pakfire;

--
-- Name: user_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE user_messages_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_messages_id_seq OWNER TO pakfire;

--
-- Name: user_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE user_messages_id_seq OWNED BY user_messages.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE users (
    id bigint NOT NULL,
    name character varying(32) NOT NULL,
    realname character varying(255),
    passphrase character varying(153) NOT NULL,
    state users_state NOT NULL,
    locale character varying(8),
    timezone character varying(64),
    activated users_activated DEFAULT 'N'::users_activated NOT NULL,
    activation_code character varying(20),
    deleted users_deleted DEFAULT 'N'::users_deleted NOT NULL,
    registered timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE users OWNER TO pakfire;

--
-- Name: users_emails; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE users_emails (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    email character varying(128) NOT NULL,
    "primary" users_emails_primary DEFAULT 'N'::users_emails_primary NOT NULL
);


ALTER TABLE users_emails OWNER TO pakfire;

--
-- Name: users_emails_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE users_emails_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE users_emails_id_seq OWNER TO pakfire;

--
-- Name: users_emails_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE users_emails_id_seq OWNED BY users_emails.id;


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE users_id_seq OWNER TO pakfire;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE users_id_seq OWNED BY users.id;


--
-- Name: users_permissions; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE users_permissions (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    create_scratch_builds users_permissions_create_scratch_builds DEFAULT 'N'::users_permissions_create_scratch_builds NOT NULL,
    maintain_builders users_permissions_maintain_builders DEFAULT 'N'::users_permissions_maintain_builders NOT NULL,
    manage_critical_path users_permissions_manage_critical_path DEFAULT 'N'::users_permissions_manage_critical_path NOT NULL,
    manage_mirrors users_permissions_manage_mirrors DEFAULT 'N'::users_permissions_manage_mirrors NOT NULL,
    vote users_permissions_vote DEFAULT 'N'::users_permissions_vote NOT NULL
);


ALTER TABLE users_permissions OWNER TO pakfire;

--
-- Name: users_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE users_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE users_permissions_id_seq OWNER TO pakfire;

--
-- Name: users_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE users_permissions_id_seq OWNED BY users_permissions.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY arches ALTER COLUMN id SET DEFAULT nextval('arches_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builders ALTER COLUMN id SET DEFAULT nextval('builders_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builders_arches ALTER COLUMN id SET DEFAULT nextval('builders_arches_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builders_history ALTER COLUMN id SET DEFAULT nextval('builders_history_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builds ALTER COLUMN id SET DEFAULT nextval('builds_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builds_bugs ALTER COLUMN id SET DEFAULT nextval('builds_bugs_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builds_bugs_updates ALTER COLUMN id SET DEFAULT nextval('builds_bugs_updates_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builds_comments ALTER COLUMN id SET DEFAULT nextval('builds_comments_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builds_history ALTER COLUMN id SET DEFAULT nextval('builds_history_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builds_watchers ALTER COLUMN id SET DEFAULT nextval('builds_watchers_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY distributions ALTER COLUMN id SET DEFAULT nextval('distributions_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY distro_arches ALTER COLUMN id SET DEFAULT nextval('distro_arches_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY images_types ALTER COLUMN id SET DEFAULT nextval('images_types_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY jobs ALTER COLUMN id SET DEFAULT nextval('jobs_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY jobs_packages ALTER COLUMN id SET DEFAULT nextval('jobs_packages_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY keys ALTER COLUMN id SET DEFAULT nextval('keys_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY keys_subkeys ALTER COLUMN id SET DEFAULT nextval('keys_subkeys_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY logfiles ALTER COLUMN id SET DEFAULT nextval('logfiles_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY mirrors ALTER COLUMN id SET DEFAULT nextval('mirrors_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY mirrors_history ALTER COLUMN id SET DEFAULT nextval('mirrors_history_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY packages ALTER COLUMN id SET DEFAULT nextval('packages_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY packages_properties ALTER COLUMN id SET DEFAULT nextval('packages_properties_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY queue_delete ALTER COLUMN id SET DEFAULT nextval('queue_delete_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY repositories ALTER COLUMN id SET DEFAULT nextval('repositories_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY repositories_aux ALTER COLUMN id SET DEFAULT nextval('repositories_aux_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY repositories_builds ALTER COLUMN id SET DEFAULT nextval('repositories_builds_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY slogans ALTER COLUMN id SET DEFAULT nextval('slogans_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY sources ALTER COLUMN id SET DEFAULT nextval('sources_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY sources_commits ALTER COLUMN id SET DEFAULT nextval('sources_commits_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY uploads ALTER COLUMN id SET DEFAULT nextval('uploads_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY user_messages ALTER COLUMN id SET DEFAULT nextval('user_messages_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY users ALTER COLUMN id SET DEFAULT nextval('users_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY users_emails ALTER COLUMN id SET DEFAULT nextval('users_emails_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY users_permissions ALTER COLUMN id SET DEFAULT nextval('users_permissions_id_seq'::regclass);


--
-- Name: idx_2197943_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY arches
    ADD CONSTRAINT idx_2197943_primary PRIMARY KEY (id);


--
-- Name: idx_2197954_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY builders
    ADD CONSTRAINT idx_2197954_primary PRIMARY KEY (id);


--
-- Name: idx_2197975_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY builders_arches
    ADD CONSTRAINT idx_2197975_primary PRIMARY KEY (id);


--
-- Name: idx_2197982_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY builders_history
    ADD CONSTRAINT idx_2197982_primary PRIMARY KEY (id);


--
-- Name: idx_2197988_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY builds
    ADD CONSTRAINT idx_2197988_primary PRIMARY KEY (id);


--
-- Name: idx_2198002_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY builds_bugs
    ADD CONSTRAINT idx_2198002_primary PRIMARY KEY (id);


--
-- Name: idx_2198008_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY builds_bugs_updates
    ADD CONSTRAINT idx_2198008_primary PRIMARY KEY (id);


--
-- Name: idx_2198018_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY builds_comments
    ADD CONSTRAINT idx_2198018_primary PRIMARY KEY (id);


--
-- Name: idx_2198027_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY builds_history
    ADD CONSTRAINT idx_2198027_primary PRIMARY KEY (id);


--
-- Name: idx_2198033_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY builds_watchers
    ADD CONSTRAINT idx_2198033_primary PRIMARY KEY (id);


--
-- Name: idx_2198039_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY distributions
    ADD CONSTRAINT idx_2198039_primary PRIMARY KEY (id);


--
-- Name: idx_2198048_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY distro_arches
    ADD CONSTRAINT idx_2198048_primary PRIMARY KEY (id);


--
-- Name: idx_2198057_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY images_types
    ADD CONSTRAINT idx_2198057_primary PRIMARY KEY (id);


--
-- Name: idx_2198063_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT idx_2198063_primary PRIMARY KEY (id);


--
-- Name: idx_2198085_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY jobs_packages
    ADD CONSTRAINT idx_2198085_primary PRIMARY KEY (id);


--
-- Name: idx_2198094_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY keys
    ADD CONSTRAINT idx_2198094_primary PRIMARY KEY (id);


--
-- Name: idx_2198103_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY keys_subkeys
    ADD CONSTRAINT idx_2198103_primary PRIMARY KEY (id);


--
-- Name: idx_2198109_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY logfiles
    ADD CONSTRAINT idx_2198109_primary PRIMARY KEY (id);


--
-- Name: idx_2198115_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY mirrors
    ADD CONSTRAINT idx_2198115_primary PRIMARY KEY (id);


--
-- Name: idx_2198126_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY mirrors_history
    ADD CONSTRAINT idx_2198126_primary PRIMARY KEY (id);


--
-- Name: idx_2198132_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY packages
    ADD CONSTRAINT idx_2198132_primary PRIMARY KEY (id);


--
-- Name: idx_2198147_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY packages_properties
    ADD CONSTRAINT idx_2198147_primary PRIMARY KEY (id);


--
-- Name: idx_2198155_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY queue_delete
    ADD CONSTRAINT idx_2198155_primary PRIMARY KEY (id);


--
-- Name: idx_2198164_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY repositories
    ADD CONSTRAINT idx_2198164_primary PRIMARY KEY (id);


--
-- Name: idx_2198179_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY repositories_aux
    ADD CONSTRAINT idx_2198179_primary PRIMARY KEY (id);


--
-- Name: idx_2198189_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY repositories_builds
    ADD CONSTRAINT idx_2198189_primary PRIMARY KEY (id);


--
-- Name: idx_2198207_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY slogans
    ADD CONSTRAINT idx_2198207_primary PRIMARY KEY (id);


--
-- Name: idx_2198213_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY sources
    ADD CONSTRAINT idx_2198213_primary PRIMARY KEY (id);


--
-- Name: idx_2198222_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY sources_commits
    ADD CONSTRAINT idx_2198222_primary PRIMARY KEY (id);


--
-- Name: idx_2198232_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY uploads
    ADD CONSTRAINT idx_2198232_primary PRIMARY KEY (id);


--
-- Name: idx_2198244_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT idx_2198244_primary PRIMARY KEY (id);


--
-- Name: idx_2198256_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY users_emails
    ADD CONSTRAINT idx_2198256_primary PRIMARY KEY (id);


--
-- Name: idx_2198263_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY users_permissions
    ADD CONSTRAINT idx_2198263_primary PRIMARY KEY (id);


--
-- Name: idx_2198274_primary; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY user_messages
    ADD CONSTRAINT idx_2198274_primary PRIMARY KEY (id);


--
-- Name: idx_2197949_host_arch; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2197949_host_arch ON arches_compat USING btree (host_arch);


--
-- Name: idx_2197982_builder_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2197982_builder_id ON builders_history USING btree (builder_id);


--
-- Name: idx_2197988_pkg_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2197988_pkg_id ON builds USING btree (pkg_id);


--
-- Name: idx_2197988_state; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2197988_state ON builds USING btree (state);


--
-- Name: idx_2197988_type; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2197988_type ON builds USING btree (type);


--
-- Name: idx_2197988_uuid; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE UNIQUE INDEX idx_2197988_uuid ON builds USING btree (uuid);


--
-- Name: idx_2198002_build_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE UNIQUE INDEX idx_2198002_build_id ON builds_bugs USING btree (build_id, bug_id);


--
-- Name: idx_2198018_build_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198018_build_id ON builds_comments USING btree (build_id);


--
-- Name: idx_2198018_user_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198018_user_id ON builds_comments USING btree (user_id);


--
-- Name: idx_2198052_pkg_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198052_pkg_id ON filelists USING btree (pkg_id);


--
-- Name: idx_2198063_arch_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198063_arch_id ON jobs USING btree (arch_id);


--
-- Name: idx_2198063_build_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198063_build_id ON jobs USING btree (build_id);


--
-- Name: idx_2198063_state; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198063_state ON jobs USING btree (state);


--
-- Name: idx_2198063_time_finished; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198063_time_finished ON jobs USING btree (time_finished);


--
-- Name: idx_2198063_type; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198063_type ON jobs USING btree (type);


--
-- Name: idx_2198063_uuid; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE UNIQUE INDEX idx_2198063_uuid ON jobs USING btree (uuid);


--
-- Name: idx_2198074_job_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198074_job_id ON jobs_buildroots USING btree (job_id);


--
-- Name: idx_2198080_job_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198080_job_id ON jobs_history USING btree (job_id);


--
-- Name: idx_2198089_job_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE UNIQUE INDEX idx_2198089_job_id ON jobs_repos USING btree (job_id, repo_id);


--
-- Name: idx_2198094_fingerprint; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE UNIQUE INDEX idx_2198094_fingerprint ON keys USING btree (fingerprint);


--
-- Name: idx_2198132_epoch; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198132_epoch ON packages USING btree (epoch);


--
-- Name: idx_2198132_name; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198132_name ON packages USING btree (name);


--
-- Name: idx_2198132_release; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198132_release ON packages USING btree (release);


--
-- Name: idx_2198132_type; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198132_type ON packages USING btree (type);


--
-- Name: idx_2198132_uuid; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198132_uuid ON packages USING btree (uuid);


--
-- Name: idx_2198132_version; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198132_version ON packages USING btree (version);


--
-- Name: idx_2198139_pkg_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198139_pkg_id ON packages_deps USING btree (pkg_id);


--
-- Name: idx_2198139_type; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198139_type ON packages_deps USING btree (type);


--
-- Name: idx_2198147_name; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE UNIQUE INDEX idx_2198147_name ON packages_properties USING btree (name);


--
-- Name: idx_2198189_build_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE UNIQUE INDEX idx_2198189_build_id ON repositories_builds USING btree (build_id);


--
-- Name: idx_2198193_build_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198193_build_id ON repositories_history USING btree (build_id);


--
-- Name: idx_2198196_session_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE UNIQUE INDEX idx_2198196_session_id ON sessions USING btree (session_id);


--
-- Name: idx_2198199_k; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE UNIQUE INDEX idx_2198199_k ON settings USING btree (k);


--
-- Name: idx_2198213_identifier; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE UNIQUE INDEX idx_2198213_identifier ON sources USING btree (identifier);


--
-- Name: idx_2198222_revision; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198222_revision ON sources_commits USING btree (revision);


--
-- Name: idx_2198232_uuid; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE UNIQUE INDEX idx_2198232_uuid ON uploads USING btree (uuid);


--
-- Name: idx_2198244_name; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE UNIQUE INDEX idx_2198244_name ON users USING btree (name);


--
-- Name: idx_2198256_email; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE UNIQUE INDEX idx_2198256_email ON users_emails USING btree (email);


--
-- Name: idx_2198256_user_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198256_user_id ON users_emails USING btree (user_id);


--
-- Name: on_update_current_timestamp; Type: TRIGGER; Schema: public; Owner: pakfire
--

CREATE TRIGGER on_update_current_timestamp BEFORE UPDATE ON sources FOR EACH ROW EXECUTE PROCEDURE on_update_current_timestamp_sources();


--
-- PostgreSQL database dump complete
--

