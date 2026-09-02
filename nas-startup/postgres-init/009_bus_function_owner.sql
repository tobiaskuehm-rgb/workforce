\set ON_ERROR_STOP on

-- Die zwoelf SECURITY-DEFINER-Busfunktionen laufen nicht mehr als Superuser.
--
-- Review finding G-045. `G-025` wollte `workforce_app` das SUPERUSER-Attribut
-- nehmen. Das geht nicht: `initdb` macht `POSTGRES_USER` zum
-- Bootstrap-Superuser, und PostgreSQL lehnt `ALTER ROLE ... NOSUPERUSER`
-- darauf ab. Gemessen am 2026-09-01, Nachweis in
-- `evidence/2026-09-01_g025_bootstrap_superuser.md`.
--
-- Der Befund war damit nicht erledigt, sondern falsch zugeschnitten. Die
-- eigentliche Frage lautet nicht "darf workforce_app Superuser sein" - er muss
-- es bleiben -, sondern **als wer laufen die Funktionen**. Eine
-- SECURITY-DEFINER-Funktion laeuft als ihr Eigentümer; solange das der
-- Superuser ist, laeuft jeder Busaufruf mit Superuserrechten.
--
-- Am 2026-09-02 gemessener Ausgangszustand:
--
--     security_definer | eigentuemer   | anzahl
--     t                | workforce_app |     12
--     f                | workforce_app |     15
--     workforce_app: rolsuper = t (einziger Superuser)
--
-- Diese Migration legt einen eigenen Eigentümer an und gibt ihm genau die
-- Rechte, die die Funktionen brauchen - **nicht** das Eigentum an den
-- Tabellen. Das ist der ganze Gewinn: Nur der Eigentuemer einer Tabelle oder
-- ein Superuser kann `ALTER TABLE ... DISABLE TRIGGER`, und genau darauf
-- beruhen die Append-only-Zusicherungen aus `006`/`007`. Ein Eigentuemer, der
-- die Tabellen nicht besitzt, kann das Audit nicht abschalten.
--
-- **Die zwoelf sind gepinnt, nicht gesucht** (Review finding G-071). Ein
-- erster Entwurf waehlte dynamisch jede SECURITY-DEFINER-Funktion im Schema
-- `workforce`, waehrend der Kommentar daneben von den zwoelf Busfunktionen
-- sprach. Heute waere das dasselbe; nach einer Anwendung von `004` waere es
-- etwas anderes: Knowledge bringt sieben eigene SECURITY-DEFINER-Funktionen
-- mit, und die waeren stillschweigend in den Bus-Eigentuemerkontext gewandert.
-- Genau das darf nicht als Nebenwirkung passieren - Knowledge braucht seine
-- eigene Eigentuemerentscheidung, und diese Migration nimmt sie nicht vorweg.
-- Steht etwas anderes im Katalog als die zwoelf, bricht sie ab.
--
-- Die uebrigen fuenfzehn Funktionen laufen ohnehin als Aufrufer; ihr Eigentum
-- zu verschieben haette keine Sicherheitswirkung und nur die Angriffsflaeche
-- vergroessert.
--
-- Vorbedingung, am 2026-09-02 geprueft: Alle zwoelf pinnen bereits ihren
-- `search_path` (`proconfig IS NOT NULL`), sonst waere ein Eigentuemerwechsel
-- die falsche Reihenfolge.
--
-- **Nicht angewendet.** Diese Migration hat ihr eigenes Gate in `compose.yaml`
-- und braucht ein eigenes Fenster mit eigener Freigabe. Ein Fehlgriff bei den
-- Rechten legt den Bus still - deshalb der Abnahmetest daneben und der
-- Rueckbau als Teil derselben Entscheidung.

BEGIN;

SELECT set_config('app.actor_id', 'SYSTEM-MIGRATION', true);
SELECT set_config('app.request_id', 'MIG-009-BUS-FUNCTION-OWNER', true);

