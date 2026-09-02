\set ON_ERROR_STOP on

-- Abnahmetest fuer 009_bus_function_owner (Befunde G-045, G-071).
--
-- Die Migration verschiebt das Eigentum der zwoelf SECURITY-DEFINER-
-- Busfunktionen auf eine Rolle ohne Superuser-Attribut, die keine Relation
-- besitzt. Der Test prueft alle Haelften, denn nur zusammen ergeben sie die
-- Aussage:
--
--   * genau die zwoelf gehoeren `workforce_owner` - nicht weniger und
--     nicht mehr
--   * er besitzt keine Relation und kann deshalb kein
--     `ALTER TABLE ... DISABLE TRIGGER` - darauf beruhen die
--     Append-only-Zusicherungen aus 006/007
--   * seine Tabellenrechte sind **genau** die Allowlist aus 009
--   * jedes sicherheitsrelevante Rollenattribut ist aus
--
-- Und die Frage, ohne die der Test nur belegt, dass etwas kaputt ist: kann die
-- API ihre Funktionen noch aufrufen? Ein Eigentuemerwechsel nimmt bestehende
-- GRANTs nicht weg, aber behauptet ist das schnell.
--
-- Liest nur den Katalog, laeuft in einer Transaktion und endet mit ROLLBACK.

BEGIN;

-- 1. Marker und Rolle.
DO $$
DECLARE
    v_count integer;
    v_attribute record;
BEGIN
    SELECT count(*) INTO v_count
    FROM workforce.schema_migrations
    WHERE migration_id = '009_bus_function_owner';
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_MARKER_COUNT: % statt 1', v_count;
    END IF;

    SELECT rolsuper, rolcanlogin, rolcreatedb, rolcreaterole,
           rolbypassrls, rolinherit, rolreplication
      INTO v_attribute
    FROM pg_roles WHERE rolname = 'workforce_owner';
    IF NOT FOUND THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_OWNER_ROLE_MISSING';
    END IF;
    -- Alle sieben, einzeln benannt (`G-071`): `rolinherit` und
    -- `rolreplication` fehlten in der ersten Fassung. Vererbung wuerde die
    -- Rolle an fremden Rechten teilhaben lassen, und eine
    -- Replikationsverbindung liest den ganzen WAL-Strom - also jede Tabelle,
    -- an der die Allowlist unten gerade sorgfaeltig vorbeigeht.
    IF v_attribute.rolsuper OR v_attribute.rolcanlogin
       OR v_attribute.rolcreatedb OR v_attribute.rolcreaterole
       OR v_attribute.rolbypassrls OR v_attribute.rolinherit
       OR v_attribute.rolreplication THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_OWNER_ROLE_TOO_POWERFUL';
    END IF;
END;
$$;

-- 2. Genau die zwoelf, mit Stelligkeit und Eigentuemer. Die erste Fassung
--    fragte "0 beim Superuser" und ">0 vorhanden" - eine zu breite
--    Verschiebung haette das bestanden (`G-071`).
DO $$
DECLARE
    v_erwartet text[] := ARRAY[
        'bus_authenticate:2', 'bus_send_message:13', 'bus_acknowledge_message:6',
        'bus_list_messages:4', 'bus_create_task:11', 'bus_list_tasks:4',
        'bus_transition_task:6', 'bus_create_handoff:12', 'bus_list_handoffs:4',
        'bus_transition_handoff:6', 'bus_identify_for_audit:2',
        'bus_record_denial:8'
    ];
    v_gehoert text[];
    v_fehlend text[];
    v_zuviel text[];
BEGIN
    -- Alles, was workforce_owner gehoert - ohne Filter auf den Namen, damit
    -- eine unerwartete Eigentumsverschiebung als Zuviel auffaellt.
    SELECT coalesce(array_agg(p.proname || ':' || p.pronargs
                              ORDER BY p.proname, p.pronargs), '{}')
      INTO v_gehoert
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    JOIN pg_roles r ON r.oid = p.proowner
    WHERE n.nspname = 'workforce' AND r.rolname = 'workforce_owner';

    SELECT coalesce(array_agg(x), '{}') INTO v_fehlend
    FROM unnest(v_erwartet) AS x WHERE x <> ALL (v_gehoert);
    SELECT coalesce(array_agg(x), '{}') INTO v_zuviel
    FROM unnest(v_gehoert) AS x WHERE x <> ALL (v_erwartet);

    IF array_length(v_fehlend, 1) IS NOT NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_NOT_TRANSFERRED: %',
            array_to_string(v_fehlend, ', ');
    END IF;
    IF array_length(v_zuviel, 1) IS NOT NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_UNEXPECTED_OWNERSHIP: %',
            array_to_string(v_zuviel, ', ');
    END IF;

    -- Und sie sind noch SECURITY DEFINER. Ohne das waere die Uebertragung
    -- vollzogen und wirkungslos.
    IF EXISTS (
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        JOIN pg_roles r ON r.oid = p.proowner
        WHERE n.nspname = 'workforce' AND r.rolname = 'workforce_owner'
          AND NOT p.prosecdef
    ) THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_OWNED_BUT_NOT_SECURITY_DEFINER';
    END IF;
END;
$$;

-- 2b. Keine fremde SECURITY-DEFINER-Funktion laeuft als Superuser.
--
--     Heute ist diese Menge leer. Sobald `004` angewendet wird, sind es die
--     sieben Knowledge-Funktionen - und dann ist dieser Test rot. Das ist
--     Absicht: 009 trifft die Eigentuemerentscheidung fuer Knowledge
--     ausdruecklich **nicht** (`G-071`), und ein NOTICE an dieser Stelle hiesse,
--     dass sieben Funktionen wieder als Bootstrap-Superuser laufen und es
--     niemandem auffaellt. Der Ausweg ist eine eigene Migration fuer
--     Knowledge, nicht ein weicherer Test.
DO $$
DECLARE
    v_fremd text[];
