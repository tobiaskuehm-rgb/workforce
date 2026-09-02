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

-- 2. Genau die zwoelf, ueber ihre vollstaendige Identitaetssignatur.
--
--    Die erste Fassung fragte "0 beim Superuser" und ">0 vorhanden" - eine zu
--    breite Verschiebung haette das bestanden (`G-071`). Die zweite pinnte
--    `name:stelligkeit` und haette eine gleichnamige Funktion mit gleicher
--    Argumentzahl und anderen Parametertypen nicht unterschieden (`G-075`).
--    Aufgeloest wird deshalb ueber `to_regprocedure()`, und jede weitere
--    Aussage haengt an der **OID** - derselben, die auch die Migration
--    verwendet hat.
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
    v_zuviel text[];
BEGIN
    FOREACH v_signatur IN ARRAY v_signaturen LOOP
        v_proc := to_regprocedure(v_signatur);
        IF v_proc IS NULL THEN
            RAISE EXCEPTION 'ACCEPTANCE_009_SIGNATURE_NOT_FOUND: %', v_signatur;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE oid = v_proc::oid AND prosecdef) THEN
            RAISE EXCEPTION 'ACCEPTANCE_009_NOT_SECURITY_DEFINER: %', v_signatur;
        END IF;
        IF NOT EXISTS (
            SELECT 1 FROM pg_proc p JOIN pg_roles r ON r.oid = p.proowner
            WHERE p.oid = v_proc::oid AND r.rolname = 'workforce_owner'
        ) THEN
            RAISE EXCEPTION 'ACCEPTANCE_009_NOT_TRANSFERRED: %', v_signatur;
        END IF;
        v_oids := v_oids || v_proc::oid;
    END LOOP;

    -- Die Gegenrichtung: nichts ausserhalb der zwoelf gehoert ihm. Ohne das
    -- bestuende der Test auch ueber einer zu breiten Verschiebung.
    SELECT coalesce(array_agg(p.oid::regprocedure::text ORDER BY 1), '{}')
      INTO v_zuviel
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    JOIN pg_roles r ON r.oid = p.proowner
    WHERE n.nspname = 'workforce' AND r.rolname = 'workforce_owner'
      AND NOT (p.oid = ANY (v_oids));
    IF array_length(v_zuviel, 1) IS NOT NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_UNEXPECTED_OWNERSHIP: %',
            array_to_string(v_zuviel, ', ');
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

-- 4. Die Rechte sind **genau** die Allowlist. Ein `ALL TABLES` waere hier
--    sofort sichtbar, und nach einer Anwendung von `004` haette es auch
--    saemtliche Knowledge-Tabellen umfasst (`G-071`).
--
--    Gelesen wird der **Katalog**, nicht `information_schema.role_table_grants`
--    (`G-074`). Zwei Gruende: Die Sicht zeigt nur Rechte, bei denen der
--    aufrufende Benutzer Erteiler, Empfaenger oder Mitglied ist, und die erste
--    Fassung gruppierte ohne Schema - zwei gleichnamige Tabellen in zwei
--    Schemata waeren zu einer Zeile verschmolzen. Der Schluessel traegt das
--    Schema deshalb mit, und `aclexplode` erfasst jede Relationsart, also auch
--    eine Sequenz oder eine Sicht ausserhalb von `workforce`.
DO $$
DECLARE
    v_erwartet text[] := ARRAY[
        'workforce.active_project_members=SELECT',
        'workforce.bus_channels=SELECT',
        'workforce.bus_credentials=SELECT',
        'workforce.bus_denials=INSERT',
        'workforce.bus_events=INSERT',
        'workforce.bus_handoffs=INSERT,SELECT,UPDATE',
        'workforce.bus_member_capabilities=SELECT',
        'workforce.bus_messages=INSERT,SELECT,UPDATE',
        'workforce.bus_route_allowlist=SELECT',
        'workforce.bus_tasks=INSERT,SELECT,UPDATE',
        'workforce.employee_project_memberships=SELECT',
        'workforce.employees=SELECT',
        'workforce.projects=SELECT'
    ];
    v_ist text[];
    v_fehlend text[];
    v_zuviel text[];
