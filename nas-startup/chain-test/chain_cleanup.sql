\set ON_ERROR_STOP on

-- Reverses everything chain_prepare.sql created, and closes the channel.
--
-- Nothing is deleted. The connector identity, its membership, its capability
-- and its three routes are set to REVOKED; prevent_hard_delete blocks a DELETE
-- on every bus table anyway, and the registry follows the same rule. What the
-- run produced - tasks, messages, acknowledgements, audit and denial rows -
-- stays: that is the evidence, not a live permission.
--
-- Must use the same run suffix as the prepare step. A REVOKED credential can
-- never be reactivated, so a mismatched suffix leaves a live credential behind
-- and the final check below fails loudly rather than quietly.

BEGIN;

SELECT set_config('chain.run_suffix', :'run_suffix', false);
SELECT set_config('chain.connector', 'CEO-TG-' || :'run_suffix', false);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP'
          AND channel_status NOT IN ('DISABLED', 'TESTING')
    ) THEN
        RAISE EXCEPTION 'CHAIN_CLEANUP_CHANNEL_STATE_DENIED';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.employees
        WHERE employee_id = current_setting('chain.connector')
    ) THEN
        RAISE EXCEPTION 'CHAIN_CLEANUP_UNKNOWN_RUN_SUFFIX';
    END IF;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-CHAIN-TEST', true);
SELECT set_config('app.request_id',
                  'CHAIN-CLEANUP-' || current_setting('chain.run_suffix'), true);

UPDATE workforce.bus_credentials
SET credential_status = 'REVOKED',
    revoked_at = clock_timestamp(),
    revocation_reason = 'Chain test completed or stopped'
WHERE credential_id IN (
        ('CRED-CHAIN-CONNECTOR-' || current_setting('chain.run_suffix')),
        ('CRED-CHAIN-AGENT-'     || current_setting('chain.run_suffix'))
      )
  AND credential_status <> 'REVOKED';

-- A revocation needs its metadata, not just the status: every bus table has a
-- CHECK that REVOKED implies revoked_at and a non-empty revocation_reason.
-- Setting only the status aborts the whole transaction (found in the chain run
-- on 2026-09-01), which is the constraint doing exactly its job - a revoked
-- row without a reason would be a hole in the audit trail.
UPDATE workforce.bus_route_allowlist
SET route_status = 'REVOKED',
    revoked_at = clock_timestamp(),
    revocation_reason = 'Chain test completed or stopped'
WHERE route_id LIKE 'ROUTE-CHAIN-' || current_setting('chain.run_suffix') || '%'
  AND route_status <> 'REVOKED';

UPDATE workforce.bus_member_capabilities
SET capability_status = 'REVOKED',
    revoked_at = clock_timestamp(),
    revocation_reason = 'Chain test completed or stopped'
WHERE project_id = 'START-UP'
  AND employee_id = current_setting('chain.connector')
  AND capability_status <> 'REVOKED';

UPDATE workforce.employee_project_memberships
SET membership_status = 'REVOKED',
    revoked_at = clock_timestamp()
WHERE project_id = 'START-UP'
  AND employee_id = current_setting('chain.connector')
  AND membership_status <> 'REVOKED';

-- The identity itself is retired, not removed. A REVOKED identity can never be
-- reactivated, which is why every run creates its own.
UPDATE workforce.employees
SET employment_status = 'REVOKED',
    revoked_at = clock_timestamp()
WHERE employee_id = current_setting('chain.connector')
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
        RAISE EXCEPTION 'CHAIN_CLEANUP_ACTIVE_CREDENTIAL_REMAINS';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.bus_route_allowlist
        WHERE route_id LIKE 'ROUTE-CHAIN-%' AND route_status = 'ACTIVE'
    ) THEN
        RAISE EXCEPTION 'CHAIN_CLEANUP_ACTIVE_CHAIN_ROUTE_REMAINS';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP' AND channel_status = 'DISABLED'
    ) THEN
        RAISE EXCEPTION 'CHAIN_CLEANUP_CHANNEL_NOT_DISABLED';
    END IF;
END;
$$;

COMMIT;

SELECT
    'PASS' AS result,
    ch.channel_status,
    (SELECT employment_status FROM workforce.employees
     WHERE employee_id = current_setting('chain.connector')) AS connector_identity,
    (SELECT count(*)::integer FROM workforce.bus_route_allowlist
     WHERE route_id LIKE 'ROUTE-CHAIN-' || current_setting('chain.run_suffix') || '%'
       AND route_status = 'ACTIVE') AS active_chain_routes,
    (SELECT count(*)::integer FROM workforce.bus_credentials
     WHERE credential_status = 'ACTIVE'
       AND (expires_at IS NULL OR expires_at > clock_timestamp())) AS active_credentials
FROM workforce.bus_channels AS ch
WHERE ch.project_id = 'START-UP';
