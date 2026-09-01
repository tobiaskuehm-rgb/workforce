\set ON_ERROR_STOP on

DO $$
BEGIN
    IF current_setting('app.visible_demo', true) <> 'ENABLED' THEN
        RAISE EXCEPTION 'VISIBLE_DEMO_GUARD_REQUIRED';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.schema_migrations
        WHERE migration_id = '003_workforce_bus_trigger_fix'
    ) THEN
        RAISE EXCEPTION 'Workforce Bus migrations 002/003 are required.';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP' AND channel_status = 'DISABLED'
    ) THEN
        RAISE EXCEPTION 'Visible demo requires the initial DISABLED channel.';
    END IF;

    IF EXISTS (SELECT 1 FROM workforce.bus_credentials) THEN
        RAISE EXCEPTION 'Visible demo requires zero pre-existing credentials.';
    END IF;

    IF to_regclass('workforce.bus_access_events') IS NULL THEN
        RAISE EXCEPTION 'Local access-audit extension is missing.';
    END IF;
END;
$$;

BEGIN;

SELECT set_config('app.actor_id', 'SYSTEM-DEMO', true);
SELECT set_config('app.request_id', 'DEMO-SETUP', true);

UPDATE workforce.bus_channels
SET channel_status = 'TESTING'
WHERE project_id = 'START-UP';

INSERT INTO workforce.bus_credentials (
    credential_id, project_id, employee_id, token_hash,
    credential_scope, source_ref, expires_at
) VALUES
    ('CRED-DEMO-KARL-20260814', 'START-UP', 'SAO-001', repeat('a', 64),
        'ACCEPTANCE', 'DEC-021/ENG-005', clock_timestamp() + interval '1 hour'),
    ('CRED-DEMO-THORSTEN-20260814', 'START-UP', 'RAS-001', repeat('b', 64),
        'ACCEPTANCE', 'DEC-021/ENG-005', clock_timestamp() + interval '1 hour'),
    ('CRED-DEMO-NORA-20260814', 'START-UP', 'EAC-001', repeat('c', 64),
        'ACCEPTANCE', 'DEC-021/ENG-005', clock_timestamp() + interval '1 hour'),
    ('CRED-DEMO-GERD-20260814', 'START-UP', 'AI-ENG-001', repeat('d', 64),
        'ACCEPTANCE', 'DEC-021/ENG-005', clock_timestamp() + interval '1 hour');

DO $$
DECLARE
    v_task workforce.bus_tasks%ROWTYPE;
    v_message workforce.bus_messages%ROWTYPE;
    v_count integer;
