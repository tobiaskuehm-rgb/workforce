\set ON_ERROR_STOP on

-- Der benannte Rueckbau zu 009_bus_function_owner.
--
-- ROLLBACK-FUER: 009_bus_function_owner.sql
--
-- Vertretungsreview 2026-09-03, `SV-2026-09-03-04`: Der Kopf von `009`
-- versprach einen Rueckbau, den es im Repo nicht gab - keine Migration `010`,
-- kein Runbook-Abschnitt, kein Nachweis. Das ist Leitplanke 7 an ihrer
-- operativen Stelle: Der Satz stand in dem Absatz, den man liest, waehrend man
-- ueber die Freigabe entscheidet. `009` sagt seither, dass der Rueckbau fehlt;
-- diese Datei ist er.
--
-- **Was zurueckgenommen wird - und was das kostet.** `009` verschiebt das
-- Eigentum der zwoelf SECURITY-DEFINER-Busfunktionen auf `workforce_owner` und
-- erteilt ihm eine Tabellen-Allowlist. Geht im Fenster etwas schief, ist der
-- teure Ausgang eine zu **enge** Allowlist: Die Funktionen laufen als eine
-- Rolle, die an eine gebrauchte Tabelle nicht herankommt, und der Bus steht.
-- Diese Migration gibt das Eigentum zurueck und nimmt der Rolle jedes Recht.
-- Danach ist die Lage dieselbe wie vor `009`, bis auf die Rolle selbst.
--
-- **Die Rolle bleibt stehen, und das ist eine Entscheidung, kein Rest.**
-- Der Kopf von `009` nannte zwei Wege - `DROP OWNED BY` vor `DROP ROLE`, oder
-- die bewusste Entscheidung, sie stehen zu lassen. Es wird die zweite, aus
-- drei Gruenden:
--
--   1. `DROP OWNED BY` **loescht Objekte**, nicht nur Rechte. Sein Umfang
--      haengt davon ab, was der Rolle in dem Moment gehoert, in dem er laeuft.
--      Ein loeschendes Verb, dessen Wirkung aus dem Laufzeitzustand kommt,
--      gehoert nicht in eine Migration dieses Projekts (Leitplanke 1 und 2).
--   2. Eine Rolle mit `NOLOGIN`, ohne ein einziges Recht und ohne ein einziges
--      Objekt ist wirkungslos. Der sicherheitsrelevante Teil des Rueckbaus ist
--      der Eigentumswechsel, nicht der Katalogeintrag.
--   3. `009` ist ausdruecklich darauf gebaut, eine vorhandene Rolle
--      vorzufinden: `CREATE ROLE ... IF NOT EXISTS`, danach `ALTER ROLE` auf
--      alle Attribute und ein `REVOKE ALL` vor jedem `GRANT`. Der Weg
--      `009` -> `010` -> `011` ist damit von `009` selbst vorgesehen.
--
-- **Ob `DROP ROLE workforce_owner` danach durchginge, ist nicht gemessen** und
-- wird hier deshalb auch nicht behauptet. Der Grund ist nicht Bequemlichkeit:
-- `pg_shdepend` ist clusterweit, und diese Migration sieht nur ihre eigene
-- Datenbank. Ein Recht in einer anderen Datenbank desselben Clusters wuerde den
-- `DROP` weiter blockieren, ohne dass irgendeine Pruefung hier davon wuesste -
-- genau die Fehlerklasse, die `G-043` bezahlt hat.
--
-- **Ein zweiter Anlauf ist `011`, kein erneutes `009`.** Der Marker von `009`
-- bleibt stehen - er wird nicht geloescht, weil in dieser Datenbank nichts
-- geloescht wird -, also meldet das Gate danach dauerhaft "already applied".
-- Das ist kein Nebeneffekt, den man reparieren muesste, sondern die Regel
-- dieses Projekts: eine angewendete Migration wird nie wieder bearbeitet,
-- Korrekturen sind eine neue Nummer.
--
-- **Nicht angewendet, und nie gelaufen.** Diese Migration hat ihr eigenes Gate
-- in `compose.yaml` und ist bis heute (2026-09-03) auf keiner Instanz
-- ausgefuehrt worden - auch nicht im Wegwerf-Container von
-- `g045_owner_probe.py`, der vor ihr entstand. Geprueft ist bisher nur ihre
-- Struktur (`test_sql_structure.py`) und ihre Uebereinstimmung mit `009`
-- (`test_bus_function_owner_rollback.py`). Wer sie im Fenster braucht, laesst
-- den Abnahmetest daneben laufen.

BEGIN;

SELECT set_config('app.actor_id', 'SYSTEM-MIGRATION', true);
SELECT set_config('app.request_id', 'MIG-010-BUS-FUNCTION-OWNER-ROLLBACK', true);

