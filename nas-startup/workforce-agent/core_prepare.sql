\set ON_ERROR_STOP on

-- Three short-lived ACCEPTANCE credentials for the ENG-008 core roundtrip.
-- DEC-027 fixes the cast: the core is Gerd, Karl and Anastasia.
--
--   SAO-001     Karl       creates and closes the task
--   AI-ENG-001  Gerd       owner, first piece, hands off
--   PEO-001     Anastasia  accepts the handoff, returns her result
--
-- Creates no identity, membership, capability or route. All three have had
-- them since migration 002; this script verifies and issues credentials only.
-- Credential ids carry a per-run suffix because a REVOKED credential can never
-- be reactivated.

BEGIN;

SELECT set_config('core.run_suffix', :'run_suffix', false);

DO $$
DECLARE
    member text;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP' AND channel_status = 'DISABLED'
    ) THEN
        RAISE EXCEPTION 'CORE_PREPARE_CHANNEL_NOT_DISABLED';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.bus_credentials
        WHERE credential_status = 'ACTIVE'
          AND (expires_at IS NULL OR expires_at > clock_timestamp())
    ) THEN
        RAISE EXCEPTION 'CORE_PREPARE_ACTIVE_CREDENTIAL_EXISTS';
    END IF;

    FOREACH member IN ARRAY ARRAY['SAO-001', 'AI-ENG-001', 'PEO-001'] LOOP
        IF NOT EXISTS (
            SELECT 1 FROM workforce.active_project_members
            WHERE project_id = 'START-UP' AND employee_id = member
        ) THEN
            RAISE EXCEPTION 'CORE_PREPARE_MEMBER_NOT_ACTIVE:%', member;
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM workforce.bus_member_capabilities
            WHERE project_id = 'START-UP' AND employee_id = member
              AND capability_status = 'ACTIVE' AND can_send
        ) THEN
            RAISE EXCEPTION 'CORE_PREPARE_SEND_CAPABILITY_MISSING:%', member;
        END IF;
    END LOOP;

    -- The roundtrip needs a HANDOFF route Gerd -> Anastasia. Without it the
    -- run would fail halfway and leave a task open, so check up front.
    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_route_allowlist
        WHERE project_id = 'START-UP' AND sender_id = 'AI-ENG-001'
          AND recipient_id = 'PEO-001' AND route_kind = 'HANDOFF'
          AND route_status = 'ACTIVE'
    ) THEN
        RAISE EXCEPTION 'CORE_PREPARE_HANDOFF_ROUTE_MISSING';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_route_allowlist
        WHERE project_id = 'START-UP' AND sender_id = 'SAO-001'
          AND recipient_id = 'AI-ENG-001' AND route_kind = 'TASK'
          AND route_status = 'ACTIVE'
    ) THEN
        RAISE EXCEPTION 'CORE_PREPARE_TASK_ROUTE_MISSING';
    END IF;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-CORE-ROUNDTRIP', true);
SELECT set_config('app.request_id', 'CORE-PREPARE', true);

INSERT INTO workforce.bus_credentials (
    credential_id, project_id, employee_id, token_hash,
    credential_scope, credential_status, source_ref, expires_at
) VALUES
    (('CRED-CORE-KARL-' || current_setting('core.run_suffix')), 'START-UP',
     'SAO-001', :'karl_token_hash', 'ACCEPTANCE', 'ACTIVE', :'source_ref',
     clock_timestamp() + interval '30 minutes'),
    (('CRED-CORE-GERD-' || current_setting('core.run_suffix')), 'START-UP',
     'AI-ENG-001', :'gerd_token_hash', 'ACCEPTANCE', 'ACTIVE', :'source_ref',
     clock_timestamp() + interval '30 minutes'),
    (('CRED-CORE-ANASTASIA-' || current_setting('core.run_suffix')), 'START-UP',
     'PEO-001', :'anastasia_token_hash', 'ACCEPTANCE', 'ACTIVE', :'source_ref',
     clock_timestamp() + interval '30 minutes');

UPDATE workforce.bus_channels
SET channel_status = 'TESTING', source_ref = :'source_ref'
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
 AND cred.credential_id LIKE ('CRED-CORE-%-' || current_setting('core.run_suffix'))
WHERE ch.project_id = 'START-UP'
ORDER BY cred.employee_id;
