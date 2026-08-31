\set ON_ERROR_STOP on

-- Prepares the full chain: Telegram -> Connector -> Bus -> Agent -> Bus ->
-- Connector -> Telegram. Every piece has been proven on its own; they have
-- never run together.
--
-- Two things this fixes that no earlier package had:
--
-- 1. **The return leg was structurally impossible.** realtest2_prepare.sql
--    creates ROUTE-CEOTG002-AIENG001-{TASK,MESSAGE} - outbound only. No route
--    ever allowed anyone to write *to* the connector identity, so
--    publish_inbox_notifications() would always have found an empty inbox.
--    This script creates both directions.
--
-- 2. The connector talks to AGENT-ENG-001, not to AI-ENG-001. The agent moved
--    to its own identity (security review A1); pointing the connector at the
--    human's identity again would undo that.
--
-- Creates a fresh connector identity per run, because a REVOKED identity can
-- never be reactivated. Everything it creates is revoked by chain_cleanup.sql.

BEGIN;

SELECT set_config('chain.run_suffix', :'run_suffix', false);
SELECT set_config('chain.connector', 'CEO-TG-' || :'run_suffix', false);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP' AND channel_status = 'DISABLED'
    ) THEN
        RAISE EXCEPTION 'CHAIN_PREPARE_CHANNEL_NOT_DISABLED';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.bus_credentials
        WHERE credential_status = 'ACTIVE'
          AND (expires_at IS NULL OR expires_at > clock_timestamp())
    ) THEN
        RAISE EXCEPTION 'CHAIN_PREPARE_ACTIVE_CREDENTIAL_EXISTS';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.employees
        WHERE employee_id = current_setting('chain.connector')
    ) THEN
        RAISE EXCEPTION 'CHAIN_PREPARE_RUN_SUFFIX_ALREADY_USED';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.active_project_members
        WHERE project_id = 'START-UP' AND employee_id = 'AGENT-ENG-001'
    ) THEN
        RAISE EXCEPTION 'CHAIN_PREPARE_AGENT_IDENTITY_MISSING';
    END IF;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-CHAIN-TEST', true);
SELECT set_config('app.request_id', 'CHAIN-PREPARE', true);

-- A technical connector identity, explicitly not an employee - the pattern
-- CEO-TG-002 established and AGENT-ENG-001 follows.
INSERT INTO workforce.employees (
    employee_id, display_name, role_code, role_title,
    organizational_area, employment_status, source_ref
) VALUES (
    current_setting('chain.connector'),
    'Telegram Chain Connector – ' || current_setting('chain.run_suffix'),
    'SYSTEM_CONNECTOR',
    'Technical chain-test connector – not an employee',
    'CEO Office / Technical Integration',
    'ACTIVE',
    :'source_ref'
);

INSERT INTO workforce.employee_project_memberships (
    employee_id, project_id, membership_status, source_ref
) VALUES (
    current_setting('chain.connector'), 'START-UP', 'ACTIVE', :'source_ref'
);

INSERT INTO workforce.bus_member_capabilities (
    project_id, employee_id, capability_status, read_scope,
    task_authority, can_send, can_create_handoff, source_ref
) VALUES (
    'START-UP', current_setting('chain.connector'), 'ACTIVE',
    'PARTICIPANT', 'PROPOSE', true, false, :'source_ref'
);

-- Both directions. The outbound one carries the task and the request; the
-- return one is what makes an answer reach the human at all.
INSERT INTO workforce.bus_route_allowlist (
    route_id, project_id, sender_id, recipient_id, route_kind, route_status, source_ref
) VALUES
    ('ROUTE-CHAIN-' || current_setting('chain.run_suffix') || '-OUT-TASK',
     'START-UP', current_setting('chain.connector'), 'AGENT-ENG-001',
     'TASK', 'ACTIVE', :'source_ref'),
    ('ROUTE-CHAIN-' || current_setting('chain.run_suffix') || '-OUT-MESSAGE',
     'START-UP', current_setting('chain.connector'), 'AGENT-ENG-001',
     'MESSAGE', 'ACTIVE', :'source_ref'),
    ('ROUTE-CHAIN-' || current_setting('chain.run_suffix') || '-BACK-MESSAGE',
     'START-UP', 'AGENT-ENG-001', current_setting('chain.connector'),
     'MESSAGE', 'ACTIVE', :'source_ref');

INSERT INTO workforce.bus_credentials (
    credential_id, project_id, employee_id, token_hash,
    credential_scope, credential_status, source_ref, expires_at
) VALUES
    ('CRED-CHAIN-CONNECTOR-' || current_setting('chain.run_suffix'), 'START-UP',
     current_setting('chain.connector'), :'connector_token_hash',
     'ACCEPTANCE', 'ACTIVE', :'source_ref',
     clock_timestamp() + interval '30 minutes'),
    ('CRED-CHAIN-AGENT-' || current_setting('chain.run_suffix'), 'START-UP',
     'AGENT-ENG-001', :'agent_token_hash',
     'ACCEPTANCE', 'ACTIVE', :'source_ref',
     clock_timestamp() + interval '30 minutes');

UPDATE workforce.bus_channels
SET channel_status = 'TESTING', source_ref = :'source_ref'
WHERE project_id = 'START-UP';

COMMIT;

SELECT
    'PASS' AS result,
    ch.channel_status,
    cred.employee_id,
    cred.credential_status,
    (cred.expires_at > clock_timestamp()) AS unexpired,
    (SELECT count(*)::integer FROM workforce.bus_route_allowlist
     WHERE route_id LIKE 'ROUTE-CHAIN-' || current_setting('chain.run_suffix') || '%'
       AND route_status = 'ACTIVE') AS chain_routes
FROM workforce.bus_channels AS ch
JOIN workforce.bus_credentials AS cred
  ON cred.project_id = ch.project_id
 AND cred.credential_id LIKE 'CRED-CHAIN-%-' || current_setting('chain.run_suffix')
WHERE ch.project_id = 'START-UP'
ORDER BY cred.employee_id;