BEGIN
    -- 1. Karl erstellt den Arbeitsauftrag und sendet ihn an Thorsten.
    v_task := workforce.bus_create_task(
        repeat('a', 64),
        'DEMO-TASK-CREATE',
        'ENG-DEMO-001',
        'START-UP',
        'RAS-001',
        'OPEN',
        'CRITICAL',
        'Kommunikationskern sichtbar pruefen',
        'Strukturiertes Ergebnis mit Audit- und Sicherheitsnachweis',
        'DEC-021/ENG-005',
        clock_timestamp() + interval '1 day'
    );

    v_message := workforce.bus_send_message(
        repeat('a', 64),
        'DEMO-MSG-KARL-THORSTEN',
        'MSG-DEMO-KARL-THORSTEN-001',
        'START-UP',
        'RAS-001',
        'IDEM-DEMO-KARL-THORSTEN-001',
        'P0-Arbeitsauftrag Kommunikationskern',
        'Bitte den lokalen Kommunikationsablauf pruefen und ein strukturiertes Ergebnis liefern.',
        'INTERNAL_REVIEW',
        'PROJECT_INTERNAL',
        'ENG-DEMO-001',
        NULL,
        NULL
    );

    IF v_task.creator_id <> 'SAO-001'
       OR v_task.owner_id <> 'RAS-001'
       OR v_task.task_status <> 'OPEN'
       OR v_message.sender_id <> 'SAO-001'
       OR v_message.recipient_id <> 'RAS-001'
       OR v_message.delivery_status <> 'DELIVERED' THEN
        RAISE EXCEPTION 'Step 1 failed: Karl assignment/delivery mismatch.';
    END IF;

    -- 2. Thorsten sieht und bestaetigt den Auftrag.
    SELECT count(*) INTO v_count
    FROM workforce.bus_list_messages(repeat('b', 64), 'START-UP', 'INBOX', 100)
    WHERE message_id = 'MSG-DEMO-KARL-THORSTEN-001';
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'Step 2 failed: Thorsten inbox mismatch.';
    END IF;

    v_message := workforce.bus_acknowledge_message(
        repeat('b', 64),
        'DEMO-MSG-THORSTEN-ACK',
        'START-UP',
        'MSG-DEMO-KARL-THORSTEN-001',
        'ACCEPTED',
        'Auftrag angenommen; Bearbeitung gestartet.'
    );
    IF v_message.delivery_status <> 'ACCEPTED' OR v_message.accepted_at IS NULL THEN
        RAISE EXCEPTION 'Step 2 failed: acknowledgement missing.';
    END IF;

    PERFORM workforce.bus_transition_task(
        repeat('b', 64), 'DEMO-TASK-IN-PROGRESS', 'START-UP',
        'ENG-DEMO-001', 'IN_PROGRESS', NULL
    );

    -- 3. Thorsten gibt sein strukturiertes Ergebnis an Karl zurueck.
    v_message := workforce.bus_send_message(
        repeat('b', 64),
        'DEMO-MSG-THORSTEN-RESULT',
        'MSG-DEMO-THORSTEN-RESULT-001',
        'START-UP',
        'SAO-001',
        'IDEM-DEMO-THORSTEN-RESULT-001',
        'Ergebnis Kommunikationspruefung',
        '{"result":"PASS","finding":"Zustellung, Annahme und Rueckgabe funktionieren","next":"Handoff an Nora"}',
        'INTERNAL_STATUS',
        'PROJECT_INTERNAL',
        'ENG-DEMO-001',
        NULL,
        'MSG-DEMO-KARL-THORSTEN-001'
    );
    IF v_message.sender_id <> 'RAS-001'
       OR v_message.recipient_id <> 'SAO-001'
       OR v_message.correlation_id <> 'MSG-DEMO-KARL-THORSTEN-001' THEN
        RAISE EXCEPTION 'Step 3 failed: result return mismatch.';
    END IF;

    PERFORM workforce.bus_transition_task(
        repeat('b', 64), 'DEMO-TASK-REVIEW', 'START-UP',
        'ENG-DEMO-001', 'REVIEW', NULL
    );
END;
$$;

DO $$
DECLARE
    v_handoff workforce.bus_handoffs%ROWTYPE;
    v_count integer;
BEGIN
    -- 4. Thorsten uebergibt das Ergebnis an Nora.
    v_handoff := workforce.bus_create_handoff(
        repeat('b', 64),
        'DEMO-HANDOFF-THORSTEN-NORA',
        'HO-DEMO-001',
        'START-UP',
        'EAC-001',
        'OPEN',
        'Der P0-Kommunikationstest ist technisch ausgefuehrt; Ergebnis liegt strukturiert vor.',
        'Empfang bestaetigen und Closed Loop dokumentieren.',
        'DEC-021/ENG-005',
        'ENG-DEMO-001',
        'Keine externe oder produktive Aktion.',
        'Unmittelbar nach Ergebnisrueckgabe'
    );
    IF v_handoff.sender_id <> 'RAS-001'
       OR v_handoff.recipient_id <> 'EAC-001'
       OR v_handoff.handoff_status <> 'OPEN' THEN
        RAISE EXCEPTION 'Step 4 failed: handoff mismatch.';
    END IF;

    -- 5. Nora empfaengt und bestaetigt die Uebergabe.
    SELECT count(*) INTO v_count
    FROM workforce.bus_list_handoffs(repeat('c', 64), 'START-UP', 'INBOX', 100)
    WHERE handoff_id = 'HO-DEMO-001';
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'Step 5 failed: Nora handoff inbox mismatch.';
    END IF;

    v_handoff := workforce.bus_transition_handoff(
        repeat('c', 64),
        'DEMO-HANDOFF-NORA-ACCEPT',
        'START-UP',
        'HO-DEMO-001',
        'ACCEPTED',
        'Empfang bestaetigt; Closed Loop dokumentiert.'
    );
    IF v_handoff.handoff_status <> 'ACCEPTED' OR v_handoff.accepted_at IS NULL THEN
        RAISE EXCEPTION 'Step 5 failed: Nora acceptance missing.';
    END IF;
