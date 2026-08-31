\set ON_ERROR_STOP on

BEGIN TRANSACTION READ ONLY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM workforce.schema_migrations
        WHERE migration_id = '003_workforce_bus_trigger_fix'
    ) THEN
        RAISE EXCEPTION 'TG_REALTEST2_PREFLIGHT_MIGRATION_MISSING';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.bus_channels
        WHERE project_id = 'START-UP' AND channel_status = 'DISABLED'
    ) THEN
        RAISE EXCEPTION 'TG_REALTEST2_PREFLIGHT_CHANNEL_NOT_DISABLED';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.bus_credentials
        WHERE credential_status = 'ACTIVE'
          AND (expires_at IS NULL OR expires_at > clock_timestamp())
    ) THEN
        RAISE EXCEPTION 'TG_REALTEST2_PREFLIGHT_ACTIVE_CREDENTIAL_EXISTS';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.employees WHERE employee_id = 'CEO-TG-002'
    ) THEN
        RAISE EXCEPTION 'TG_REALTEST2_PREFLIGHT_IDENTITY_ALREADY_EXISTS';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.bus_tasks WHERE task_id = 'ENG-TG-REALTEST-002'
    ) THEN
        RAISE EXCEPTION 'TG_REALTEST2_PREFLIGHT_TASK_ALREADY_EXISTS';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.active_project_members
        WHERE project_id = 'START-UP' AND employee_id = 'AI-ENG-001'
    ) THEN
        RAISE EXCEPTION 'TG_REALTEST2_PREFLIGHT_TARGET_NOT_ACTIVE';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.employees
        WHERE employee_id = 'CEO-TG-001' AND employment_status = 'REVOKED'
    ) THEN
        RAISE EXCEPTION 'TG_REALTEST2_PREFLIGHT_PREVIOUS_IDENTITY_NOT_REVOKED';
    END IF;
END;
$$;

SELECT
    'PASS' AS result,
    ch.channel_status,
    (
        SELECT count(*)::integer
        FROM workforce.bus_credentials
        WHERE credential_status = 'ACTIVE'
          AND (expires_at IS NULL OR expires_at > clock_timestamp())
    ) AS active_unexpired_credentials,
    (
        SELECT employment_status
        FROM workforce.employees
        WHERE employee_id = 'CEO-TG-001'
    ) AS previous_identity_status,
    NOT EXISTS (
        SELECT 1 FROM workforce.employees WHERE employee_id = 'CEO-TG-002'
    ) AS new_identity_absent,
    NOT EXISTS (
        SELECT 1 FROM workforce.bus_tasks WHERE task_id = 'ENG-TG-REALTEST-002'
    ) AS new_task_absent,
    EXISTS (
        SELECT 1 FROM workforce.active_project_members
        WHERE project_id = 'START-UP' AND employee_id = 'AI-ENG-001'
    ) AS target_active
FROM workforce.bus_channels AS ch
WHERE ch.project_id = 'START-UP';

ROLLBACK;