-- 1. Der Eigentuemer. NOLOGIN, weil niemand sich als er anmelden soll: Er
--    existiert ausschliesslich als Rechtekontext der Funktionen. Deshalb
--    braucht er auch kein Passwort und kann - anders als die Login-Rollen aus
--    `007` - hier angelegt werden, statt vorher von Hand.
--
--    NOREPLICATION gehoert dazu (`G-071`): Eine Replikationsverbindung liest
--    den gesamten WAL-Strom und damit jede Tabelle, an der die Rechte unten
--    gerade sorgfaeltig vorbeigehen.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'workforce_owner') THEN
        CREATE ROLE workforce_owner
            NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
            NOINHERIT NOBYPASSRLS NOREPLICATION;
    END IF;
END;
$$;

-- Falls die Rolle schon existierte: die Attribute sind Teil der Zusicherung,
-- nicht Teil des Zufalls.
ALTER ROLE workforce_owner
    NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
    NOINHERIT NOBYPASSRLS NOREPLICATION;

-- 2. Die zwoelf, als Name und Stelligkeit. Die Stelligkeit steht dabei, weil
--    sie eine Ueberladung von der gemeinten Funktion unterscheidet - dieselbe
--    Frage wie in `G-044`, wo fuenf Argumente statt dreizehn einen Nachweis
--    erzeugt haben, der gruen aussah und nichts pruefte. Die Typen stehen
--    nicht dabei: Ihre Schreibweise im Katalog ist eine andere als in der
--    Quelle (`timestamptz` wird `timestamp with time zone`), und ein
--    abgeschriebener Typname waere genau die Sorte Gedaechtnisleistung, die
--    dieses Projekt nicht will. `test_bus_function_owner.py` haelt die Liste
--    stattdessen gegen `002` und `005`.
--
-- 2a. Und die Gegenprobe: Der Katalog muss **genau** diese Menge enthalten.
--     Ein Zuviel heisst, dass eine fremde Migration SECURITY-DEFINER-
--     Funktionen mitgebracht hat - heute waere das Knowledge aus `004`.
--     Dann bricht diese Migration ab, statt eine Entscheidung zu treffen,
--     die ihr nicht gehoert.
DO $$
DECLARE
    v_erwartet text[] := ARRAY[
        'bus_authenticate:2',
        'bus_send_message:13',
        'bus_acknowledge_message:6',
        'bus_list_messages:4',
        'bus_create_task:11',
        'bus_list_tasks:4',
        'bus_transition_task:6',
        'bus_create_handoff:12',
        'bus_list_handoffs:4',
        'bus_transition_handoff:6',
        'bus_identify_for_audit:2',
        'bus_record_denial:8'
    ];
    v_gefunden text[];
    v_zuviel text[];
    v_fehlend text[];
BEGIN
    SELECT coalesce(array_agg(p.proname || ':' || p.pronargs
                              ORDER BY p.proname, p.pronargs), '{}')
      INTO v_gefunden
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'workforce' AND p.prosecdef;

    SELECT coalesce(array_agg(x), '{}') INTO v_zuviel
    FROM unnest(v_gefunden) AS x WHERE x <> ALL (v_erwartet);
    SELECT coalesce(array_agg(x), '{}') INTO v_fehlend
    FROM unnest(v_erwartet) AS x WHERE x <> ALL (v_gefunden);

    IF array_length(v_zuviel, 1) IS NOT NULL THEN
        RAISE EXCEPTION
            'MIGRATION_009_UNEXPECTED_SECURITY_DEFINER: % - diese Funktionen '
            'gehoeren nicht zum Bus. Ihr Eigentum ist eine eigene Entscheidung '
            'mit eigener Migration (G-071).', array_to_string(v_zuviel, ', ');
    END IF;
    IF array_length(v_fehlend, 1) IS NOT NULL THEN
        RAISE EXCEPTION 'MIGRATION_009_MISSING_BUS_FUNCTIONS: %',
            array_to_string(v_fehlend, ', ');
    END IF;
END;
$$;