END;
$$;

DO $$
DECLARE
    v_task workforce.bus_tasks%ROWTYPE;
    v_count integer;
    v_error text;
BEGIN
    -- 6. Karl kann Nachrichten, Task und Handoff projektweit nachvollziehen.
    SELECT count(*) INTO v_count
    FROM workforce.bus_list_messages(repeat('a', 64), 'START-UP', 'PROJECT', 100)
    WHERE message_id IN (
        'MSG-DEMO-KARL-THORSTEN-001',
        'MSG-DEMO-THORSTEN-RESULT-001'
    );
    IF v_count <> 2 THEN
        RAISE EXCEPTION 'Step 6 failed: Karl project message view mismatch.';
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.bus_list_tasks(repeat('a', 64), 'START-UP', 'PROJECT', 100)
    WHERE task_id = 'ENG-DEMO-001' AND task_status = 'REVIEW';
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'Step 6 failed: Karl task view mismatch.';
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.bus_list_handoffs(repeat('a', 64), 'START-UP', 'PROJECT', 100)
    WHERE handoff_id = 'HO-DEMO-001' AND handoff_status = 'ACCEPTED';
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'Step 6 failed: Karl handoff view mismatch.';
    END IF;

    v_task := workforce.bus_transition_task(
        repeat('a', 64),
        'DEMO-TASK-DONE',
        'START-UP',
        'ENG-DEMO-001',
        'DONE',
        'Thorsten-Ergebnis und Nora-Handoff geprueft; sichtbarer lokaler Ablauf PASS.'
    );
    IF v_task.task_status <> 'DONE' OR v_task.completed_at IS NULL THEN
        RAISE EXCEPTION 'Step 6 failed: task completion missing.';
    END IF;

    -- 7/8. Gerd versucht unberechtigten PROJECT-Read; Denial wird auditierbar erfasst.
    BEGIN
        PERFORM *
        FROM workforce.bus_list_messages(repeat('d', 64), 'START-UP', 'PROJECT', 100);
        RAISE EXCEPTION 'Unauthorized read unexpectedly succeeded.';
    EXCEPTION
        WHEN insufficient_privilege THEN
            GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
            IF v_error <> 'BUS_PROJECT_READ_DENIED' THEN
                RAISE;
            END IF;
            PERFORM workforce.bus_record_access_event(
                'START-UP', repeat('d', 64), 'DEMO-UNAUTHORIZED-READ',
                'READ_ATTEMPT', 'PROJECT', 'START-UP', 'DENIED', v_error
            );
    END;

    -- 9/10. Gleiche Uebertragung: identische Nachricht, genau ein Datensatz.
    PERFORM workforce.bus_send_message(
        repeat('a', 64),
        'DEMO-MSG-KARL-THORSTEN-RETRY',
        'MSG-DEMO-KARL-THORSTEN-001',
        'START-UP',
        'RAS-001',
        'IDEM-DEMO-KARL-THORSTEN-001',
        'P0-Arbeitsauftrag Kommunikationskern',
        'Bitte den lokalen Kommunikationsablauf pruefen und ein strukturiertes Ergebnis liefern.',
        'INTERNAL_REVIEW',
        'PROJECT_INTERNAL',
        'ENG-DEMO-001',
        NULL,
        NULL
    );

    SELECT count(*) INTO v_count
    FROM workforce.bus_messages
    WHERE project_id = 'START-UP'
      AND sender_id = 'SAO-001'
      AND idempotency_key = 'IDEM-DEMO-KARL-THORSTEN-001';
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'Step 10 failed: duplicate processing count is %.', v_count;
    END IF;

    PERFORM workforce.bus_record_access_event(
        'START-UP', repeat('a', 64), 'DEMO-DUPLICATE-DELIVERY',
        'DELIVERY_ATTEMPT', 'MESSAGE', 'MSG-DEMO-KARL-THORSTEN-001',
        'DUPLICATE_BLOCKED', 'BUS_IDEMPOTENT_REPLAY'
    );
