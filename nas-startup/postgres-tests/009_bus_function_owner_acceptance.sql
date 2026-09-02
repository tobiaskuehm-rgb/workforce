\set ON_ERROR_STOP on

-- Abnahmetest fuer 009_bus_function_owner (Befund G-045).
--
-- Die Migration verschiebt das Eigentum der SECURITY-DEFINER-Funktionen auf
-- eine Rolle ohne Superuser-Attribut, die die Tabellen **nicht** besitzt. Der
-- Test prueft beide Haelften, denn nur zusammen ergeben sie die Aussage:
--
--   * keine SECURITY-DEFINER-Funktion gehoert mehr einem Superuser
--   * der neue Eigentuemer besitzt keine Tabelle und kann deshalb kein
--     `ALTER TABLE ... DISABLE TRIGGER` - darauf beruhen die
--     Append-only-Zusicherungen aus 006/007
--
-- Und die dritte Frage, ohne die der Test nur belegt, dass etwas kaputt ist:
-- kann die API ihre Funktionen noch aufrufen? Ein Eigentuemerwechsel nimmt
-- bestehende GRANTs nicht weg, aber behauptet ist das schnell.
--
-- Liest nur den Katalog, laeuft in einer Transaktion und endet mit ROLLBACK.

BEGIN;

DO $$
DECLARE
    v_count integer;
    v_super integer;
    v_tabellen integer;
    v_attribute record;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM workforce.schema_migrations
        WHERE migration_id = '009_bus_function_owner'
    ) THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_MIGRATION_MISSING';
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.schema_migrations
    WHERE migration_id = '009_bus_function_owner';
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_MARKER_COUNT: % statt 1', v_count;
    END IF;

    -- 1. Die Rolle, mit ihren Attributen. Sie sind Teil der Zusicherung:
    --    eine anmeldefaehige oder rechteerbende Rolle waere etwas anderes.
    SELECT rolsuper, rolcanlogin, rolcreatedb, rolcreaterole, rolbypassrls
      INTO v_attribute
    FROM pg_roles WHERE rolname = 'workforce_owner';
    IF NOT FOUND THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_OWNER_ROLE_MISSING';
    END IF;
    IF v_attribute.rolsuper OR v_attribute.rolcanlogin
       OR v_attribute.rolcreatedb OR v_attribute.rolcreaterole
       OR v_attribute.rolbypassrls THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_OWNER_ROLE_TOO_POWERFUL';
    END IF;

    -- 2. Keine SECURITY-DEFINER-Funktion laeuft mehr als Superuser.
    SELECT count(*) INTO v_super
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    JOIN pg_roles r ON r.oid = p.proowner
    WHERE n.nspname = 'workforce' AND p.prosecdef AND r.rolsuper;
    IF v_super <> 0 THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_SECURITY_DEFINER_STILL_SUPERUSER: %', v_super;
    END IF;

    -- Und es gibt sie ueberhaupt noch - sonst waere die Null oben wertlos.
    SELECT count(*) INTO v_count
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'workforce' AND p.prosecdef;
    IF v_count = 0 THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_NO_SECURITY_DEFINER_FUNCTIONS';
    END IF;

    -- 3. Der Kern: Der neue Eigentuemer besitzt keine Tabelle. Besaesse er
    --    eine, koennte er ihre Trigger abschalten - und die Migration haette
    --    das Problem nur umbenannt.
    SELECT count(*) INTO v_tabellen
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN pg_roles r ON r.oid = c.relowner
    WHERE n.nspname IN ('workforce', 'public')
      AND c.relkind IN ('r', 'p')
      AND r.rolname = 'workforce_owner';
    IF v_tabellen <> 0 THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_OWNER_OWNS_TABLES: %', v_tabellen;
    END IF;

    RAISE NOTICE 'Bus function owner acceptance: PASS (% SECURITY DEFINER, 0 beim Superuser, 0 Tabellen)',
        v_count;
END;
$$;

-- 4. Die API kann ihre Funktionen weiterhin aufrufen. Ein Eigentuemerwechsel
--    nimmt GRANTs nicht weg - aber ein Abnahmetest, der nur Verbote prueft,
--    besteht auch auf einem stillgelegten Bus.
DO $$
DECLARE
    v_name text;
    v_fehlend text := '';
BEGIN
    -- Die zehn, die die API wirklich aufruft. `bus_authenticate` und
    -- `bus_identify_for_audit` stehen bewusst **nicht** hier: Sie sind interne
    -- Helfer, die nur aus den anderen Funktionen heraus laufen, und `007` hat
    -- der API das EXECUTE darauf absichtlich nicht erteilt. Meine erste
    -- Fassung dieses Tests verlangte es - das waere eine Aufweichung gewesen,
    -- und die Messung gegen die Produktion hat sie gefunden.
    FOREACH v_name IN ARRAY ARRAY[
        'bus_send_message', 'bus_acknowledge_message', 'bus_list_messages',
        'bus_create_task', 'bus_list_tasks', 'bus_create_handoff',
        'bus_list_handoffs', 'bus_transition_task', 'bus_transition_handoff',
        'bus_record_denial'
    ] LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'workforce' AND p.proname = v_name
              AND has_function_privilege('workforce_api', p.oid, 'EXECUTE')
        ) THEN
            v_fehlend := v_fehlend || ' ' || v_name;
        END IF;
    END LOOP;
    IF v_fehlend <> '' THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_API_LOST_EXECUTE:%', v_fehlend;
    END IF;
    RAISE NOTICE 'API-Ausfuehrungsrechte unveraendert: PASS';
END;
$$;

-- 4b. Und die Gegenrichtung: Die internen Helfer bleiben fuer die API
--     unerreichbar. Ein Test, der nur prueft, dass genug erlaubt ist, wuerde
--     eine zu weit geoeffnete Datenbank nicht bemerken.
DO $$
DECLARE
    v_name text;
    v_zuviel text := '';
BEGIN
    FOREACH v_name IN ARRAY ARRAY['bus_authenticate', 'bus_identify_for_audit'] LOOP
        IF EXISTS (
            SELECT 1 FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'workforce' AND p.proname = v_name
              AND has_function_privilege('workforce_api', p.oid, 'EXECUTE')
        ) THEN
            v_zuviel := v_zuviel || ' ' || v_name;
        END IF;
    END LOOP;
    IF v_zuviel <> '' THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_API_REACHES_INTERNALS:%', v_zuviel;
    END IF;
    RAISE NOTICE 'Interne Helfer bleiben unerreichbar: PASS';
END;
$$;

-- 5. Selbstpruefung. Jede Aussage oben ist "etwas ist nicht da". Waeren die
--    Katalogabfragen falsch gebaut, faenden sie nichts und alles bestuende.
--    Also nach einer Rolle fragen, die es nicht gibt, und verlangen, dass das
--    auffaellt.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'workforce_gibt_es_nicht_009') THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_SELF_CHECK_FAILED';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'workforce' AND p.prosecdef
    ) THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_SELF_CHECK_FAILED';
    END IF;
    RAISE NOTICE 'Bus function owner self-check: PASS';
END;
$$;

ROLLBACK;
