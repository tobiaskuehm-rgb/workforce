\set ON_ERROR_STOP on

-- Abnahmetest fuer 010_bus_function_owner_rollback (`SV-2026-09-03-04`).
--
-- Der Rueckbau hat zwei Haelften, und nur zusammen ergeben sie die Aussage:
--
--   * die zwoelf SECURITY-DEFINER-Busfunktionen gehoeren wieder dem
--     Eigentuemer des Schemas `workforce` - und die API kann sie aufrufen,
--     denn ein Rueckbau, der einen stillgelegten Bus hinterlaesst, ist keiner
--   * `workforce_owner` haelt kein einziges Recht mehr und besitzt nichts
--
-- Fast jede Aussage hier lautet "etwas ist nicht da". Waeren die
-- Katalogabfragen falsch gebaut, faenden sie nichts und alles bestuende -
-- dieselbe Falle, die im `009`-Abnahmetest als leerer Join steckte
-- (`SV-2026-09-03-03`, Regel 47). Abschnitt 4 stellt deshalb die Gegenfrage:
-- Sieht dieselbe Abfrage ueberhaupt etwas, wenn es etwas zu sehen gibt?
--
-- Liest nur den Katalog, laeuft in einer Transaktion und endet mit ROLLBACK.

BEGIN;

-- 1. Der Marker.
DO $$
DECLARE
    v_marker integer;
BEGIN
    SELECT count(*) INTO v_marker
    FROM workforce.schema_migrations
    WHERE migration_id = '010_bus_function_owner_rollback';
    IF v_marker <> 1 THEN
        RAISE EXCEPTION 'ACCEPTANCE_010_MARKER_COUNT: % statt 1', v_marker;
    END IF;
END;
$$;

-- 2. Die zwoelf gehoeren wieder dem Schemaeigentuemer - und die zehn oeffentlichen
--    sind fuer `workforce_api` weiterhin aufrufbar.
--
--    Der Zieleigentuemer wird gelesen, nicht genannt, mit demselben Anker wie
--    die Migration: `pg_namespace.nspowner` von `workforce`. Ein
--    abgeschriebener Rollenname waere hier dieselbe Klasse wie ein
--    abgeschriebener Containername (`G-042`).
--
--    `bus_authenticate` und `bus_identify_for_audit` sind interne Helfer;
--    `007` hat der API das EXECUTE darauf absichtlich nicht erteilt. Die zehn
--    aufrufbaren werden deshalb aus den zwoelf minus diesen beiden abgeleitet
--    und nicht als dritte Liste gefuehrt - zwei Listen koennen auseinanderlaufen.
DO $$
DECLARE
    v_signaturen text[] := ARRAY[
        'workforce.bus_authenticate(text, text)',
        'workforce.bus_send_message(text, text, text, text, text, text, text, text, text, text, text, text, text)',
        'workforce.bus_acknowledge_message(text, text, text, text, text, text)',
        'workforce.bus_list_messages(text, text, text, integer)',
        'workforce.bus_create_task(text, text, text, text, text, text, text, text, text, text, timestamptz)',
        'workforce.bus_list_tasks(text, text, text, integer)',
        'workforce.bus_transition_task(text, text, text, text, text, text)',
        'workforce.bus_create_handoff(text, text, text, text, text, text, text, text, text, text, text, text)',
        'workforce.bus_list_handoffs(text, text, text, integer)',
        'workforce.bus_transition_handoff(text, text, text, text, text, text)',
        'workforce.bus_identify_for_audit(text, text)',
        'workforce.bus_record_denial(text, text, text, text, text, text, text, integer)'
    ];
    v_intern text[] := ARRAY[
        'workforce.bus_authenticate(text, text)',
        'workforce.bus_identify_for_audit(text, text)'
    ];
    v_signatur text;
    v_proc regprocedure;
    v_ziel name;
    v_eigner name;
    v_darf boolean;
    v_hat boolean;
    v_fehlend text := '';
    v_zuviel text := '';
    v_aufrufbar integer := 0;
