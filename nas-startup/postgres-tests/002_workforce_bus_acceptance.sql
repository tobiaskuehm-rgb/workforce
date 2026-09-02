\set ON_ERROR_STOP on

BEGIN;

DO $$
DECLARE
    v_count integer;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM workforce.schema_migrations
        WHERE migration_id = '002_workforce_bus'
    ) THEN
        RAISE EXCEPTION 'Migration 002_workforce_bus is missing.';
    END IF;

    -- Bis 2026-09-02 stand hier `<> 5` (review finding G-049). Aktiv sind
    -- inzwischen sechs, weil AGENT-ENG-001 fuer die Agentenlaufzeit
    -- dazukam; drei Telegram-Identitaeten sind angelegt und widerrufen
    -- worden. Eine Bestandszahl ist keine Eigenschaft des Busses.
    SELECT count(*) INTO v_count
    FROM workforce.bus_member_capabilities
    WHERE project_id = 'START-UP'
      AND capability_status = 'ACTIVE'
      AND employee_id IN ('SAO-001', 'AI-ENG-001', 'PEO-001', 'RAS-001', 'EAC-001');
    IF v_count <> 5 THEN
        RAISE EXCEPTION 'Bootstrap capabilities not active: found % of 5', v_count;
    END IF;

    -- Und die Regel, die fuer jeden Widerruf in diesem Projekt gilt: ohne
    -- Zeitpunkt und Begruendung gibt es keinen. Das ist eine Eigenschaft,
    -- die mit jeder neuen widerrufenen Capability mitwaechst, statt von ihr
    -- gebrochen zu werden.
    SELECT count(*) INTO v_count
    FROM workforce.bus_member_capabilities
    WHERE capability_status = 'REVOKED'
      AND (revoked_at IS NULL
           OR nullif(btrim(coalesce(revocation_reason, '')), '') IS NULL);
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'Revoked capabilities without metadata: %', v_count;
    END IF;

    -- Bis 2026-09-02 `<> 60`, inzwischen sind es 68 (G-049). Die Zahl waechst
    -- mit jeder Identitaet, die Routen bekommt; sie ist keine Eigenschaft der
    -- Allowlist. Geprueft wird stattdessen ihre Unversehrtheit: keine Route
    -- zeigt auf jemanden, den es nicht als aktives Mitglied gibt, und keine
    -- zeigt auf sich selbst. Beides bricht, wenn jemand die Tabelle von Hand
    -- fuellt - und beides bleibt richtig, wenn sie legitim waechst.
    SELECT count(*) INTO v_count
    FROM workforce.bus_route_allowlist r
    WHERE r.project_id = 'START-UP'
      AND r.route_status = 'ACTIVE'
      AND (NOT EXISTS (
              SELECT 1 FROM workforce.active_project_members m
              WHERE m.project_id = r.project_id AND m.employee_id = r.sender_id)
           OR NOT EXISTS (
              SELECT 1 FROM workforce.active_project_members m
              WHERE m.project_id = r.project_id AND m.employee_id = r.recipient_id));
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'Active routes pointing at non-members: %', v_count;
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.bus_route_allowlist
    WHERE project_id = 'START-UP'
      AND route_status = 'ACTIVE'
      AND sender_id = recipient_id;
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'Active self-routes: %', v_count;
    END IF;

    -- Die Absicht war richtig, das Mass nicht (G-049): `count(*) <> 0` ueber
    -- die ganze Tabelle war wahr, solange nie ein Zugang ausgegeben worden
    -- war. Inzwischen liegen dort 21, alle REVOKED, aus dokumentierten
    -- Entscheidungen und Testlaeufen. Gemeint ist: die Migration selbst darf
    -- keinen Zugang anlegen, denn das hiesse, ein Passwort in eine
    -- versionierte Datei zu schreiben. Genau das wird jetzt geprueft.
    SELECT count(*) INTO v_count
    FROM workforce.bus_credentials
    WHERE source_ref LIKE '%002_workforce_bus%'
       OR source_ref LIKE 'MIG-002%';
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'Migration seeded credentials; found %.', v_count;
    END IF;

    -- Und die Widerrufsregel, die im ganzen Projekt gilt: kein Widerruf ohne
    -- Zeitpunkt und Begruendung. Waechst mit, statt zu brechen.
    SELECT count(*) INTO v_count
    FROM workforce.bus_credentials
    WHERE credential_status = 'REVOKED'
      AND (revoked_at IS NULL
           OR nullif(btrim(coalesce(revocation_reason, '')), '') IS NULL);
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'Revoked credentials without metadata: %', v_count;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM workforce.bus_channels
        WHERE project_id = 'START-UP'
          AND channel_status = 'DISABLED'
    ) THEN
        RAISE EXCEPTION 'Bus must remain disabled after migration.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM workforce.bus_member_capabilities
        WHERE project_id = 'START-UP'
          AND employee_id = 'SAO-001'
          AND read_scope = 'PROJECT'
          AND task_authority = 'COORDINATE'
    ) THEN
        RAISE EXCEPTION 'Karl project read/coordination capability is missing.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM workforce.bus_member_capabilities
        WHERE project_id = 'START-UP'
          AND employee_id = 'EAC-001'
          AND read_scope = 'PROJECT'
          AND task_authority = 'PROPOSE'
    ) THEN
        RAISE EXCEPTION 'Nora project read/proposal boundary is missing.';
    END IF;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-ACCEPTANCE', true);
