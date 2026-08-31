\set ON_ERROR_STOP on

-- Issues the two short-lived ACCEPTANCE credentials the worker-core gate needs
-- and opens the channel for the test window.
--
--   AGENT-ENG-001  the runtime under test
--   SAO-001        the requester whose messages it answers
--
-- Creates no identity, membership, capability or route. Those are permanent
-- and belong to agent_identity_create.sql and the migration; this only checks
-- they are in place and refuses to run if they are not.
--
-- Credential ids carry a per-run suffix. A REVOKED credential can never be
-- reactivated (trigger bus_guard_credential_update), so a fixed id would make
-- the package single-use - the defect the bus realtest hit on 2026-08-31.

BEGIN;

SELECT set_config('wc.run_suffix', :'run_suffix', false);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM workforce.schema_migrations
        WHERE migration_id = '003_workforce_bus_trigger_fix'
    ) THEN
        RAISE EXCEPTION 'WORKERCORE_PREPARE_MIGRATION_MISSING';
    END IF;

    -- The denial audit is part of what this run has to leave behind.
    IF NOT EXISTS (
        SELECT 1 FROM workforce.schema_migrations
        WHERE migration_id = '004_bus_denial_audit'
    ) THEN
        RAISE EXCEPTION 'WORKERCORE_PREPARE_DENIAL_AUDIT_MISSING';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP' AND channel_status = 'DISABLED'
    ) THEN
        RAISE EXCEPTION 'WORKERCORE_PREPARE_CHANNEL_NOT_DISABLED';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.bus_credentials
        WHERE credential_status = 'ACTIVE'
          AND (expires_at IS NULL OR expires_at > clock_timestamp())
    ) THEN
        RAISE EXCEPTION 'WORKERCORE_PREPARE_ACTIVE_CREDENTIAL_EXISTS';
    END IF;

    -- The agent identity is the whole point of security review A1. Running
    -- this gate under AI-ENG-001 would prove the wrong thing.
    IF NOT EXISTS (
        SELECT 1 FROM workforce.employees WHERE employee_id = 'AGENT-ENG-001'
    ) THEN
        RAISE EXCEPTION 'WORKERCORE_PREPARE_AGENT_IDENTITY_MISSING';
    END IF;

    -- Both directions have to be allowed, or the run fails halfway through on
    -- something that has nothing to do with the runtime.
    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_route_allowlist
        WHERE project_id = 'START-UP' AND sender_id = 'SAO-001'
          AND recipient_id = 'AGENT-ENG-001' AND route_kind = 'MESSAGE'
          AND route_status = 'ACTIVE'
    ) THEN
        RAISE EXCEPTION 'WORKERCORE_PREPARE_ROUTE_TO_AGENT_MISSING';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_route_allowlist
        WHERE project_id = 'START-UP' AND sender_id = 'AGENT-ENG-001'
          AND recipient_id = 'SAO-001' AND route_kind = 'MESSAGE'
          AND route_status = 'ACTIVE'
    ) THEN
        RAISE EXCEPTION 'WORKERCORE_PREPARE_ROUTE_FROM_AGENT_MISSING';
    END IF;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-WORKER-CORE', true);
SELECT set_config('app.request_id',
                  'WORKERCORE-PREPARE-' || current_setting('wc.run_suffix'), true);

INSERT INTO workforce.bus_credentials (
    credential_id, project_id, employee_id, token_hash,
    credential_scope, credential_status, source_ref, expires_at
) VALUES (
    ('CRED-ACCEPT-WC-AGENT-' || current_setting('wc.run_suffix')),
    'START-UP', 'AGENT-ENG-001', :'agent_token_hash',
    'ACCEPTANCE', 'ACTIVE', :'source_ref',
    clock_timestamp() + interval '30 minutes'
), (
    ('CRED-ACCEPT-WC-KARL-' || current_setting('wc.run_suffix')),
    'START-UP', 'SAO-001', :'karl_token_hash',
    'ACCEPTANCE', 'ACTIVE', :'source_ref',
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
    cred.credential_status,
    (cred.expires_at > clock_timestamp()) AS credential_unexpired
FROM workforce.bus_channels AS ch
JOIN workforce.bus_credentials AS cred
  ON cred.project_id = ch.project_id
 AND cred.credential_id LIKE 'CRED-ACCEPT-WC-%' || current_setting('wc.run_suffix')
WHERE ch.project_id = 'START-UP'
ORDER BY cred.employee_id;
