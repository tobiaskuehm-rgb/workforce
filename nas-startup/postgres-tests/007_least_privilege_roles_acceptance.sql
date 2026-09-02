\set ON_ERROR_STOP on

-- Acceptance test for migration 007_least_privilege_roles (review finding G-047).
--
-- 007 is the migration the whole audit argument rests on: the API's runtime
-- account may call the bus functions and nothing else, and the functions are
-- SECURITY DEFINER, so the route allowlist and the append-only triggers are
-- binding rather than advisory.
--
-- It ran in production on 2026-09-01 and had no acceptance test. What proved
-- it was the rollout window's own negative test - and that one was wrong on
-- its first attempt (G-044: five arguments instead of thirteen, so PostgreSQL
-- answered "function does not exist", exactly what it would have answered if
-- 007 had never run). This file exists so the proof can be repeated by anybody
-- at any time instead of living in a window nobody can re-enter.
--
-- Reads the catalog only, inside a transaction that is rolled back. Safe
-- against production.

BEGIN;

DO $$
DECLARE
    v_row record;
    v_offen text;
    v_count integer;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM workforce.schema_migrations
        WHERE migration_id = '007_least_privilege_roles'
    ) THEN
        RAISE EXCEPTION 'ACCEPTANCE_007_MIGRATION_MISSING';
    END IF;

    -- 1. Both roles exist and carry none of the four attributes. 007 refuses
    --    to run otherwise, but a later ALTER ROLE would not be noticed by the
    --    migration - only by a check like this one.
    FOR v_row IN
        SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolbypassrls
        FROM pg_roles WHERE rolname IN ('workforce_api', 'workforce_backup')
    LOOP
        IF v_row.rolsuper OR v_row.rolcreaterole
           OR v_row.rolcreatedb OR v_row.rolbypassrls THEN
            RAISE EXCEPTION 'ACCEPTANCE_007_ROLE_TOO_PRIVILEGED: %', v_row.rolname;
        END IF;
    END LOOP;

    SELECT count(*) INTO v_count
    FROM pg_roles WHERE rolname IN ('workforce_api', 'workforce_backup');
    IF v_count <> 2 THEN
        RAISE EXCEPTION 'ACCEPTANCE_007_ROLE_MISSING: % von 2 vorhanden', v_count;
    END IF;

    -- 2. The heart of G-035: PostgreSQL grants EXECUTE on every new function
    --    to PUBLIC by default. If that default is back, granting EXECUTE to
    --    workforce_api adds nothing and every role can call the bus.
    SELECT string_agg(p.proname, ', ' ORDER BY p.proname) INTO v_offen
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'workforce'
      AND has_function_privilege('public', p.oid, 'EXECUTE');
    IF v_offen IS NOT NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_007_PUBLIC_MAY_EXECUTE: %', v_offen;
    END IF;

    -- 3. And the other half: workforce_api may still call what it needs. A
    --    revocation that also removed the API's own access would be "secure"
    --    and broken.
    IF NOT has_function_privilege('workforce_api',
            'workforce.bus_record_denial(text,text,text,text,text,text,text,integer)',
            'EXECUTE') THEN
        RAISE EXCEPTION 'ACCEPTANCE_007_API_CANNOT_RECORD_DENIAL';
    END IF;

    SELECT count(*) INTO v_count
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'workforce'
      AND p.proname LIKE 'bus\_%'
      AND has_function_privilege('workforce_api', p.oid, 'EXECUTE');
    IF v_count < 5 THEN
        RAISE EXCEPTION 'ACCEPTANCE_007_API_LOST_BUS_FUNCTIONS: nur %', v_count;
    END IF;

    -- 4. Write-only auditing. The API records refusals and must not be able to
    --    read them back - proven in the rollout window, kept here.
    IF has_table_privilege('workforce_api', 'workforce.bus_denials', 'SELECT') THEN
        RAISE EXCEPTION 'ACCEPTANCE_007_API_MAY_READ_DENIALS';
    END IF;

    -- 5. What it may read: the two tables it needs to answer /bus/v1/status.
    IF NOT has_table_privilege('workforce_api', 'workforce.bus_channels', 'SELECT')
       OR NOT has_table_privilege('workforce_api', 'workforce.schema_migrations', 'SELECT') THEN
        RAISE EXCEPTION 'ACCEPTANCE_007_API_CANNOT_READ_STATUS_TABLES';
    END IF;

    -- 6. The API has no direct access to the bus tables. Everything goes
    --    through the SECURITY DEFINER functions or not at all.
    IF has_table_privilege('workforce_api', 'workforce.bus_messages', 'SELECT')
       OR has_table_privilege('workforce_api', 'workforce.bus_messages', 'INSERT') THEN
        RAISE EXCEPTION 'ACCEPTANCE_007_API_REACHES_BUS_TABLES_DIRECTLY';
    END IF;

    -- 7. The backup role reads everything and writes nothing. The first
    --    rollout attempt failed on `permission denied for sequence`, so the
    --    sequences are checked too.
    SELECT string_agg(c.relname, ', ' ORDER BY c.relname) INTO v_offen
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname IN ('workforce', 'public')
      AND c.relkind IN ('r', 'p')
      AND NOT has_table_privilege('workforce_backup', c.oid, 'SELECT');
    IF v_offen IS NOT NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_007_BACKUP_CANNOT_READ: %', v_offen;
    END IF;

    SELECT string_agg(c.relname, ', ' ORDER BY c.relname) INTO v_offen
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname IN ('workforce', 'public')
      AND c.relkind IN ('r', 'p')
      AND (has_table_privilege('workforce_backup', c.oid, 'INSERT')
        OR has_table_privilege('workforce_backup', c.oid, 'UPDATE')
        OR has_table_privilege('workforce_backup', c.oid, 'DELETE'));
    IF v_offen IS NOT NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_007_BACKUP_MAY_WRITE: %', v_offen;
    END IF;

    RAISE NOTICE 'Least-privilege roles acceptance: PASS';
END;
$$;

-- 8. The self-check. Every assertion above is of the form "this privilege is
--    absent"; if `has_function_privilege` were being called in a way that
--    always returns false, all of them would pass and prove nothing. So:
--    demand that the owner *can* do what the others cannot.
DO $$
BEGIN
    IF NOT has_function_privilege('workforce_app',
            'workforce.bus_record_denial(text,text,text,text,text,text,text,integer)',
            'EXECUTE') THEN
        RAISE EXCEPTION 'ACCEPTANCE_007_SELF_CHECK_FAILED: der Eigentuemer darf nicht ausfuehren';
    END IF;
    IF NOT has_table_privilege('workforce_app', 'workforce.bus_denials', 'SELECT') THEN
        RAISE EXCEPTION 'ACCEPTANCE_007_SELF_CHECK_FAILED: der Eigentuemer darf nicht lesen';
    END IF;
    RAISE NOTICE 'Least-privilege roles self-check: PASS';
END;
$$;

ROLLBACK;
