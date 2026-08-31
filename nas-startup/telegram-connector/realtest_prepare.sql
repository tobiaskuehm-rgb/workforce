\set ON_ERROR_STOP on

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM workforce.schema_migrations
        WHERE migration_id = '003_workforce_bus_trigger_fix'
    ) THEN
        RAISE EXCEPTION 'TG_REALTEST_MIGRATION_MISSING';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP' AND channel_status = 'DISABLED'
    ) THEN
        RAISE EXCEPTION 'TG_REALTEST_CHANNEL_NOT_DISABLED';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.bus_credentials
        WHERE credential_status = 'ACTIVE'
          AND (expires_at IS NULL OR expires_at > clock_timestamp())
    ) THEN
        RAISE EXCEPTION 'TG_REALTEST_ACTIVE_CREDENTIAL_EXISTS';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.employees WHERE employee_id = 'CEO-TG-001'
    ) THEN
        RAISE EXCEPTION 'TG_REALTEST_IDENTITY_ALREADY_EXISTS';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.active_project_members
        WHERE project_id = 'START-UP' AND employee_id = 'AI-ENG-001'
    ) THEN
        RAISE EXCEPTION 'TG_REALTEST_TARGET_NOT_ACTIVE';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.bus_tasks WHERE task_id = 'ENG-TG-REALTEST-001'
    ) THEN
        RAISE EXCEPTION 'TG_REALTEST_TASK_ALREADY_EXISTS';
    END IF;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-TG-REALTEST', true);
SELECT set_config('app.request_id', 'TG-REALTEST-PREPARE', true);

INSERT INTO workforce.employees (
    employee_id,
    display_name,
    role_code,
    role_title,
    organizational_area,
    employment_status,
    source_ref
) VALUES (
    'CEO-TG-001',
    'Telegram CEO Connector – Acceptance',
    'SYSTEM_CONNECTOR',
    'Technical Acceptance Connector – not an employee',
    'CEO Office / Technical Integration',
    'ACTIVE',
    'DEC-024/ENG-007'
);

INSERT INTO workforce.employee_project_memberships (
    employee_id,
    project_id,
    membership_status,
    source_ref
) VALUES (
    'CEO-TG-001',
    'START-UP',
    'ACTIVE',
    'DEC-024/ENG-007'
);

INSERT INTO workforce.bus_member_capabilities (
    project_id,
    employee_id,
    capability_status,
    read_scope,
    task_authority,
    can_send,
    can_create_handoff,
    source_ref
) VALUES (
    'START-UP',
    'CEO-TG-001',
    'ACTIVE',
    'PARTICIPANT',
    'PROPOSE',
    true,
    false,
    'DEC-024/ENG-007'
);

INSERT INTO workforce.bus_route_allowlist (
    route_id,
    project_id,
    sender_id,
    recipient_id,
    route_kind,
    route_status,
    source_ref
) VALUES
    (
        'ROUTE-CEOTG001-AIENG001-TASK',
        'START-UP',
        'CEO-TG-001',
        'AI-ENG-001',
        'TASK',
        'ACTIVE',
        'DEC-024/ENG-007'
    ),
    (
        'ROUTE-CEOTG001-AIENG001-MESSAGE',
        'START-UP',
        'CEO-TG-001',
        'AI-ENG-001',
        'MESSAGE',
        'ACTIVE',
        'DEC-024/ENG-007'
    );

INSERT INTO workforce.bus_credentials (
    credential_id,
    project_id,
    employee_id,
    token_hash,
    credential_scope,
    credential_status,
    source_ref,
    expires_at
) VALUES (
    'CRED-TG-CEO-REALTEST-001',
    'START-UP',
    'CEO-TG-001',
    :'workforce_token_hash',
    'ACCEPTANCE',
    'ACTIVE',
    'DEC-024/ENG-007',
    clock_timestamp() + interval '30 minutes'
);

UPDATE workforce.bus_channels
SET channel_status = 'TESTING',
    source_ref = 'DEC-024/ENG-007'
WHERE project_id = 'START-UP';

COMMIT;

SELECT
    'PASS' AS result,
    ch.channel_status,
    cap.employee_id,
    cap.read_scope,
    cap.task_authority,
    cap.can_send,
    cap.can_create_handoff,
    cred.credential_scope,
    cred.credential_status,
    (cred.expires_at > clock_timestamp()) AS credential_unexpired,
    count(route.route_id)::integer AS active_route_count
FROM workforce.bus_channels AS ch
JOIN workforce.bus_member_capabilities AS cap
  ON cap.project_id = ch.project_id
 AND cap.employee_id = 'CEO-TG-001'
JOIN workforce.bus_credentials AS cred
  ON cred.project_id = ch.project_id
 AND cred.employee_id = cap.employee_id
LEFT JOIN workforce.bus_route_allowlist AS route
  ON route.project_id = ch.project_id
 AND route.sender_id = cap.employee_id
 AND route.route_status = 'ACTIVE'
WHERE ch.project_id = 'START-UP'
GROUP BY
    ch.channel_status,
    cap.employee_id,
    cap.read_scope,
    cap.task_authority,
    cap.can_send,
    cap.can_create_handoff,
    cred.credential_scope,
    cred.credential_status,
    cred.expires_at;