-- 1. Vorbedingungen. Ein Rueckbau, der auch dann "gelingt", wenn es nichts
--    zurueckzubauen gibt, ist die Sorte Erfolgsmeldung, die `G-068` gekostet
--    hat: `rm -f` auf einen Namen, den es nie gab.
DO $$
DECLARE
    v_marker integer;
BEGIN
    SELECT count(*) INTO v_marker
    FROM workforce.schema_migrations
    WHERE migration_id = '009_bus_function_owner';
    IF v_marker <> 1 THEN
        RAISE EXCEPTION 'MIGRATION_010_009_NOT_APPLIED: Marker % statt 1', v_marker;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'workforce_owner') THEN
        RAISE EXCEPTION 'MIGRATION_010_OWNER_ROLE_MISSING';
    END IF;
END;
$$;

-- 2. Das Eigentum geht zurueck - an eine Rolle, die **gelesen** wird.
--
--    Der naheliegende Weg waere `OWNER TO workforce_app` gewesen. Das ist
--    heute richtig und morgen ein abgeschriebener Name (`G-042`): Wer den
--    Bootstrap-Benutzer der Instanz anders nennt, bekaeme eine Migration, die
--    das Eigentum an eine fremde oder gar nicht existierende Rolle uebergibt.
--
--    Gelesen wird stattdessen der Eigentuemer des Schemas `workforce` - den
--    hat `001` angelegt und `009` fasst ihn nicht an. Als zweiter, unabhaengiger
--    Anker dient der Eigentuemer von `workforce.bus_messages`. Stimmen beide
--    nicht ueberein, bricht die Migration ab, statt zu raten: Das waere ein
--    halb migrierter Zustand, und in dem ist Raten die schlechteste Antwort.
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
    v_signatur text;
    v_proc regprocedure;
    v_oids oid[] := '{}';
    v_ziel name;
    v_anker name;
    v_fremd text[];
    v_count integer := 0;
BEGIN
    SELECT r.rolname INTO v_ziel
    FROM pg_namespace n
    JOIN pg_roles r ON r.oid = n.nspowner
    WHERE n.nspname = 'workforce';
    IF v_ziel IS NULL THEN
        RAISE EXCEPTION 'MIGRATION_010_SCHEMA_OWNER_UNKNOWN';
    END IF;
    IF v_ziel = 'workforce_owner' THEN
        RAISE EXCEPTION 'MIGRATION_010_TARGET_IS_THE_ROLLED_BACK_ROLE: %', v_ziel;
    END IF;

    SELECT r.rolname INTO v_anker
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN pg_roles r ON r.oid = c.relowner
    WHERE n.nspname = 'workforce' AND c.relname = 'bus_messages';
    IF v_anker IS DISTINCT FROM v_ziel THEN
        RAISE EXCEPTION 'MIGRATION_010_OWNER_ANCHORS_DISAGREE: Schema %, bus_messages %',
            v_ziel, v_anker;
    END IF;

    -- Dieselben zwoelf, in derselben Schreibweise wie in `009`, aufgeloest
    -- ueber `to_regprocedure` (`G-075`). Eine veraenderte Signatur ist damit
    -- ein benannter Abbruch und kein stiller Treffer.
    FOREACH v_signatur IN ARRAY v_signaturen LOOP
        v_proc := to_regprocedure(v_signatur);
        IF v_proc IS NULL THEN
            RAISE EXCEPTION 'MIGRATION_010_SIGNATURE_NOT_FOUND: %', v_signatur;
        END IF;
        v_oids := v_oids || v_proc::oid;
    END LOOP;

    -- Zurueckgegeben wird nur, was `009` auch genommen hat. Gehoert eine der
    -- zwoelf jemand anderem, ist der Zustand nicht der, den diese Migration
    -- zurueckbaut - und ein Eigentumswechsel waere dann eine eigene
    -- Entscheidung mit eigener Migration.
    SELECT coalesce(array_agg(p.oid::regprocedure::text ORDER BY p.oid::regprocedure::text), '{}')
      INTO v_fremd
    FROM pg_proc p
    JOIN pg_roles r ON r.oid = p.proowner
    WHERE p.oid = ANY (v_oids) AND r.rolname <> 'workforce_owner';
    IF array_length(v_fremd, 1) IS NOT NULL THEN
        RAISE EXCEPTION 'MIGRATION_010_NOT_OWNED_BY_ROLLBACK_ROLE: %',
            array_to_string(v_fremd, ', ');
    END IF;

    FOREACH v_proc IN ARRAY v_oids::regprocedure[] LOOP
        EXECUTE format('ALTER FUNCTION %s OWNER TO %I', v_proc::text, v_ziel);
        v_count := v_count + 1;
    END LOOP;

    IF EXISTS (
        SELECT 1 FROM pg_proc p
        JOIN pg_roles r ON r.oid = p.proowner
        WHERE p.oid = ANY (v_oids) AND r.rolname <> v_ziel
    ) THEN
        RAISE EXCEPTION 'MIGRATION_010_OWNER_RETURN_FAILED';
    END IF;

    RAISE NOTICE 'Eigentuemer zurueckgegeben: % Funktionen an %', v_count, v_ziel;
