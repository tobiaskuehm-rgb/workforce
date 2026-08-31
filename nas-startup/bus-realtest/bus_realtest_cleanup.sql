\set ON_ERROR_STOP on

BEGIN;

SELECT set_config('bus.run_suffix', :'run_suffix', false);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP'
          AND channel_status NOT IN ('DISABLED', 'TESTING')
    ) THEN
        RAISE EXCEPTION 'BUS_REALTEST_CLEANUP_CHANNEL_STATE_DENIED';
    END IF;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-BUS-REALTEST', true);
SELECT set_config('app.request_id', 'BUS-REALTEST-CLEANUP', true);

-- Only the two test credentials and the channel state are touched here.
-- Karl's and Thorsten's employee, membership, capability and route rows
-- are permanent and are intentionally left untouched by this cleanup.

UPDATE workforce.bus_credentials
SET credential_status = 'REVOKED',
    revoked_at = clock_timestamp(),
    revocation_reason = 'Bus realtest Karl/Thorsten completed or stopped'
WHERE credential_id IN (('CRED-ACCEPT-KARL-' || current_setting('bus.run_suffix')), ('CRED-ACCEPT-THORSTEN-' || current_setting('bus.run_suffix')))
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
        RAISE EXCEPTION 'BUS_REALTEST_CLEANUP_ACTIVE_CREDENTIAL_REMAINS';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP' AND channel_status = 'DISABLED'
    ) THEN
        RAISE EXCEPTION 'BUS_REALTEST_CLEANUP_CHANNEL_NOT_DISABLED';
    END IF;
END;
$$;

COMMIT;

SELECT
    'PASS' AS result,
    ch.channel_status,
    cred.employee_id,
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
 AND cred.credential_id IN (('CRED-ACCEPT-KARL-' || current_setting('bus.run_suffix')), ('CRED-ACCEPT-THORSTEN-' || current_setting('bus.run_suffix')))
WHERE ch.project_id = 'START-UP'
ORDER BY cred.employee_id;
