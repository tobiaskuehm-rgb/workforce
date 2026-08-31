\set ON_ERROR_STOP on

BEGIN;

CREATE SCHEMA workforce;

CREATE TABLE workforce.schema_migrations (
    migration_id text PRIMARY KEY,
    description text NOT NULL,
    applied_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE workforce.projects (
    project_id text PRIMARY KEY,
    display_name text NOT NULL,
    project_status text NOT NULL DEFAULT 'ACTIVE',
    source_ref text NOT NULL,
    version bigint NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    revoked_at timestamptz,
    revocation_reason text,
    CONSTRAINT projects_id_format CHECK (project_id ~ '^[A-Z][A-Z0-9-]{2,31}$'),
    CONSTRAINT projects_display_name_length CHECK (char_length(display_name) BETWEEN 1 AND 120),
    CONSTRAINT projects_status CHECK (project_status IN ('ACTIVE', 'SUSPENDED', 'REVOKED', 'INACTIVE')),
    CONSTRAINT projects_version_positive CHECK (version >= 1),
    CONSTRAINT projects_revocation_consistent CHECK (
        (project_status = 'REVOKED' AND revoked_at IS NOT NULL)
        OR (project_status <> 'REVOKED' AND revoked_at IS NULL)
    )
);

CREATE TABLE workforce.employees (
    employee_id text PRIMARY KEY,
    display_name text NOT NULL,
    role_code text NOT NULL,
    role_title text NOT NULL,
    organizational_area text NOT NULL,
    employment_status text NOT NULL DEFAULT 'PROBATION',
    source_ref text NOT NULL,
    version bigint NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    revoked_at timestamptz,
    revocation_reason text,
    CONSTRAINT employees_id_format CHECK (employee_id ~ '^[A-Z][A-Z0-9-]{2,31}$'),
    CONSTRAINT employees_display_name_length CHECK (char_length(display_name) BETWEEN 1 AND 100),
    CONSTRAINT employees_role_code_format CHECK (role_code ~ '^[A-Z][A-Z0-9_]{2,63}$'),
    CONSTRAINT employees_role_title_length CHECK (char_length(role_title) BETWEEN 1 AND 160),
    CONSTRAINT employees_area_length CHECK (char_length(organizational_area) BETWEEN 1 AND 160),
    CONSTRAINT employees_status CHECK (employment_status IN ('PROBATION', 'ACTIVE', 'SUSPENDED', 'REVOKED', 'INACTIVE')),
    CONSTRAINT employees_version_positive CHECK (version >= 1),
    CONSTRAINT employees_revocation_consistent CHECK (
        (employment_status = 'REVOKED' AND revoked_at IS NOT NULL)
        OR (employment_status <> 'REVOKED' AND revoked_at IS NULL)
    )
);

CREATE TABLE workforce.employee_project_memberships (
    employee_id text NOT NULL REFERENCES workforce.employees(employee_id),
    project_id text NOT NULL REFERENCES workforce.projects(project_id),
    membership_status text NOT NULL DEFAULT 'ACTIVE',
    source_ref text NOT NULL,
    version bigint NOT NULL DEFAULT 1,
    joined_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    revoked_at timestamptz,
    revocation_reason text,
    PRIMARY KEY (employee_id, project_id),
    CONSTRAINT memberships_status CHECK (membership_status IN ('ACTIVE', 'SUSPENDED', 'REVOKED', 'INACTIVE')),
    CONSTRAINT memberships_version_positive CHECK (version >= 1),
    CONSTRAINT memberships_revocation_consistent CHECK (
        (membership_status = 'REVOKED' AND revoked_at IS NOT NULL)
        OR (membership_status <> 'REVOKED' AND revoked_at IS NULL)
    )
);

CREATE TABLE workforce.registry_events (
    event_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    record_type text NOT NULL,
    record_key text NOT NULL,
    event_type text NOT NULL,
    actor_id text NOT NULL,
    request_id text,
    old_record jsonb,
    new_record jsonb,
    occurred_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT registry_events_type CHECK (record_type IN ('PROJECT', 'EMPLOYEE', 'PROJECT_MEMBERSHIP')),
    CONSTRAINT registry_events_event CHECK (event_type IN ('INSERT', 'UPDATE')),
    CONSTRAINT registry_events_actor_present CHECK (char_length(actor_id) BETWEEN 1 AND 128)
);

CREATE INDEX registry_events_record_idx
    ON workforce.registry_events (record_type, record_key, event_id);

CREATE INDEX registry_events_request_idx
    ON workforce.registry_events (request_id)
    WHERE request_id IS NOT NULL;

CREATE INDEX memberships_project_status_idx
    ON workforce.employee_project_memberships (project_id, membership_status, employee_id);

CREATE FUNCTION workforce.touch_versioned_row()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.version := OLD.version + 1;
    NEW.updated_at := clock_timestamp();
    RETURN NEW;
END;
$$;

CREATE FUNCTION workforce.prevent_hard_delete()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION USING
        ERRCODE = '55000',
        MESSAGE = format('Hard delete blocked for workforce.%I; use an explicit status change and revocation metadata.', TG_TABLE_NAME);
END;
$$;

CREATE FUNCTION workforce.record_registry_change()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_record_type text;
    v_record_key text;
    v_actor_id text;
    v_request_id text;
    v_old_record jsonb;
    v_new_record jsonb;
BEGIN
    v_actor_id := COALESCE(NULLIF(current_setting('app.actor_id', true), ''), 'SYSTEM-UNATTRIBUTED');
    v_request_id := NULLIF(current_setting('app.request_id', true), '');

    IF TG_TABLE_NAME = 'projects' THEN
        v_record_type := 'PROJECT';
        v_record_key := COALESCE(NEW.project_id, OLD.project_id);
    ELSIF TG_TABLE_NAME = 'employees' THEN
        v_record_type := 'EMPLOYEE';
        v_record_key := COALESCE(NEW.employee_id, OLD.employee_id);
    ELSIF TG_TABLE_NAME = 'employee_project_memberships' THEN
        v_record_type := 'PROJECT_MEMBERSHIP';
        v_record_key := COALESCE(NEW.employee_id, OLD.employee_id) || '@' || COALESCE(NEW.project_id, OLD.project_id);
    ELSE
        RAISE EXCEPTION 'Unsupported registry table: %', TG_TABLE_NAME;
    END IF;

    IF TG_OP = 'INSERT' THEN
        v_old_record := NULL;
        v_new_record := to_jsonb(NEW);
    ELSE
        v_old_record := to_jsonb(OLD);
        v_new_record := to_jsonb(NEW);
    END IF;

    INSERT INTO workforce.registry_events (
        record_type,
        record_key,
        event_type,
        actor_id,
        request_id,
        old_record,
        new_record
    ) VALUES (
        v_record_type,
        v_record_key,
        TG_OP,
        v_actor_id,
        v_request_id,
        v_old_record,
        v_new_record
    );

    RETURN NEW;
END;
$$;

CREATE FUNCTION workforce.prevent_registry_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION USING
        ERRCODE = '55000',
        MESSAGE = 'Registry events are append-only.';
END;
$$;

CREATE TRIGGER projects_touch_version
BEFORE UPDATE ON workforce.projects
FOR EACH ROW EXECUTE FUNCTION workforce.touch_versioned_row();

CREATE TRIGGER employees_touch_version
BEFORE UPDATE ON workforce.employees
FOR EACH ROW EXECUTE FUNCTION workforce.touch_versioned_row();

CREATE TRIGGER memberships_touch_version
BEFORE UPDATE ON workforce.employee_project_memberships
FOR EACH ROW EXECUTE FUNCTION workforce.touch_versioned_row();

CREATE TRIGGER projects_no_hard_delete
BEFORE DELETE ON workforce.projects
FOR EACH ROW EXECUTE FUNCTION workforce.prevent_hard_delete();

CREATE TRIGGER employees_no_hard_delete
BEFORE DELETE ON workforce.employees
FOR EACH ROW EXECUTE FUNCTION workforce.prevent_hard_delete();

CREATE TRIGGER memberships_no_hard_delete
BEFORE DELETE ON workforce.employee_project_memberships
FOR EACH ROW EXECUTE FUNCTION workforce.prevent_hard_delete();

CREATE TRIGGER projects_audit
AFTER INSERT OR UPDATE ON workforce.projects
FOR EACH ROW EXECUTE FUNCTION workforce.record_registry_change();

CREATE TRIGGER employees_audit
AFTER INSERT OR UPDATE ON workforce.employees
FOR EACH ROW EXECUTE FUNCTION workforce.record_registry_change();

CREATE TRIGGER memberships_audit
AFTER INSERT OR UPDATE ON workforce.employee_project_memberships
FOR EACH ROW EXECUTE FUNCTION workforce.record_registry_change();

CREATE TRIGGER registry_events_append_only
BEFORE UPDATE OR DELETE ON workforce.registry_events
FOR EACH ROW EXECUTE FUNCTION workforce.prevent_registry_event_mutation();

CREATE VIEW workforce.active_employees AS
SELECT
    employee_id,
    display_name,
    role_code,
    role_title,
    organizational_area,
    employment_status,
    source_ref,
    version,
    created_at,
    updated_at
FROM workforce.employees
WHERE employment_status IN ('PROBATION', 'ACTIVE');

CREATE VIEW workforce.active_project_members AS
SELECT
    m.project_id,
    p.display_name AS project_name,
    e.employee_id,
    e.display_name,
    e.role_code,
    e.role_title,
    e.organizational_area,
    e.employment_status,
    m.membership_status,
    m.version AS membership_version
FROM workforce.employee_project_memberships AS m
JOIN workforce.projects AS p ON p.project_id = m.project_id
JOIN workforce.employees AS e ON e.employee_id = m.employee_id
WHERE p.project_status = 'ACTIVE'
  AND m.membership_status = 'ACTIVE'
  AND e.employment_status IN ('PROBATION', 'ACTIVE');

SELECT set_config('app.actor_id', 'SYSTEM-BOOTSTRAP', true);
SELECT set_config('app.request_id', 'MIG-001-EMPLOYEE-REGISTRY', true);

INSERT INTO workforce.projects (
    project_id,
    display_name,
    project_status,
    source_ref
) VALUES (
    'START-UP',
    'Start UP',
    'ACTIVE',
    'DEC-003'
);

INSERT INTO workforce.employees (
    employee_id,
    display_name,
    role_code,
    role_title,
    organizational_area,
    employment_status,
    source_ref
) VALUES
    ('AI-ENG-001', 'Gerd', 'AI_ENGINEERING', 'AI Engineer / KI-Systemarchitekt', 'AI Engineering', 'PROBATION', 'DEC-002'),
    ('RAS-001', 'Thorsten', 'RESEARCH_STRATEGY', 'AI Research & Strategy Analyst', 'Research & Strategy', 'PROBATION', 'DEC-002'),
    ('PEO-001', 'Anastasia', 'PEOPLE_ORGANIZATION', 'AI People & Organization Specialist', 'People & Organization', 'PROBATION', 'DEC-002'),
    ('SAO-001', 'Karl', 'STRATEGY_OPERATIONS', 'AI Strategy & Operations Specialist', 'Strategy & Operations', 'PROBATION', 'DEC-002'),
    ('EAC-001', 'Nora', 'EXECUTIVE_ASSISTANCE', 'AI Executive Assistant & Communications Coordinator', 'CEO Office / Executive Administration', 'PROBATION', 'DEC-013');

INSERT INTO workforce.employee_project_memberships (
    employee_id,
    project_id,
    membership_status,
    source_ref
) VALUES
    ('AI-ENG-001', 'START-UP', 'ACTIVE', 'DEC-003'),
    ('RAS-001', 'START-UP', 'ACTIVE', 'DEC-003'),
    ('PEO-001', 'START-UP', 'ACTIVE', 'DEC-003'),
    ('SAO-001', 'START-UP', 'ACTIVE', 'DEC-003'),
    ('EAC-001', 'START-UP', 'ACTIVE', 'DEC-014');

INSERT INTO workforce.schema_migrations (migration_id, description)
VALUES ('001_employee_registry', 'Projects, employee identities, project memberships and append-only registry audit');

COMMIT;