BEGIN
    SELECT r.rolname INTO v_ziel
    FROM pg_namespace n
    JOIN pg_roles r ON r.oid = n.nspowner
    WHERE n.nspname = 'workforce';
    IF v_ziel IS NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_010_SCHEMA_OWNER_UNKNOWN';
    END IF;
    IF v_ziel = 'workforce_owner' THEN
        RAISE EXCEPTION 'ACCEPTANCE_010_TARGET_IS_THE_ROLLED_BACK_ROLE: %', v_ziel;
    END IF;

    FOREACH v_signatur IN ARRAY v_signaturen LOOP
        v_proc := to_regprocedure(v_signatur);
        IF v_proc IS NULL THEN
            RAISE EXCEPTION 'ACCEPTANCE_010_SIGNATURE_NOT_FOUND: %', v_signatur;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE oid = v_proc::oid AND prosecdef) THEN
            RAISE EXCEPTION 'ACCEPTANCE_010_NOT_SECURITY_DEFINER: %', v_signatur;
        END IF;

        SELECT r.rolname INTO v_eigner
        FROM pg_proc p
        JOIN pg_roles r ON r.oid = p.proowner
        WHERE p.oid = v_proc::oid;
        IF v_eigner IS DISTINCT FROM v_ziel THEN
            RAISE EXCEPTION 'ACCEPTANCE_010_NOT_RETURNED: % gehoert %', v_signatur, v_eigner;
        END IF;

        v_darf := NOT (v_signatur = ANY (v_intern));
        v_hat := has_function_privilege('workforce_api', v_proc::oid, 'EXECUTE');
        IF v_darf THEN
            v_aufrufbar := v_aufrufbar + 1;
            IF NOT v_hat THEN
                v_fehlend := v_fehlend || ' ' || v_signatur;
            END IF;
        ELSIF v_hat THEN
            v_zuviel := v_zuviel || ' ' || v_signatur;
        END IF;
    END LOOP;

    IF v_fehlend <> '' THEN
        RAISE EXCEPTION 'ACCEPTANCE_010_API_LOST_EXECUTE:%', v_fehlend;
    END IF;
    IF v_zuviel <> '' THEN
        RAISE EXCEPTION 'ACCEPTANCE_010_API_REACHES_INTERNALS:%', v_zuviel;
    END IF;
    IF v_aufrufbar <> 10 THEN
        RAISE EXCEPTION 'ACCEPTANCE_010_CALLABLE_COUNT: % statt 10', v_aufrufbar;
    END IF;
END;
$$;

-- 3. `workforce_owner` ist rechtlos und besitzt nichts.
--
--    Fehlt die Rolle ganz, ist das kein Fehlschlag - der Sicherheitszustand
--    waere dann sogar staerker -, aber es ist auch nicht das, was `010`
--    herstellt: Die Migration laesst sie ausdruecklich stehen. Also wird es
--    benannt statt stillschweigend hingenommen, und die Pruefungen darunter
--    entfallen sichtbar.
DO $$
DECLARE
    v_relationen text[];
    v_funktionen text[];
    v_schemata text[];
    v_vorgaben integer;
    v_eigene_relationen integer;
    v_eigene_funktionen integer;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'workforce_owner') THEN
        RAISE NOTICE 'ACCEPTANCE_010_NOTE: workforce_owner existiert nicht - 010 laesst '
                     'die Rolle stehen, hier hat also jemand von Hand nachgeraeumt. '
                     'Die Rechtepruefungen dieses Abschnitts entfallen.';
        RETURN;
    END IF;

    SELECT coalesce(array_agg(n.nspname || '.' || c.relname || '=' || a.privilege_type
                              ORDER BY n.nspname, c.relname, a.privilege_type), '{}')
      INTO v_relationen
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    CROSS JOIN LATERAL aclexplode(c.relacl) AS a
    JOIN pg_roles r ON r.oid = a.grantee
    WHERE r.rolname = 'workforce_owner';
    IF array_length(v_relationen, 1) IS NOT NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_010_RELATION_PRIVILEGES_REMAIN: %',
            array_to_string(v_relationen, ', ');
    END IF;

    SELECT coalesce(array_agg(p.oid::regprocedure::text || '=' || a.privilege_type
                              ORDER BY p.oid::regprocedure::text, a.privilege_type), '{}')
      INTO v_funktionen
    FROM pg_proc p
    CROSS JOIN LATERAL aclexplode(p.proacl) AS a
    JOIN pg_roles r ON r.oid = a.grantee
    WHERE r.rolname = 'workforce_owner';
    IF array_length(v_funktionen, 1) IS NOT NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_010_FUNCTION_PRIVILEGES_REMAIN: %',
            array_to_string(v_funktionen, ', ');
    END IF;

    SELECT coalesce(array_agg(n.nspname || '=' || a.privilege_type
                              ORDER BY n.nspname, a.privilege_type), '{}')
      INTO v_schemata
    FROM pg_namespace n
    CROSS JOIN LATERAL aclexplode(n.nspacl) AS a
    JOIN pg_roles r ON r.oid = a.grantee
    WHERE r.rolname = 'workforce_owner';
    IF array_length(v_schemata, 1) IS NOT NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_010_SCHEMA_PRIVILEGES_REMAIN: %',
            array_to_string(v_schemata, ', ');
    END IF;

    SELECT count(*) INTO v_vorgaben
    FROM pg_default_acl d
    CROSS JOIN LATERAL aclexplode(d.defaclacl) AS a
    JOIN pg_roles r ON r.oid = a.grantee
    WHERE r.rolname = 'workforce_owner';
    IF v_vorgaben <> 0 THEN
        RAISE EXCEPTION 'ACCEPTANCE_010_DEFAULT_ACL_REMAINS: %', v_vorgaben;
    END IF;

    SELECT count(*) INTO v_eigene_relationen
    FROM pg_class c
    JOIN pg_roles r ON r.oid = c.relowner
    WHERE r.rolname = 'workforce_owner';
    IF v_eigene_relationen <> 0 THEN
        RAISE EXCEPTION 'ACCEPTANCE_010_OWNER_STILL_OWNS_RELATIONS: %', v_eigene_relationen;
    END IF;

    SELECT count(*) INTO v_eigene_funktionen
    FROM pg_proc p
    JOIN pg_roles r ON r.oid = p.proowner
    WHERE r.rolname = 'workforce_owner';
    IF v_eigene_funktionen <> 0 THEN
        RAISE EXCEPTION 'ACCEPTANCE_010_OWNER_STILL_OWNS_FUNCTIONS: %', v_eigene_funktionen;
    END IF;
