\set ON_ERROR_STOP on

-- Revokes the three core credentials and closes the channel. Success, failure
-- and timeout lead into the same cleanup.
--
-- Identities, memberships, capabilities and routes of SAO-001, AI-ENG-001 and
-- PEO-001 are permanent and deliberately untouched - they existed long before
-- this package. Tasks, handoffs, messages and audit rows stay too: they are
-- the evidence the roundtrip produced, and core_audit.sql reads them.

BEGIN;

SELECT set_config('core.run_suffix', :'run_suffix', false);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP'
          AND channel_status NOT IN ('DISABLED', 'TESTING')
    ) THEN
        RAISE EXCEPTION 'CORE_CLEANUP_CHANNEL_STATE_DENIED';
    END IF;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-CORE-ROUNDTRIP', true);
SELECT set_config('app.request_id', 'CORE-CLEANUP', true);

UPDATE workforce.bus_credentials
SET credential_status = 'REVOKED',
    revoked_at = clock_timestamp(),
    revocation_reason = 'Core roundtrip completed or stopped'
WHERE credential_id LIKE ('CRED-CORE-%-' || current_setting('core.run_suffix'))
  AND credential_status <> 'REVOKED';

UPDATE workforce.bus_channels
SET channel_status = 'DISABLED', source_ref = 'DEC-016/ENG-003'
WHERE project_id = 'START-UP' AND channel_status = 'TESTING';

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM workforce.bus_credentials
        WHERE credential_status = 'ACTIVE'
          AND (expires_at IS NULL OR expires_at > clock_timestamp())
    ) THEN
        RAISE EXCEPTION 'CORE_CLEANUP_ACTIVE_CREDENTIAL_REMAINS';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP' AND channel_status = 'DISABLED'
    ) THEN
        RAISE EXCEPTION 'CORE_CLEANUP_CHANNEL_NOT_DISABLED';
    END IF;
END;
$$;

COMMIT;

SELECT 'PASS' AS result, ch.channel_status, cred.employee_id, cred.credential_status,
    (SELECT count(*)::integer FROM workforce.bus_credentials
     WHERE credential_status = 'ACTIVE'
       AND (expires_at IS NULL OR expires_at > clock_timestamp())) AS active_total
FROM workforce.bus_channels AS ch
JOIN workforce.bus_credentials AS cred
  ON cred.project_id = ch.project_id
 AND cred.credential_id LIKE ('CRED-CORE-%-' || current_setting('core.run_suffix'))
WHERE ch.project_id = 'START-UP'
ORDER BY cred.employee_id;
