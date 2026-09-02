\set ON_ERROR_STOP on

-- Die zwoelf SECURITY-DEFINER-Funktionen laufen nicht mehr als Superuser.
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
-- **Nur die zwoelf SECURITY-DEFINER-Funktionen wechseln den Eigentuemer.** Die
-- uebrigen fuenfzehn laufen ohnehin als Aufrufer; ihr Eigentum zu verschieben
-- haette keine Sicherheitswirkung und nur die Angriffsflaeche vergroessert.
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
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'workforce_owner') THEN
        CREATE ROLE workforce_owner
            NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
    END IF;
END;
$$;

-- Falls die Rolle schon existierte: die Attribute sind Teil der Zusicherung,
-- nicht Teil des Zufalls.
ALTER ROLE workforce_owner
    NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;

-- 2. Rechte. Genau so viel, wie die Funktionen zum Arbeiten brauchen.
--    **Kein DELETE**: Daten werden in dieser Datenbank nicht geloescht,
--    sondern in einen Status ueberfuehrt. `prevent_hard_delete` blockt es
--    ohnehin - das Recht gar nicht erst zu erteilen ist die erste Linie,
--    der Trigger die zweite.
GRANT USAGE ON SCHEMA workforce, public TO workforce_owner;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA workforce TO workforce_owner;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO workforce_owner;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA workforce TO workforce_owner;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO workforce_owner;

-- 2b. EXECUTE auf die Triggerfunktionen - und der Grund, warum das hier steht,
--     ist eine **nicht belegte** Annahme.
--
--     Die neun Guard- und Auditfunktionen (`bus_record_change`,
--     `bus_guard_*`, `bus_touch_versioned_row`) sind nicht SECURITY DEFINER
--     und bleiben deshalb bei `workforce_app`. Nach dem Eigentumswechsel
--     feuern sie in einem Kontext, in dem `workforce_owner` der ausfuehrende
--     Nutzer ist. Nach meinem Verstaendnis prueft PostgreSQL EXECUTE auf eine
--     Triggerfunktion beim `CREATE TRIGGER`, nicht beim Ausloesen - dann waere
--     dieser GRANT ueberfluessig.
--
--     **Geprueft habe ich das nicht.** `007` hat EXECUTE von PUBLIC entzogen;
--     traefe meine Annahme nicht zu, stuende der Bus nach dieser Migration
--     still. Der GRANT kostet nichts und nimmt die Frage aus dem Fenster
--     heraus. Wer sie beantworten will, misst es in einem Wegwerf-Container
--     nach und kann diesen Block dann mit Begruendung entfernen.
DO $$
DECLARE
    v_signature text;
BEGIN
    FOR v_signature IN
        SELECT format('workforce.%I(%s)', p.proname,
                      pg_get_function_identity_arguments(p.oid))
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'workforce'
          AND NOT p.prosecdef
    LOOP
        EXECUTE format('GRANT EXECUTE ON FUNCTION %s TO workforce_owner', v_signature);
    END LOOP;
END;
$$;

-- 3. Eigentumsuebergang, ausschliesslich fuer SECURITY DEFINER.
DO $$
DECLARE
    v_signature text;
    v_count integer := 0;
BEGIN
    FOR v_signature IN
        SELECT format('workforce.%I(%s)', p.proname,
                      pg_get_function_identity_arguments(p.oid))
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'workforce'
          AND p.prosecdef
    LOOP
        EXECUTE format('ALTER FUNCTION %s OWNER TO workforce_owner', v_signature);
        v_count := v_count + 1;
    END LOOP;

    IF v_count = 0 THEN
        RAISE EXCEPTION 'MIGRATION_009_NO_SECURITY_DEFINER_FUNCTIONS';
    END IF;
    RAISE NOTICE 'Eigentuemer gewechselt: % Funktionen', v_count;
END;
$$;

-- 4. Die Zusicherung, in derselben Transaktion geprueft. Bleibt eine
--    SECURITY-DEFINER-Funktion beim Superuser, war der Wechsel unvollstaendig
--    und die ganze Migration faellt zurueck.
DO $$
DECLARE
    v_rest integer;
BEGIN
    SELECT count(*) INTO v_rest
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    JOIN pg_roles r ON r.oid = p.proowner
    WHERE n.nspname = 'workforce' AND p.prosecdef AND r.rolsuper;
    IF v_rest <> 0 THEN
        RAISE EXCEPTION 'MIGRATION_009_STILL_SUPERUSER_OWNED: %', v_rest;
    END IF;
END;
$$;

INSERT INTO workforce.schema_migrations (migration_id, description)
VALUES ('009_bus_function_owner',
        'SECURITY DEFINER functions owned by workforce_owner, a non-superuser '
        'that does not own the tables and therefore cannot disable the audit triggers');

COMMIT;