SELECT set_config('app.request_id', 'TEST-BUS-SETUP', true);

UPDATE workforce.bus_channels
SET channel_status = 'TESTING'
WHERE project_id = 'START-UP';

INSERT INTO workforce.bus_credentials (
    credential_id,
    project_id,
    employee_id,
    token_hash,
    credential_scope,
    source_ref,
    expires_at
) VALUES
    ('CRED-ACCEPT-KARL', 'START-UP', 'SAO-001', repeat('a', 64), 'ACCEPTANCE', 'ENG-003-TEST', clock_timestamp() + interval '1 hour'),
    ('CRED-ACCEPT-GERD', 'START-UP', 'AI-ENG-001', repeat('b', 64), 'ACCEPTANCE', 'ENG-003-TEST', clock_timestamp() + interval '1 hour'),
    ('CRED-ACCEPT-NORA', 'START-UP', 'EAC-001', repeat('c', 64), 'ACCEPTANCE', 'ENG-003-TEST', clock_timestamp() + interval '1 hour');

DO $$
DECLARE
    v_message workforce.bus_messages%ROWTYPE;
    v_count integer;
BEGIN
    v_message := workforce.bus_send_message(
        repeat('a', 64),
        'REQ-E2E-KARL-GERD-001',
        'MSG-E2E-KARL-GERD-001',
        'START-UP',
        'AI-ENG-001',
        'IDEM-E2E-KARL-GERD-001',
        'Technikstatus',
        'Bitte Registry- und Busstatus prüfen.',
        'INTERNAL_REVIEW',
        'NEED_TO_KNOW',
        'ENG-003',
        'HO-020',
        NULL
    );

    IF v_message.sender_id <> 'SAO-001'
       OR v_message.recipient_id <> 'AI-ENG-001'
       OR v_message.delivery_status <> 'DELIVERED'
       OR v_message.hop_count <> 0 THEN
        RAISE EXCEPTION 'Karl to Gerd delivery is inconsistent.';
    END IF;

    PERFORM workforce.bus_send_message(
        repeat('a', 64),
        'REQ-E2E-KARL-GERD-RETRY',
        'MSG-E2E-KARL-GERD-001',
        'START-UP',
        'AI-ENG-001',
        'IDEM-E2E-KARL-GERD-001',
        'Technikstatus',
        'Bitte Registry- und Busstatus prüfen.',
        'INTERNAL_REVIEW',
        'NEED_TO_KNOW',
        'ENG-003',
        'HO-020',
        NULL
    );

    SELECT count(*) INTO v_count
    FROM workforce.bus_messages
    WHERE idempotency_key = 'IDEM-E2E-KARL-GERD-001';
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'Idempotent retry created % messages.', v_count;
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.bus_list_messages(repeat('b', 64), 'START-UP', 'INBOX', 100)
    WHERE message_id = 'MSG-E2E-KARL-GERD-001';
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'Gerd inbox did not receive Karl message.';
    END IF;

    v_message := workforce.bus_acknowledge_message(
        repeat('b', 64),
        'REQ-E2E-GERD-ACK-001',
        'START-UP',
        'MSG-E2E-KARL-GERD-001',
        'ACCEPTED',
        'Prüfung übernommen.'
    );

    IF v_message.delivery_status <> 'ACCEPTED' OR v_message.accepted_at IS NULL THEN
        RAISE EXCEPTION 'Gerd acknowledgement was not recorded.';
    END IF;

    v_message := workforce.bus_send_message(
        repeat('b', 64),
        'REQ-E2E-GERD-KARL-001',
        'MSG-E2E-GERD-KARL-001',
        'START-UP',
        'SAO-001',
        'IDEM-E2E-GERD-KARL-001',
        'Technikstatus angenommen',
        'Prüfung ist in Arbeit.',
        'INTERNAL_STATUS',
        'NEED_TO_KNOW',
        'ENG-003',
        'HO-020',
        'MSG-E2E-KARL-GERD-001'
    );

    IF v_message.correlation_id <> 'MSG-E2E-KARL-GERD-001' OR v_message.hop_count <> 1 THEN
        RAISE EXCEPTION 'Reply correlation or hop count is inconsistent.';
    END IF;
