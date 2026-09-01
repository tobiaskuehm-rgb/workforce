\set ON_ERROR_STOP on

-- Acceptance test for migration 005_bus_denial_audit (review finding G-018).
--
-- Everything here runs inside one transaction and is rolled back, so it can be
-- run against production. It writes test rows through the real function and
-- then undoes them; nothing survives.
--
-- The interesting cases are the refusals. A table that accepted a message body
-- or a token would defeat its own purpose, so the constraints are tested by
-- trying to violate them and demanding that the attempt fails.

BEGIN;

DO $$
DECLARE
    v_denial_id bigint;
    v_actor text;
    v_count integer;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM workforce.schema_migrations
        WHERE migration_id = '005_bus_denial_audit'
    ) THEN
        RAISE EXCEPTION 'Migration 005_bus_denial_audit is missing.';
    END IF;

    -- 1. A refusal by an unknown token is still recorded, attributed UNKNOWN.
    v_denial_id := workforce.bus_record_denial(
        'START-UP', 'no-such-token-hash', 'ACCEPT-004-1',
        'TASK_TRANSITION', 'TASK', 'ENG-ACCEPT-004',
        'BUS_TASK_TRANSITION_DENIED', 403
    );
    SELECT actor_id INTO v_actor
    FROM workforce.bus_denials WHERE denial_id = v_denial_id;
    IF v_actor <> 'UNKNOWN' THEN
        RAISE EXCEPTION 'Expected UNKNOWN actor for an unmatched token, got %.', v_actor;
    END IF;

    -- 2. The token hash itself must not appear anywhere in the row.
    SELECT count(*) INTO v_count
    FROM workforce.bus_denials
    WHERE denial_id = v_denial_id
      AND (actor_id || operation || record_type || coalesce(record_key, '')
           || error_code || request_id) LIKE '%no-such-token-hash%';
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'The token hash reached the denial row.';
    END IF;

    -- 3. Append-only: neither UPDATE nor DELETE may touch a recorded denial.
    BEGIN
        UPDATE workforce.bus_denials SET error_code = 'CHANGED'
        WHERE denial_id = v_denial_id;
        RAISE EXCEPTION 'A denial row could be updated.';
    EXCEPTION
        WHEN sqlstate '55000' THEN NULL;
    END;

    BEGIN
        DELETE FROM workforce.bus_denials WHERE denial_id = v_denial_id;
        RAISE EXCEPTION 'A denial row could be deleted.';
    EXCEPTION
        WHEN sqlstate '55000' THEN NULL;
    END;

    -- 4. Content cannot be smuggled in. A message body is neither a valid
    --    error code nor a valid operation, and the constraints say so rather
    --    than a comment promising it.
    BEGIN
        PERFORM workforce.bus_record_denial(
            'START-UP', 'x', 'ACCEPT-004-2', 'TASK_TRANSITION', 'TASK',
            'ENG-ACCEPT-004',
            'Bitte ueberweise das Geld an folgendes Konto', 403
        );
        RAISE EXCEPTION 'A free-text error code was accepted.';
    EXCEPTION
        WHEN check_violation THEN NULL;
    END;

    BEGIN
        PERFORM workforce.bus_record_denial(
            'START-UP', 'x', 'ACCEPT-004-3', 'ein ganzer Satz als Operation',
            'TASK', 'ENG-ACCEPT-004', 'BUS_TASK_TRANSITION_DENIED', 403
        );
        RAISE EXCEPTION 'A free-text operation was accepted.';
    EXCEPTION
        WHEN check_violation THEN NULL;
    END;

    BEGIN
        PERFORM workforce.bus_record_denial(
            'START-UP', 'x', 'ACCEPT-004-4', 'TASK_TRANSITION', 'TASK',
            repeat('x', 129), 'BUS_TASK_TRANSITION_DENIED', 403
        );
        RAISE EXCEPTION 'An over-long record key was accepted.';
    EXCEPTION
        WHEN check_violation THEN NULL;
    END;

    BEGIN
        PERFORM workforce.bus_record_denial(
            'START-UP', 'x', 'ACCEPT-004-5', 'TASK_TRANSITION', 'NACHRICHTENTEXT',
            'ENG-ACCEPT-004', 'BUS_TASK_TRANSITION_DENIED', 403
        );
        RAISE EXCEPTION 'An unknown record type was accepted.';
    EXCEPTION
        WHEN check_violation THEN NULL;
    END;

    -- 5. An empty record key is stored as NULL, not as an empty string.
    v_denial_id := workforce.bus_record_denial(
        'START-UP', 'x', 'ACCEPT-004-6', 'MESSAGE_LIST', 'MESSAGE', '   ',
        'BUS_PROJECT_READ_DENIED', 403
    );
    IF (SELECT record_key FROM workforce.bus_denials WHERE denial_id = v_denial_id)
       IS NOT NULL THEN
        RAISE EXCEPTION 'A blank record key was stored instead of NULL.';
    END IF;

    RAISE NOTICE 'Bus denial audit acceptance: PASS';
END;
$$;

ROLLBACK;
