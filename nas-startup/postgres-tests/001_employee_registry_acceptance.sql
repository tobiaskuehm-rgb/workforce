\set ON_ERROR_STOP on

BEGIN;

DO $$
DECLARE
    v_count integer;
BEGIN
    -- Was hier bis 2026-09-02 stand, war `count(*) <> 5` (review finding
    -- G-049). Das war eine Aussage ueber die Belegschaft vom August, keine
    -- ueber das System: inzwischen gibt es neun Eintraege, weil
    -- AGENT-ENG-001 fuer die Agentenlaufzeit dazukam und drei
    -- Telegram-Identitaeten angelegt und wieder widerrufen wurden. Ein
    -- Abnahmetest, der eine Bestandsgroesse festschreibt, laesst sich genau
    -- einmal gegen die Produktion fahren - und der Kopf dieser Datei sagt,
    -- dass er jederzeit laufen darf.
    --
    -- Geprueft wird deshalb, was dauerhaft gilt: die fuenf Bootstrap-
    -- Identitaeten sind da, und keine Identitaet existiert ohne Herkunft.
    SELECT count(*) INTO v_count
    FROM workforce.employees
    WHERE employee_id IN ('SAO-001', 'AI-ENG-001', 'PEO-001', 'RAS-001', 'EAC-001');
    IF v_count <> 5 THEN
        RAISE EXCEPTION 'Bootstrap identities incomplete: found % of 5', v_count;
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.employees
    WHERE nullif(btrim(coalesce(source_ref, '')), '') IS NULL;
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'Employees without a source reference: %', v_count;
    END IF;

    -- Auch hier eine Bestandszahl statt einer Eigenschaft (G-049): aktiv
    -- sind inzwischen sechs, weil AGENT-ENG-001 dazukam. Geprueft wird, dass
    -- die fuenf Bootstrap-Identitaeten Mitglied sind - das aendert sich nicht,
    -- wenn jemand hinzukommt.
    SELECT count(*) INTO v_count
    FROM workforce.active_project_members
    WHERE project_id = 'START-UP'
      AND employee_id IN ('SAO-001', 'AI-ENG-001', 'PEO-001', 'RAS-001', 'EAC-001');
    IF v_count <> 5 THEN
        RAISE EXCEPTION 'Bootstrap members not active: found % of 5', v_count;
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.registry_events
    WHERE actor_id = 'SYSTEM-BOOTSTRAP'
      AND request_id = 'MIG-001-EMPLOYEE-REGISTRY';
    IF v_count <> 11 THEN
        RAISE EXCEPTION 'Expected 11 bootstrap audit events, found %', v_count;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM workforce.employees
        WHERE employee_id = 'EAC-001'
          AND display_name = 'Nora'
          AND employment_status = 'PROBATION'
          AND source_ref = 'DEC-013'
    ) THEN
        RAISE EXCEPTION 'Nora identity or source reference is missing or inconsistent.';
    END IF;
END;
$$;

DO $$
BEGIN
    BEGIN
        INSERT INTO workforce.employees (
            employee_id,
            display_name,
            role_code,
            role_title,
            organizational_area,
            employment_status,
            source_ref
        ) VALUES (
            'invalid id',
            'Invalid',
            'TEST_ROLE',
            'Invalid test row',
            'Acceptance Test',
            'PROBATION',
            'TEST'
        );
        RAISE EXCEPTION 'Invalid employee ID was accepted.';
    EXCEPTION
        WHEN check_violation THEN NULL;
    END;
END;
$$;

DO $$
BEGIN
    BEGIN
        DELETE FROM workforce.employees WHERE employee_id = 'SAO-001';
        RAISE EXCEPTION 'Hard delete was accepted.';
    EXCEPTION
        WHEN SQLSTATE '55000' THEN NULL;
    END;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-ACCEPTANCE', true);
SELECT set_config('app.request_id', 'TEST-REGISTRY-AUDIT', true);

DO $$
DECLARE
    v_before_version bigint;
    v_after_version bigint;
    v_before_events bigint;
    v_after_events bigint;
BEGIN
    SELECT version INTO v_before_version
    FROM workforce.employees
    WHERE employee_id = 'EAC-001';

    SELECT count(*) INTO v_before_events
    FROM workforce.registry_events;

    UPDATE workforce.employees
    SET display_name = display_name
    WHERE employee_id = 'EAC-001';

    SELECT version INTO v_after_version
    FROM workforce.employees
    WHERE employee_id = 'EAC-001';

    SELECT count(*) INTO v_after_events
    FROM workforce.registry_events;

    IF v_after_version <> v_before_version + 1 THEN
        RAISE EXCEPTION 'Version did not increment exactly once.';
    END IF;

    IF v_after_events <> v_before_events + 1 THEN
        RAISE EXCEPTION 'Registry update did not create exactly one audit event.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM workforce.registry_events
        WHERE record_type = 'EMPLOYEE'
          AND record_key = 'EAC-001'
          AND event_type = 'UPDATE'
          AND actor_id = 'SYSTEM-ACCEPTANCE'
          AND request_id = 'TEST-REGISTRY-AUDIT'
    ) THEN
        RAISE EXCEPTION 'Audit event is missing actor or request attribution.';
    END IF;
END;
$$;

DO $$
BEGIN
    BEGIN
        UPDATE workforce.registry_events
        SET actor_id = actor_id
        WHERE event_id = (SELECT min(event_id) FROM workforce.registry_events);
        RAISE EXCEPTION 'Append-only audit event was mutable.';
    EXCEPTION
        WHEN SQLSTATE '55000' THEN NULL;
    END;
END;
$$;

SELECT 'PASS: Employee Registry schema, seed identities, project scope, versioning and audit controls' AS acceptance_result;

ROLLBACK;