END;
$$;

DO $$
DECLARE
    v_task workforce.bus_tasks%ROWTYPE;
    v_count integer;
BEGIN
    v_task := workforce.bus_create_task(
        repeat('a', 64),
        'REQ-E2E-TASK-CREATE-001',
        'ENG-E2E-001',
        'START-UP',
        'AI-ENG-001',
        'OPEN',
        'HIGH',
        'Workforce-Bus prüfen',
        'Technische Abnahme mit Auditnachweis',
        'ENG-003',
        clock_timestamp() + interval '1 day'
    );

    IF v_task.creator_id <> 'SAO-001' OR v_task.owner_id <> 'AI-ENG-001' OR v_task.task_status <> 'OPEN' THEN
        RAISE EXCEPTION 'Karl task coordination boundary is inconsistent.';
    END IF;

    v_task := workforce.bus_create_task(
        repeat('a', 64),
        'REQ-E2E-TASK-CREATE-RETRY',
        'ENG-E2E-001',
        'START-UP',
        'AI-ENG-001',
        'OPEN',
        'HIGH',
        'Workforce-Bus prüfen',
        'Technische Abnahme mit Auditnachweis',
        'ENG-003',
        v_task.review_at
    );

    IF v_task.version <> 1 THEN
        RAISE EXCEPTION 'Idempotent task retry changed version to %.', v_task.version;
    END IF;

    PERFORM workforce.bus_transition_task(
        repeat('b', 64),
        'REQ-E2E-TASK-START-001',
        'START-UP',
        'ENG-E2E-001',
        'IN_PROGRESS',
        NULL
    );

    PERFORM workforce.bus_transition_task(
        repeat('b', 64),
        'REQ-E2E-TASK-REVIEW-001',
        'START-UP',
        'ENG-E2E-001',
        'REVIEW',
        NULL
    );

    v_task := workforce.bus_transition_task(
        repeat('a', 64),
        'REQ-E2E-TASK-DONE-001',
        'START-UP',
        'ENG-E2E-001',
        'DONE',
        'Registry-, API- und Busabnahme protokolliert.'
    );

    IF v_task.task_status <> 'DONE' OR v_task.completed_at IS NULL OR v_task.version <> 4 THEN
        RAISE EXCEPTION 'Task lifecycle or versioning is inconsistent.';
    END IF;

    v_task := workforce.bus_transition_task(
        repeat('a', 64),
        'REQ-E2E-TASK-DONE-RETRY',
        'START-UP',
        'ENG-E2E-001',
        'DONE',
        'Registry-, API- und Busabnahme protokolliert.'
    );

    IF v_task.version <> 4 THEN
        RAISE EXCEPTION 'Idempotent final task transition changed version to %.', v_task.version;
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.bus_list_tasks(repeat('b', 64), 'START-UP', 'OWNED', 100)
    WHERE task_id = 'ENG-E2E-001';
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'Gerd owned-task view did not return the assigned task.';
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.bus_list_tasks(repeat('c', 64), 'START-UP', 'PROJECT', 100)
    WHERE task_id = 'ENG-E2E-001';
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'Nora project task view did not return the project task.';
    END IF;

    BEGIN
        PERFORM * FROM workforce.bus_list_tasks(repeat('b', 64), 'START-UP', 'PROJECT', 100);
        RAISE EXCEPTION 'Participant-only employee received project-wide task access.';
    EXCEPTION
        WHEN insufficient_privilege THEN
            IF SQLERRM <> 'BUS_PROJECT_READ_DENIED' THEN RAISE; END IF;
    END;
