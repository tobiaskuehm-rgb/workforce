\set ON_ERROR_STOP on

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM workforce.schema_migrations
        WHERE migration_id = '003_workforce_bus_trigger_fix'
    ) THEN
        RAISE EXCEPTION 'BUS_REALTEST_MIGRATION_MISSING';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP' AND channel_status = 'DISABLED'
    ) THEN
        RAISE EXCEPTION 'BUS_REALTEST_CHANNEL_NOT_DISABLED';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.bus_credentials
        WHERE credential_status = 'ACTIVE'
          AND (expires_at IS NULL OR expires_at > clock_timestamp())
    ) THEN
        RAISE EXCEPTION 'BUS_REALTEST_ACTIVE_CREDENTIAL_EXISTS';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.active_project_members
        WHERE project_id = 'START-UP' AND employee_id = 'SAO-001'
    ) THEN
        RAISE EXCEPTION 'BUS_REALTEST_KARL_NOT_ACTIVE';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.active_project_members
        WHERE project_id = 'START-UP' AND employee_id = 'RAS-001'
    ) THEN
        RAISE EXCEPTION 'BUS_REALTEST_THORSTEN_NOT_ACTIVE';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_route_allowlist
        WHERE project_id = 'START-UP'
          AND sender_id = 'SAO-001' AND recipient_id = 'RAS-001'
          AND route_kind = 'MESSAGE' AND route_status = 'ACTIVE'
    ) THEN
        RAISE EXCEPTION 'BUS_REALTEST_ROUTE_KARL_TO_THORSTEN_MISSING';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_route_allowlist
        WHERE project_id = 'START-UP'
          AND sender_id = 'RAS-001' AND recipient_id = 'SAO-001'
          AND route_kind = 'MESSAGE' AND route_status = 'ACTIVE'
    ) THEN
        RAISE EXCEPTION 'BUS_REALTEST_ROUTE_THORSTEN_TO_KARL_MISSING';
    END IF;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-BUS-REALTEST', true);
SELECT set_config('app.request_id', 'BUS-REALTEST-PREPARE', true);

-- Karl and Thorsten already exist as employees, active START-UP members,
-- with bus capabilities and a MESSAGE route in both directions seeded by
-- 002_workforce_bus.sql. This script only issues two short-lived
-- ACCEPTANCE credentials and opens the channel for the test window; it
-- does not create, modify or revoke either identity, membership,
-- capability or route.

INSERT INTO workforce.bus_credentials (
    credential_id,
    project_id,
    employee_id,
    token_hash,
    credential_scope,
    credential_status,
    source_ref,
    expires_at
) VALUES
    (
        'CRED-ACCEPT-KARL-001',
        'START-UP',
        'SAO-001',
        :'karl_token_hash',
        'ACCEPTANCE',
        'ACTIVE',
        :'source_ref',
        clock_timestamp() + interval '30 minutes'
    ),
    (
        'CRED-ACCEPT-THORSTEN-001',
        'START-UP',
        'RAS-001',
        :'thorsten_token_hash',
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
    cred.credential_scope,
    cred.credential_status,
    (cred.expires_at > clock_timestamp()) AS credential_unexpired,
    cred.expires_at
FROM workforce.bus_channels AS ch
JOIN workforce.bus_credentials AS cred
  ON cred.project_id = ch.project_id
 AND cred.credential_id IN ('CRED-ACCEPT-KARL-001', 'CRED-ACCEPT-THORSTEN-001')
WHERE ch.project_id = 'START-UP'
ORDER BY cred.employee_id;
