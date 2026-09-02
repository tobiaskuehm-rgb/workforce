\set ON_ERROR_STOP on

-- Acceptance test for migration 003_workforce_bus_trigger_fix (review finding G-047).
--
-- 003 is small: it added `updated_at` to workforce.bus_credentials, backfilled
-- it from issued_at, and made it NOT NULL with a default. The reason is in its
-- own description - the version trigger is **shared**. `bus_touch_versioned_row`
-- is attached to six tables, and it writes `version` and `updated_at` on every
-- one of them. A table missing either column does not fail at migration time;
-- it fails the first time somebody updates a row there.
--
-- So this test does not check one column. It checks the precondition the shared
-- trigger needs, on every table that carries it - which is what 003 was really
-- about, and what a second missing column would break again.
--
-- **What this file deliberately does not test:** that the trigger actually
-- bumps the values on UPDATE. That is 002's behaviour and belongs to 002's
-- acceptance test; repeating it here would mean writing and updating a
-- credential row, and the guard triggers on that table decide which updates
-- are even allowed. 003 changed schema, so this tests schema.
--
-- Reads the catalog only, inside a transaction that is rolled back.

BEGIN;

DO $$
DECLARE
    v_tabellen text[] := ARRAY[
        'bus_channels', 'bus_credentials', 'bus_handoffs',
        'bus_member_capabilities', 'bus_route_allowlist', 'bus_tasks'
    ];
    v_fehlt text;
    v_nullable text;
    v_ohne_trigger text;
    v_count integer;
    v_default text;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM workforce.schema_migrations
        WHERE migration_id = '003_workforce_bus_trigger_fix'
    ) THEN
        RAISE EXCEPTION 'ACCEPTANCE_003_MIGRATION_MISSING';
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.schema_migrations
    WHERE migration_id = '003_workforce_bus_trigger_fix';
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'ACCEPTANCE_003_MARKER_COUNT: % statt 1', v_count;
    END IF;

    -- 1. The column 003 was written for, with the properties it set.
    SELECT c.column_default INTO v_default
    FROM information_schema.columns c
    WHERE c.table_schema = 'workforce'
      AND c.table_name = 'bus_credentials'
      AND c.column_name = 'updated_at';
    IF v_default IS NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_003_UPDATED_AT_MISSING_OR_WITHOUT_DEFAULT';
    END IF;
    IF v_default NOT LIKE '%clock_timestamp%' THEN
        RAISE EXCEPTION 'ACCEPTANCE_003_UNEXPECTED_DEFAULT: %', v_default;
    END IF;

    -- 2. Every table on the shared trigger needs both columns. This is the
    --    check that would have caught the original defect, and would catch the
    --    next one on a different table.
    SELECT string_agg(t.name || '.' || s.spalte, ', ' ORDER BY t.name, s.spalte)
      INTO v_fehlt
    FROM unnest(v_tabellen) AS t(name)
    CROSS JOIN (VALUES ('version'), ('updated_at')) AS s(spalte)
    WHERE NOT EXISTS (
        SELECT 1 FROM information_schema.columns c
        WHERE c.table_schema = 'workforce'
          AND c.table_name = t.name
          AND c.column_name = s.spalte
    );
    IF v_fehlt IS NOT NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_003_SHARED_TRIGGER_COLUMN_MISSING: %', v_fehlt;
    END IF;

    -- 3. And both NOT NULL. A nullable column would let the trigger write into
    --    a row that reads as "never touched", which is worse than an error.
    SELECT string_agg(c.table_name || '.' || c.column_name, ', '
                      ORDER BY c.table_name, c.column_name)
      INTO v_nullable
    FROM information_schema.columns c
    WHERE c.table_schema = 'workforce'
      AND c.table_name = ANY(v_tabellen)
      AND c.column_name IN ('version', 'updated_at')
      AND c.is_nullable = 'YES';
    IF v_nullable IS NOT NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_003_SHARED_TRIGGER_COLUMN_NULLABLE: %', v_nullable;
    END IF;

    -- 4. The trigger is still attached everywhere. Columns without the trigger
    --    would be dead weight and the table would silently stop versioning.
    SELECT string_agg(t.name, ', ' ORDER BY t.name) INTO v_ohne_trigger
    FROM unnest(v_tabellen) AS t(name)
    WHERE NOT EXISTS (
        SELECT 1
        FROM pg_trigger tg
        JOIN pg_proc p ON p.oid = tg.tgfoid
        WHERE tg.tgrelid = to_regclass('workforce.' || quote_ident(t.name))
          AND NOT tg.tgisinternal
          AND p.proname = 'bus_touch_versioned_row'
    );
    IF v_ohne_trigger IS NOT NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_003_TOUCH_TRIGGER_MISSING: %', v_ohne_trigger;
    END IF;

    RAISE NOTICE 'Bus trigger fix acceptance: PASS (% Tabellen am gemeinsamen Trigger)',
        array_length(v_tabellen, 1);
END;
$$;

-- 5. The self-check. Every assertion above is "something is absent"; if the
--    catalog queries were malformed they would find nothing and all of them
--    would pass. So ask for a column that does not exist and demand it is
--    reported as missing.
DO $$
DECLARE
    v_fehlt text;
BEGIN
    SELECT string_agg(s.spalte, ', ') INTO v_fehlt
    FROM (VALUES ('gibt_es_nicht_003')) AS s(spalte)
    WHERE NOT EXISTS (
        SELECT 1 FROM information_schema.columns c
        WHERE c.table_schema = 'workforce'
          AND c.table_name = 'bus_credentials'
          AND c.column_name = s.spalte
    );
    IF v_fehlt IS NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_003_SELF_CHECK_FAILED';
    END IF;
    RAISE NOTICE 'Bus trigger fix self-check: PASS';
END;
$$;

ROLLBACK;
