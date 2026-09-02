\set ON_ERROR_STOP on

-- Acceptance test for migration 006_legacy_registry_tables (review finding G-047).
--
-- 006 moved the seven legacy registry tables out of the API startup path, so
-- the runtime account no longer needs DDL. The migration ran in production on
-- 2026-09-01 and had no acceptance test until now - it was proven through the
-- rollout window's own checks, which nobody can repeat afterwards.
--
-- Everything here reads the catalog and is rolled back, so it can be run
-- against production at any time. It writes nothing.
--
-- The point is not "the tables exist somewhere". It is that they exist in
-- `public`, where the API looks for them, and that there is no second set in
-- `workforce` that a search_path change could make the API read instead.

BEGIN;

DO $$
DECLARE
    v_expected text[] := ARRAY[
        'roles', 'workers', 'tasks', 'activity_log',
        'task_notes', 'documents', 'document_versions'
    ];
    v_missing text;
    v_doppelt text;
    v_ohne_pk text;
    v_count integer;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM workforce.schema_migrations
        WHERE migration_id = '006_legacy_registry_tables'
    ) THEN
        RAISE EXCEPTION 'ACCEPTANCE_006_MIGRATION_MISSING';
    END IF;

    -- 1. Exactly one marker row. Two would mean the migration ran twice and
    --    the gate runner's count check has stopped meaning anything.
    SELECT count(*) INTO v_count
    FROM workforce.schema_migrations
    WHERE migration_id = '006_legacy_registry_tables';
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'ACCEPTANCE_006_MARKER_COUNT: % statt 1', v_count;
    END IF;

    -- 2. All seven in `public`. Named individually, because "seven tables
    --    exist" would also pass if one were missing and something else had
    --    been added.
    SELECT string_agg(name, ', ' ORDER BY name) INTO v_missing
    FROM unnest(v_expected) AS name
    WHERE to_regclass('public.' || quote_ident(name)) IS NULL;
    IF v_missing IS NOT NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_006_TABLE_MISSING: %', v_missing;
    END IF;

    -- 3. No second set in `workforce`. The API resolves these unqualified, so
    --    a duplicate there plus a search_path change would silently swap which
    --    tables it reads - the kind of thing that looks healthy and is not.
    SELECT string_agg(name, ', ' ORDER BY name) INTO v_doppelt
    FROM unnest(v_expected) AS name
    WHERE to_regclass('workforce.' || quote_ident(name)) IS NOT NULL;
    IF v_doppelt IS NOT NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_006_TABLE_DUPLICATED_IN_WORKFORCE: %', v_doppelt;
    END IF;

    -- 4. Each has a primary key. A table without one is not the table the API
    --    was written against.
    SELECT string_agg(name, ', ' ORDER BY name) INTO v_ohne_pk
    FROM unnest(v_expected) AS name
    WHERE NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        WHERE c.conrelid = to_regclass('public.' || quote_ident(name))
          AND c.contype = 'p'
    );
    IF v_ohne_pk IS NOT NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_006_PRIMARY_KEY_MISSING: %', v_ohne_pk;
    END IF;

    RAISE NOTICE 'Legacy registry tables acceptance: PASS (% Tabellen in public)',
        array_length(v_expected, 1);
END;
$$;

-- 5. The negative that gives the rest its meaning: the same query against a
--    name that does not exist has to come back missing. Without this, a typo
--    in `to_regclass` would make every check above pass silently.
DO $$
DECLARE
    v_treffer regclass;
BEGIN
    v_treffer := to_regclass('public.' || quote_ident('gibt_es_nicht_006'));
    IF v_treffer IS NOT NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_006_SELF_CHECK_FAILED';
    END IF;
    RAISE NOTICE 'Legacy registry tables self-check: PASS';
END;
$$;

ROLLBACK;