BEGIN
    SELECT coalesce(array_agg(p.proname ORDER BY p.proname), '{}') INTO v_fremd
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    JOIN pg_roles r ON r.oid = p.proowner
    WHERE n.nspname = 'workforce' AND p.prosecdef AND r.rolsuper;
    IF array_length(v_fremd, 1) IS NOT NULL THEN
        RAISE EXCEPTION
            'ACCEPTANCE_009_SECURITY_DEFINER_STILL_SUPERUSER: % - diese '
            'Funktionen brauchen ihre eigene Eigentuemerentscheidung (G-071)',
            array_to_string(v_fremd, ', ');
    END IF;
END;
$$;

-- 3. Der Kern: Der Eigentuemer besitzt keine Relation. Besaesse er eine,
--    koennte er ihre Trigger abschalten - und die Migration haette das
--    Problem nur umbenannt.
DO $$
DECLARE
    v_relationen integer;
BEGIN
    SELECT count(*) INTO v_relationen
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN pg_roles r ON r.oid = c.relowner
    WHERE n.nspname IN ('workforce', 'public')
      AND r.rolname = 'workforce_owner';
    IF v_relationen <> 0 THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_OWNER_OWNS_RELATIONS: %', v_relationen;
    END IF;
END;
$$;

-- 4. Die Tabellenrechte sind **genau** die Allowlist. Ein `ALL TABLES` waere
--    hier sofort sichtbar, und nach einer Anwendung von `004` haette es auch
--    saemtliche Knowledge-Tabellen umfasst (`G-071`).
DO $$
DECLARE
    v_erwartet text[] := ARRAY[
        'active_project_members=SELECT',
        'bus_channels=SELECT',
        'bus_credentials=SELECT',
        'bus_denials=INSERT',
        'bus_events=INSERT',
        'bus_handoffs=INSERT,SELECT,UPDATE',
        'bus_member_capabilities=SELECT',
        'bus_messages=INSERT,SELECT,UPDATE',
        'bus_route_allowlist=SELECT',
        'bus_tasks=INSERT,SELECT,UPDATE',
        'employee_project_memberships=SELECT',
        'employees=SELECT',
        'projects=SELECT'
    ];
    v_ist text[];
    v_fehlend text[];
    v_zuviel text[];
BEGIN
    SELECT coalesce(array_agg(zeile ORDER BY zeile), '{}') INTO v_ist
    FROM (
        SELECT table_name || '=' ||
               string_agg(DISTINCT privilege_type, ',' ORDER BY privilege_type) AS zeile
        FROM information_schema.role_table_grants
        WHERE grantee = 'workforce_owner'
        GROUP BY table_schema, table_name
    ) AS g;

    SELECT coalesce(array_agg(x), '{}') INTO v_fehlend
    FROM unnest(v_erwartet) AS x WHERE x <> ALL (v_ist);
    SELECT coalesce(array_agg(x), '{}') INTO v_zuviel
    FROM unnest(v_ist) AS x WHERE x <> ALL (v_erwartet);

    IF array_length(v_fehlend, 1) IS NOT NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_GRANT_MISSING: %',
            array_to_string(v_fehlend, ', ');
    END IF;
    IF array_length(v_zuviel, 1) IS NOT NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_GRANT_TOO_BROAD: %',
            array_to_string(v_zuviel, ', ');
    END IF;
END;
$$;

-- 4b. Und nichts ausserhalb von `workforce`: kein Schema `public`, keine
--     Sequenz. Beides stand in der ersten Fassung und wurde von nichts
--     gebraucht (`G-071`).
DO $$
BEGIN
    IF has_schema_privilege('workforce_owner', 'public', 'USAGE') THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_PUBLIC_SCHEMA_GRANTED';
    END IF;
    IF EXISTS (
        SELECT 1 FROM information_schema.usage_privileges
        WHERE grantee = 'workforce_owner' AND object_type = 'SEQUENCE'
    ) THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_SEQUENCE_GRANTED';
    END IF;
END;
$$;

-- 5. Die API kann ihre Funktionen weiterhin aufrufen. Ein Eigentuemerwechsel
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
END;
$$;

-- 5b. Und die Gegenrichtung: Die internen Helfer bleiben fuer die API
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
END;
$$;

-- 6. Selbstpruefung. Fast jede Aussage oben ist "etwas ist nicht da". Waeren
--    die Katalogabfragen falsch gebaut, faenden sie nichts und alles bestuende.
--    Also nach einer Rolle fragen, die es nicht gibt, und verlangen, dass die
--    Abfragen ueberhaupt etwas sehen.
DO $$
DECLARE
    v_count integer;
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'workforce_gibt_es_nicht_009') THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_SELF_CHECK_FAILED';
    END IF;

    SELECT count(*) INTO v_count
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    JOIN pg_roles r ON r.oid = p.proowner
    WHERE n.nspname = 'workforce' AND p.prosecdef
      AND r.rolname = 'workforce_owner';
    IF v_count <> 12 THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_SELF_CHECK_FAILED: % statt 12', v_count;
    END IF;

    SELECT count(*) INTO v_count
    FROM information_schema.role_table_grants WHERE grantee = 'workforce_owner';
    IF v_count = 0 THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_SELF_CHECK_FAILED: keine Rechte sichtbar';
    END IF;

    RAISE NOTICE 'Bus function owner acceptance: PASS';
END;
$$;

ROLLBACK;