END;
$$;

DO $$
DECLARE
    v_count integer;
BEGIN
    IF (SELECT count(*) FROM workforce.bus_events WHERE request_id LIKE 'DEMO-%') < 10 THEN
        RAISE EXCEPTION 'Core audit trail is incomplete.';
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.bus_access_events
    WHERE request_id = 'DEMO-UNAUTHORIZED-READ'
      AND actor_id = 'AI-ENG-001'
      AND outcome = 'DENIED'
      AND reason_code = 'BUS_PROJECT_READ_DENIED';
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'Denied access audit is missing.';
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.bus_access_events
    WHERE request_id = 'DEMO-DUPLICATE-DELIVERY'
      AND outcome = 'DUPLICATE_BLOCKED';
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'Duplicate protection audit is missing.';
    END IF;

    BEGIN
        UPDATE workforce.bus_access_events
        SET reason_code = 'TAMPERED'
        WHERE request_id = 'DEMO-UNAUTHORIZED-READ';
        RAISE EXCEPTION 'Access audit mutation unexpectedly succeeded.';
    EXCEPTION
        WHEN object_not_in_prerequisite_state THEN
            NULL;
    END;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-DEMO-CLEANUP', true);
SELECT set_config('app.request_id', 'DEMO-CLEANUP', true);

UPDATE workforce.bus_credentials
SET credential_status = 'REVOKED',
    revoked_at = clock_timestamp(),
    revocation_reason = 'Local visible demo completed'
WHERE source_ref = 'DEC-021/ENG-005';

UPDATE workforce.bus_channels
SET channel_status = 'DISABLED'
WHERE project_id = 'START-UP';

COMMIT;

SELECT jsonb_build_object(
    'result', 'PASS',
    'acceptance_state', 'GELB',
    'flow', jsonb_build_array(
        '1 Karl created and delivered task to Thorsten',
        '2 Thorsten received and accepted',
        '3 Thorsten returned structured result',
        '4 Thorsten handed result to Nora',
        '5 Nora confirmed receipt',
        '6 Karl traced and completed the task',
        '7/8 unauthorized project read denied and audited',
        '9/10 duplicate transmission returned the same message and created one record'
    ),
    'message_status', (
        SELECT delivery_status FROM workforce.bus_messages
        WHERE message_id = 'MSG-DEMO-KARL-THORSTEN-001'
    ),
    'task_status', (
        SELECT task_status FROM workforce.bus_tasks WHERE task_id = 'ENG-DEMO-001'
    ),
    'handoff_status', (
        SELECT handoff_status FROM workforce.bus_handoffs WHERE handoff_id = 'HO-DEMO-001'
    ),
    'duplicate_message_count', (
        SELECT count(*) FROM workforce.bus_messages
        WHERE idempotency_key = 'IDEM-DEMO-KARL-THORSTEN-001'
    ),
    'core_audit_events', (
        SELECT count(*) FROM workforce.bus_events WHERE request_id LIKE 'DEMO-%'
    ),
    'denied_access_events', (
        SELECT count(*) FROM workforce.bus_access_events
        WHERE outcome = 'DENIED'
    ),
    'duplicate_block_events', (
        SELECT count(*) FROM workforce.bus_access_events
        WHERE outcome = 'DUPLICATE_BLOCKED'
    ),
    'channel_status_after_test', (
        SELECT channel_status FROM workforce.bus_channels WHERE project_id = 'START-UP'
    ),
    'active_credentials_after_test', (
        SELECT count(*) FROM workforce.bus_credentials
        WHERE credential_status = 'ACTIVE'
    )
) AS visible_protocol;
