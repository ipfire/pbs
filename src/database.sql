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
-- Name: builds_auto_move; Type: TYPE; Schema: public; Owner: pakfire
--

CREATE TYPE builds_auto_move AS ENUM (
    'N',
    'Y'
);


ALTER TYPE builds_auto_move OWNER TO pakfire;

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
    name text NOT NULL
);


ALTER TABLE arches OWNER TO pakfire;

--
-- Name: arches_compat; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE arches_compat (
    native_arch text NOT NULL,
    build_arch text NOT NULL,
    CONSTRAINT arches_compat_unique CHECK ((native_arch <> build_arch))
);


ALTER TABLE arches_compat OWNER TO pakfire;

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
-- Name: builders; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE builders (
    id integer NOT NULL,
    name text NOT NULL,
    passphrase text,
    description text,
    enabled boolean DEFAULT false NOT NULL,
    deleted boolean DEFAULT false NOT NULL,
    loadavg text DEFAULT '0'::character varying NOT NULL,
    testmode boolean DEFAULT true NOT NULL,
    max_jobs bigint DEFAULT 1::bigint NOT NULL,
    pakfire_version text,
    os_name text,
    cpu_model text,
    cpu_count integer DEFAULT 1 NOT NULL,
    cpu_arch text,
    cpu_bogomips double precision,
    memory bigint DEFAULT 0 NOT NULL,
    overload builders_overload DEFAULT 'N'::builders_overload NOT NULL,
    free_space bigint DEFAULT 0 NOT NULL,
    host_key_id text,
    time_created timestamp without time zone DEFAULT now() NOT NULL,
    time_updated timestamp without time zone,
    time_keepalive timestamp without time zone,
    loadavg1 double precision,
    loadavg5 double precision,
    loadavg15 double precision,
    mem_total bigint,
    mem_free bigint,
    swap_total bigint,
    swap_free bigint,
    space_free bigint
);


ALTER TABLE builders OWNER TO pakfire;

--
-- Name: builders_history; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE builders_history (
    id integer NOT NULL,
    builder_id integer NOT NULL,
    action builders_history_action NOT NULL,
    user_id integer,
    "time" timestamp without time zone NOT NULL
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
-- Name: builds; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE builds (
    id integer NOT NULL,
    uuid text NOT NULL,
    pkg_id integer NOT NULL,
    type builds_type DEFAULT 'release'::builds_type NOT NULL,
    state builds_state DEFAULT 'building'::builds_state NOT NULL,
    severity builds_severity,
    message text,
    time_created timestamp without time zone NOT NULL,
    update_year integer,
    update_num integer,
    depends_on integer,
    distro_id integer NOT NULL,
    owner_id integer,
    public builds_public DEFAULT 'Y'::builds_public NOT NULL,
    priority integer DEFAULT 0 NOT NULL,
    auto_move builds_auto_move DEFAULT 'N'::builds_auto_move NOT NULL
);


ALTER TABLE builds OWNER TO pakfire;

--
-- Name: builds_bugs; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE builds_bugs (
    id integer NOT NULL,
    build_id integer NOT NULL,
    bug_id integer NOT NULL
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
    id integer NOT NULL,
    bug_id integer NOT NULL,
    status text,
    resolution text,
    comment text,
    "time" timestamp without time zone NOT NULL,
    error boolean DEFAULT false NOT NULL,
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
    id integer NOT NULL,
    build_id integer NOT NULL,
    user_id integer NOT NULL,
    text text NOT NULL,
    credit integer NOT NULL,
    time_created timestamp without time zone NOT NULL,
    time_updated timestamp without time zone
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
    id integer NOT NULL,
    build_id integer NOT NULL,
    action builds_history_action NOT NULL,
    user_id integer,
    "time" timestamp without time zone NOT NULL,
    bug_id integer
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
    id integer NOT NULL,
    name text NOT NULL,
    epoch integer NOT NULL,
    version text NOT NULL,
    release text NOT NULL,
    type packages_type NOT NULL,
    arch text NOT NULL,
    groups text NOT NULL,
    maintainer text NOT NULL,
    license text NOT NULL,
    url text NOT NULL,
    summary text NOT NULL,
    description text NOT NULL,
    size bigint NOT NULL,
    supported_arches text,
    uuid text NOT NULL,
    commit_id integer,
    build_id text NOT NULL,
    build_host text NOT NULL,
    build_time timestamp without time zone NOT NULL,
    path text NOT NULL,
    filesize bigint NOT NULL,
    hash_sha512 text NOT NULL
);


ALTER TABLE packages OWNER TO pakfire;

--
-- Name: repositories_builds; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE repositories_builds (
    id integer NOT NULL,
    repo_id integer NOT NULL,
    build_id bigint NOT NULL,
    time_added timestamp without time zone NOT NULL
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
          WHERE (p.name = packages.name)
          ORDER BY builds_1.time_created
         LIMIT 1)) AND (builds.state <> ALL (ARRAY['obsolete'::builds_state, 'broken'::builds_state]))));