END;
$$;

-- 3. Jedes Recht wird zurueckgenommen, und zwar pauschal statt als Spiegel der
--    Allowlist aus `009`.
--
--    Eine gespiegelte Liste haette denselben Fehler wie ein Rueckbau, der
--    Dateinamen raet (`G-068`): Sie waere richtig fuer die Fassung von `009`,
--    die beim Schreiben danebenlag, und stumm fuer jedes Recht, das eine
--    andere Fassung einmal erteilt hat. Der Endzustand soll nicht von der
--    Vorgeschichte abhaengen, also lautet die Aussage "keins" und nicht
--    "diese dreizehn nicht mehr". Betroffen ist ausschliesslich
--    `workforce_owner` - eine Rolle, die es ohne `009` nicht gibt.
REVOKE ALL ON ALL TABLES IN SCHEMA workforce FROM workforce_owner;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA workforce FROM workforce_owner;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA workforce FROM workforce_owner;
REVOKE ALL ON SCHEMA workforce FROM workforce_owner;
REVOKE ALL ON SCHEMA public FROM workforce_owner;

-- 4. Nachgemessen, in derselben Transaktion. Die Aussage ist bewusst total:
--    keine Relation, keine Funktion, kein Schema, keine Vorgabe-ACL, kein
--    Eigentum. Eine Teilaussage waere hier wertlos - der ganze Zweck des
--    Rueckbaus ist, dass von der Rolle nichts Wirksames uebrig bleibt.
DO $$
DECLARE
    v_relationen text[];
    v_funktionen text[];
    v_schemata text[];
    v_vorgaben integer;
    v_eigene_relationen integer;
    v_eigene_funktionen integer;
BEGIN
    SELECT coalesce(array_agg(n.nspname || '.' || c.relname || '=' || a.privilege_type
                              ORDER BY n.nspname, c.relname, a.privilege_type), '{}')
      INTO v_relationen
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    CROSS JOIN LATERAL aclexplode(c.relacl) AS a
    JOIN pg_roles r ON r.oid = a.grantee
    WHERE r.rolname = 'workforce_owner';
    IF array_length(v_relationen, 1) IS NOT NULL THEN
        RAISE EXCEPTION 'MIGRATION_010_RELATION_PRIVILEGES_REMAIN: %',
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
        RAISE EXCEPTION 'MIGRATION_010_FUNCTION_PRIVILEGES_REMAIN: %',
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
        RAISE EXCEPTION 'MIGRATION_010_SCHEMA_PRIVILEGES_REMAIN: %',
            array_to_string(v_schemata, ', ');
    END IF;

    -- Vorgabe-ACLs erteilt `009` nicht. Sie stehen hier trotzdem, weil eine
    -- uebersehene Vorgabe der Rolle **kuenftige** Objekte zuspielen wuerde -
    -- ein Recht, das erst nach dem Rueckbau entsteht, faende keine Pruefung
    -- mehr vor.
    SELECT count(*) INTO v_vorgaben
    FROM pg_default_acl d
    CROSS JOIN LATERAL aclexplode(d.defaclacl) AS a
    JOIN pg_roles r ON r.oid = a.grantee
    WHERE r.rolname = 'workforce_owner';
    IF v_vorgaben <> 0 THEN
        RAISE EXCEPTION 'MIGRATION_010_DEFAULT_ACL_REMAINS: %', v_vorgaben;
    END IF;

    -- Ueber alle Schemata, nicht nur ueber `workforce` und `public`: Die
    -- Aussage lautet "besitzt nichts", und eine Aussage mit Schemafilter waere
    -- eine andere.
    SELECT count(*) INTO v_eigene_relationen
    FROM pg_class c
    JOIN pg_roles r ON r.oid = c.relowner
    WHERE r.rolname = 'workforce_owner';
    IF v_eigene_relationen <> 0 THEN
        RAISE EXCEPTION 'MIGRATION_010_OWNER_STILL_OWNS_RELATIONS: %', v_eigene_relationen;
    END IF;

    SELECT count(*) INTO v_eigene_funktionen
    FROM pg_proc p
    JOIN pg_roles r ON r.oid = p.proowner
    WHERE r.rolname = 'workforce_owner';
    IF v_eigene_funktionen <> 0 THEN
        RAISE EXCEPTION 'MIGRATION_010_OWNER_STILL_OWNS_FUNCTIONS: %', v_eigene_funktionen;
    END IF;

    RAISE NOTICE 'workforce_owner ist rechtlos und besitzt nichts';
END;
$$;

INSERT INTO workforce.schema_migrations (migration_id, description)
VALUES ('010_bus_function_owner_rollback',
        'Rollback of 009: the twelve bus SECURITY DEFINER functions are owned by '
        'the workforce schema owner again and workforce_owner holds no privilege '
        'and owns no object; the role itself is deliberately left in place');

COMMIT;