END;
$$;

DO $$
DECLARE
    v_handoff workforce.bus_handoffs%ROWTYPE;
    v_message workforce.bus_messages%ROWTYPE;
    v_count integer;
BEGIN
    v_handoff := workforce.bus_create_handoff(
        repeat('b', 64),
        'REQ-E2E-HANDOFF-CREATE-001',
        'HO-E2E-001',
        'START-UP',
        'EAC-001',
        'OPEN',
        'Technischer Prüfstatus und offene Nachweise.',
        'Closed-Loop-Nachhalten bis zur Abnahme.',
        'ENG-003/HO-020',
        'ENG-E2E-001',
        'Keine externe oder privilegierte Aktion.',
        'Nach technischem PASS'
    );

    IF v_handoff.sender_id <> 'AI-ENG-001' OR v_handoff.recipient_id <> 'EAC-001' THEN
        RAISE EXCEPTION 'Gerd to Nora handoff is inconsistent.';
    END IF;

    v_handoff := workforce.bus_create_handoff(
        repeat('b', 64),
        'REQ-E2E-HANDOFF-CREATE-RETRY',
        'HO-E2E-001',
        'START-UP',
        'EAC-001',
        'OPEN',
        'Technischer Prüfstatus und offene Nachweise.',
        'Closed-Loop-Nachhalten bis zur Abnahme.',
        'ENG-003/HO-020',
        'ENG-E2E-001',
        'Keine externe oder privilegierte Aktion.',
        'Nach technischem PASS'
    );

    IF v_handoff.version <> 1 THEN
        RAISE EXCEPTION 'Idempotent handoff retry changed version to %.', v_handoff.version;
    END IF;

    v_handoff := workforce.bus_transition_handoff(
        repeat('c', 64),
        'REQ-E2E-HANDOFF-ACCEPT-001',
        'START-UP',
        'HO-E2E-001',
        'ACCEPTED',
        'Administratives Nachhalten übernommen.'
    );

    IF v_handoff.handoff_status <> 'ACCEPTED' OR v_handoff.accepted_at IS NULL THEN
        RAISE EXCEPTION 'Nora handoff acceptance was not recorded.';
    END IF;

    v_handoff := workforce.bus_transition_handoff(
        repeat('c', 64),
        'REQ-E2E-HANDOFF-ACCEPT-RETRY',
        'START-UP',
        'HO-E2E-001',
        'ACCEPTED',
        'Administratives Nachhalten übernommen.'
    );

    IF v_handoff.version <> 2 THEN
        RAISE EXCEPTION 'Idempotent handoff acceptance changed version to %.', v_handoff.version;
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.bus_list_handoffs(repeat('c', 64), 'START-UP', 'INBOX', 100)
    WHERE handoff_id = 'HO-E2E-001';
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'Nora handoff inbox did not return the accepted handoff.';
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.bus_list_handoffs(repeat('a', 64), 'START-UP', 'PROJECT', 100)
    WHERE handoff_id = 'HO-E2E-001';
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'Karl project handoff view did not return the handoff.';
    END IF;

    BEGIN
        PERFORM * FROM workforce.bus_list_handoffs(repeat('b', 64), 'START-UP', 'PROJECT', 100);
        RAISE EXCEPTION 'Participant-only employee received project-wide handoff access.';
    EXCEPTION
        WHEN insufficient_privilege THEN
            IF SQLERRM <> 'BUS_PROJECT_READ_DENIED' THEN RAISE; END IF;
    END;

    v_message := workforce.bus_send_message(
        repeat('c', 64),
        'REQ-E2E-NORA-GERD-001',
        'MSG-E2E-NORA-GERD-001',
        'START-UP',
        'AI-ENG-001',
        'IDEM-E2E-NORA-GERD-001',
        'Handoff angenommen',
        'Closed Loop ist eröffnet; keine externe Aktion ausgelöst.',
        'INTERNAL_COORDINATION',
        'PROJECT_INTERNAL',
        'ENG-E2E-001',
        'HO-E2E-001',
        NULL
    );

    IF v_message.sender_id <> 'EAC-001' OR v_message.recipient_id <> 'AI-ENG-001' THEN
        RAISE EXCEPTION 'Nora to Gerd message identity is inconsistent.';
    END IF;