ALTER TABLE builds_latest OWNER TO pakfire;

--
-- Name: jobs; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE jobs (
    id integer NOT NULL,
    uuid text NOT NULL,
    type jobs_type DEFAULT 'build'::jobs_type NOT NULL,
    build_id integer NOT NULL,
    state jobs_state DEFAULT 'new'::jobs_state NOT NULL,
    arch text NOT NULL,
    time_created timestamp without time zone NOT NULL,
    time_started timestamp without time zone,
    time_finished timestamp without time zone,
    start_not_before timestamp without time zone,
    builder_id integer,
    tries integer DEFAULT 0 NOT NULL,
    aborted_state integer DEFAULT 0 NOT NULL,
    message text
);


ALTER TABLE jobs OWNER TO pakfire;

--
-- Name: builds_times; Type: VIEW; Schema: public; Owner: pakfire
--

CREATE VIEW builds_times AS
 SELECT builds.id AS build_id,
    jobs.arch,
    jobs.type AS job_type,
    (jobs.time_finished - jobs.time_started) AS duration
   FROM (jobs
     LEFT JOIN builds ON ((jobs.build_id = builds.id)))
  WHERE (jobs.state = 'finished'::jobs_state);


ALTER TABLE builds_times OWNER TO pakfire;

--
-- Name: builds_watchers; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE builds_watchers (
    id integer NOT NULL,
    build_id integer NOT NULL,
    user_id integer NOT NULL
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
    id integer NOT NULL,
    name text NOT NULL,
    sname text NOT NULL,
    slogan text NOT NULL,
    description text,
    vendor text NOT NULL,
    contact text,
    tag text NOT NULL,
    deleted boolean DEFAULT false NOT NULL
);


ALTER TABLE distributions OWNER TO pakfire;

--
-- Name: distributions_arches; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE distributions_arches (
    id integer NOT NULL,
    distro_id integer NOT NULL,
    arch text NOT NULL
);


ALTER TABLE distributions_arches OWNER TO pakfire;

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

ALTER SEQUENCE distro_arches_id_seq OWNED BY distributions_arches.id;


--
-- Name: filelists; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE filelists (
    pkg_id integer NOT NULL,
    name text NOT NULL,
    size bigint NOT NULL,
    hash_sha512 text,
    type integer NOT NULL,
    config filelists_config NOT NULL,
    mode integer NOT NULL,
    "user" text NOT NULL,
    "group" text NOT NULL,
    mtime timestamp without time zone NOT NULL,
    capabilities text
);


ALTER TABLE filelists OWNER TO pakfire;

