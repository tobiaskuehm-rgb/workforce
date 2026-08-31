\set ON_ERROR_STOP on

-- Revokes exactly ONE of the two acceptance credentials while the channel
-- stays TESTING. Closes the last gap in activation-gate item 6 (security
-- review 2026-08-31, F7): after the regular cleanup the channel is DISABLED,
-- and then every bus endpoint answers 503 BUS_CHANNEL_NOT_ACTIVE before the
-- token is ever examined, so "revoked credential -> 401" cannot be shown.
--
-- Karl's credential is deliberately left ACTIVE so the follow-up probe can
-- prove the revocation is targeted and not a channel-wide side effect.

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP' AND channel_status = 'TESTING'
    ) THEN
        RAISE EXCEPTION 'BUS_REVOKETEST_CHANNEL_NOT_TESTING';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_credentials
        WHERE credential_id = 'CRED-ACCEPT-THORSTEN-001'
          AND credential_status = 'ACTIVE'
          AND (expires_at IS NULL OR expires_at > clock_timestamp())
    ) THEN
        RAISE EXCEPTION 'BUS_REVOKETEST_THORSTEN_CREDENTIAL_NOT_ACTIVE';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_credentials
        WHERE credential_id = 'CRED-ACCEPT-KARL-001'
          AND credential_status = 'ACTIVE'
          AND (expires_at IS NULL OR expires_at > clock_timestamp())
    ) THEN
        RAISE EXCEPTION 'BUS_REVOKETEST_KARL_CREDENTIAL_NOT_ACTIVE';
    END IF;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-BUS-REALTEST', true);
SELECT set_config('app.request_id', 'BUS-REVOKETEST-REVOKE', true);

UPDATE workforce.bus_credentials
SET credential_status = 'REVOKED',
    revoked_at = clock_timestamp(),
    revocation_reason = 'Revocation negative test: prove a revoked credential is refused while the channel is still TESTING'
WHERE credential_id = 'CRED-ACCEPT-THORSTEN-001'
  AND credential_status = 'ACTIVE';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_credentials
        WHERE credential_id = 'CRED-ACCEPT-THORSTEN-001'
          AND credential_status = 'REVOKED'
    ) THEN
        RAISE EXCEPTION 'BUS_REVOKETEST_REVOCATION_DID_NOT_APPLY';
    END IF;

    -- Karl must survive, otherwise the probe cannot tell a targeted
    -- revocation apart from a channel-wide outage.
    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_credentials
        WHERE credential_id = 'CRED-ACCEPT-KARL-001'
          AND credential_status = 'ACTIVE'
    ) THEN
        RAISE EXCEPTION 'BUS_REVOKETEST_KARL_CREDENTIAL_LOST';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP' AND channel_status = 'TESTING'
    ) THEN
        RAISE EXCEPTION 'BUS_REVOKETEST_CHANNEL_LEFT_TESTING';
    END IF;
END;
$$;

COMMIT;

SELECT
    'PASS' AS result,
    ch.channel_status,
    cred.employee_id,
    cred.credential_id,
    cred.credential_status
FROM workforce.bus_channels AS ch
JOIN workforce.bus_credentials AS cred
  ON cred.project_id = ch.project_id
 AND cred.credential_id IN ('CRED-ACCEPT-KARL-001', 'CRED-ACCEPT-THORSTEN-001')
WHERE ch.project_id = 'START-UP'
ORDER BY cred.employee_id;