END;
$$;

-- 4. Selbstpruefung. Ohne sie belegt Abschnitt 3 nur, dass die Abfragen nichts
--    finden - was auch eine falsch gebaute Abfrage schafft.
DO $$
DECLARE
    v_count integer;
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'workforce_gibt_es_nicht_010') THEN
        RAISE EXCEPTION 'ACCEPTANCE_010_SELF_CHECK_FAILED';
    END IF;

    -- Dieselbe Abfrageform wie in Abschnitt 3, nur ohne den Rollenfilter: Sie
    -- muss Zeilen liefern. Tut sie es nicht, sieht `aclexplode` hier gar nichts
    -- und die leeren Ergebnisse oben sagen nichts ueber `workforce_owner`.
    SELECT count(*) INTO v_count
    FROM pg_class c
    CROSS JOIN LATERAL aclexplode(c.relacl) AS a
    JOIN pg_roles r ON r.oid = a.grantee;
    IF v_count = 0 THEN
        RAISE EXCEPTION 'ACCEPTANCE_010_SELF_CHECK_FAILED: aclexplode sieht keine Rechte';
    END IF;

    -- Und die Eigentumsabfrage sieht die zwoelf wirklich - beim
    -- Schemaeigentuemer, wo sie nach dem Rueckbau hingehoeren.
    SELECT count(*) INTO v_count
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    JOIN pg_roles r ON r.oid = p.proowner
    JOIN pg_namespace s ON s.nspname = 'workforce'
    WHERE n.nspname = 'workforce' AND p.prosecdef AND r.oid = s.nspowner;
    -- **Mindestens** zwoelf, nicht genau zwoelf. Die praezise Aussage - genau
    -- diese zwoelf gehoeren dem Ziel - steht in Abschnitt 2 und haengt dort an
    -- der einzelnen Signatur. Hier geht es nur darum, dass die Abfrage
    -- ueberhaupt sieht; eine Gleichheit waere nach einer Anwendung von `004`
    -- falsch rot geworden, weil Knowledge sieben eigene mitbringt, die nach
    -- einem Rueckbau voellig zu Recht beim Schemaeigentuemer liegen.
    IF v_count < 12 THEN
        RAISE EXCEPTION 'ACCEPTANCE_010_SELF_CHECK_FAILED: nur % SECURITY-DEFINER-Funktionen '
                        'beim Schemaeigentuemer, mindestens 12 erwartet', v_count;
    END IF;

    RAISE NOTICE 'Bus function owner rollback acceptance: PASS';
END;
$$;

ROLLBACK;