-- 3. Rechte, als Allowlist statt als `ALL TABLES` (`G-071`). Die Liste ist aus
--    den Rumpfen der zwoelf Funktionen abgeleitet und nicht geschaetzt;
--    `test_bus_function_owner.py` leitet sie erneut aus `002`/`005` ab und
--    vergleicht. Ein `ALL TABLES` haette nach einer Anwendung von `004` auch
--    saemtliche Knowledge-Tabellen umfasst.
--
--    **Kein DELETE**: Daten werden in dieser Datenbank nicht geloescht,
--    sondern in einen Status ueberfuehrt. `prevent_hard_delete` blockt es
--    ohnehin - das Recht gar nicht erst zu erteilen ist die erste Linie,
--    der Trigger die zweite.
--
--    Das REVOKE davor macht den Endzustand unabhaengig davon, was eine
--    fruehere Fassung dieser Migration der Rolle einmal erteilt hat. Es
--    betrifft ausschliesslich `workforce_owner`, also eine Rolle, die es ohne
--    diese Datei nicht gibt.
REVOKE ALL ON ALL TABLES IN SCHEMA workforce FROM workforce_owner;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA workforce FROM workforce_owner;
REVOKE ALL ON SCHEMA public FROM workforce_owner;

GRANT USAGE ON SCHEMA workforce TO workforce_owner;

-- Nur gelesen: Identitaet, Mitgliedschaft, Kanal, Credential, Capability,
-- Route. Das ist der gesamte Eingabesatz von `bus_authenticate` und der
-- Routenpruefung.
GRANT SELECT ON
    workforce.projects,
    workforce.employees,
    workforce.employee_project_memberships,
    workforce.active_project_members,
    workforce.bus_channels,
    workforce.bus_credentials,
    workforce.bus_member_capabilities,
    workforce.bus_route_allowlist
TO workforce_owner;

-- Gelesen und fortgeschrieben: die drei Bus-Datensatztypen.
GRANT SELECT, INSERT, UPDATE ON
    workforce.bus_messages,
    workforce.bus_tasks,
    workforce.bus_handoffs
TO workforce_owner;

-- Nur beschrieben, nie gelesen und nie geaendert: die beiden Auditpfade.
-- `bus_events` fuellt der Trigger `bus_record_change`; der ist **nicht**
-- SECURITY DEFINER und laeuft im Aufruf deshalb als `workforce_owner`.
-- Ohne dieses INSERT stuende die Auditspur still - der teuerste Ausgang
-- einer zu engen Allowlist, und der Grund, warum `g045_owner_probe.py`
-- ihn misst statt ihn zu behaupten.
GRANT INSERT ON
    workforce.bus_events,
    workforce.bus_denials
TO workforce_owner;

-- 3b. **Kein** EXECUTE auf die Triggerfunktionen - und das ist eine
--     nachgeschlagene Entscheidung, keine Annahme.
--
--     Die neun Guard- und Auditfunktionen (`bus_record_change`,
--     `bus_guard_*`, `bus_touch_versioned_row`) sind nicht SECURITY DEFINER
--     und bleiben bei `workforce_app`. Nach dem Eigentumswechsel feuern sie in
--     einem Kontext, in dem `workforce_owner` der ausfuehrende Nutzer ist -
--     der hat auf sie kein EXECUTE, weil `007` es von PUBLIC entzogen hat.
--
--     Die Frage war, ob das die Trigger stillegt. Antwort aus der
--     PostgreSQL-17-Dokumentation zu CREATE TRIGGER:
--
--       "To create or replace a trigger on a table, the user must have the
--        TRIGGER privilege on the table. The user must also have EXECUTE
--        privilege on the trigger function."
--
--     Das ist die Anforderung beim **Anlegen** des Triggers, nicht beim
--     Ausloesen; beim Feuern wird nicht erneut geprueft. Die Trigger dieser
--     Datenbank sind in `002` von `workforce_app` angelegt worden, also lange
--     vor dem REVOKE - sie feuern weiter.
--
--     Ein erster Entwurf dieser Migration erteilte das EXECUTE vorsichtshalber.
--     Ein Recht, das niemand braucht, ist aber kein Sicherheitsnetz, sondern
--     eine Rechteerweiterung ohne Begruendung. `g045_owner_probe.py` misst es
--     vor dem Fenster empirisch nach; bis dahin traegt die Dokumentation die
--     Aussage, und dass sie sie traegt, steht hier.
--
-- 3c. **Keine Sequenzrechte, und das ist nicht belegt, sondern gemessen.**
--     Jede Identitaetsspalte dieser Datenbank ist
--     `GENERATED ALWAYS AS IDENTITY`; ihre Sequenz ist an die Spalte gebunden.
--     Ob ein INSERT dafuer USAGE auf der Sequenz braucht, sagt die
--     PostgreSQL-17-Dokumentation zu CREATE TABLE nicht - nachgeschlagen am
--     2026-09-02, und ein Recht auf Verdacht zu erteilen waere derselbe
--     Fehlgriff wie das EXECUTE oben. Der Probelauf schreibt deshalb ueber die
--     Auditspur in `bus_events`, deren Schluessel genau so eine Spalte ist:
--     Geht es durch, braucht es nichts; scheitert es, nennt der Fehler die
--     Sequenz und das Recht kommt gezielt dazu.

