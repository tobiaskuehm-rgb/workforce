\set ON_ERROR_STOP on

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM workforce.schema_migrations
        WHERE migration_id = '001_employee_registry'
    ) THEN
        RAISE EXCEPTION 'Migration 001_employee_registry is required.';
    END IF;
END;
$$;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

SELECT set_config('app.actor_id', 'SYSTEM-MIGRATION', true);
SELECT set_config('app.request_id', 'MIG-004-KNOWLEDGE-CAPABILITY', true);

CREATE TABLE workforce.knowledge_systems (
    project_id text PRIMARY KEY REFERENCES workforce.projects(project_id),
    system_status text NOT NULL DEFAULT 'DISABLED',
    source_ref text NOT NULL,
    version bigint NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    revoked_at timestamptz,
    revocation_reason text,
    CONSTRAINT knowledge_systems_status CHECK (
        system_status IN ('DISABLED', 'TESTING', 'ACTIVE', 'REVOKED')
    ),
    CONSTRAINT knowledge_systems_version_positive CHECK (version >= 1),
    CONSTRAINT knowledge_systems_revocation_consistent CHECK (
        (system_status = 'REVOKED' AND revoked_at IS NOT NULL
            AND nullif(btrim(revocation_reason), '') IS NOT NULL)
        OR (system_status <> 'REVOKED' AND revoked_at IS NULL
            AND revocation_reason IS NULL)
    )
);

