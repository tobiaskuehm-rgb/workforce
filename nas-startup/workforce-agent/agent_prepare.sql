\set ON_ERROR_STOP on

-- Issues one short-lived ACCEPTANCE credential for the agent identity and
-- opens the channel for the test window. Creates no identity, membership,
-- capability or route - agent_identity_create.sql did that once, permanently.
-- This script only verifies they are in place.
--
-- The identity is AGENT-ENG-001, not AI-ENG-001. Borrowing Gerd's credential
-- made every machine answer look like a message from a person on probation
-- (security review A1); the dedicated identity carries role_code SYSTEM_AGENT
-- and a role_title that says "not an employee" outright.
--
-- Credential ids carry a per-run suffix. A REVOKED credential can never be
-- reactivated (trigger bus_guard_credential_update), so a fixed id would make
-- the package single-use - the defect the bus realtest hit on 2026-08-31.

BEGIN;

SELECT set_config('agent.run_suffix', :'run_suffix', false);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM workforce.schema_migrations
        WHERE migration_id = '003_workforce_bus_trigger_fix'
    ) THEN
        RAISE EXCEPTION 'AGENT_PREPARE_MIGRATION_MISSING';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP' AND channel_status = 'DISABLED'
    ) THEN
        RAISE EXCEPTION 'AGENT_PREPARE_CHANNEL_NOT_DISABLED';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.bus_credentials
        WHERE credential_status = 'ACTIVE'
          AND (expires_at IS NULL OR expires_at > clock_timestamp())
    ) THEN
        RAISE EXCEPTION 'AGENT_PREPARE_ACTIVE_CREDENTIAL_EXISTS';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.bus_credentials
        WHERE credential_id = ('CRED-ACCEPT-AGENT-' || current_setting('agent.run_suffix'))
    ) THEN
        RAISE EXCEPTION 'AGENT_PREPARE_RUN_SUFFIX_ALREADY_USED';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.active_project_members
        WHERE project_id = 'START-UP' AND employee_id = 'AGENT-ENG-001'
    ) THEN
        RAISE EXCEPTION 'AGENT_PREPARE_IDENTITY_NOT_ACTIVE';
    END IF;

    -- The agent must be able to send, or it could read work and never answer.
    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_member_capabilities
        WHERE project_id = 'START-UP'
          AND employee_id = 'AGENT-ENG-001'
          AND capability_status = 'ACTIVE'
          AND can_send
    ) THEN
        RAISE EXCEPTION 'AGENT_PREPARE_SEND_CAPABILITY_MISSING';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_route_allowlist
        WHERE project_id = 'START-UP'
          AND sender_id = 'AGENT-ENG-001'
          AND route_kind = 'MESSAGE'
          AND route_status = 'ACTIVE'
    ) THEN
        RAISE EXCEPTION 'AGENT_PREPARE_NO_ACTIVE_ROUTE';
    END IF;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-WORKFORCE-AGENT', true);
SELECT set_config('app.request_id', 'AGENT-PREPARE', true);

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
    ('CRED-ACCEPT-AGENT-' || current_setting('agent.run_suffix')),
    'START-UP',
    'AGENT-ENG-001',
    :'agent_token_hash',
    'ACCEPTANCE',
    'ACTIVE',
    :'source_ref',
    clock_timestamp() + interval '30 minutes'
);

UPDATE workforce.bus_channels
SET channel_status = 'TESTING',
    source_ref = :'source_ref'
WHERE project_id = 'START-UP';

COMMIT;

SELECT
    'PASS' AS result,
    ch.channel_status,
    cred.employee_id,
    cred.credential_id,
    cred.credential_scope,
    cred.credential_status,
    (cred.expires_at > clock_timestamp()) AS credential_unexpired,
    cred.expires_at,
    (
        SELECT count(*)::integer
        FROM workforce.bus_messages
        WHERE recipient_id = 'AGENT-ENG-001'
          AND project_id = 'START-UP'
          AND delivery_status = 'DELIVERED'
    ) AS pending_inbox_messages
FROM workforce.bus_channels AS ch
JOIN workforce.bus_credentials AS cred
  ON cred.project_id = ch.project_id
 AND cred.credential_id = ('CRED-ACCEPT-AGENT-' || current_setting('agent.run_suffix'))
WHERE ch.project_id = 'START-UP';