-- 4. Eigentumsuebergang, ausschliesslich fuer die gepinnte Menge. Die
--    Signatur kommt aus dem Katalog (`regprocedure`), nie aus dem Gedaechtnis.
DO $$
DECLARE
    v_erwartet text[] := ARRAY[
        'bus_authenticate:2', 'bus_send_message:13', 'bus_acknowledge_message:6',
        'bus_list_messages:4', 'bus_create_task:11', 'bus_list_tasks:4',
        'bus_transition_task:6', 'bus_create_handoff:12', 'bus_list_handoffs:4',
        'bus_transition_handoff:6', 'bus_identify_for_audit:2',
        'bus_record_denial:8'
    ];
    v_signature text;
    v_count integer := 0;
BEGIN
    FOR v_signature IN
        SELECT p.oid::regprocedure::text
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'workforce'
          AND p.prosecdef
          AND p.proname || ':' || p.pronargs = ANY (v_erwartet)
    LOOP
        EXECUTE format('ALTER FUNCTION %s OWNER TO workforce_owner', v_signature);
        v_count := v_count + 1;
    END LOOP;

    IF v_count <> array_length(v_erwartet, 1) THEN
        RAISE EXCEPTION 'MIGRATION_009_OWNER_TRANSFER_INCOMPLETE: % von %',
            v_count, array_length(v_erwartet, 1);
    END IF;
    RAISE NOTICE 'Eigentuemer gewechselt: % Funktionen', v_count;
END;
$$;

-- 5. Die Zusicherung, in derselben Transaktion geprueft. Sie ist auf die
--    zwoelf eingegrenzt und nicht auf "alles im Schema": Nach einer spaeteren
--    Anwendung von `004` waeren die Knowledge-Funktionen wieder beim
--    Bootstrap-Superuser, und eine schemaweite Aussage waere ab dann
--    stillschweigend falsch (`G-071`). Was diese Migration verspricht, ist
--    genau das, was sie angefasst hat.
DO $$
DECLARE
    v_rest integer;
    v_fremd integer;
BEGIN
    SELECT count(*) INTO v_rest
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    JOIN pg_roles r ON r.oid = p.proowner
    WHERE n.nspname = 'workforce' AND p.prosecdef
      AND p.proname LIKE 'bus\_%'
      AND r.rolname <> 'workforce_owner';
    IF v_rest <> 0 THEN
        RAISE EXCEPTION 'MIGRATION_009_STILL_SUPERUSER_OWNED: %', v_rest;
    END IF;

    -- Und der Eigentuemer hat keine Tabelle bekommen. Besaesse er eine,
    -- koennte er ihre Trigger abschalten, und die Migration haette das
    -- Problem nur umbenannt.
    SELECT count(*) INTO v_fremd
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN pg_roles r ON r.oid = c.relowner
    WHERE n.nspname IN ('workforce', 'public')
      AND r.rolname = 'workforce_owner';
    IF v_fremd <> 0 THEN
        RAISE EXCEPTION 'MIGRATION_009_OWNER_OWNS_RELATIONS: %', v_fremd;
    END IF;
END;
$$;

INSERT INTO workforce.schema_migrations (migration_id, description)
VALUES ('009_bus_function_owner',
        'The twelve bus SECURITY DEFINER functions are owned by workforce_owner, '
        'a non-superuser that owns no relation and holds an explicit table '
        'allowlist, and therefore cannot disable the audit triggers');

COMMIT;