CREATE TABLE workforce.knowledge_member_permissions (
    project_id text NOT NULL,
    employee_id text NOT NULL,
    permission_status text NOT NULL DEFAULT 'ACTIVE',
    can_create_candidate boolean NOT NULL DEFAULT false,
    can_review_owned boolean NOT NULL DEFAULT false,
    can_assess boolean NOT NULL DEFAULT false,
    can_manage_role_packs boolean NOT NULL DEFAULT false,
    source_ref text NOT NULL,
    version bigint NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    revoked_at timestamptz,
    revocation_reason text,
    PRIMARY KEY (project_id, employee_id),
    FOREIGN KEY (employee_id, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    CONSTRAINT knowledge_permissions_status CHECK (
        permission_status IN ('ACTIVE', 'SUSPENDED', 'REVOKED')
    ),
    CONSTRAINT knowledge_permissions_version_positive CHECK (version >= 1),
    CONSTRAINT knowledge_permissions_revocation_consistent CHECK (
        (permission_status = 'REVOKED' AND revoked_at IS NOT NULL
            AND nullif(btrim(revocation_reason), '') IS NOT NULL)
        OR (permission_status <> 'REVOKED' AND revoked_at IS NULL
            AND revocation_reason IS NULL)
    )
);

CREATE TABLE workforce.knowledge_credentials (
    credential_id text PRIMARY KEY,
    project_id text NOT NULL,
    employee_id text NOT NULL,
    token_hash text NOT NULL UNIQUE,
    credential_scope text NOT NULL,
    credential_status text NOT NULL DEFAULT 'ACTIVE',
    source_ref text NOT NULL,
    version bigint NOT NULL DEFAULT 1,
    issued_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    expires_at timestamptz,
    revoked_at timestamptz,
    revocation_reason text,
    FOREIGN KEY (employee_id, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    CONSTRAINT knowledge_credentials_id_format CHECK (
        credential_id ~ '^KCRED-[A-Z0-9-]{8,96}$'
    ),
    CONSTRAINT knowledge_credentials_hash_format CHECK (token_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT knowledge_credentials_scope CHECK (
        credential_scope IN ('ACCEPTANCE', 'PRODUCTION')
    ),
    CONSTRAINT knowledge_credentials_status CHECK (
        credential_status IN ('ACTIVE', 'SUSPENDED', 'REVOKED')
    ),
    CONSTRAINT knowledge_credentials_acceptance_expiry CHECK (
        credential_scope <> 'ACCEPTANCE' OR expires_at IS NOT NULL
    ),
    CONSTRAINT knowledge_credentials_expiry_after_issue CHECK (
        expires_at IS NULL OR expires_at > issued_at
    ),
    CONSTRAINT knowledge_credentials_revocation_consistent CHECK (
        (credential_status = 'REVOKED' AND revoked_at IS NOT NULL
            AND nullif(btrim(revocation_reason), '') IS NOT NULL)
        OR (credential_status <> 'REVOKED' AND revoked_at IS NULL
            AND revocation_reason IS NULL)
    )
);

CREATE TABLE workforce.knowledge_objects (
    knowledge_id text NOT NULL,
    version integer NOT NULL,
    project_id text NOT NULL REFERENCES workforce.projects(project_id),
    title text NOT NULL,
    knowledge_class text NOT NULL,
    domain text NOT NULL,
    owner_id text NOT NULL,
    classification text NOT NULL,
    knowledge_status text NOT NULL DEFAULT 'DRAFT',
    provenance_source text NOT NULL,
    approved_by text,
    approved_at timestamptz,
    valid_from timestamptz,
    review_due timestamptz,
    stale_after timestamptz,
    supersedes_version integer,
    tags text[] NOT NULL DEFAULT ARRAY[]::text[],
    content text NOT NULL,
    content_hash text NOT NULL,
    created_by text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    revoked_at timestamptz,
    revocation_reason text,
    PRIMARY KEY (knowledge_id, version),
    FOREIGN KEY (owner_id, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    FOREIGN KEY (created_by, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    FOREIGN KEY (approved_by, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    FOREIGN KEY (knowledge_id, supersedes_version)
        REFERENCES workforce.knowledge_objects(knowledge_id, version),
    CONSTRAINT knowledge_objects_id_format CHECK (
        knowledge_id ~ '^KN-[A-Z0-9-]{3,60}$'
    ),
    CONSTRAINT knowledge_objects_version_positive CHECK (version >= 1),
    CONSTRAINT knowledge_objects_title_length CHECK (char_length(title) BETWEEN 1 AND 240),
    CONSTRAINT knowledge_objects_class CHECK (
        knowledge_class IN ('K0', 'K1', 'K2', 'K3', 'K4', 'K5')
    ),
    CONSTRAINT knowledge_objects_domain_length CHECK (char_length(domain) BETWEEN 1 AND 120),
    CONSTRAINT knowledge_objects_classification CHECK (
        classification IN ('PROJECT_INTERNAL', 'NEED_TO_KNOW')
    ),
    CONSTRAINT knowledge_objects_status CHECK (
        knowledge_status IN ('DRAFT', 'REVIEW', 'APPROVED', 'SUPERSEDED', 'REVOKED')
    ),
    CONSTRAINT knowledge_objects_provenance_length CHECK (
        char_length(provenance_source) BETWEEN 1 AND 1000
    ),
    CONSTRAINT knowledge_objects_content_length CHECK (char_length(content) BETWEEN 1 AND 100000),
    CONSTRAINT knowledge_objects_hash_format CHECK (content_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT knowledge_objects_supersedes_older CHECK (
        supersedes_version IS NULL OR supersedes_version < version
    ),
    CONSTRAINT knowledge_objects_dates_ordered CHECK (
        (review_due IS NULL OR valid_from IS NULL OR review_due > valid_from)
        AND (stale_after IS NULL OR valid_from IS NULL OR stale_after > valid_from)
    ),
    CONSTRAINT knowledge_objects_approval_consistent CHECK (
        (knowledge_status IN ('APPROVED', 'SUPERSEDED')
            AND approved_by IS NOT NULL AND approved_at IS NOT NULL
            AND valid_from IS NOT NULL)
        OR knowledge_status IN ('DRAFT', 'REVIEW', 'REVOKED')
    ),
    CONSTRAINT knowledge_objects_revocation_consistent CHECK (
        (knowledge_status = 'REVOKED' AND revoked_at IS NOT NULL
            AND nullif(btrim(revocation_reason), '') IS NOT NULL)
        OR (knowledge_status <> 'REVOKED' AND revoked_at IS NULL
            AND revocation_reason IS NULL)
    )
);

CREATE UNIQUE INDEX knowledge_one_current_approved_idx
    ON workforce.knowledge_objects (project_id, knowledge_id)
    WHERE knowledge_status = 'APPROVED';

CREATE INDEX knowledge_retrieval_filter_idx
    ON workforce.knowledge_objects (
        project_id,
        knowledge_status,
        domain,
        classification,
        knowledge_id,
        version DESC
    );

CREATE VIEW workforce.knowledge_object_states AS
SELECT
    object.*,
    CASE
        WHEN object.knowledge_status = 'APPROVED'
         AND object.stale_after IS NOT NULL
         AND object.stale_after <= clock_timestamp() THEN 'STALE'
        ELSE object.knowledge_status
    END AS actuality_status
FROM workforce.knowledge_objects AS object;

CREATE TABLE workforce.knowledge_audiences (
    project_id text NOT NULL,
    knowledge_id text NOT NULL,
    version integer NOT NULL,
    audience_kind text NOT NULL,
    audience_value text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (knowledge_id, version, audience_kind, audience_value),
    FOREIGN KEY (knowledge_id, version)
        REFERENCES workforce.knowledge_objects(knowledge_id, version),
    CONSTRAINT knowledge_audiences_kind CHECK (
        audience_kind IN ('PROJECT', 'ROLE', 'EMPLOYEE')
    ),
    CONSTRAINT knowledge_audiences_value_length CHECK (
        char_length(audience_value) BETWEEN 1 AND 128
    )
);

CREATE INDEX knowledge_audience_lookup_idx
    ON workforce.knowledge_audiences (
        project_id,
        audience_kind,
        audience_value,
        knowledge_id,
        version
    );

CREATE TABLE workforce.knowledge_role_pack_entries (
    project_id text NOT NULL,
    employee_id text NOT NULL,
    knowledge_id text NOT NULL,
    entry_status text NOT NULL DEFAULT 'ACTIVE',
    source_ref text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    revoked_at timestamptz,
    revocation_reason text,
    PRIMARY KEY (project_id, employee_id, knowledge_id),
    FOREIGN KEY (employee_id, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    CONSTRAINT role_pack_entry_status CHECK (
        entry_status IN ('ACTIVE', 'SUSPENDED', 'REVOKED')
    ),
    CONSTRAINT role_pack_entry_revocation_consistent CHECK (
        (entry_status = 'REVOKED' AND revoked_at IS NOT NULL
            AND nullif(btrim(revocation_reason), '') IS NOT NULL)
        OR (entry_status <> 'REVOKED' AND revoked_at IS NULL
            AND revocation_reason IS NULL)
    )
);

CREATE INDEX role_pack_employee_idx
    ON workforce.knowledge_role_pack_entries (project_id, employee_id, entry_status, knowledge_id);

CREATE TABLE workforce.knowledge_retrieval_runs (
    run_id text PRIMARY KEY,
    project_id text NOT NULL,
    employee_id text NOT NULL,
    task_ref text,
    query_hash text NOT NULL,
    domain_filter text,
    retrieval_mode text NOT NULL,
    eligible_count integer NOT NULL DEFAULT 0,
    returned_count integer NOT NULL DEFAULT 0,
    occurred_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    FOREIGN KEY (employee_id, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    CONSTRAINT retrieval_runs_id_format CHECK (run_id ~ '^KRUN-[A-Z0-9-]{8,80}$'),
    CONSTRAINT retrieval_runs_query_hash CHECK (query_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT retrieval_runs_mode CHECK (retrieval_mode IN ('GENERAL', 'ROLE_PACK')),
    CONSTRAINT retrieval_runs_counts CHECK (eligible_count >= 0 AND returned_count >= 0)
);

CREATE TABLE workforce.knowledge_context_items (
    run_id text NOT NULL REFERENCES workforce.knowledge_retrieval_runs(run_id),
    item_position integer NOT NULL,
    knowledge_id text NOT NULL,
    version integer NOT NULL,
    chunk_ref text NOT NULL DEFAULT 'FULL',
    content_hash text NOT NULL,
    retrieval_score double precision NOT NULL,
    retrieved_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (run_id, item_position),
    FOREIGN KEY (knowledge_id, version)
        REFERENCES workforce.knowledge_objects(knowledge_id, version),
    CONSTRAINT context_items_position CHECK (item_position >= 1),
    CONSTRAINT context_items_chunk_length CHECK (char_length(chunk_ref) BETWEEN 1 AND 200),
    CONSTRAINT context_items_hash_format CHECK (content_hash ~ '^[0-9a-f]{64}$')
);

CREATE TABLE workforce.capability_definitions (
    capability_id text PRIMARY KEY,
    project_id text NOT NULL REFERENCES workforce.projects(project_id),
    title text NOT NULL,
    description text NOT NULL,
    owner_id text NOT NULL,
    capability_status text NOT NULL DEFAULT 'ACTIVE',
    source_ref text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    FOREIGN KEY (owner_id, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    CONSTRAINT capability_definitions_id_format CHECK (
        capability_id ~ '^CAP-[A-Z0-9-]{3,60}$'
    ),
    CONSTRAINT capability_definitions_title_length CHECK (char_length(title) BETWEEN 1 AND 240),
    CONSTRAINT capability_definitions_status CHECK (
        capability_status IN ('ACTIVE', 'SUSPENDED', 'REVOKED')
    )
);

CREATE TABLE workforce.training_assessments (
    assessment_id text PRIMARY KEY,
    project_id text NOT NULL,
    employee_id text NOT NULL,
    capability_id text NOT NULL REFERENCES workforce.capability_definitions(capability_id),
    assessor_id text NOT NULL,
    assessed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    context_run_id text REFERENCES workforce.knowledge_retrieval_runs(run_id),
    score integer NOT NULL,
    error_class text NOT NULL,
    feedback text NOT NULL,
    training_action text NOT NULL,
    retest_of text REFERENCES workforce.training_assessments(assessment_id),
    retest_result text,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    FOREIGN KEY (employee_id, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    FOREIGN KEY (assessor_id, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    CONSTRAINT training_assessments_id_format CHECK (
        assessment_id ~ '^ASMT-[A-Z0-9-]{3,60}$'
    ),
    CONSTRAINT training_assessments_score CHECK (score BETWEEN 0 AND 5),
    CONSTRAINT training_assessments_error_class CHECK (
        error_class IN ('E1', 'E2', 'E3', 'E4', 'E5', 'E6')
    ),
    CONSTRAINT training_assessments_feedback_length CHECK (
        char_length(feedback) BETWEEN 1 AND 8000
    ),
    CONSTRAINT training_assessments_action_length CHECK (
        char_length(training_action) BETWEEN 1 AND 4000
    )
);

CREATE TABLE workforce.capability_records (
    project_id text NOT NULL,
    employee_id text NOT NULL,
    capability_id text NOT NULL REFERENCES workforce.capability_definitions(capability_id),
    current_level integer NOT NULL,
    target_level integer NOT NULL,
    latest_assessment_id text NOT NULL REFERENCES workforce.training_assessments(assessment_id),
    evidence_assessment_refs text[] NOT NULL,
    last_assessed_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (project_id, employee_id, capability_id),
    FOREIGN KEY (employee_id, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    CONSTRAINT capability_records_current_level CHECK (current_level BETWEEN 0 AND 5),
    CONSTRAINT capability_records_target_level CHECK (target_level BETWEEN 0 AND 5)
);

CREATE TABLE workforce.knowledge_events (
    event_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id text NOT NULL,
    record_type text NOT NULL,
    record_key text NOT NULL,
    event_type text NOT NULL,
    actor_id text NOT NULL,
    request_id text NOT NULL,
    old_record jsonb,
    new_record jsonb,
    occurred_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT knowledge_events_record_type CHECK (
        record_type IN (
            'SYSTEM', 'PERMISSION', 'CREDENTIAL', 'KNOWLEDGE',
            'ROLE_PACK', 'ASSESSMENT', 'CAPABILITY_RECORD'
        )
    ),
    CONSTRAINT knowledge_events_event_type CHECK (event_type IN ('INSERT', 'UPDATE')),
    CONSTRAINT knowledge_events_actor_present CHECK (char_length(actor_id) BETWEEN 1 AND 128),
    CONSTRAINT knowledge_events_request_present CHECK (char_length(request_id) BETWEEN 1 AND 128)
);

CREATE INDEX knowledge_events_record_idx
    ON workforce.knowledge_events (project_id, record_type, record_key, event_id);

CREATE INDEX knowledge_events_request_idx
    ON workforce.knowledge_events (request_id, event_id);

CREATE FUNCTION workforce.knowledge_touch_versioned_row()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.version := OLD.version + 1;
    NEW.updated_at := clock_timestamp();
    RETURN NEW;
END;
$$;

CREATE FUNCTION workforce.knowledge_prevent_hard_delete()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION USING
        ERRCODE = '55000',
        MESSAGE = 'KNOWLEDGE_HARD_DELETE_DENIED';
END;
$$;

CREATE FUNCTION workforce.knowledge_record_change()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_project_id text;
    v_record_type text;
    v_record_key text;
    v_actor_id text;
    v_request_id text;
    v_old_record jsonb;
    v_new_record jsonb;
BEGIN
    v_actor_id := NULLIF(current_setting('app.actor_id', true), '');
    v_request_id := NULLIF(current_setting('app.request_id', true), '');

    IF v_actor_id IS NULL OR v_request_id IS NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            MESSAGE = 'KNOWLEDGE_AUDIT_CONTEXT_REQUIRED';
    END IF;

    CASE TG_TABLE_NAME
        WHEN 'knowledge_systems' THEN
            v_project_id := COALESCE(NEW.project_id, OLD.project_id);
            v_record_type := 'SYSTEM';
            v_record_key := v_project_id;
        WHEN 'knowledge_member_permissions' THEN
            v_project_id := COALESCE(NEW.project_id, OLD.project_id);
            v_record_type := 'PERMISSION';
            v_record_key := COALESCE(NEW.employee_id, OLD.employee_id);
        WHEN 'knowledge_credentials' THEN
            v_project_id := COALESCE(NEW.project_id, OLD.project_id);
            v_record_type := 'CREDENTIAL';
            v_record_key := COALESCE(NEW.credential_id, OLD.credential_id);
        WHEN 'knowledge_objects' THEN
            v_project_id := COALESCE(NEW.project_id, OLD.project_id);
            v_record_type := 'KNOWLEDGE';
            v_record_key := COALESCE(NEW.knowledge_id, OLD.knowledge_id)
                || '@' || COALESCE(NEW.version, OLD.version)::text;
        WHEN 'knowledge_role_pack_entries' THEN
            v_project_id := COALESCE(NEW.project_id, OLD.project_id);
            v_record_type := 'ROLE_PACK';
            v_record_key := COALESCE(NEW.employee_id, OLD.employee_id)
                || '@' || COALESCE(NEW.knowledge_id, OLD.knowledge_id);
        WHEN 'training_assessments' THEN
            v_project_id := COALESCE(NEW.project_id, OLD.project_id);
            v_record_type := 'ASSESSMENT';
            v_record_key := COALESCE(NEW.assessment_id, OLD.assessment_id);
        WHEN 'capability_records' THEN
            v_project_id := COALESCE(NEW.project_id, OLD.project_id);
            v_record_type := 'CAPABILITY_RECORD';
            v_record_key := COALESCE(NEW.employee_id, OLD.employee_id)
                || '@' || COALESCE(NEW.capability_id, OLD.capability_id);
        ELSE
            RAISE EXCEPTION 'Unsupported knowledge audit table: %', TG_TABLE_NAME;
    END CASE;

    IF TG_TABLE_NAME = 'knowledge_credentials' THEN
        v_old_record := CASE WHEN TG_OP = 'UPDATE' THEN to_jsonb(OLD) - 'token_hash' END;
        v_new_record := to_jsonb(NEW) - 'token_hash';
    ELSE
        v_old_record := CASE WHEN TG_OP = 'UPDATE' THEN to_jsonb(OLD) END;
        v_new_record := to_jsonb(NEW);
    END IF;

    INSERT INTO workforce.knowledge_events (
        project_id, record_type, record_key, event_type,
        actor_id, request_id, old_record, new_record
    ) VALUES (
        v_project_id, v_record_type, v_record_key, TG_OP,
        v_actor_id, v_request_id, v_old_record, v_new_record
    );

    RETURN NEW;
END;
$$;

CREATE FUNCTION workforce.knowledge_prevent_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION USING
        ERRCODE = '55000',
        MESSAGE = 'KNOWLEDGE_AUDIT_IMMUTABLE';
END;
$$;

CREATE FUNCTION workforce.knowledge_guard_object_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.knowledge_id IS DISTINCT FROM OLD.knowledge_id
       OR NEW.version IS DISTINCT FROM OLD.version
       OR NEW.project_id IS DISTINCT FROM OLD.project_id
       OR NEW.title IS DISTINCT FROM OLD.title
       OR NEW.knowledge_class IS DISTINCT FROM OLD.knowledge_class
       OR NEW.domain IS DISTINCT FROM OLD.domain
       OR NEW.owner_id IS DISTINCT FROM OLD.owner_id
       OR NEW.classification IS DISTINCT FROM OLD.classification
       OR NEW.provenance_source IS DISTINCT FROM OLD.provenance_source
       OR NEW.review_due IS DISTINCT FROM OLD.review_due
       OR NEW.stale_after IS DISTINCT FROM OLD.stale_after
       OR NEW.tags IS DISTINCT FROM OLD.tags
       OR NEW.content IS DISTINCT FROM OLD.content
       OR NEW.content_hash IS DISTINCT FROM OLD.content_hash
       OR NEW.created_by IS DISTINCT FROM OLD.created_by
       OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'KNOWLEDGE_VERSION_IMMUTABLE';
    END IF;

    IF OLD.knowledge_status = NEW.knowledge_status
       OR NOT (
           (OLD.knowledge_status = 'DRAFT' AND NEW.knowledge_status IN ('REVIEW', 'REVOKED'))
           OR (OLD.knowledge_status = 'REVIEW' AND NEW.knowledge_status IN ('APPROVED', 'REVOKED'))
           OR (OLD.knowledge_status = 'APPROVED' AND NEW.knowledge_status IN ('SUPERSEDED', 'REVOKED'))
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'KNOWLEDGE_STATUS_TRANSITION_DENIED';
    END IF;

    IF NEW.knowledge_status = 'REVIEW' AND (
        NEW.approved_by IS DISTINCT FROM OLD.approved_by
        OR NEW.approved_at IS DISTINCT FROM OLD.approved_at
        OR NEW.valid_from IS DISTINCT FROM OLD.valid_from
        OR NEW.supersedes_version IS DISTINCT FROM OLD.supersedes_version
        OR NEW.revoked_at IS DISTINCT FROM OLD.revoked_at
        OR NEW.revocation_reason IS DISTINCT FROM OLD.revocation_reason
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'KNOWLEDGE_REVIEW_MUTATION_DENIED';
    END IF;

    IF NEW.knowledge_status = 'APPROVED' AND (
        OLD.approved_by IS NOT NULL
        OR OLD.approved_at IS NOT NULL
        OR NEW.approved_by IS NULL
        OR NEW.approved_at IS NULL
        OR NEW.revoked_at IS NOT NULL
        OR NEW.revocation_reason IS NOT NULL
        OR (OLD.valid_from IS NOT NULL AND NEW.valid_from IS DISTINCT FROM OLD.valid_from)
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'KNOWLEDGE_APPROVAL_MUTATION_DENIED';
    END IF;

    IF NEW.knowledge_status = 'SUPERSEDED' AND (
        NEW.approved_by IS DISTINCT FROM OLD.approved_by
        OR NEW.approved_at IS DISTINCT FROM OLD.approved_at
        OR NEW.valid_from IS DISTINCT FROM OLD.valid_from
        OR NEW.supersedes_version IS DISTINCT FROM OLD.supersedes_version
        OR NEW.revoked_at IS DISTINCT FROM OLD.revoked_at
        OR NEW.revocation_reason IS DISTINCT FROM OLD.revocation_reason
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'KNOWLEDGE_SUPERSEDE_MUTATION_DENIED';
    END IF;

    IF NEW.knowledge_status = 'REVOKED' AND (
        NEW.revoked_at IS NULL OR nullif(btrim(NEW.revocation_reason), '') IS NULL
        OR NEW.approved_by IS DISTINCT FROM OLD.approved_by
        OR NEW.approved_at IS DISTINCT FROM OLD.approved_at
        OR NEW.valid_from IS DISTINCT FROM OLD.valid_from
        OR NEW.supersedes_version IS DISTINCT FROM OLD.supersedes_version
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'KNOWLEDGE_REVOCATION_MUTATION_DENIED';
    END IF;

    RETURN NEW;
END;
$$;

CREATE FUNCTION workforce.knowledge_guard_credential_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.credential_id IS DISTINCT FROM OLD.credential_id
       OR NEW.project_id IS DISTINCT FROM OLD.project_id
       OR NEW.employee_id IS DISTINCT FROM OLD.employee_id
       OR NEW.token_hash IS DISTINCT FROM OLD.token_hash
       OR NEW.credential_scope IS DISTINCT FROM OLD.credential_scope
       OR NEW.issued_at IS DISTINCT FROM OLD.issued_at THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'KNOWLEDGE_CREDENTIAL_IDENTITY_IMMUTABLE';
    END IF;

    IF OLD.credential_status = 'REVOKED' AND NEW.credential_status <> 'REVOKED' THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'KNOWLEDGE_CREDENTIAL_REVOCATION_FINAL';
    END IF;

    NEW.version := OLD.version + 1;
    NEW.updated_at := clock_timestamp();
    RETURN NEW;
END;
$$;

CREATE TRIGGER knowledge_systems_touch
BEFORE UPDATE ON workforce.knowledge_systems
FOR EACH ROW EXECUTE FUNCTION workforce.knowledge_touch_versioned_row();

CREATE TRIGGER knowledge_permissions_touch
BEFORE UPDATE ON workforce.knowledge_member_permissions
FOR EACH ROW EXECUTE FUNCTION workforce.knowledge_touch_versioned_row();

CREATE TRIGGER knowledge_credentials_guard
BEFORE UPDATE ON workforce.knowledge_credentials
FOR EACH ROW EXECUTE FUNCTION workforce.knowledge_guard_credential_update();

CREATE TRIGGER knowledge_objects_guard
BEFORE UPDATE ON workforce.knowledge_objects
FOR EACH ROW EXECUTE FUNCTION workforce.knowledge_guard_object_update();

CREATE TRIGGER knowledge_systems_audit
AFTER INSERT OR UPDATE ON workforce.knowledge_systems
FOR EACH ROW EXECUTE FUNCTION workforce.knowledge_record_change();

CREATE TRIGGER knowledge_permissions_audit
AFTER INSERT OR UPDATE ON workforce.knowledge_member_permissions
FOR EACH ROW EXECUTE FUNCTION workforce.knowledge_record_change();

CREATE TRIGGER knowledge_credentials_audit
AFTER INSERT OR UPDATE ON workforce.knowledge_credentials
FOR EACH ROW EXECUTE FUNCTION workforce.knowledge_record_change();

CREATE TRIGGER knowledge_objects_audit
AFTER INSERT OR UPDATE ON workforce.knowledge_objects
FOR EACH ROW EXECUTE FUNCTION workforce.knowledge_record_change();

CREATE TRIGGER role_pack_entries_audit
AFTER INSERT OR UPDATE ON workforce.knowledge_role_pack_entries
FOR EACH ROW EXECUTE FUNCTION workforce.knowledge_record_change();

CREATE TRIGGER training_assessments_audit
AFTER INSERT ON workforce.training_assessments
FOR EACH ROW EXECUTE FUNCTION workforce.knowledge_record_change();

CREATE TRIGGER capability_records_audit
AFTER INSERT OR UPDATE ON workforce.capability_records
FOR EACH ROW EXECUTE FUNCTION workforce.knowledge_record_change();

CREATE TRIGGER knowledge_objects_no_delete
BEFORE DELETE ON workforce.knowledge_objects
FOR EACH ROW EXECUTE FUNCTION workforce.knowledge_prevent_hard_delete();

CREATE TRIGGER knowledge_audiences_no_delete
BEFORE DELETE ON workforce.knowledge_audiences
FOR EACH ROW EXECUTE FUNCTION workforce.knowledge_prevent_hard_delete();

CREATE TRIGGER role_pack_entries_no_delete
BEFORE DELETE ON workforce.knowledge_role_pack_entries
FOR EACH ROW EXECUTE FUNCTION workforce.knowledge_prevent_hard_delete();

CREATE TRIGGER retrieval_runs_no_delete
BEFORE DELETE ON workforce.knowledge_retrieval_runs
FOR EACH ROW EXECUTE FUNCTION workforce.knowledge_prevent_hard_delete();

CREATE TRIGGER context_items_no_delete
BEFORE DELETE ON workforce.knowledge_context_items
FOR EACH ROW EXECUTE FUNCTION workforce.knowledge_prevent_hard_delete();

CREATE TRIGGER assessments_no_delete
BEFORE DELETE ON workforce.training_assessments
FOR EACH ROW EXECUTE FUNCTION workforce.knowledge_prevent_hard_delete();

CREATE TRIGGER capability_records_no_delete
BEFORE DELETE ON workforce.capability_records
FOR EACH ROW EXECUTE FUNCTION workforce.knowledge_prevent_hard_delete();

CREATE TRIGGER knowledge_events_append_only
BEFORE UPDATE OR DELETE ON workforce.knowledge_events
FOR EACH ROW EXECUTE FUNCTION workforce.knowledge_prevent_event_mutation();

CREATE FUNCTION workforce.knowledge_authenticate(
    p_project_id text,
    p_token_hash text
)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, workforce
AS $$
DECLARE
    v_employee_id text;
BEGIN
    SELECT c.employee_id
    INTO v_employee_id
    FROM workforce.knowledge_credentials AS c
    JOIN workforce.knowledge_systems AS s
      ON s.project_id = c.project_id
    JOIN workforce.knowledge_member_permissions AS permission
      ON permission.project_id = c.project_id
     AND permission.employee_id = c.employee_id
    JOIN workforce.employee_project_memberships AS membership
      ON membership.project_id = c.project_id
     AND membership.employee_id = c.employee_id
    JOIN workforce.employees AS employee
      ON employee.employee_id = c.employee_id
    JOIN workforce.projects AS project
      ON project.project_id = c.project_id
    WHERE c.project_id = p_project_id
      AND c.token_hash = p_token_hash
      AND c.credential_status = 'ACTIVE'
      AND (c.expires_at IS NULL OR c.expires_at > clock_timestamp())
      AND permission.permission_status = 'ACTIVE'
      AND membership.membership_status = 'ACTIVE'
      AND employee.employment_status IN ('PROBATION', 'ACTIVE')
      AND project.project_status = 'ACTIVE'
      AND (
          (s.system_status = 'TESTING' AND c.credential_scope = 'ACCEPTANCE')
          OR (s.system_status = 'ACTIVE' AND c.credential_scope = 'PRODUCTION')
      );

    IF v_employee_id IS NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '42501',
            MESSAGE = 'KNOWLEDGE_AUTH_FAILED';
    END IF;

    RETURN v_employee_id;
END;
$$;

CREATE FUNCTION workforce.knowledge_create_candidate(
    p_token_hash text,
    p_request_id text,
    p_project_id text,
    p_knowledge_id text,
    p_title text,
    p_knowledge_class text,
    p_domain text,
    p_owner_id text,
    p_classification text,
    p_provenance_source text,
    p_valid_from timestamptz,
    p_review_due timestamptz,
    p_stale_after timestamptz,
    p_tags text[],
    p_content text,
    p_audiences jsonb
)
RETURNS workforce.knowledge_objects
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, workforce
AS $$
DECLARE
    v_actor_id text;
    v_version integer;
    v_latest workforce.knowledge_objects%ROWTYPE;
    v_audience jsonb;
    v_object workforce.knowledge_objects%ROWTYPE;
BEGIN
    IF p_request_id IS NULL OR char_length(p_request_id) NOT BETWEEN 1 AND 128 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'KNOWLEDGE_REQUEST_ID_REQUIRED';
    END IF;

    v_actor_id := workforce.knowledge_authenticate(p_project_id, p_token_hash);

    IF NOT EXISTS (
        SELECT 1
        FROM workforce.knowledge_member_permissions
        WHERE project_id = p_project_id
          AND employee_id = v_actor_id
          AND permission_status = 'ACTIVE'
          AND can_create_candidate
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'KNOWLEDGE_CANDIDATE_DENIED';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM workforce.active_project_members
        WHERE project_id = p_project_id
          AND employee_id = p_owner_id
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'KNOWLEDGE_OWNER_DENIED';
    END IF;

    IF jsonb_typeof(p_audiences) <> 'array' OR jsonb_array_length(p_audiences) < 1 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'KNOWLEDGE_AUDIENCE_REQUIRED';
    END IF;

    SELECT * INTO v_latest
    FROM workforce.knowledge_objects
    WHERE knowledge_id = p_knowledge_id
      AND project_id = p_project_id
    ORDER BY version DESC
    LIMIT 1;

    IF FOUND AND (
        v_latest.owner_id <> p_owner_id
        OR v_latest.knowledge_class <> p_knowledge_class
        OR v_latest.domain <> p_domain
        OR v_latest.classification <> p_classification
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'KNOWLEDGE_LINEAGE_POLICY_IMMUTABLE';
    END IF;

    SELECT COALESCE(max(version), 0) + 1 INTO v_version
    FROM workforce.knowledge_objects
    WHERE knowledge_id = p_knowledge_id;

    PERFORM set_config('app.actor_id', v_actor_id, true);
    PERFORM set_config('app.request_id', p_request_id, true);

    INSERT INTO workforce.knowledge_objects (
        knowledge_id, version, project_id, title, knowledge_class, domain,
        owner_id, classification, knowledge_status, provenance_source,
        valid_from, review_due, stale_after, tags, content, content_hash, created_by
    ) VALUES (
        p_knowledge_id, v_version, p_project_id, p_title, p_knowledge_class, p_domain,
        p_owner_id, p_classification, 'DRAFT', p_provenance_source,
        p_valid_from, p_review_due, p_stale_after, COALESCE(p_tags, ARRAY[]::text[]),
        p_content, encode(public.digest(p_content, 'sha256'), 'hex'), v_actor_id
    )
    RETURNING * INTO v_object;

    FOR v_audience IN SELECT value FROM jsonb_array_elements(p_audiences)
    LOOP
        IF NOT (v_audience ? 'kind' AND v_audience ? 'value')
           OR v_audience->>'kind' NOT IN ('PROJECT', 'ROLE', 'EMPLOYEE')
           OR nullif(btrim(v_audience->>'value'), '') IS NULL THEN
            RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'KNOWLEDGE_AUDIENCE_INVALID';
        END IF;

        IF v_audience->>'kind' = 'PROJECT' AND (
            v_audience->>'value' <> p_project_id
            OR p_classification <> 'PROJECT_INTERNAL'
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'KNOWLEDGE_PROJECT_AUDIENCE_DENIED';
        END IF;

        IF v_audience->>'kind' = 'EMPLOYEE' AND NOT EXISTS (
            SELECT 1 FROM workforce.active_project_members
            WHERE project_id = p_project_id
              AND employee_id = v_audience->>'value'
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'KNOWLEDGE_EMPLOYEE_AUDIENCE_DENIED';
        END IF;

        IF v_audience->>'kind' = 'ROLE' AND NOT EXISTS (
            SELECT 1 FROM workforce.active_project_members
            WHERE project_id = p_project_id
              AND role_code = v_audience->>'value'
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'KNOWLEDGE_ROLE_AUDIENCE_DENIED';
        END IF;

        INSERT INTO workforce.knowledge_audiences (
            project_id, knowledge_id, version, audience_kind, audience_value
        ) VALUES (
            p_project_id, p_knowledge_id, v_version,
            v_audience->>'kind', v_audience->>'value'
        );
    END LOOP;

    RETURN v_object;
END;
$$;

CREATE FUNCTION workforce.knowledge_submit_review(
    p_token_hash text,
    p_request_id text,
    p_project_id text,
    p_knowledge_id text,
    p_version integer
)
RETURNS workforce.knowledge_objects
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, workforce
AS $$
DECLARE
    v_actor_id text;
    v_object workforce.knowledge_objects%ROWTYPE;
BEGIN
    v_actor_id := workforce.knowledge_authenticate(p_project_id, p_token_hash);

    SELECT * INTO v_object
    FROM workforce.knowledge_objects
    WHERE project_id = p_project_id
      AND knowledge_id = p_knowledge_id
      AND version = p_version
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'KNOWLEDGE_NOT_FOUND';
    END IF;
    IF v_object.knowledge_status <> 'DRAFT' THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'KNOWLEDGE_REVIEW_STATE_INVALID';
    END IF;
    IF v_actor_id NOT IN (v_object.created_by, v_object.owner_id) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'KNOWLEDGE_REVIEW_DENIED';
    END IF;

    PERFORM set_config('app.actor_id', v_actor_id, true);
    PERFORM set_config('app.request_id', p_request_id, true);

    UPDATE workforce.knowledge_objects
    SET knowledge_status = 'REVIEW', updated_at = clock_timestamp()
    WHERE knowledge_id = p_knowledge_id AND version = p_version
    RETURNING * INTO v_object;

    RETURN v_object;
END;
$$;

CREATE FUNCTION workforce.knowledge_approve(
    p_token_hash text,
    p_request_id text,
    p_project_id text,
    p_knowledge_id text,
    p_version integer
)
RETURNS workforce.knowledge_objects
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, workforce
AS $$
DECLARE
    v_actor_id text;
    v_previous_version integer;
    v_object workforce.knowledge_objects%ROWTYPE;
BEGIN
    v_actor_id := workforce.knowledge_authenticate(p_project_id, p_token_hash);

    SELECT * INTO v_object
    FROM workforce.knowledge_objects
    WHERE project_id = p_project_id
      AND knowledge_id = p_knowledge_id
      AND version = p_version
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'KNOWLEDGE_NOT_FOUND';
    END IF;
    IF v_object.knowledge_status <> 'REVIEW' THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'KNOWLEDGE_APPROVAL_STATE_INVALID';
    END IF;
    IF v_actor_id <> v_object.owner_id THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'KNOWLEDGE_APPROVAL_DENIED';
    END IF;
    IF v_actor_id = v_object.created_by THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'KNOWLEDGE_SELF_PUBLISH_DENIED';
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM workforce.knowledge_member_permissions
        WHERE project_id = p_project_id
          AND employee_id = v_actor_id
          AND permission_status = 'ACTIVE'
          AND can_review_owned
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'KNOWLEDGE_APPROVAL_DENIED';
    END IF;

    SELECT version INTO v_previous_version
    FROM workforce.knowledge_objects
    WHERE project_id = p_project_id
      AND knowledge_id = p_knowledge_id
      AND knowledge_status = 'APPROVED'
    FOR UPDATE;

    PERFORM set_config('app.actor_id', v_actor_id, true);
    PERFORM set_config('app.request_id', p_request_id, true);

    IF v_previous_version IS NOT NULL THEN
        UPDATE workforce.knowledge_objects
        SET knowledge_status = 'SUPERSEDED', updated_at = clock_timestamp()
        WHERE project_id = p_project_id
          AND knowledge_id = p_knowledge_id
          AND version = v_previous_version;
    END IF;

    UPDATE workforce.knowledge_objects
    SET knowledge_status = 'APPROVED',
        approved_by = v_actor_id,
        approved_at = clock_timestamp(),
        valid_from = COALESCE(valid_from, clock_timestamp()),
        supersedes_version = v_previous_version,
        updated_at = clock_timestamp()
    WHERE knowledge_id = p_knowledge_id AND version = p_version
    RETURNING * INTO v_object;

    RETURN v_object;
END;
$$;

CREATE FUNCTION workforce.knowledge_revoke(
    p_token_hash text,
    p_request_id text,
    p_project_id text,
    p_knowledge_id text,
    p_version integer,
    p_reason text
)
RETURNS workforce.knowledge_objects
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, workforce
AS $$
DECLARE
    v_actor_id text;
    v_object workforce.knowledge_objects%ROWTYPE;
BEGIN
    v_actor_id := workforce.knowledge_authenticate(p_project_id, p_token_hash);

    SELECT * INTO v_object
    FROM workforce.knowledge_objects
    WHERE project_id = p_project_id
      AND knowledge_id = p_knowledge_id
      AND version = p_version
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'KNOWLEDGE_NOT_FOUND';
    END IF;
    IF v_actor_id <> v_object.owner_id OR nullif(btrim(p_reason), '') IS NULL THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'KNOWLEDGE_REVOCATION_DENIED';
    END IF;
    IF v_object.knowledge_status IN ('SUPERSEDED', 'REVOKED') THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'KNOWLEDGE_TERMINAL_STATE_FINAL';
    END IF;

    PERFORM set_config('app.actor_id', v_actor_id, true);
    PERFORM set_config('app.request_id', p_request_id, true);

    UPDATE workforce.knowledge_objects
    SET knowledge_status = 'REVOKED',
        revoked_at = clock_timestamp(),
        revocation_reason = p_reason,
        updated_at = clock_timestamp()
    WHERE knowledge_id = p_knowledge_id AND version = p_version
    RETURNING * INTO v_object;

    RETURN v_object;
END;
$$;

CREATE FUNCTION workforce.knowledge_retrieve(
    p_token_hash text,
    p_run_id text,
    p_project_id text,
    p_query text,
    p_domain text DEFAULT NULL,
    p_retrieval_mode text DEFAULT 'GENERAL',
    p_task_ref text DEFAULT NULL,
    p_limit integer DEFAULT 5
)
RETURNS TABLE (
    run_id text,
    knowledge_id text,
    version integer,
    title text,
    knowledge_class text,
    domain text,
    classification text,
    content text,
    content_hash text,
    chunk_ref text,
    retrieval_score double precision,
    retrieved_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, workforce
AS $$
DECLARE
    v_actor_id text;
    v_role_code text;
    v_eligible_count integer;
BEGIN
    IF p_retrieval_mode NOT IN ('GENERAL', 'ROLE_PACK')
       OR p_limit NOT BETWEEN 1 AND 20
       OR nullif(btrim(p_query), '') IS NULL THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'KNOWLEDGE_RETRIEVAL_INVALID';
    END IF;

    v_actor_id := workforce.knowledge_authenticate(p_project_id, p_token_hash);

    SELECT role_code INTO v_role_code
    FROM workforce.employees
    WHERE employee_id = v_actor_id;

    -- Permission, lifecycle, currentness, audience and role-pack filtering happen
    -- before any full-text vector or score is computed.
    WITH eligible AS MATERIALIZED (
        SELECT object.knowledge_id, object.version
        FROM workforce.knowledge_objects AS object
        WHERE object.project_id = p_project_id
          AND object.knowledge_status = 'APPROVED'
          AND object.valid_from <= clock_timestamp()
          AND (object.stale_after IS NULL OR object.stale_after > clock_timestamp())
          AND (p_domain IS NULL OR object.domain = p_domain)
          AND EXISTS (
              SELECT 1
              FROM workforce.knowledge_audiences AS audience
              WHERE audience.project_id = object.project_id
                AND audience.knowledge_id = object.knowledge_id
                AND audience.version = object.version
                AND (
                    (audience.audience_kind = 'EMPLOYEE' AND audience.audience_value = v_actor_id)
                    OR (audience.audience_kind = 'ROLE' AND audience.audience_value = v_role_code)
                    OR (
                        audience.audience_kind = 'PROJECT'
                        AND audience.audience_value = p_project_id
                        AND object.classification = 'PROJECT_INTERNAL'
                    )
                )
          )
          AND (
              p_retrieval_mode = 'GENERAL'
              OR EXISTS (
                  SELECT 1
                  FROM workforce.knowledge_role_pack_entries AS pack
                  WHERE pack.project_id = object.project_id
                    AND pack.employee_id = v_actor_id
                    AND pack.knowledge_id = object.knowledge_id
                    AND pack.entry_status = 'ACTIVE'
              )
          )
    )
    SELECT count(*) INTO v_eligible_count FROM eligible;

    INSERT INTO workforce.knowledge_retrieval_runs (
        run_id, project_id, employee_id, task_ref, query_hash,
        domain_filter, retrieval_mode, eligible_count
    ) VALUES (
        p_run_id, p_project_id, v_actor_id, p_task_ref,
        encode(public.digest(p_query, 'sha256'), 'hex'), p_domain,
        p_retrieval_mode, v_eligible_count
    );

    RETURN QUERY
    WITH eligible AS MATERIALIZED (
        SELECT object.*
        FROM workforce.knowledge_objects AS object
        WHERE object.project_id = p_project_id
          AND object.knowledge_status = 'APPROVED'
          AND object.valid_from <= clock_timestamp()
          AND (object.stale_after IS NULL OR object.stale_after > clock_timestamp())
          AND (p_domain IS NULL OR object.domain = p_domain)
          AND EXISTS (
              SELECT 1
              FROM workforce.knowledge_audiences AS audience
              WHERE audience.project_id = object.project_id
                AND audience.knowledge_id = object.knowledge_id
                AND audience.version = object.version
                AND (
                    (audience.audience_kind = 'EMPLOYEE' AND audience.audience_value = v_actor_id)
                    OR (audience.audience_kind = 'ROLE' AND audience.audience_value = v_role_code)
                    OR (
                        audience.audience_kind = 'PROJECT'
                        AND audience.audience_value = p_project_id
                        AND object.classification = 'PROJECT_INTERNAL'
                    )
                )
          )
          AND (
              p_retrieval_mode = 'GENERAL'
              OR EXISTS (
                  SELECT 1
                  FROM workforce.knowledge_role_pack_entries AS pack
                  WHERE pack.project_id = object.project_id
                    AND pack.employee_id = v_actor_id
                    AND pack.knowledge_id = object.knowledge_id
                    AND pack.entry_status = 'ACTIVE'
              )
          )
    ), ranked AS (
        SELECT eligible.*,
               (
                   ts_rank_cd(
                       to_tsvector('simple', eligible.title || ' ' || eligible.content
                           || ' ' || array_to_string(eligible.tags, ' ')),
                       websearch_to_tsquery('simple', p_query)
                   )
                   + CASE WHEN p_domain IS NOT NULL AND eligible.domain = p_domain THEN 0.25 ELSE 0 END
               )::double precision AS score
        FROM eligible
        WHERE to_tsvector('simple', eligible.title || ' ' || eligible.content
                    || ' ' || array_to_string(eligible.tags, ' '))
              @@ websearch_to_tsquery('simple', p_query)
    ), selected AS MATERIALIZED (
        SELECT ranked.*,
               row_number() OVER (
                   ORDER BY ranked.score DESC, ranked.knowledge_id, ranked.version DESC
               )::integer AS position
        FROM ranked
        ORDER BY ranked.score DESC, ranked.knowledge_id, ranked.version DESC
        LIMIT p_limit
    ), inserted AS (
        INSERT INTO workforce.knowledge_context_items (
            run_id, item_position, knowledge_id, version,
            chunk_ref, content_hash, retrieval_score
        )
        SELECT p_run_id, selected.position, selected.knowledge_id, selected.version,
               'FULL', selected.content_hash, selected.score
        FROM selected
        RETURNING *
    ), counted AS (
        UPDATE workforce.knowledge_retrieval_runs
        SET returned_count = (SELECT count(*) FROM inserted)
        WHERE workforce.knowledge_retrieval_runs.run_id = p_run_id
        RETURNING workforce.knowledge_retrieval_runs.run_id
    )
    SELECT p_run_id, selected.knowledge_id, selected.version, selected.title,
           selected.knowledge_class, selected.domain, selected.classification,
           selected.content, selected.content_hash, inserted.chunk_ref,
           inserted.retrieval_score, inserted.retrieved_at
    FROM selected
    JOIN inserted
      ON inserted.run_id = p_run_id
     AND inserted.item_position = selected.position
    CROSS JOIN counted
    ORDER BY selected.position;
END;
$$;

CREATE FUNCTION workforce.knowledge_record_assessment(
    p_token_hash text,
    p_request_id text,
    p_project_id text,
    p_assessment_id text,
    p_employee_id text,
    p_capability_id text,
    p_score integer,
    p_target_level integer,
    p_error_class text,
    p_feedback text,
    p_training_action text,
    p_context_run_id text DEFAULT NULL,
    p_retest_of text DEFAULT NULL,
    p_retest_result text DEFAULT NULL
)
RETURNS workforce.capability_records
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, workforce
AS $$
DECLARE
    v_actor_id text;
    v_original workforce.training_assessments%ROWTYPE;
    v_record workforce.capability_records%ROWTYPE;
BEGIN
    v_actor_id := workforce.knowledge_authenticate(p_project_id, p_token_hash);

    IF NOT EXISTS (
        SELECT 1
        FROM workforce.knowledge_member_permissions
        WHERE project_id = p_project_id
          AND employee_id = v_actor_id
          AND permission_status = 'ACTIVE'
          AND can_assess
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'CAPABILITY_ASSESSMENT_DENIED';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.active_project_members
        WHERE project_id = p_project_id AND employee_id = p_employee_id
    ) OR NOT EXISTS (
        SELECT 1 FROM workforce.capability_definitions
        WHERE project_id = p_project_id
          AND capability_id = p_capability_id
          AND capability_status = 'ACTIVE'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'CAPABILITY_SCOPE_DENIED';
    END IF;

    IF p_context_run_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM workforce.knowledge_retrieval_runs
        WHERE run_id = p_context_run_id
          AND project_id = p_project_id
          AND employee_id = p_employee_id
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'CAPABILITY_CONTEXT_DENIED';
    END IF;

    IF p_retest_of IS NOT NULL THEN
        SELECT * INTO v_original
        FROM workforce.training_assessments
        WHERE assessment_id = p_retest_of;
        IF NOT FOUND
           OR v_original.project_id <> p_project_id
           OR v_original.employee_id <> p_employee_id
           OR v_original.capability_id <> p_capability_id THEN
            RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'CAPABILITY_RETEST_DENIED';
        END IF;
    END IF;

    PERFORM set_config('app.actor_id', v_actor_id, true);
    PERFORM set_config('app.request_id', p_request_id, true);

    INSERT INTO workforce.training_assessments (
        assessment_id, project_id, employee_id, capability_id, assessor_id,
        context_run_id, score, error_class, feedback, training_action,
        retest_of, retest_result
    ) VALUES (
        p_assessment_id, p_project_id, p_employee_id, p_capability_id, v_actor_id,
        p_context_run_id, p_score, p_error_class, p_feedback, p_training_action,
        p_retest_of, p_retest_result
    );

    INSERT INTO workforce.capability_records (
        project_id, employee_id, capability_id, current_level, target_level,
        latest_assessment_id, evidence_assessment_refs, last_assessed_at
    ) VALUES (
        p_project_id, p_employee_id, p_capability_id, p_score, p_target_level,
        p_assessment_id, ARRAY[p_assessment_id], clock_timestamp()
    )
    ON CONFLICT (project_id, employee_id, capability_id) DO UPDATE
    SET current_level = EXCLUDED.current_level,
        target_level = EXCLUDED.target_level,
        latest_assessment_id = EXCLUDED.latest_assessment_id,
        evidence_assessment_refs = array_append(
            workforce.capability_records.evidence_assessment_refs,
            EXCLUDED.latest_assessment_id
        ),
        last_assessed_at = EXCLUDED.last_assessed_at,
        updated_at = clock_timestamp()
    RETURNING * INTO v_record;

    RETURN v_record;
END;
$$;

INSERT INTO workforce.knowledge_systems (project_id, system_status, source_ref)
VALUES ('START-UP', 'DISABLED', 'ENG-004/HO-023');

INSERT INTO workforce.schema_migrations (migration_id, description)
VALUES (
    '004_knowledge_capability',
    'Permission-first knowledge lifecycle, role packs, context manifests, assessments and capability records'
);

COMMIT;