--
-- Name: images_types; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE images_types (
    id integer NOT NULL,
    type text NOT NULL
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
-- Name: jobs_active; Type: VIEW; Schema: public; Owner: pakfire
--

CREATE VIEW jobs_active AS
 SELECT jobs.id,
    jobs.uuid,
    jobs.type,
    jobs.build_id,
    jobs.state,
    jobs.arch,
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
-- Name: jobs_buildroots; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE jobs_buildroots (
    job_id integer NOT NULL,
    tries integer NOT NULL,
    pkg_uuid text NOT NULL,
    pkg_name text NOT NULL
);


ALTER TABLE jobs_buildroots OWNER TO pakfire;

--
-- Name: jobs_history; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE jobs_history (
    job_id integer NOT NULL,
    action jobs_history_action NOT NULL,
    state jobs_history_state,
    user_id integer,
    "time" timestamp without time zone NOT NULL,
    builder_id integer,
    test_job_id integer
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
    id integer NOT NULL,
    job_id integer NOT NULL,
    pkg_id integer NOT NULL
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
 WITH queue AS (
         SELECT jobs.id,
            rank() OVER (ORDER BY jobs.type, builds.priority DESC, jobs.tries, jobs.time_created) AS rank
           FROM (jobs
             LEFT JOIN builds ON ((jobs.build_id = builds.id)))
          WHERE (jobs.state = 'pending'::jobs_state)
        )
 SELECT queue.id AS job_id,
    queue.rank
   FROM queue;


ALTER TABLE jobs_queue OWNER TO pakfire;

--
-- Name: jobs_repos; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE jobs_repos (
    job_id integer NOT NULL,
    repo_id integer NOT NULL
);


ALTER TABLE jobs_repos OWNER TO pakfire;

--
-- Name: keys; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE keys (
    id integer NOT NULL,
    fingerprint text NOT NULL,
    uids text NOT NULL,
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
    id integer NOT NULL,
    key_id integer NOT NULL,
    fingerprint text NOT NULL,
    time_created timestamp without time zone NOT NULL,
    time_expires timestamp without time zone,
    algo text
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
    id integer NOT NULL,
    job_id integer NOT NULL,
    path text NOT NULL,
    filesize bigint NOT NULL,
    hash_sha512 text NOT NULL
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
    id integer NOT NULL,
    hostname text NOT NULL,
    path text NOT NULL,
    owner text,
    contact text,
    deleted boolean DEFAULT false NOT NULL
);


ALTER TABLE mirrors OWNER TO pakfire;

--
-- Name: mirrors_checks; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE mirrors_checks (
    id integer NOT NULL,
    mirror_id integer NOT NULL,
    "timestamp" timestamp without time zone DEFAULT now() NOT NULL,
    response_time double precision,
    http_status integer,
    last_sync_at timestamp without time zone,
    status text DEFAULT 'OK'::text NOT NULL
);


ALTER TABLE mirrors_checks OWNER TO pakfire;

--
-- Name: mirrors_checks_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE mirrors_checks_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE mirrors_checks_id_seq OWNER TO pakfire;

--
-- Name: mirrors_checks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE mirrors_checks_id_seq OWNED BY mirrors_checks.id;


--
-- Name: mirrors_history; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE mirrors_history (
    id integer NOT NULL,
    mirror_id integer NOT NULL,
    action mirrors_history_action NOT NULL,
    user_id integer,
    "time" timestamp without time zone NOT NULL
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
    pkg_id integer NOT NULL,
    type packages_deps_type NOT NULL,
    what text NOT NULL
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
    id integer NOT NULL,
    name text NOT NULL,
    critical_path packages_properties_critical_path DEFAULT 'N'::packages_properties_critical_path NOT NULL,
    priority integer DEFAULT 0 NOT NULL
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
    id integer NOT NULL,
    path text NOT NULL
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
-- Name: relation_sizes; Type: VIEW; Schema: public; Owner: pakfire
--

CREATE VIEW relation_sizes AS
 SELECT c.relname AS relation,
    pg_size_pretty(pg_relation_size((c.oid)::regclass)) AS size
   FROM (pg_class c
     LEFT JOIN pg_namespace n ON ((n.oid = c.relnamespace)))
  WHERE (n.nspname <> ALL (ARRAY['pg_catalog'::name, 'information_schema'::name]))
  ORDER BY pg_relation_size((c.oid)::regclass) DESC;


ALTER TABLE relation_sizes OWNER TO pakfire;

--
-- Name: repositories; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE repositories (
    id integer NOT NULL,
    name text NOT NULL,
    type repositories_type DEFAULT 'testing'::repositories_type NOT NULL,
    description text NOT NULL,
    distro_id integer NOT NULL,
    parent_id integer,
    key_id integer,
    mirrored boolean DEFAULT false NOT NULL,
    enabled_for_builds boolean DEFAULT false NOT NULL,
    score_needed integer DEFAULT 0 NOT NULL,
    last_update timestamp without time zone,
    time_min integer DEFAULT 0 NOT NULL,
    time_max integer DEFAULT 0 NOT NULL,
    update_started timestamp without time zone,
    update_ended timestamp without time zone,
    deleted boolean DEFAULT false NOT NULL
);


ALTER TABLE repositories OWNER TO pakfire;

--
-- Name: repositories_aux; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE repositories_aux (
    id integer NOT NULL,
    name text NOT NULL,
    description text,
    url text NOT NULL,
    distro_id integer NOT NULL,
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
    from_repo_id integer,
    to_repo_id integer,
    user_id integer,
    "time" timestamp without time zone NOT NULL
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
    id integer NOT NULL,
    session_id text NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    valid_until timestamp without time zone DEFAULT (now() + '7 days'::interval) NOT NULL,
    user_id integer NOT NULL,
    impersonated_user_id integer,
    address inet,
    user_agent text,
    CONSTRAINT sessions_impersonation_check CHECK (((impersonated_user_id IS NULL) OR (user_id <> impersonated_user_id)))
);


ALTER TABLE sessions OWNER TO pakfire;

--
-- Name: sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: pakfire
--

CREATE SEQUENCE sessions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE sessions_id_seq OWNER TO pakfire;

--
-- Name: sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: pakfire
--

ALTER SEQUENCE sessions_id_seq OWNED BY sessions.id;


--
-- Name: settings; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE settings (
    k text NOT NULL,
    v text NOT NULL
);


ALTER TABLE settings OWNER TO pakfire;

--
-- Name: slogans; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE slogans (
    id integer NOT NULL,
    message text NOT NULL
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
    id integer NOT NULL,
    name text NOT NULL,
    identifier text NOT NULL,
    url text NOT NULL,
    gitweb text,
    revision text NOT NULL,
    branch text NOT NULL,
    updated timestamp without time zone,
    distro_id integer NOT NULL
);


ALTER TABLE sources OWNER TO pakfire;

--
-- Name: sources_commits; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE sources_commits (
    id integer NOT NULL,
    source_id integer NOT NULL,
    revision text NOT NULL,
    author text NOT NULL,
    committer text NOT NULL,
    subject text NOT NULL,
    body text NOT NULL,
    date timestamp without time zone NOT NULL,
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
    id integer NOT NULL,
    uuid text NOT NULL,
    user_id integer,
    builder_id integer,
    filename text NOT NULL,
    hash text NOT NULL,
    size bigint NOT NULL,
    progress bigint DEFAULT 0 NOT NULL,
    finished uploads_finished DEFAULT 'N'::uploads_finished NOT NULL,
    time_started timestamp without time zone DEFAULT now() NOT NULL,
    time_finished timestamp without time zone
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
    id integer NOT NULL,
    frm text NOT NULL,
    "to" text NOT NULL,
    subject text NOT NULL,
    text text NOT NULL,
    time_added timestamp without time zone DEFAULT now() NOT NULL
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
    id integer NOT NULL,
    name text NOT NULL,
    realname text,
    passphrase text NOT NULL,
    state users_state NOT NULL,
    locale text,
    timezone text,
    activated users_activated DEFAULT 'N'::users_activated NOT NULL,
    activation_code text,
    deleted users_deleted DEFAULT 'N'::users_deleted NOT NULL,
    registered timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE users OWNER TO pakfire;

--
-- Name: users_emails; Type: TABLE; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE TABLE users_emails (
    id integer NOT NULL,
    user_id integer NOT NULL,
    email text NOT NULL,
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
    id integer NOT NULL,
    user_id integer NOT NULL,
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

ALTER TABLE ONLY distributions_arches ALTER COLUMN id SET DEFAULT nextval('distro_arches_id_seq'::regclass);


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

ALTER TABLE ONLY mirrors_checks ALTER COLUMN id SET DEFAULT nextval('mirrors_checks_id_seq'::regclass);


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

ALTER TABLE ONLY sessions ALTER COLUMN id SET DEFAULT nextval('sessions_id_seq'::regclass);


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
-- Name: arches_compat_unique; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY arches_compat
    ADD CONSTRAINT arches_compat_unique UNIQUE (native_arch, build_arch);


--
-- Name: arches_name; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY arches
    ADD CONSTRAINT arches_name UNIQUE (name);


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

ALTER TABLE ONLY distributions_arches
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
-- Name: jobs_packages_unique; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY jobs_packages
    ADD CONSTRAINT jobs_packages_unique UNIQUE (job_id, pkg_id);


--
-- Name: mirrors_checks_pkey; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY mirrors_checks
    ADD CONSTRAINT mirrors_checks_pkey PRIMARY KEY (id);


--
-- Name: sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- Name: sessions_session_id_key; Type: CONSTRAINT; Schema: public; Owner: pakfire; Tablespace: 
--

ALTER TABLE ONLY sessions
    ADD CONSTRAINT sessions_session_id_key UNIQUE (session_id);


--
-- Name: arches_compat_native_arch; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX arches_compat_native_arch ON arches_compat USING btree (native_arch);


--
-- Name: builders_name; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE UNIQUE INDEX builders_name ON builders USING btree (name) WHERE (deleted IS FALSE);


--
-- Name: builds_watchers_build_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX builds_watchers_build_id ON builds_watchers USING btree (build_id);


--
-- Name: distributions_arches_distro_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX distributions_arches_distro_id ON distributions_arches USING btree (distro_id);


--
-- Name: distributions_sname; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE UNIQUE INDEX distributions_sname ON distributions USING btree (sname) WHERE (deleted IS FALSE);


--
-- Name: filelists_name; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX filelists_name ON filelists USING btree (name);


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
-- Name: idx_2198132_name; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198132_name ON packages USING btree (name);


--
-- Name: idx_2198132_type; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198132_type ON packages USING btree (type);


--
-- Name: idx_2198132_uuid; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198132_uuid ON packages USING btree (uuid);


--
-- Name: idx_2198139_pkg_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX idx_2198139_pkg_id ON packages_deps USING btree (pkg_id);


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
-- Name: jobs_arch; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX jobs_arch ON jobs USING btree (arch);


--
-- Name: jobs_buildroots_pkg_uuid; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX jobs_buildroots_pkg_uuid ON jobs_buildroots USING btree (pkg_uuid);


--
-- Name: mirrors_checks_sort; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX mirrors_checks_sort ON mirrors_checks USING btree (mirror_id, "timestamp");

ALTER TABLE mirrors_checks CLUSTER ON mirrors_checks_sort;


--
-- Name: repositories_builds_repo_id; Type: INDEX; Schema: public; Owner: pakfire; Tablespace: 
--

CREATE INDEX repositories_builds_repo_id ON repositories_builds USING btree (repo_id);


--
-- Name: on_update_current_timestamp; Type: TRIGGER; Schema: public; Owner: pakfire
--

CREATE TRIGGER on_update_current_timestamp BEFORE UPDATE ON sources FOR EACH ROW EXECUTE PROCEDURE on_update_current_timestamp_sources();


--
-- Name: arches_compat_build_arch; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY arches_compat
    ADD CONSTRAINT arches_compat_build_arch FOREIGN KEY (build_arch) REFERENCES arches(name);


--
-- Name: builders_history_builder_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builders_history
    ADD CONSTRAINT builders_history_builder_id FOREIGN KEY (builder_id) REFERENCES builders(id);


--
-- Name: builders_history_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builders_history
    ADD CONSTRAINT builders_history_user_id FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: builds_bug_build_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builds_bugs
    ADD CONSTRAINT builds_bug_build_id FOREIGN KEY (build_id) REFERENCES builds(id);


--
-- Name: builds_comments_build_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builds_comments
    ADD CONSTRAINT builds_comments_build_id FOREIGN KEY (build_id) REFERENCES builds(id);


--
-- Name: builds_comments_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builds_comments
    ADD CONSTRAINT builds_comments_user_id FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: builds_depends_on; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builds
    ADD CONSTRAINT builds_depends_on FOREIGN KEY (depends_on) REFERENCES builds(id);


--
-- Name: builds_distro_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builds
    ADD CONSTRAINT builds_distro_id FOREIGN KEY (distro_id) REFERENCES distributions(id);


--
-- Name: builds_history_build_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builds_history
    ADD CONSTRAINT builds_history_build_id FOREIGN KEY (build_id) REFERENCES builds(id);


--
-- Name: builds_history_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builds_history
    ADD CONSTRAINT builds_history_user_id FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: builds_owner_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builds
    ADD CONSTRAINT builds_owner_id FOREIGN KEY (owner_id) REFERENCES users(id);


--
-- Name: builds_pkg_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builds
    ADD CONSTRAINT builds_pkg_id FOREIGN KEY (pkg_id) REFERENCES packages(id);


--
-- Name: builds_watchers_build_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builds_watchers
    ADD CONSTRAINT builds_watchers_build_id FOREIGN KEY (build_id) REFERENCES builds(id);


--
-- Name: builds_watchers_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY builds_watchers
    ADD CONSTRAINT builds_watchers_user_id FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: distributions_arches_arch; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY distributions_arches
    ADD CONSTRAINT distributions_arches_arch FOREIGN KEY (arch) REFERENCES arches(name);


--
-- Name: distro_arches_distro_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY distributions_arches
    ADD CONSTRAINT distro_arches_distro_id FOREIGN KEY (distro_id) REFERENCES distributions(id);


--
-- Name: filelists_pkg_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY filelists
    ADD CONSTRAINT filelists_pkg_id FOREIGN KEY (pkg_id) REFERENCES packages(id);


--
-- Name: jobs_arch; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_arch FOREIGN KEY (arch) REFERENCES arches(name);


--
-- Name: jobs_build_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_build_id FOREIGN KEY (build_id) REFERENCES builds(id);


--
-- Name: jobs_builder_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_builder_id FOREIGN KEY (builder_id) REFERENCES builders(id);


--
-- Name: jobs_buildroots_job_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY jobs_buildroots
    ADD CONSTRAINT jobs_buildroots_job_id FOREIGN KEY (job_id) REFERENCES jobs(id);


--
-- Name: jobs_history_builder_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY jobs_history
    ADD CONSTRAINT jobs_history_builder_id FOREIGN KEY (builder_id) REFERENCES builders(id);


--
-- Name: jobs_history_job_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY jobs_history
    ADD CONSTRAINT jobs_history_job_id FOREIGN KEY (job_id) REFERENCES jobs(id);


--
-- Name: jobs_history_test_job_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY jobs_history
    ADD CONSTRAINT jobs_history_test_job_id FOREIGN KEY (test_job_id) REFERENCES jobs(id);


--
-- Name: jobs_history_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY jobs_history
    ADD CONSTRAINT jobs_history_user_id FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: jobs_packaged_job_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY jobs_packages
    ADD CONSTRAINT jobs_packaged_job_id FOREIGN KEY (job_id) REFERENCES jobs(id);


--
-- Name: jobs_packages_pkg_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY jobs_packages
    ADD CONSTRAINT jobs_packages_pkg_id FOREIGN KEY (pkg_id) REFERENCES packages(id);


--
-- Name: jobs_repos_job_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY jobs_repos
    ADD CONSTRAINT jobs_repos_job_id FOREIGN KEY (job_id) REFERENCES jobs(id);


--
-- Name: jobs_repos_repo_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY jobs_repos
    ADD CONSTRAINT jobs_repos_repo_id FOREIGN KEY (repo_id) REFERENCES repositories(id);


--
-- Name: keys_subkeys_key_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY keys_subkeys
    ADD CONSTRAINT keys_subkeys_key_id FOREIGN KEY (key_id) REFERENCES keys(id);


--
-- Name: logfiles_job_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY logfiles
    ADD CONSTRAINT logfiles_job_id FOREIGN KEY (job_id) REFERENCES jobs(id);


--
-- Name: mirrors_checks_mirror_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY mirrors_checks
    ADD CONSTRAINT mirrors_checks_mirror_id FOREIGN KEY (mirror_id) REFERENCES mirrors(id);


--
-- Name: mirrors_history_mirror_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY mirrors_history
    ADD CONSTRAINT mirrors_history_mirror_id FOREIGN KEY (mirror_id) REFERENCES mirrors(id);


--
-- Name: mirrors_history_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY mirrors_history
    ADD CONSTRAINT mirrors_history_user_id FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: packages_arch; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY packages
    ADD CONSTRAINT packages_arch FOREIGN KEY (arch) REFERENCES arches(name);


--
-- Name: packages_commit_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY packages
    ADD CONSTRAINT packages_commit_id FOREIGN KEY (commit_id) REFERENCES sources_commits(id);


--
-- Name: packages_deps_pkg_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY packages_deps
    ADD CONSTRAINT packages_deps_pkg_id FOREIGN KEY (pkg_id) REFERENCES packages(id);


--
-- Name: repositories_aux_distro_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY repositories_aux
    ADD CONSTRAINT repositories_aux_distro_id FOREIGN KEY (distro_id) REFERENCES distributions(id);


--
-- Name: repositories_builds_build_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY repositories_builds
    ADD CONSTRAINT repositories_builds_build_id FOREIGN KEY (build_id) REFERENCES builds(id);


--
-- Name: repositories_builds_repo_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY repositories_builds
    ADD CONSTRAINT repositories_builds_repo_id FOREIGN KEY (repo_id) REFERENCES repositories(id);


--
-- Name: repositories_distro_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY repositories
    ADD CONSTRAINT repositories_distro_id FOREIGN KEY (distro_id) REFERENCES distributions(id);


--
-- Name: repositories_history_build_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY repositories_history
    ADD CONSTRAINT repositories_history_build_id FOREIGN KEY (build_id) REFERENCES builds(id);


--
-- Name: repositories_history_from_repo_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY repositories_history
    ADD CONSTRAINT repositories_history_from_repo_id FOREIGN KEY (from_repo_id) REFERENCES repositories(id);


--
-- Name: repositories_history_to_repo_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY repositories_history
    ADD CONSTRAINT repositories_history_to_repo_id FOREIGN KEY (to_repo_id) REFERENCES repositories(id);


--
-- Name: repositories_history_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY repositories_history
    ADD CONSTRAINT repositories_history_user_id FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: repositories_key_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY repositories
    ADD CONSTRAINT repositories_key_id FOREIGN KEY (key_id) REFERENCES keys(id);


--
-- Name: repositories_parent_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY repositories
    ADD CONSTRAINT repositories_parent_id FOREIGN KEY (parent_id) REFERENCES repositories(id);


--
-- Name: sessions_impersonated_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY sessions
    ADD CONSTRAINT sessions_impersonated_user_id FOREIGN KEY (impersonated_user_id) REFERENCES users(id);


--
-- Name: sessions_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY sessions
    ADD CONSTRAINT sessions_user_id FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: sources_commits_source_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY sources_commits
    ADD CONSTRAINT sources_commits_source_id FOREIGN KEY (source_id) REFERENCES sources(id);


--
-- Name: sources_distro_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY sources
    ADD CONSTRAINT sources_distro_id FOREIGN KEY (distro_id) REFERENCES distributions(id);


--
-- Name: uploads_builder_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY uploads
    ADD CONSTRAINT uploads_builder_id FOREIGN KEY (builder_id) REFERENCES builders(id);


--
-- Name: uploads_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY uploads
    ADD CONSTRAINT uploads_user_id FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: users_emails_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY users_emails
    ADD CONSTRAINT users_emails_user_id FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: users_permissions_user_id; Type: FK CONSTRAINT; Schema: public; Owner: pakfire
--

ALTER TABLE ONLY users_permissions
    ADD CONSTRAINT users_permissions_user_id FOREIGN KEY (user_id) REFERENCES users(id);


--
-- PostgreSQL database dump complete
--