BEGIN
    SELECT coalesce(array_agg(zeile ORDER BY zeile), '{}') INTO v_ist
    FROM (
        SELECT n.nspname || '.' || c.relname || '=' ||
               string_agg(DISTINCT a.privilege_type, ',' ORDER BY a.privilege_type) AS zeile
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        CROSS JOIN LATERAL aclexplode(c.relacl) AS a
        JOIN pg_roles r ON r.oid = a.grantee
        WHERE r.rolname = 'workforce_owner'
        GROUP BY n.nspname, c.relname
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

-- 4b. Kein **direkter** Grant auf das Schema `public`.
--
--     Die erste Fassung fragte hier `has_schema_privilege(..., 'public',
--     'USAGE')` und erwartete `false`. Das waere auf jeder frischen
--     PostgreSQL-17-Instanz falsch rot geworden (`G-074`): Die Funktion
--     beantwortet das **effektive** Recht, und die Dokumentation zu Schemata
--     sagt fuer `public` ausdruecklich "By default, everyone has that
--     privilege on the schema public" - erteilt an die Pseudorolle `PUBLIC`.
--     Ein Widerruf allein bei `workforce_owner` kann ein ueber `PUBLIC`
--     geerbtes Recht nicht negieren, und keine der Migrationen `001` bis `009`
--     entzieht `USAGE ON SCHEMA public FROM PUBLIC`.
--
--     Das global zu tun waere eine Rechteentscheidung weit ausserhalb dieser
--     Busmigration. Die Zusicherung, die 009 wirklich macht, lautet deshalb:
--     **kein direkter Eintrag fuer `workforce_owner`**. Genau das wird hier
--     gelesen. `aclexplode` gibt fuer `PUBLIC` die Grantee-OID `0`, zu der es
--     keine Zeile in `pg_roles` gibt - der Join blendet die Pseudorolle also
--     aus, ohne dass es dafuer eine Sonderregel braucht. Ist `nspacl` NULL,
--     gilt die Voreinstellung und es gibt definitionsgemaess keinen direkten
--     Eintrag.
DO $$
DECLARE
    v_direkt text[];
    v_schema_rechte text;
BEGIN
    SELECT coalesce(array_agg(n.nspname || ':' || a.privilege_type
                              ORDER BY n.nspname, a.privilege_type), '{}')
      INTO v_direkt
    FROM pg_namespace n
    CROSS JOIN LATERAL aclexplode(n.nspacl) AS a
    JOIN pg_roles r ON r.oid = a.grantee
    WHERE r.rolname = 'workforce_owner'
      AND n.nspname <> 'workforce';
    IF array_length(v_direkt, 1) IS NOT NULL THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_FOREIGN_SCHEMA_GRANTED: %',
            array_to_string(v_direkt, ', ');
    END IF;

    -- Und auf `workforce` hat er **genau** USAGE - nicht mindestens USAGE.
    --
    -- Die erste Fassung fragte nur nach dem Vorhandensein. Eine Rolle, die
    -- diese Migration bereits vorfindet, koennte `CREATE` auf dem Schema
    -- mitbringen; die Migration entzog es nicht und der Test sah es nicht.
    -- `CREATE` ist hier kein kleines Extra: Damit legt die Rolle eigene
    -- Relationen in `workforce` an, ist deren Eigentuemerin und kann auf
    -- ihnen Trigger abschalten. Das ist genau der Weg, den 009 zumachen soll.
    SELECT coalesce(string_agg(DISTINCT a.privilege_type, ',' ORDER BY a.privilege_type),
                    '(keine)')
      INTO v_schema_rechte
    FROM pg_namespace n
    CROSS JOIN LATERAL aclexplode(n.nspacl) AS a
    JOIN pg_roles r ON r.oid = a.grantee
    WHERE r.rolname = 'workforce_owner' AND n.nspname = 'workforce';
    IF v_schema_rechte <> 'USAGE' THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_WORKFORCE_SCHEMA_PRIVILEGES: % statt USAGE',
            v_schema_rechte;
    END IF;
END;
$$;

-- 5. Die API kann ihre Funktionen weiterhin aufrufen - und nur die.
--
--    Ein Eigentuemerwechsel nimmt GRANTs nicht weg, aber ein Abnahmetest, der
--    nur Verbote prueft, besteht auch auf einem stillgelegten Bus. Geprueft
--    wird an derselben OID (`G-075`): Die erste Fassung suchte nur den
--    Funktionsnamen, und ein zweiter Overload gleichen Namens haette die
--    Bedingung miterfuellt.
--
--    `bus_authenticate` und `bus_identify_for_audit` sind interne Helfer, die
--    nur aus den anderen Funktionen heraus laufen; `007` hat der API das
--    EXECUTE darauf absichtlich nicht erteilt. Meine erste Fassung dieses
--    Tests verlangte es - das waere eine Aufweichung gewesen, und die Messung
--    gegen die Produktion hat sie gefunden. Die zehn aufrufbaren werden
--    deshalb nicht als dritte Liste gefuehrt, sondern aus den zwoelf minus
--    diesen beiden abgeleitet; zwei Listen koennen nicht auseinanderlaufen.
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
    v_darf boolean;
    v_hat boolean;
    v_fehlend text := '';
    v_zuviel text := '';
    v_aufrufbar integer := 0;
BEGIN
    FOREACH v_signatur IN ARRAY v_signaturen LOOP
        v_proc := to_regprocedure(v_signatur);
        IF v_proc IS NULL THEN
            RAISE EXCEPTION 'ACCEPTANCE_009_SIGNATURE_NOT_FOUND: %', v_signatur;
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
        RAISE EXCEPTION 'ACCEPTANCE_009_API_LOST_EXECUTE:%', v_fehlend;
    END IF;
    IF v_zuviel <> '' THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_API_REACHES_INTERNALS:%', v_zuviel;
    END IF;
    IF v_aufrufbar <> 10 THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_CALLABLE_COUNT: % statt 10', v_aufrufbar;
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
    FROM pg_class c
    CROSS JOIN LATERAL aclexplode(c.relacl) AS a
    JOIN pg_roles r ON r.oid = a.grantee
    WHERE r.rolname = 'workforce_owner';
    IF v_count = 0 THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_SELF_CHECK_FAILED: keine Rechte sichtbar';
    END IF;

    -- Und die Gegenprobe zu `G-074`: Der Katalogblick muss die Pseudorolle
    -- PUBLIC ausblenden, sonst haette der Test oben denselben Fehler wie die
    -- erste Fassung - nur an einer anderen Stelle. `public` traegt die
    -- Vorgabefreigabe an PUBLIC; sie darf hier nicht als direkter Eintrag
    -- auftauchen.
    -- Diese Pruefung war in ihrer ersten Fassung **logisch leer**: Sie
    -- verlangte `a.grantee = 0` und jointe gleichzeitig auf `pg_roles`, wo es
    -- zur OID 0 keine Zeile gibt. Der Join hat jede Zeile entfernt, `EXISTS`
    -- war immer falsch, und der Waechter konnte nie anschlagen - ein Waechter,
    -- der nicht hinsehen kann, meldet PASS. Die beiden Tatsachen brauchen
    -- deshalb zwei getrennte Abfragen.
    --
    -- (a) Die Vorgabefreigabe an PUBLIC existiert wirklich. Ohne sie waere
    --     die Aussage von Abschnitt 4b gruen ueber einer leeren Menge.
    IF NOT EXISTS (
        SELECT 1 FROM pg_namespace n
        CROSS JOIN LATERAL aclexplode(n.nspacl) AS a
        WHERE n.nspname = 'public' AND a.grantee = 0 AND a.privilege_type = 'USAGE'
    ) THEN
        RAISE EXCEPTION
            'ACCEPTANCE_009_SELF_CHECK_FAILED: keine PUBLIC-Vorgabe auf public - '
            'dann prueft Abschnitt 4b nichts';
    END IF;

    -- (b) Und der Join auf `pg_roles`, den Abschnitt 4b verwendet, blendet
    --     genau diesen Eintrag aus. Erst beides zusammen belegt, dass dort
    --     die Pseudorolle uebergangen wird und nicht etwa alles.
    IF EXISTS (
        SELECT 1 FROM pg_namespace n
        CROSS JOIN LATERAL aclexplode(n.nspacl) AS a
        JOIN pg_roles r ON r.oid = a.grantee
        WHERE n.nspname = 'public' AND a.grantee = 0
    ) THEN
        RAISE EXCEPTION 'ACCEPTANCE_009_SELF_CHECK_FAILED: PUBLIC nicht ausgeblendet';
    END IF;

    RAISE NOTICE 'Bus function owner acceptance: PASS';
END;
$$;

ROLLBACK;
