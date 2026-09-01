\set ON_ERROR_STOP on

-- Separates the API's runtime account from the owner of everything.
--
-- Review finding G-025: `workforce_app` is SUPERUSER, CREATEROLE, CREATEDB and
-- BYPASSRLS, and at the same time the owner of the schema, of all 15 tables
-- and of all 24 functions - ten of which are SECURITY DEFINER and therefore
-- ran with superuser rights. A superuser can also disable the append-only
-- triggers, which is what the entire audit argument rests on. The API used
-- that account for every request.
--
-- The prerequisite was migration 006: the API no longer creates tables at
-- startup, so its account no longer needs DDL.
--
-- **What this migration does not do:**
--
--   * It does not create the roles. Creating a login role means setting a
--     password, and a password has no business in a versioned file. The
--     operator creates `workforce_api` and `workforce_backup` beforehand,
--     with values from the secret store, and this migration refuses to run
--     otherwise.
--   * It does not take SUPERUSER away from `workforce_app`. That is the last
--     step, it is not additive, and it locks the API out if anything below is
--     wrong. It belongs in its own window, after this has been verified:
--
--         ALTER ROLE workforce_app NOSUPERUSER NOCREATEROLE NOCREATEDB NOBYPASSRLS;
--
--     `workforce_app` stays the owner and the migration account either way -
--     migrations need DDL, and DDL on its own schema needs no superuser.
--
-- Grants are given to the *function*, not to the tables behind it. The bus
-- functions are SECURITY DEFINER and run as their owner, so the API can do
-- exactly what they allow and nothing else. That is the property that makes
-- the route allowlist and the append-only triggers binding rather than
-- advisory.

BEGIN;

SELECT set_config('app.actor_id', 'SYSTEM-MIGRATION', true);
SELECT set_config('app.request_id', 'MIG-007-LEAST-PRIVILEGE-ROLES', true);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'workforce_api') THEN
        RAISE EXCEPTION 'MIGRATION_007_ROLE_MISSING: workforce_api. Vorher anlegen: CREATE ROLE workforce_api LOGIN PASSWORD ''<aus dem Secret-Store>'';';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'workforce_backup') THEN
        RAISE EXCEPTION 'MIGRATION_007_ROLE_MISSING: workforce_backup. Vorher anlegen: CREATE ROLE workforce_backup LOGIN PASSWORD ''<aus dem Secret-Store>'';';
    END IF;

    -- A runtime account that is itself privileged would make the rest of this
    -- migration decoration.
    IF EXISTS (SELECT 1 FROM pg_roles
               WHERE rolname IN ('workforce_api', 'workforce_backup')
                 AND (rolsuper OR rolcreaterole OR rolcreatedb OR rolbypassrls)) THEN
        RAISE EXCEPTION 'MIGRATION_007_ROLE_TOO_PRIVILEGED: workforce_api/workforce_backup duerfen weder SUPERUSER noch CREATEROLE, CREATEDB oder BYPASSRLS haben';
    END IF;
END;
$$;

-- --- The API runtime account -----------------------------------------------

GRANT USAGE ON SCHEMA workforce TO workforce_api;

-- Nothing broad: no table privileges in the workforce schema at all. Every
-- bus and knowledge operation goes through a SECURITY DEFINER function.
REVOKE ALL ON ALL TABLES IN SCHEMA workforce FROM workforce_api;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA workforce FROM workforce_api;

-- Granted by name, not by signature, and only for functions that exist.
--
-- The API calls functions from three migrations: the bus functions from 002,
-- the knowledge functions from 004 and bus_record_denial from 005. A static
-- GRANT list would therefore fail whenever one of those gates is still
-- closed - and would chain 007 to exactly the gates that G-031 separated.
-- So: grant what is there, name what is not, and let a later run of this
-- migration pick up the rest.
DO $$
DECLARE
    v_name text;
    v_signature text;
    v_granted integer := 0;
    v_skipped text[] := ARRAY[]::text[];
BEGIN
    FOREACH v_name IN ARRAY ARRAY[
        -- 002_workforce_bus
        'bus_send_message', 'bus_acknowledge_message', 'bus_list_messages',
        'bus_create_task', 'bus_transition_task', 'bus_list_tasks',
        'bus_create_handoff', 'bus_transition_handoff', 'bus_list_handoffs',
        -- 004_knowledge_capability
        'knowledge_create_candidate', 'knowledge_submit_review',
        'knowledge_approve', 'knowledge_revoke', 'knowledge_retrieve',
        'knowledge_record_assessment',
        -- 005_bus_denial_audit
        'bus_record_denial'
    ] LOOP
        FOR v_signature IN
            SELECT format('workforce.%I(%s)', p.proname,
                          pg_get_function_identity_arguments(p.oid))
            FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'workforce' AND p.proname = v_name
        LOOP
            EXECUTE format('GRANT EXECUTE ON FUNCTION %s TO workforce_api', v_signature);
            v_granted := v_granted + 1;
        END LOOP;

        IF NOT EXISTS (
            SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'workforce' AND p.proname = v_name
        ) THEN
            v_skipped := v_skipped || v_name;
        END IF;
    END LOOP;

    RAISE NOTICE 'workforce_api: EXECUTE auf % Funktion(en) erteilt', v_granted;
    IF array_length(v_skipped, 1) IS NOT NULL THEN
        RAISE NOTICE 'noch nicht vorhanden, Migration fehlt: %',
                     array_to_string(v_skipped, ', ');
    END IF;
END;
$$;

-- The two reads the API does directly, both harmless metadata: whether the
-- channel is open, and which migrations are present.
GRANT SELECT ON workforce.bus_channels, workforce.schema_migrations TO workforce_api;

-- The legacy registry in the public schema. These tables have no function
-- layer, so the API needs direct access - but only the four verbs it uses,
-- and never DDL.
GRANT USAGE ON SCHEMA public TO workforce_api;
GRANT SELECT, INSERT, UPDATE ON
    public.roles, public.workers, public.tasks, public.activity_log,
    public.task_notes, public.documents, public.document_versions
TO workforce_api;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO workforce_api;

-- Deliberately no DELETE: nothing in the API deletes, and the project rule is
-- status change instead of deletion.

-- --- The backup account ----------------------------------------------------

GRANT USAGE ON SCHEMA workforce, public TO workforce_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA workforce TO workforce_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO workforce_backup;
-- Read only. A backup account that can write is a backup account that can be
-- used to change what it is supposed to preserve.

INSERT INTO workforce.schema_migrations (
    migration_id,
    description
) VALUES (
    '007_least_privilege_roles',
    'Separates the API runtime and backup accounts from the owning role; grants execute on the bus functions instead of table access'
);

COMMIT;

SELECT
    r.rolname,
    r.rolsuper AS superuser,
    r.rolcreaterole AS createrole,
    r.rolcreatedb AS createdb,
    r.rolbypassrls AS bypass_rls
FROM pg_roles r
WHERE r.rolname IN ('workforce_app', 'workforce_api', 'workforce_backup')
ORDER BY r.rolname;