END;
$$;

DO $$
DECLARE
    v_count integer;
BEGIN
    PERFORM workforce.bus_send_message(
        repeat('a', 64),
        'REQ-E2E-PROJECT-READ-001',
        'MSG-E2E-PROJECT-READ-001',
        'START-UP',
        'AI-ENG-001',
        'IDEM-E2E-PROJECT-READ-001',
        'Projektweiter Status',
        'Dieser Status ist für die projektweite Kommunikationssicht freigegeben.',
        'INTERNAL_STATUS',
        'PROJECT_INTERNAL',
        'ENG-003',
        'HO-020',
        NULL
    );

    SELECT count(*) INTO v_count
    FROM workforce.bus_list_messages(repeat('a', 64), 'START-UP', 'PROJECT', 100);
    IF v_count < 4 THEN
        RAISE EXCEPTION 'Karl project read returned too few messages: %.', v_count;
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.bus_list_messages(repeat('c', 64), 'START-UP', 'PROJECT', 100);
    IF v_count < 2 THEN
        RAISE EXCEPTION 'Nora project read returned too few messages: %.', v_count;
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.bus_list_messages(repeat('c', 64), 'START-UP', 'PROJECT', 100)
    WHERE message_id = 'MSG-E2E-PROJECT-READ-001';
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'Nora could not read a PROJECT_INTERNAL message.';
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.bus_list_messages(repeat('c', 64), 'START-UP', 'PROJECT', 100)
    WHERE message_id = 'MSG-E2E-KARL-GERD-001';
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'Nora project read bypassed NEED_TO_KNOW participant scope.';
    END IF;

    BEGIN
        PERFORM * FROM workforce.bus_list_messages(repeat('b', 64), 'START-UP', 'PROJECT', 100);
        RAISE EXCEPTION 'Participant-only employee received project-wide read access.';
    EXCEPTION
        WHEN insufficient_privilege THEN
            IF SQLERRM <> 'BUS_PROJECT_READ_DENIED' THEN RAISE; END IF;
    END;
END;
$$;

