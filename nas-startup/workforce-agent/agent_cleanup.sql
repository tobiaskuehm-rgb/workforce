\set ON_ERROR_STOP on

-- Revokes the agent's credential and closes the channel. Runs after every
-- agent run - success, failure or timeout lead into the same cleanup.
--
-- Identity, membership, capability and routes of AI-ENG-001 are permanent and
-- are deliberately left untouched: they existed before this package and other
-- work depends on them. Only the credential this run issued is revoked.
--
-- Messages, acknowledgements and audit rows the run produced stay - they are
-- evidence, not a live permission.

BEGIN;

SELECT set_config('agent.run_suffix', :'run_suffix', false);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP'
          AND channel_status NOT IN ('DISABLED', 'TESTING')
    ) THEN
        RAISE EXCEPTION 'AGENT_CLEANUP_CHANNEL_STATE_DENIED';
    END IF;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-WORKFORCE-AGENT', true);
SELECT set_config('app.request_id', 'AGENT-CLEANUP', true);

UPDATE workforce.bus_credentials
SET credential_status = 'REVOKED',
    revoked_at = clock_timestamp(),
    revocation_reason = 'Workforce agent run completed or stopped'
WHERE credential_id = ('CRED-ACCEPT-AGENT-' || current_setting('agent.run_suffix'))
  AND credential_status <> 'REVOKED';

UPDATE workforce.bus_channels
SET channel_status = 'DISABLED',
    source_ref = 'DEC-016/ENG-003'
WHERE project_id = 'START-UP'
  AND channel_status = 'TESTING';

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM workforce.bus_credentials
        WHERE credential_status = 'ACTIVE'
          AND (expires_at IS NULL OR expires_at > clock_timestamp())
    ) THEN
        RAISE EXCEPTION 'AGENT_CLEANUP_ACTIVE_CREDENTIAL_REMAINS';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP' AND channel_status = 'DISABLED'
    ) THEN
        RAISE EXCEPTION 'AGENT_CLEANUP_CHANNEL_NOT_DISABLED';
    END IF;
END;
$$;

COMMIT;

SELECT
    'PASS' AS result,
    ch.channel_status,
    cred.employee_id,
    cred.credential_id,
    cred.credential_status,
    (
        SELECT count(*)::integer
        FROM workforce.bus_credentials
        WHERE credential_status = 'ACTIVE'
          AND (expires_at IS NULL OR expires_at > clock_timestamp())
    ) AS active_unexpired_credentials_total
FROM workforce.bus_channels AS ch
JOIN workforce.bus_credentials AS cred
  ON cred.project_id = ch.project_id
 AND cred.credential_id = ('CRED-ACCEPT-AGENT-' || current_setting('agent.run_suffix'))
WHERE ch.project_id = 'START-UP';
