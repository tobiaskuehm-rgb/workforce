\set ON_ERROR_STOP on

-- Revokes both worker-core credentials and closes the channel. Runs after
-- every run - success, failure or timeout lead into the same cleanup.
--
-- Messages, acknowledgements, audit rows and denial rows the run produced stay
-- behind: they are the evidence, not a live permission.

BEGIN;

SELECT set_config('wc.run_suffix', :'run_suffix', false);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP'
          AND channel_status NOT IN ('DISABLED', 'TESTING')
    ) THEN
        RAISE EXCEPTION 'WORKERCORE_CLEANUP_CHANNEL_STATE_DENIED';
    END IF;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-WORKER-CORE', true);
SELECT set_config('app.request_id',
                  'WORKERCORE-CLEANUP-' || current_setting('wc.run_suffix'), true);

UPDATE workforce.bus_credentials
SET credential_status = 'REVOKED',
    revoked_at = clock_timestamp(),
    revocation_reason = 'Worker core gate completed or stopped'
WHERE credential_id IN (
        ('CRED-ACCEPT-WC-AGENT-' || current_setting('wc.run_suffix')),
        ('CRED-ACCEPT-WC-KARL-'  || current_setting('wc.run_suffix'))
      )
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
        RAISE EXCEPTION 'WORKERCORE_CLEANUP_ACTIVE_CREDENTIAL_REMAINS';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP' AND channel_status = 'DISABLED'
    ) THEN
        RAISE EXCEPTION 'WORKERCORE_CLEANUP_CHANNEL_NOT_DISABLED';
    END IF;
END;
$$;

COMMIT;

SELECT
    'PASS' AS result,
    ch.channel_status,
    (
        SELECT count(*)::integer
        FROM workforce.bus_credentials
        WHERE credential_status = 'ACTIVE'
          AND (expires_at IS NULL OR expires_at > clock_timestamp())
    ) AS active_unexpired_credentials_total
FROM workforce.bus_channels AS ch
WHERE ch.project_id = 'START-UP';