DO $$
BEGIN
    BEGIN
        PERFORM workforce.bus_send_message(
            repeat('a', 64), 'REQ-NEG-OUTSIDE-001', 'MSG-NEG-OUTSIDE-001', 'OTHER-PROJECT',
            'AI-ENG-001', 'IDEM-NEG-OUTSIDE-001', 'Denied', 'Denied',
            'INTERNAL_COMMUNICATION', 'NEED_TO_KNOW', NULL, NULL, NULL
        );
        RAISE EXCEPTION 'Access outside START-UP was accepted.';
    EXCEPTION
        WHEN insufficient_privilege THEN
            IF SQLERRM <> 'BUS_AUTH_FAILED' THEN RAISE; END IF;
    END;

    BEGIN
        PERFORM workforce.bus_send_message(
            repeat('a', 64), 'REQ-NEG-EXTERNAL-001', 'MSG-NEG-EXTERNAL-001', 'START-UP',
            'AI-ENG-001', 'IDEM-NEG-EXTERNAL-001', 'Denied', 'Send external email',
            'EXTERNAL_EMAIL', 'NEED_TO_KNOW', NULL, NULL, NULL
        );
        RAISE EXCEPTION 'External action class was accepted.';
    EXCEPTION
        WHEN insufficient_privilege THEN
            IF SQLERRM <> 'BUS_ACTION_CLASS_DENIED' THEN RAISE; END IF;
    END;

    BEGIN
        PERFORM workforce.bus_acknowledge_message(
            repeat('a', 64), 'REQ-NEG-ACK-001', 'START-UP',
            'MSG-E2E-NORA-GERD-001', 'ACCEPTED', 'Spoofed acknowledgement'
        );
        RAISE EXCEPTION 'Non-recipient acknowledgement was accepted.';
    EXCEPTION
        WHEN insufficient_privilege THEN
            IF SQLERRM <> 'BUS_ACK_DENIED' THEN RAISE; END IF;
    END;

    BEGIN
        PERFORM workforce.bus_send_message(
            repeat('a', 64), 'REQ-NEG-IDEM-001', 'MSG-E2E-KARL-GERD-001', 'START-UP',
            'AI-ENG-001', 'IDEM-E2E-KARL-GERD-001', 'Technikstatus', 'Changed payload',
            'INTERNAL_REVIEW', 'NEED_TO_KNOW', 'ENG-003', 'HO-020', NULL
        );
        RAISE EXCEPTION 'Changed payload reused an idempotency key.';
    EXCEPTION
        WHEN unique_violation THEN
            IF SQLERRM <> 'BUS_IDEMPOTENCY_CONFLICT' THEN RAISE; END IF;
    END;

    BEGIN
        UPDATE workforce.bus_messages
        SET body = 'Changed outside the controlled function'
        WHERE message_id = 'MSG-E2E-KARL-GERD-001';
        RAISE EXCEPTION 'Immutable message payload was changed.';
    EXCEPTION
        WHEN object_not_in_prerequisite_state THEN
            IF SQLERRM <> 'BUS_MESSAGE_PAYLOAD_IMMUTABLE' THEN RAISE; END IF;
    END;

    BEGIN
        UPDATE workforce.bus_credentials
        SET token_hash = repeat('d', 64)
        WHERE credential_id = 'CRED-ACCEPT-KARL';
        RAISE EXCEPTION 'Immutable credential identity was changed.';
    EXCEPTION
        WHEN object_not_in_prerequisite_state THEN
            IF SQLERRM <> 'BUS_CREDENTIAL_IDENTITY_IMMUTABLE' THEN RAISE; END IF;
    END;
END;
$$;

DO $$
DECLARE
    v_message workforce.bus_messages%ROWTYPE;
