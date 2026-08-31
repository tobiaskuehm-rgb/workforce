\set ON_ERROR_STOP on

BEGIN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP'
          AND channel_status NOT IN ('DISABLED', 'TESTING')
    ) THEN
        RAISE EXCEPTION 'TG_REALTEST_CLEANUP_CHANNEL_STATE_DENIED';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.employees
        WHERE employee_id = 'CEO-TG-001'
          AND source_ref <> 'DEC-024/ENG-007'
    ) THEN
        RAISE EXCEPTION 'TG_REALTEST_CLEANUP_IDENTITY_SOURCE_MISMATCH';
    END IF;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-TG-REALTEST', true);
SELECT set_config('app.request_id', 'TG-REALTEST-CLEANUP', true);

UPDATE workforce.bus_credentials
SET credential_status = 'REVOKED',
    revoked_at = clock_timestamp(),
    revocation_reason = 'DEC-024 Telegram realtest completed or stopped'
WHERE credential_id = 'CRED-TG-CEO-REALTEST-001'
  AND credential_status <> 'REVOKED';

UPDATE workforce.bus_route_allowlist
SET route_status = 'REVOKED',
    revoked_at = clock_timestamp(),
    revocation_reason = 'DEC-024 Telegram realtest completed or stopped'
WHERE sender_id = 'CEO-TG-001'
  AND project_id = 'START-UP'
  AND route_status <> 'REVOKED';

UPDATE workforce.bus_member_capabilities
SET capability_status = 'REVOKED',
    revoked_at = clock_timestamp(),
    revocation_reason = 'DEC-024 Telegram realtest completed or stopped'
WHERE employee_id = 'CEO-TG-001'
  AND project_id = 'START-UP'
  AND capability_status <> 'REVOKED';

UPDATE workforce.employee_project_memberships
SET membership_status = 'REVOKED',
    revoked_at = clock_timestamp(),
    revocation_reason = 'DEC-024 Telegram realtest completed or stopped'
WHERE employee_id = 'CEO-TG-001'
  AND project_id = 'START-UP'
  AND membership_status <> 'REVOKED';

UPDATE workforce.employees
SET employment_status = 'REVOKED',
    revoked_at = clock_timestamp(),
    revocation_reason = 'DEC-024 Telegram realtest completed or stopped'
WHERE employee_id = 'CEO-TG-001'
  AND employment_status <> 'REVOKED';

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
        RAISE EXCEPTION 'TG_REALTEST_CLEANUP_ACTIVE_CREDENTIAL_REMAINS';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP' AND channel_status = 'DISABLED'
    ) THEN
        RAISE EXCEPTION 'TG_REALTEST_CLEANUP_CHANNEL_NOT_DISABLED';
    END IF;
END;
$$;

COMMIT;

SELECT
    'PASS' AS result,
    ch.channel_status,
    COALESCE(cred.credential_status, 'ABSENT') AS credential_status,
    COALESCE(cap.capability_status, 'ABSENT') AS capability_status,
    COALESCE(m.membership_status, 'ABSENT') AS membership_status,
    COALESCE(e.employment_status, 'ABSENT') AS identity_status,
    (
        SELECT count(*)::integer
        FROM workforce.bus_credentials
        WHERE credential_status = 'ACTIVE'
          AND (expires_at IS NULL OR expires_at > clock_timestamp())
    ) AS active_unexpired_credentials
FROM workforce.bus_channels AS ch
LEFT JOIN workforce.bus_credentials AS cred
  ON cred.project_id = ch.project_id
 AND cred.credential_id = 'CRED-TG-CEO-REALTEST-001'
LEFT JOIN workforce.bus_member_capabilities AS cap
  ON cap.project_id = ch.project_id
 AND cap.employee_id = 'CEO-TG-001'
LEFT JOIN workforce.employee_project_memberships AS m
  ON m.project_id = ch.project_id
 AND m.employee_id = 'CEO-TG-001'
LEFT JOIN workforce.employees AS e
  ON e.employee_id = 'CEO-TG-001'
WHERE ch.project_id = 'START-UP';