BEGIN
    v_message := workforce.bus_send_message(
        repeat('a', 64), 'REQ-LOOP-002', 'MSG-E2E-KARL-GERD-002', 'START-UP',
        'AI-ENG-001', 'IDEM-E2E-KARL-GERD-002', 'Loop test 2', 'hop 2',
        'INTERNAL_STATUS', 'NEED_TO_KNOW', NULL, NULL, 'MSG-E2E-GERD-KARL-001'
    );
    v_message := workforce.bus_send_message(
        repeat('b', 64), 'REQ-LOOP-003', 'MSG-E2E-GERD-KARL-003', 'START-UP',
        'SAO-001', 'IDEM-E2E-GERD-KARL-003', 'Loop test 3', 'hop 3',
        'INTERNAL_STATUS', 'NEED_TO_KNOW', NULL, NULL, 'MSG-E2E-KARL-GERD-002'
    );
    v_message := workforce.bus_send_message(
        repeat('a', 64), 'REQ-LOOP-004', 'MSG-E2E-KARL-GERD-004', 'START-UP',
        'AI-ENG-001', 'IDEM-E2E-KARL-GERD-004', 'Loop test 4', 'hop 4',
        'INTERNAL_STATUS', 'NEED_TO_KNOW', NULL, NULL, 'MSG-E2E-GERD-KARL-003'
    );

    IF v_message.hop_count <> 4 THEN
        RAISE EXCEPTION 'Expected hop count 4, found %.', v_message.hop_count;
    END IF;

    BEGIN
        PERFORM workforce.bus_send_message(
            repeat('b', 64), 'REQ-LOOP-005', 'MSG-E2E-GERD-KARL-005', 'START-UP',
            'SAO-001', 'IDEM-E2E-GERD-KARL-005', 'Loop test 5', 'must fail',
            'INTERNAL_STATUS', 'NEED_TO_KNOW', NULL, NULL, 'MSG-E2E-KARL-GERD-004'
        );
        RAISE EXCEPTION 'Loop hop beyond configured maximum was accepted.';
    EXCEPTION
        WHEN program_limit_exceeded THEN
            IF SQLERRM <> 'BUS_LOOP_LIMIT_EXCEEDED' THEN RAISE; END IF;
    END;
END;
$$;

DO $$
BEGIN
    BEGIN
        PERFORM set_config('app.actor_id', '', true);
        PERFORM set_config('app.request_id', '', true);
        UPDATE workforce.bus_member_capabilities
        SET can_send = false
        WHERE project_id = 'START-UP'
          AND employee_id = 'PEO-001';
        RAISE EXCEPTION 'Mutation without audit context was accepted.';
    EXCEPTION
        WHEN invalid_parameter_value THEN
            IF SQLERRM <> 'BUS_AUDIT_CONTEXT_REQUIRED' THEN RAISE; END IF;
    END;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-ACCEPTANCE', true);
SELECT set_config('app.request_id', 'TEST-BUS-REVOCATION', true);

UPDATE workforce.bus_route_allowlist
SET route_status = 'SUSPENDED'
WHERE project_id = 'START-UP'
  AND sender_id = 'AI-ENG-001'
  AND recipient_id = 'EAC-001'
  AND route_kind = 'MESSAGE';

DO $$
BEGIN
    BEGIN
        PERFORM workforce.bus_send_message(
            repeat('b', 64), 'REQ-NEG-ROUTE-001', 'MSG-NEG-ROUTE-001', 'START-UP',
            'EAC-001', 'IDEM-NEG-ROUTE-001', 'Denied', 'Handoff does not transfer send rights.',
            'INTERNAL_COMMUNICATION', 'NEED_TO_KNOW', 'ENG-E2E-001', 'HO-E2E-001', NULL
        );
        RAISE EXCEPTION 'Suspended route was bypassed through a handoff.';
    EXCEPTION
        WHEN insufficient_privilege THEN
            IF SQLERRM <> 'BUS_ROUTE_DENIED' THEN RAISE; END IF;
    END;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-ACCEPTANCE', true);
SELECT set_config('app.request_id', 'TEST-BUS-CREDENTIAL-REVOCATION', true);

UPDATE workforce.bus_credentials
SET credential_status = 'REVOKED',
    revoked_at = clock_timestamp(),
    revocation_reason = 'Acceptance test'
WHERE credential_id = 'CRED-ACCEPT-NORA';

DO $$
BEGIN
    BEGIN
        PERFORM workforce.bus_send_message(
            repeat('c', 64), 'REQ-NEG-CREDENTIAL-001', 'MSG-NEG-CREDENTIAL-001', 'START-UP',
            'SAO-001', 'IDEM-NEG-CREDENTIAL-001', 'Denied', 'Revoked credential must fail.',
            'INTERNAL_COMMUNICATION', 'NEED_TO_KNOW', NULL, NULL, NULL
        );
        RAISE EXCEPTION 'Revoked credential was accepted.';
    EXCEPTION
        WHEN insufficient_privilege THEN
            IF SQLERRM <> 'BUS_AUTH_FAILED' THEN RAISE; END IF;
    END;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-ACCEPTANCE', true);
SELECT set_config('app.request_id', 'TEST-BUS-KILL-SWITCH', true);

UPDATE workforce.bus_channels
SET channel_status = 'REVOKED',
    revoked_at = clock_timestamp(),
    revocation_reason = 'Acceptance kill-switch test'
WHERE project_id = 'START-UP';

DO $$
BEGIN
    BEGIN
        PERFORM workforce.bus_send_message(
            repeat('a', 64), 'REQ-NEG-KILL-001', 'MSG-NEG-KILL-001', 'START-UP',
            'AI-ENG-001', 'IDEM-NEG-KILL-001', 'Denied', 'Kill switch must fail closed.',
            'INTERNAL_COMMUNICATION', 'NEED_TO_KNOW', NULL, NULL, NULL
        );
        RAISE EXCEPTION 'Revoked channel accepted a message.';
    EXCEPTION
        WHEN insufficient_privilege THEN
            IF SQLERRM <> 'BUS_AUTH_FAILED' THEN RAISE; END IF;
    END;

    BEGIN
        DELETE FROM workforce.bus_messages WHERE message_id = 'MSG-E2E-KARL-GERD-001';
        RAISE EXCEPTION 'Hard delete of a bus message was accepted.';
    EXCEPTION
        WHEN object_not_in_prerequisite_state THEN NULL;
    END;

    BEGIN
        UPDATE workforce.bus_events
        SET actor_id = actor_id
        WHERE event_id = (SELECT min(event_id) FROM workforce.bus_events);
        RAISE EXCEPTION 'Bus audit event was mutable.';
    EXCEPTION
        WHEN object_not_in_prerequisite_state THEN NULL;
    END;

    BEGIN
        UPDATE workforce.bus_channels
        SET channel_status = 'TESTING',
            revoked_at = NULL,
            revocation_reason = NULL
        WHERE project_id = 'START-UP';
        RAISE EXCEPTION 'Final channel revocation was reversed.';
    EXCEPTION
        WHEN object_not_in_prerequisite_state THEN
            IF SQLERRM <> 'BUS_CHANNEL_REVOCATION_FINAL' THEN RAISE; END IF;
    END;
END;
$$;

DO $$
DECLARE
    v_count integer;
BEGIN
    SELECT count(*) INTO v_count
    FROM workforce.bus_events
    WHERE request_id LIKE 'REQ-E2E-%'
      AND actor_id IN ('SAO-001', 'AI-ENG-001', 'EAC-001');
    -- 5 message events + 4 task events + 2 handoff events.
    IF v_count <> 11 THEN
        RAISE EXCEPTION 'Expected exactly 11 attributed E2E audit events, found %.', v_count;
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.bus_events
    WHERE actor_id = 'SYSTEM-UNATTRIBUTED'
       OR request_id = 'REQUEST-UNATTRIBUTED';
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'Found % unattributed bus audit events.', v_count;
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.bus_events
    WHERE record_type = 'CREDENTIAL'
      AND (
          COALESCE(old_record, '{}'::jsonb) ? 'token_hash'
          OR COALESCE(new_record, '{}'::jsonb) ? 'token_hash'
      );
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'Found % credential hashes in the general audit payload.', v_count;
    END IF;
END;
$$;

SELECT 'PASS: Workforce Bus identity, project scope, inbox/outbox, tasks, handoffs, acknowledgement, immutable payloads, redacted audit, idempotency, loop protection, revocation and fail-closed controls' AS acceptance_result;

ROLLBACK;
