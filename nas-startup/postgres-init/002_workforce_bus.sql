\set ON_ERROR_STOP on

BEGIN;

SELECT set_config('app.actor_id', 'SYSTEM-MIGRATION', true);
SELECT set_config('app.request_id', 'MIG-002-WORKFORCE-BUS', true);

CREATE TABLE workforce.bus_channels (
    project_id text PRIMARY KEY REFERENCES workforce.projects(project_id),
    channel_status text NOT NULL DEFAULT 'DISABLED',
    max_hops integer NOT NULL DEFAULT 4,
    max_body_chars integer NOT NULL DEFAULT 8000,
    source_ref text NOT NULL,
    version bigint NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    revoked_at timestamptz,
    revocation_reason text,
    CONSTRAINT bus_channels_status CHECK (channel_status IN ('DISABLED', 'TESTING', 'ACTIVE', 'REVOKED')),
    CONSTRAINT bus_channels_hops CHECK (max_hops BETWEEN 1 AND 16),
    CONSTRAINT bus_channels_body_limit CHECK (max_body_chars BETWEEN 1 AND 32000),
    CONSTRAINT bus_channels_version_positive CHECK (version >= 1),
    CONSTRAINT bus_channels_revocation_consistent CHECK (
        (channel_status = 'REVOKED' AND revoked_at IS NOT NULL AND nullif(btrim(revocation_reason), '') IS NOT NULL)
        OR (channel_status <> 'REVOKED' AND revoked_at IS NULL AND revocation_reason IS NULL)
    )
);

CREATE TABLE workforce.bus_member_capabilities (
    project_id text NOT NULL,
    employee_id text NOT NULL,
    capability_status text NOT NULL DEFAULT 'ACTIVE',
    read_scope text NOT NULL DEFAULT 'PARTICIPANT',
    task_authority text NOT NULL DEFAULT 'PROPOSE',
    can_send boolean NOT NULL DEFAULT true,
    can_create_handoff boolean NOT NULL DEFAULT true,
    source_ref text NOT NULL,
    version bigint NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    revoked_at timestamptz,
    revocation_reason text,
    PRIMARY KEY (project_id, employee_id),
    FOREIGN KEY (employee_id, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    CONSTRAINT bus_capabilities_status CHECK (capability_status IN ('ACTIVE', 'SUSPENDED', 'REVOKED')),
    CONSTRAINT bus_capabilities_read_scope CHECK (read_scope IN ('PARTICIPANT', 'PROJECT')),
    CONSTRAINT bus_capabilities_task_authority CHECK (task_authority IN ('PROPOSE', 'COORDINATE')),
    CONSTRAINT bus_capabilities_version_positive CHECK (version >= 1),
    CONSTRAINT bus_capabilities_revocation_consistent CHECK (
        (capability_status = 'REVOKED' AND revoked_at IS NOT NULL AND nullif(btrim(revocation_reason), '') IS NOT NULL)
        OR (capability_status <> 'REVOKED' AND revoked_at IS NULL AND revocation_reason IS NULL)
    )
);

CREATE TABLE workforce.bus_route_allowlist (
    route_id text PRIMARY KEY,
    project_id text NOT NULL,
    sender_id text NOT NULL,
    recipient_id text NOT NULL,
    route_kind text NOT NULL,
    route_status text NOT NULL DEFAULT 'ACTIVE',
    source_ref text NOT NULL,
    version bigint NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    revoked_at timestamptz,
    revocation_reason text,
    UNIQUE (project_id, sender_id, recipient_id, route_kind),
    FOREIGN KEY (sender_id, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    FOREIGN KEY (recipient_id, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    CONSTRAINT bus_routes_id_format CHECK (route_id ~ '^ROUTE-[A-Z0-9-]{8,120}$'),
    CONSTRAINT bus_routes_no_self CHECK (sender_id <> recipient_id),
    CONSTRAINT bus_routes_kind CHECK (route_kind IN ('MESSAGE', 'TASK', 'HANDOFF')),
    CONSTRAINT bus_routes_status CHECK (route_status IN ('ACTIVE', 'SUSPENDED', 'REVOKED')),
    CONSTRAINT bus_routes_version_positive CHECK (version >= 1),
    CONSTRAINT bus_routes_revocation_consistent CHECK (
        (route_status = 'REVOKED' AND revoked_at IS NOT NULL AND nullif(btrim(revocation_reason), '') IS NOT NULL)
        OR (route_status <> 'REVOKED' AND revoked_at IS NULL AND revocation_reason IS NULL)
    )
);

CREATE TABLE workforce.bus_credentials (
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
    CONSTRAINT bus_credentials_id_format CHECK (credential_id ~ '^CRED-[A-Z0-9-]{8,96}$'),
    CONSTRAINT bus_credentials_hash_format CHECK (token_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT bus_credentials_scope CHECK (credential_scope IN ('ACCEPTANCE', 'PRODUCTION')),
    CONSTRAINT bus_credentials_status CHECK (credential_status IN ('ACTIVE', 'SUSPENDED', 'REVOKED')),
    CONSTRAINT bus_credentials_version_positive CHECK (version >= 1),
    CONSTRAINT bus_credentials_acceptance_expiry CHECK (
        credential_scope <> 'ACCEPTANCE' OR expires_at IS NOT NULL
    ),
    CONSTRAINT bus_credentials_expiry_after_issue CHECK (
        expires_at IS NULL OR expires_at > issued_at
    ),
    CONSTRAINT bus_credentials_revocation_consistent CHECK (
        (credential_status = 'REVOKED' AND revoked_at IS NOT NULL AND nullif(btrim(revocation_reason), '') IS NOT NULL)
        OR (credential_status <> 'REVOKED' AND revoked_at IS NULL AND revocation_reason IS NULL)
    )
);

CREATE TABLE workforce.bus_tasks (
    task_id text PRIMARY KEY,
    project_id text NOT NULL,
    creator_id text NOT NULL,
    owner_id text NOT NULL,
    task_status text NOT NULL,
    priority text NOT NULL,
    title text NOT NULL,
    expected_output text NOT NULL,
    source_ref text NOT NULL,
    review_at timestamptz,
    completion_evidence text,
    version bigint NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    completed_at timestamptz,
    FOREIGN KEY (creator_id, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    FOREIGN KEY (owner_id, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    CONSTRAINT bus_tasks_id_format CHECK (task_id ~ '^[A-Z][A-Z0-9-]{2,63}$'),
    CONSTRAINT bus_tasks_status CHECK (task_status IN ('PENDING', 'OPEN', 'IN_PROGRESS', 'BLOCKED', 'HOLD', 'REVIEW', 'DONE', 'CANCELLED')),
    CONSTRAINT bus_tasks_priority CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    CONSTRAINT bus_tasks_title_length CHECK (char_length(title) BETWEEN 1 AND 240),
    CONSTRAINT bus_tasks_output_length CHECK (char_length(expected_output) BETWEEN 1 AND 4000),
    CONSTRAINT bus_tasks_version_positive CHECK (version >= 1),
    CONSTRAINT bus_tasks_completion_consistent CHECK (
        (task_status = 'DONE' AND completed_at IS NOT NULL AND nullif(btrim(completion_evidence), '') IS NOT NULL)
        OR (task_status <> 'DONE' AND completed_at IS NULL)
    )
);

CREATE TABLE workforce.bus_handoffs (
    handoff_id text PRIMARY KEY,
    project_id text NOT NULL,
    sender_id text NOT NULL,
    recipient_id text NOT NULL,
    task_ref text,
    handoff_status text NOT NULL,
    input_summary text NOT NULL,
    expected_output text NOT NULL,
    risks_and_assumptions text,
    trigger_or_due text,
    source_ref text NOT NULL,
    response_note text,
    version bigint NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    accepted_at timestamptz,
    rejected_at timestamptz,
    cancelled_at timestamptz,
    FOREIGN KEY (sender_id, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    FOREIGN KEY (recipient_id, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    CONSTRAINT bus_handoffs_id_format CHECK (handoff_id ~ '^HO-[A-Z0-9-]{3,63}$'),
    CONSTRAINT bus_handoffs_no_self CHECK (sender_id <> recipient_id),
    CONSTRAINT bus_handoffs_task_ref_format CHECK (task_ref IS NULL OR task_ref ~ '^[A-Z][A-Z0-9-]{2,63}$'),
    CONSTRAINT bus_handoffs_status CHECK (handoff_status IN ('PENDING', 'OPEN', 'ACCEPTED', 'REJECTED', 'CANCELLED')),
    CONSTRAINT bus_handoffs_input_length CHECK (char_length(input_summary) BETWEEN 1 AND 8000),
    CONSTRAINT bus_handoffs_output_length CHECK (char_length(expected_output) BETWEEN 1 AND 4000),
    CONSTRAINT bus_handoffs_version_positive CHECK (version >= 1),
    CONSTRAINT bus_handoffs_terminal_consistent CHECK (
        (handoff_status = 'ACCEPTED' AND accepted_at IS NOT NULL AND rejected_at IS NULL AND cancelled_at IS NULL)
        OR (handoff_status = 'REJECTED' AND rejected_at IS NOT NULL AND accepted_at IS NULL AND cancelled_at IS NULL)
        OR (handoff_status = 'CANCELLED' AND cancelled_at IS NOT NULL AND accepted_at IS NULL AND rejected_at IS NULL)
        OR (handoff_status IN ('PENDING', 'OPEN') AND accepted_at IS NULL AND rejected_at IS NULL AND cancelled_at IS NULL)
    )
);

CREATE TABLE workforce.bus_messages (
    message_id text PRIMARY KEY,
    project_id text NOT NULL,
    sender_id text NOT NULL,
    recipient_id text NOT NULL,
    idempotency_key text NOT NULL,
    correlation_id text NOT NULL,
    parent_message_id text REFERENCES workforce.bus_messages(message_id),
    hop_count integer NOT NULL DEFAULT 0,
    action_class text NOT NULL,
    confidentiality text NOT NULL,
    subject text NOT NULL,
    body text NOT NULL,
    task_ref text,
    handoff_ref text,
    delivery_status text NOT NULL DEFAULT 'DELIVERED',
    acknowledgement_note text,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    delivered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    accepted_at timestamptz,
    rejected_at timestamptz,
    UNIQUE (project_id, sender_id, idempotency_key),
    FOREIGN KEY (sender_id, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    FOREIGN KEY (recipient_id, project_id)
        REFERENCES workforce.employee_project_memberships(employee_id, project_id),
    CONSTRAINT bus_messages_id_format CHECK (message_id ~ '^MSG-[A-Z0-9-]{8,80}$'),
    CONSTRAINT bus_messages_idempotency_format CHECK (idempotency_key ~ '^IDEM-[A-Z0-9-]{8,96}$'),
    CONSTRAINT bus_messages_correlation_format CHECK (correlation_id ~ '^MSG-[A-Z0-9-]{8,80}$'),
    CONSTRAINT bus_messages_no_self CHECK (sender_id <> recipient_id),
    CONSTRAINT bus_messages_hop_count CHECK (hop_count BETWEEN 0 AND 16),
    CONSTRAINT bus_messages_action_class CHECK (action_class IN ('INTERNAL_COMMUNICATION', 'INTERNAL_REVIEW', 'INTERNAL_STATUS', 'INTERNAL_COORDINATION')),
    CONSTRAINT bus_messages_confidentiality CHECK (confidentiality IN ('PROJECT_INTERNAL', 'NEED_TO_KNOW')),
    CONSTRAINT bus_messages_subject_length CHECK (char_length(subject) BETWEEN 1 AND 200),
    CONSTRAINT bus_messages_body_length CHECK (char_length(body) BETWEEN 1 AND 32000),
    CONSTRAINT bus_messages_task_ref_format CHECK (task_ref IS NULL OR task_ref ~ '^[A-Z][A-Z0-9-]{2,63}$'),
    CONSTRAINT bus_messages_handoff_ref_format CHECK (handoff_ref IS NULL OR handoff_ref ~ '^HO-[A-Z0-9-]{3,63}$'),
    CONSTRAINT bus_messages_delivery_status CHECK (delivery_status IN ('DELIVERED', 'ACCEPTED', 'REJECTED')),
    CONSTRAINT bus_messages_delivery_consistent CHECK (
        (delivery_status = 'DELIVERED' AND accepted_at IS NULL AND rejected_at IS NULL)
        OR (delivery_status = 'ACCEPTED' AND accepted_at IS NOT NULL AND rejected_at IS NULL)
        OR (delivery_status = 'REJECTED' AND rejected_at IS NOT NULL AND accepted_at IS NULL)
    )
);

CREATE TABLE workforce.bus_events (
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
    CONSTRAINT bus_events_record_type CHECK (record_type IN ('CHANNEL', 'CAPABILITY', 'ROUTE', 'CREDENTIAL', 'TASK', 'HANDOFF', 'MESSAGE')),
    CONSTRAINT bus_events_event_type CHECK (event_type IN ('INSERT', 'UPDATE')),
    CONSTRAINT bus_events_actor_present CHECK (char_length(actor_id) BETWEEN 1 AND 128),
    CONSTRAINT bus_events_request_present CHECK (char_length(request_id) BETWEEN 1 AND 128)
);

CREATE INDEX bus_routes_lookup_idx
    ON workforce.bus_route_allowlist (project_id, sender_id, recipient_id, route_kind, route_status);

CREATE INDEX bus_credentials_lookup_idx
    ON workforce.bus_credentials (project_id, token_hash, credential_status);

CREATE INDEX bus_tasks_owner_status_idx
    ON workforce.bus_tasks (project_id, owner_id, task_status, updated_at DESC);

CREATE INDEX bus_handoffs_recipient_status_idx
    ON workforce.bus_handoffs (project_id, recipient_id, handoff_status, updated_at DESC);

CREATE INDEX bus_messages_inbox_idx
    ON workforce.bus_messages (project_id, recipient_id, created_at DESC, message_id);

CREATE INDEX bus_messages_outbox_idx
    ON workforce.bus_messages (project_id, sender_id, created_at DESC, message_id);

CREATE INDEX bus_messages_correlation_idx
    ON workforce.bus_messages (project_id, correlation_id, hop_count);

CREATE INDEX bus_events_record_idx
    ON workforce.bus_events (project_id, record_type, record_key, event_id);

CREATE INDEX bus_events_request_idx
    ON workforce.bus_events (request_id, event_id);

CREATE FUNCTION workforce.bus_touch_versioned_row()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.version := OLD.version + 1;
    NEW.updated_at := clock_timestamp();
    RETURN NEW;
END;
$$;

CREATE FUNCTION workforce.bus_record_change()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_record_type text;
    v_record_key text;
    v_project_id text;
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
            MESSAGE = 'BUS_AUDIT_CONTEXT_REQUIRED';
    END IF;

    CASE TG_TABLE_NAME
        WHEN 'bus_channels' THEN
            v_record_type := 'CHANNEL';
            v_record_key := COALESCE(NEW.project_id, OLD.project_id);
            v_project_id := v_record_key;
        WHEN 'bus_member_capabilities' THEN
            v_record_type := 'CAPABILITY';
            v_record_key := COALESCE(NEW.employee_id, OLD.employee_id) || '@' || COALESCE(NEW.project_id, OLD.project_id);
            v_project_id := COALESCE(NEW.project_id, OLD.project_id);
        WHEN 'bus_route_allowlist' THEN
            v_record_type := 'ROUTE';
            v_record_key := COALESCE(NEW.route_id, OLD.route_id);
            v_project_id := COALESCE(NEW.project_id, OLD.project_id);
        WHEN 'bus_credentials' THEN
            v_record_type := 'CREDENTIAL';
            v_record_key := COALESCE(NEW.credential_id, OLD.credential_id);
            v_project_id := COALESCE(NEW.project_id, OLD.project_id);
        WHEN 'bus_tasks' THEN
            v_record_type := 'TASK';
            v_record_key := COALESCE(NEW.task_id, OLD.task_id);
            v_project_id := COALESCE(NEW.project_id, OLD.project_id);
        WHEN 'bus_handoffs' THEN
            v_record_type := 'HANDOFF';
            v_record_key := COALESCE(NEW.handoff_id, OLD.handoff_id);
            v_project_id := COALESCE(NEW.project_id, OLD.project_id);
        WHEN 'bus_messages' THEN
            v_record_type := 'MESSAGE';
            v_record_key := COALESCE(NEW.message_id, OLD.message_id);
            v_project_id := COALESCE(NEW.project_id, OLD.project_id);
        ELSE
            RAISE EXCEPTION 'Unsupported bus table: %', TG_TABLE_NAME;
    END CASE;

    -- Credential hashes are authentication material and must never be copied
    -- into the general-purpose audit payload.
    IF TG_TABLE_NAME = 'bus_credentials' THEN
        v_old_record := CASE
            WHEN TG_OP = 'UPDATE' THEN to_jsonb(OLD) - 'token_hash'
            ELSE NULL
        END;
        v_new_record := to_jsonb(NEW) - 'token_hash';
    ELSE
        v_old_record := CASE WHEN TG_OP = 'UPDATE' THEN to_jsonb(OLD) ELSE NULL END;
        v_new_record := to_jsonb(NEW);
    END IF;

    INSERT INTO workforce.bus_events (
        project_id,
        record_type,
        record_key,
        event_type,
        actor_id,
        request_id,
        old_record,
        new_record
    ) VALUES (
        v_project_id,
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

CREATE FUNCTION workforce.bus_guard_route_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.route_id IS DISTINCT FROM OLD.route_id
       OR NEW.project_id IS DISTINCT FROM OLD.project_id
       OR NEW.sender_id IS DISTINCT FROM OLD.sender_id
       OR NEW.recipient_id IS DISTINCT FROM OLD.recipient_id
       OR NEW.route_kind IS DISTINCT FROM OLD.route_kind
       OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'BUS_ROUTE_IDENTITY_IMMUTABLE';
    END IF;

    IF OLD.route_status = 'REVOKED' AND NEW.route_status <> 'REVOKED' THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'BUS_ROUTE_REVOCATION_FINAL';
    END IF;

    RETURN NEW;
END;
$$;

CREATE FUNCTION workforce.bus_guard_channel_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.project_id IS DISTINCT FROM OLD.project_id
       OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'BUS_CHANNEL_IDENTITY_IMMUTABLE';
    END IF;

    IF OLD.channel_status = 'REVOKED' AND NEW.channel_status <> 'REVOKED' THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'BUS_CHANNEL_REVOCATION_FINAL';
    END IF;

    RETURN NEW;
END;
$$;

CREATE FUNCTION workforce.bus_guard_capability_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.project_id IS DISTINCT FROM OLD.project_id
       OR NEW.employee_id IS DISTINCT FROM OLD.employee_id
       OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'BUS_CAPABILITY_IDENTITY_IMMUTABLE';
    END IF;

    IF OLD.capability_status = 'REVOKED' AND NEW.capability_status <> 'REVOKED' THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'BUS_CAPABILITY_REVOCATION_FINAL';
    END IF;

    RETURN NEW;
END;
$$;

CREATE FUNCTION workforce.bus_guard_credential_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.credential_id IS DISTINCT FROM OLD.credential_id
       OR NEW.project_id IS DISTINCT FROM OLD.project_id
       OR NEW.employee_id IS DISTINCT FROM OLD.employee_id
       OR NEW.token_hash IS DISTINCT FROM OLD.token_hash
       OR NEW.credential_scope IS DISTINCT FROM OLD.credential_scope
       OR NEW.source_ref IS DISTINCT FROM OLD.source_ref
       OR NEW.issued_at IS DISTINCT FROM OLD.issued_at
       OR NEW.expires_at IS DISTINCT FROM OLD.expires_at THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'BUS_CREDENTIAL_IDENTITY_IMMUTABLE';
    END IF;

    IF OLD.credential_status = 'REVOKED' AND NEW.credential_status <> 'REVOKED' THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'BUS_CREDENTIAL_REVOCATION_FINAL';
    END IF;

    RETURN NEW;
END;
$$;

CREATE FUNCTION workforce.bus_guard_task_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.task_id IS DISTINCT FROM OLD.task_id
       OR NEW.project_id IS DISTINCT FROM OLD.project_id
       OR NEW.creator_id IS DISTINCT FROM OLD.creator_id
       OR NEW.owner_id IS DISTINCT FROM OLD.owner_id
       OR NEW.priority IS DISTINCT FROM OLD.priority
       OR NEW.title IS DISTINCT FROM OLD.title
       OR NEW.expected_output IS DISTINCT FROM OLD.expected_output
       OR NEW.source_ref IS DISTINCT FROM OLD.source_ref
       OR NEW.review_at IS DISTINCT FROM OLD.review_at
       OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'BUS_TASK_PAYLOAD_IMMUTABLE';
    END IF;

    RETURN NEW;
END;
$$;

CREATE FUNCTION workforce.bus_guard_handoff_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.handoff_id IS DISTINCT FROM OLD.handoff_id
       OR NEW.project_id IS DISTINCT FROM OLD.project_id
       OR NEW.sender_id IS DISTINCT FROM OLD.sender_id
       OR NEW.recipient_id IS DISTINCT FROM OLD.recipient_id
       OR NEW.task_ref IS DISTINCT FROM OLD.task_ref
       OR NEW.input_summary IS DISTINCT FROM OLD.input_summary
       OR NEW.expected_output IS DISTINCT FROM OLD.expected_output
       OR NEW.risks_and_assumptions IS DISTINCT FROM OLD.risks_and_assumptions
       OR NEW.trigger_or_due IS DISTINCT FROM OLD.trigger_or_due
       OR NEW.source_ref IS DISTINCT FROM OLD.source_ref
       OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'BUS_HANDOFF_PAYLOAD_IMMUTABLE';
    END IF;

    RETURN NEW;
END;
$$;

CREATE FUNCTION workforce.bus_guard_message_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.message_id IS DISTINCT FROM OLD.message_id
       OR NEW.project_id IS DISTINCT FROM OLD.project_id
       OR NEW.sender_id IS DISTINCT FROM OLD.sender_id
       OR NEW.recipient_id IS DISTINCT FROM OLD.recipient_id
       OR NEW.idempotency_key IS DISTINCT FROM OLD.idempotency_key
       OR NEW.correlation_id IS DISTINCT FROM OLD.correlation_id
       OR NEW.parent_message_id IS DISTINCT FROM OLD.parent_message_id
       OR NEW.hop_count IS DISTINCT FROM OLD.hop_count
       OR NEW.action_class IS DISTINCT FROM OLD.action_class
       OR NEW.confidentiality IS DISTINCT FROM OLD.confidentiality
       OR NEW.subject IS DISTINCT FROM OLD.subject
       OR NEW.body IS DISTINCT FROM OLD.body
       OR NEW.task_ref IS DISTINCT FROM OLD.task_ref
       OR NEW.handoff_ref IS DISTINCT FROM OLD.handoff_ref
       OR NEW.created_at IS DISTINCT FROM OLD.created_at
       OR NEW.delivered_at IS DISTINCT FROM OLD.delivered_at THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'BUS_MESSAGE_PAYLOAD_IMMUTABLE';
    END IF;

    IF OLD.delivery_status <> 'DELIVERED'
       OR NEW.delivery_status NOT IN ('ACCEPTED', 'REJECTED') THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'BUS_MESSAGE_ACK_TRANSITION_DENIED';
    END IF;

    RETURN NEW;
END;
$$;

CREATE FUNCTION workforce.prevent_bus_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION USING
        ERRCODE = '55000',
        MESSAGE = 'Workforce bus events are append-only.';
END;
$$;

CREATE FUNCTION workforce.bus_authenticate(
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
    FROM workforce.bus_credentials AS c
    JOIN workforce.bus_channels AS ch
      ON ch.project_id = c.project_id
    JOIN workforce.bus_member_capabilities AS cap
      ON cap.project_id = c.project_id
     AND cap.employee_id = c.employee_id
    JOIN workforce.employee_project_memberships AS m
      ON m.project_id = c.project_id
     AND m.employee_id = c.employee_id
    JOIN workforce.employees AS e
      ON e.employee_id = c.employee_id
    JOIN workforce.projects AS p
      ON p.project_id = c.project_id
    WHERE c.project_id = p_project_id
      AND c.token_hash = p_token_hash
      AND c.credential_status = 'ACTIVE'
      AND (c.expires_at IS NULL OR c.expires_at > clock_timestamp())
      AND cap.capability_status = 'ACTIVE'
      AND m.membership_status = 'ACTIVE'
      AND e.employment_status IN ('PROBATION', 'ACTIVE')
      AND p.project_status = 'ACTIVE'
      AND (
          (ch.channel_status = 'TESTING' AND c.credential_scope = 'ACCEPTANCE')
          OR (ch.channel_status = 'ACTIVE' AND c.credential_scope = 'PRODUCTION')
      );

    IF v_employee_id IS NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '42501',
            MESSAGE = 'BUS_AUTH_FAILED';
    END IF;

    RETURN v_employee_id;
END;
$$;

CREATE FUNCTION workforce.bus_send_message(
    p_token_hash text,
    p_request_id text,
    p_message_id text,
    p_project_id text,
    p_recipient_id text,
    p_idempotency_key text,
    p_subject text,
    p_body text,
    p_action_class text DEFAULT 'INTERNAL_COMMUNICATION',
    p_confidentiality text DEFAULT 'NEED_TO_KNOW',
    p_task_ref text DEFAULT NULL,
    p_handoff_ref text DEFAULT NULL,
    p_parent_message_id text DEFAULT NULL
)
RETURNS workforce.bus_messages
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, workforce
AS $$
DECLARE
    v_actor_id text;
    v_max_hops integer;
    v_max_body_chars integer;
    v_parent workforce.bus_messages%ROWTYPE;
    v_message workforce.bus_messages%ROWTYPE;
    v_hop_count integer := 0;
    v_correlation_id text := p_message_id;
BEGIN
    IF p_request_id IS NULL OR char_length(p_request_id) NOT BETWEEN 1 AND 128 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'BUS_REQUEST_ID_REQUIRED';
    END IF;

    IF p_action_class NOT IN ('INTERNAL_COMMUNICATION', 'INTERNAL_REVIEW', 'INTERNAL_STATUS', 'INTERNAL_COORDINATION') THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'BUS_ACTION_CLASS_DENIED';
    END IF;

    v_actor_id := workforce.bus_authenticate(p_project_id, p_token_hash);

    SELECT ch.max_hops, ch.max_body_chars
    INTO v_max_hops, v_max_body_chars
    FROM workforce.bus_channels AS ch
    WHERE ch.project_id = p_project_id;

    IF char_length(p_body) > v_max_body_chars THEN
        RAISE EXCEPTION USING ERRCODE = '22001', MESSAGE = 'BUS_BODY_TOO_LARGE';
    END IF;

    IF v_actor_id = p_recipient_id THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'BUS_SELF_ROUTE_DENIED';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM workforce.bus_member_capabilities
        WHERE project_id = p_project_id
          AND employee_id = v_actor_id
          AND capability_status = 'ACTIVE'
          AND can_send
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'BUS_SEND_CAPABILITY_DENIED';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM workforce.active_project_members
        WHERE project_id = p_project_id
          AND employee_id = p_recipient_id
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'BUS_RECIPIENT_NOT_ACTIVE';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM workforce.bus_route_allowlist
        WHERE project_id = p_project_id
          AND sender_id = v_actor_id
          AND recipient_id = p_recipient_id
          AND route_kind = 'MESSAGE'
          AND route_status = 'ACTIVE'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'BUS_ROUTE_DENIED';
    END IF;

    IF p_parent_message_id IS NOT NULL THEN
        SELECT * INTO v_parent
        FROM workforce.bus_messages
        WHERE message_id = p_parent_message_id;

        IF NOT FOUND
           OR v_parent.project_id <> p_project_id
           OR v_parent.recipient_id <> v_actor_id
           OR v_parent.sender_id <> p_recipient_id THEN
            RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'BUS_PARENT_ROUTE_DENIED';
        END IF;

        v_hop_count := v_parent.hop_count + 1;
        v_correlation_id := v_parent.correlation_id;
    END IF;

    IF v_hop_count > v_max_hops THEN
        RAISE EXCEPTION USING ERRCODE = '54000', MESSAGE = 'BUS_LOOP_LIMIT_EXCEEDED';
    END IF;

    PERFORM set_config('app.actor_id', v_actor_id, true);
    PERFORM set_config('app.request_id', p_request_id, true);

    INSERT INTO workforce.bus_messages (
        message_id,
        project_id,
        sender_id,
        recipient_id,
        idempotency_key,
        correlation_id,
        parent_message_id,
        hop_count,
        action_class,
        confidentiality,
        subject,
        body,
        task_ref,
        handoff_ref
    ) VALUES (
        p_message_id,
        p_project_id,
        v_actor_id,
        p_recipient_id,
        p_idempotency_key,
        v_correlation_id,
        p_parent_message_id,
        v_hop_count,
        p_action_class,
        p_confidentiality,
        p_subject,
        p_body,
        p_task_ref,
        p_handoff_ref
    )
    ON CONFLICT (project_id, sender_id, idempotency_key) DO NOTHING
    RETURNING * INTO v_message;

    IF v_message.message_id IS NULL THEN
        SELECT * INTO v_message
        FROM workforce.bus_messages
        WHERE project_id = p_project_id
          AND sender_id = v_actor_id
          AND idempotency_key = p_idempotency_key;

        IF v_message.message_id <> p_message_id
           OR v_message.recipient_id <> p_recipient_id
           OR v_message.subject <> p_subject
           OR v_message.body <> p_body
           OR v_message.action_class <> p_action_class
           OR v_message.confidentiality <> p_confidentiality
           OR v_message.task_ref IS DISTINCT FROM p_task_ref
           OR v_message.handoff_ref IS DISTINCT FROM p_handoff_ref
           OR v_message.parent_message_id IS DISTINCT FROM p_parent_message_id THEN
            RAISE EXCEPTION USING ERRCODE = '23505', MESSAGE = 'BUS_IDEMPOTENCY_CONFLICT';
        END IF;
    END IF;

    RETURN v_message;
END;
$$;

CREATE FUNCTION workforce.bus_acknowledge_message(
    p_token_hash text,
    p_request_id text,
    p_project_id text,
    p_message_id text,
    p_decision text,
    p_note text DEFAULT NULL
)
RETURNS workforce.bus_messages
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, workforce
AS $$
DECLARE
    v_actor_id text;
    v_message workforce.bus_messages%ROWTYPE;
BEGIN
    IF p_request_id IS NULL OR char_length(p_request_id) NOT BETWEEN 1 AND 128 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'BUS_REQUEST_ID_REQUIRED';
    END IF;

    IF p_decision NOT IN ('ACCEPTED', 'REJECTED') THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'BUS_ACK_DECISION_INVALID';
    END IF;

    IF p_note IS NOT NULL AND char_length(p_note) > 1000 THEN
        RAISE EXCEPTION USING ERRCODE = '22001', MESSAGE = 'BUS_ACK_NOTE_TOO_LARGE';
    END IF;

    v_actor_id := workforce.bus_authenticate(p_project_id, p_token_hash);

    SELECT * INTO v_message
    FROM workforce.bus_messages
    WHERE project_id = p_project_id
      AND message_id = p_message_id
    FOR UPDATE;

    IF NOT FOUND OR v_message.recipient_id <> v_actor_id THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'BUS_ACK_DENIED';
    END IF;

    IF v_message.delivery_status = p_decision THEN
        RETURN v_message;
    END IF;

    IF v_message.delivery_status <> 'DELIVERED' THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'BUS_ACK_ALREADY_FINAL';
    END IF;

    PERFORM set_config('app.actor_id', v_actor_id, true);
    PERFORM set_config('app.request_id', p_request_id, true);

    UPDATE workforce.bus_messages
    SET delivery_status = p_decision,
        acknowledgement_note = p_note,
        accepted_at = CASE WHEN p_decision = 'ACCEPTED' THEN clock_timestamp() ELSE NULL END,
        rejected_at = CASE WHEN p_decision = 'REJECTED' THEN clock_timestamp() ELSE NULL END
    WHERE message_id = p_message_id
    RETURNING * INTO v_message;

    RETURN v_message;
END;
$$;

CREATE FUNCTION workforce.bus_list_messages(
    p_token_hash text,
    p_project_id text,
    p_scope text,
    p_limit integer DEFAULT 100
)
RETURNS SETOF workforce.bus_messages
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, workforce
AS $$
DECLARE
    v_actor_id text;
    v_read_scope text;
BEGIN
    IF p_scope NOT IN ('INBOX', 'OUTBOX', 'PROJECT') THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'BUS_READ_SCOPE_INVALID';
    END IF;

    IF p_limit NOT BETWEEN 1 AND 200 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'BUS_READ_LIMIT_INVALID';
    END IF;

    v_actor_id := workforce.bus_authenticate(p_project_id, p_token_hash);

    SELECT read_scope INTO v_read_scope
    FROM workforce.bus_member_capabilities
    WHERE project_id = p_project_id
      AND employee_id = v_actor_id
      AND capability_status = 'ACTIVE';

    IF p_scope = 'PROJECT' AND v_read_scope <> 'PROJECT' THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'BUS_PROJECT_READ_DENIED';
    END IF;

    RETURN QUERY
    SELECT m.*
    FROM workforce.bus_messages AS m
    WHERE m.project_id = p_project_id
      AND (
          (p_scope = 'INBOX' AND m.recipient_id = v_actor_id)
          OR (p_scope = 'OUTBOX' AND m.sender_id = v_actor_id)
          OR (
              p_scope = 'PROJECT'
              AND v_read_scope = 'PROJECT'
              AND (
                  m.confidentiality = 'PROJECT_INTERNAL'
                  OR m.sender_id = v_actor_id
                  OR m.recipient_id = v_actor_id
              )
          )
      )
    ORDER BY m.created_at DESC, m.message_id DESC
    LIMIT p_limit;
END;
$$;

CREATE FUNCTION workforce.bus_create_task(
    p_token_hash text,
    p_request_id text,
    p_task_id text,
    p_project_id text,
    p_owner_id text,
    p_task_status text,
    p_priority text,
    p_title text,
    p_expected_output text,
    p_source_ref text,
    p_review_at timestamptz DEFAULT NULL
)
RETURNS workforce.bus_tasks
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, workforce
AS $$
DECLARE
    v_actor_id text;
    v_task_authority text;
    v_task workforce.bus_tasks%ROWTYPE;
BEGIN
    IF p_request_id IS NULL OR char_length(p_request_id) NOT BETWEEN 1 AND 128 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'BUS_REQUEST_ID_REQUIRED';
    END IF;

    v_actor_id := workforce.bus_authenticate(p_project_id, p_token_hash);

    SELECT task_authority INTO v_task_authority
    FROM workforce.bus_member_capabilities
    WHERE project_id = p_project_id
      AND employee_id = v_actor_id
      AND capability_status = 'ACTIVE';

    IF NOT EXISTS (
        SELECT 1
        FROM workforce.active_project_members
        WHERE project_id = p_project_id
          AND employee_id = p_owner_id
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'BUS_TASK_OWNER_NOT_ACTIVE';
    END IF;

    IF v_actor_id <> p_owner_id AND NOT EXISTS (
        SELECT 1
        FROM workforce.bus_route_allowlist
        WHERE project_id = p_project_id
          AND sender_id = v_actor_id
          AND recipient_id = p_owner_id
          AND route_kind = 'TASK'
          AND route_status = 'ACTIVE'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'BUS_TASK_ROUTE_DENIED';
    END IF;

    IF p_task_status = 'PENDING' THEN
        NULL;
    ELSIF p_task_status = 'OPEN'
          AND v_task_authority = 'COORDINATE'
          AND v_actor_id = 'SAO-001'
          AND p_owner_id IN ('AI-ENG-001', 'RAS-001', 'PEO-001') THEN
        NULL;
    ELSE
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'BUS_TASK_INITIAL_STATUS_DENIED';
    END IF;

    PERFORM set_config('app.actor_id', v_actor_id, true);
    PERFORM set_config('app.request_id', p_request_id, true);

    INSERT INTO workforce.bus_tasks (
        task_id,
        project_id,
        creator_id,
        owner_id,
        task_status,
        priority,
        title,
        expected_output,
        source_ref,
        review_at
    ) VALUES (
        p_task_id,
        p_project_id,
        v_actor_id,
        p_owner_id,
        p_task_status,
        p_priority,
        p_title,
        p_expected_output,
        p_source_ref,
        p_review_at
    )
    ON CONFLICT (task_id) DO NOTHING
    RETURNING * INTO v_task;

    IF v_task.task_id IS NULL THEN
        SELECT * INTO v_task
        FROM workforce.bus_tasks
        WHERE task_id = p_task_id;

        IF v_task.project_id <> p_project_id
           OR v_task.creator_id <> v_actor_id
           OR v_task.owner_id <> p_owner_id
           OR v_task.task_status <> p_task_status
           OR v_task.priority <> p_priority
           OR v_task.title <> p_title
           OR v_task.expected_output <> p_expected_output
           OR v_task.source_ref <> p_source_ref
           OR v_task.review_at IS DISTINCT FROM p_review_at THEN
            RAISE EXCEPTION USING ERRCODE = '23505', MESSAGE = 'BUS_TASK_IDEMPOTENCY_CONFLICT';
        END IF;
    END IF;

    RETURN v_task;
END;
$$;

CREATE FUNCTION workforce.bus_list_tasks(
    p_token_hash text,
    p_project_id text,
    p_scope text,
    p_limit integer DEFAULT 100
)
RETURNS SETOF workforce.bus_tasks
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, workforce
AS $$
DECLARE
    v_actor_id text;
    v_read_scope text;
BEGIN
    IF p_scope NOT IN ('OWNED', 'CREATED', 'PROJECT') THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'BUS_TASK_READ_SCOPE_INVALID';
    END IF;

    IF p_limit NOT BETWEEN 1 AND 200 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'BUS_READ_LIMIT_INVALID';
    END IF;

    v_actor_id := workforce.bus_authenticate(p_project_id, p_token_hash);

    SELECT read_scope INTO v_read_scope
    FROM workforce.bus_member_capabilities
    WHERE project_id = p_project_id
      AND employee_id = v_actor_id
      AND capability_status = 'ACTIVE';

    IF p_scope = 'PROJECT' AND v_read_scope <> 'PROJECT' THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'BUS_PROJECT_READ_DENIED';
    END IF;

    RETURN QUERY
    SELECT t.*
    FROM workforce.bus_tasks AS t
    WHERE t.project_id = p_project_id
      AND (
          (p_scope = 'OWNED' AND t.owner_id = v_actor_id)
          OR (p_scope = 'CREATED' AND t.creator_id = v_actor_id)
          OR (p_scope = 'PROJECT' AND v_read_scope = 'PROJECT')
      )
    ORDER BY t.updated_at DESC, t.task_id DESC
    LIMIT p_limit;
END;
$$;

CREATE FUNCTION workforce.bus_transition_task(
    p_token_hash text,
    p_request_id text,
    p_project_id text,
    p_task_id text,
    p_new_status text,
    p_completion_evidence text DEFAULT NULL
)
RETURNS workforce.bus_tasks
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, workforce
AS $$
DECLARE
    v_actor_id text;
    v_task workforce.bus_tasks%ROWTYPE;
    v_allowed boolean := false;
BEGIN
    IF p_request_id IS NULL OR char_length(p_request_id) NOT BETWEEN 1 AND 128 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'BUS_REQUEST_ID_REQUIRED';
    END IF;

    v_actor_id := workforce.bus_authenticate(p_project_id, p_token_hash);

    SELECT * INTO v_task
    FROM workforce.bus_tasks
    WHERE project_id = p_project_id
      AND task_id = p_task_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'BUS_TASK_NOT_FOUND';
    END IF;

    IF v_task.task_status = p_new_status THEN
        IF p_new_status = 'DONE'
           AND v_task.completion_evidence IS DISTINCT FROM p_completion_evidence THEN
            RAISE EXCEPTION USING ERRCODE = '23505', MESSAGE = 'BUS_TASK_IDEMPOTENCY_CONFLICT';
        END IF;
        RETURN v_task;
    END IF;

    v_allowed :=
        (v_actor_id = v_task.owner_id AND v_task.task_status = 'OPEN' AND p_new_status IN ('IN_PROGRESS', 'BLOCKED', 'HOLD', 'REVIEW'))
        OR (v_actor_id = v_task.owner_id AND v_task.task_status IN ('IN_PROGRESS', 'BLOCKED', 'HOLD') AND p_new_status IN ('IN_PROGRESS', 'BLOCKED', 'HOLD', 'REVIEW'))
        OR (v_actor_id = v_task.creator_id AND v_task.task_status = 'PENDING' AND p_new_status = 'CANCELLED')
        OR (v_actor_id = 'SAO-001' AND v_task.task_status = 'PENDING' AND p_new_status = 'OPEN' AND v_task.owner_id IN ('AI-ENG-001', 'RAS-001', 'PEO-001'))
        OR (v_actor_id = v_task.creator_id AND v_task.task_status = 'REVIEW' AND p_new_status IN ('DONE', 'IN_PROGRESS'));

    IF NOT v_allowed THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'BUS_TASK_TRANSITION_DENIED';
    END IF;

    IF p_new_status = 'DONE' AND nullif(btrim(p_completion_evidence), '') IS NULL THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'BUS_TASK_COMPLETION_EVIDENCE_REQUIRED';
    END IF;

    PERFORM set_config('app.actor_id', v_actor_id, true);
    PERFORM set_config('app.request_id', p_request_id, true);

    UPDATE workforce.bus_tasks
    SET task_status = p_new_status,
        completion_evidence = CASE WHEN p_new_status = 'DONE' THEN p_completion_evidence ELSE completion_evidence END,
        completed_at = CASE WHEN p_new_status = 'DONE' THEN clock_timestamp() ELSE NULL END
    WHERE task_id = p_task_id
    RETURNING * INTO v_task;

    RETURN v_task;
END;
$$;

CREATE FUNCTION workforce.bus_create_handoff(
    p_token_hash text,
    p_request_id text,
    p_handoff_id text,
    p_project_id text,
    p_recipient_id text,
    p_handoff_status text,
    p_input_summary text,
    p_expected_output text,
    p_source_ref text,
    p_task_ref text DEFAULT NULL,
    p_risks_and_assumptions text DEFAULT NULL,
    p_trigger_or_due text DEFAULT NULL
)
RETURNS workforce.bus_handoffs
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, workforce
AS $$
DECLARE
    v_actor_id text;
    v_handoff workforce.bus_handoffs%ROWTYPE;
BEGIN
    IF p_request_id IS NULL OR char_length(p_request_id) NOT BETWEEN 1 AND 128 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'BUS_REQUEST_ID_REQUIRED';
    END IF;

    IF p_handoff_status NOT IN ('PENDING', 'OPEN') THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'BUS_HANDOFF_INITIAL_STATUS_DENIED';
    END IF;

    v_actor_id := workforce.bus_authenticate(p_project_id, p_token_hash);

    IF NOT EXISTS (
        SELECT 1
        FROM workforce.bus_member_capabilities
        WHERE project_id = p_project_id
          AND employee_id = v_actor_id
          AND capability_status = 'ACTIVE'
          AND can_create_handoff
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'BUS_HANDOFF_CAPABILITY_DENIED';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM workforce.bus_route_allowlist
        WHERE project_id = p_project_id
          AND sender_id = v_actor_id
          AND recipient_id = p_recipient_id
          AND route_kind = 'HANDOFF'
          AND route_status = 'ACTIVE'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'BUS_HANDOFF_ROUTE_DENIED';
    END IF;

    PERFORM set_config('app.actor_id', v_actor_id, true);
    PERFORM set_config('app.request_id', p_request_id, true);

    INSERT INTO workforce.bus_handoffs (
        handoff_id,
        project_id,
        sender_id,
        recipient_id,
        task_ref,
        handoff_status,
        input_summary,
        expected_output,
        risks_and_assumptions,
        trigger_or_due,
        source_ref
    ) VALUES (
        p_handoff_id,
        p_project_id,
        v_actor_id,
        p_recipient_id,
        p_task_ref,
        p_handoff_status,
        p_input_summary,
        p_expected_output,
        p_risks_and_assumptions,
        p_trigger_or_due,
        p_source_ref
    )
    ON CONFLICT (handoff_id) DO NOTHING
    RETURNING * INTO v_handoff;

    IF v_handoff.handoff_id IS NULL THEN
        SELECT * INTO v_handoff
        FROM workforce.bus_handoffs
        WHERE handoff_id = p_handoff_id;

        IF v_handoff.project_id <> p_project_id
           OR v_handoff.sender_id <> v_actor_id
           OR v_handoff.recipient_id <> p_recipient_id
           OR v_handoff.task_ref IS DISTINCT FROM p_task_ref
           OR v_handoff.handoff_status <> p_handoff_status
           OR v_handoff.input_summary <> p_input_summary
           OR v_handoff.expected_output <> p_expected_output
           OR v_handoff.risks_and_assumptions IS DISTINCT FROM p_risks_and_assumptions
           OR v_handoff.trigger_or_due IS DISTINCT FROM p_trigger_or_due
           OR v_handoff.source_ref <> p_source_ref THEN
            RAISE EXCEPTION USING ERRCODE = '23505', MESSAGE = 'BUS_HANDOFF_IDEMPOTENCY_CONFLICT';
        END IF;
    END IF;

    RETURN v_handoff;
END;
$$;

CREATE FUNCTION workforce.bus_list_handoffs(
    p_token_hash text,
    p_project_id text,
    p_scope text,
    p_limit integer DEFAULT 100
)
RETURNS SETOF workforce.bus_handoffs
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, workforce
AS $$
DECLARE
    v_actor_id text;
    v_read_scope text;
BEGIN
    IF p_scope NOT IN ('INBOX', 'OUTBOX', 'PROJECT') THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'BUS_HANDOFF_READ_SCOPE_INVALID';
    END IF;

    IF p_limit NOT BETWEEN 1 AND 200 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'BUS_READ_LIMIT_INVALID';
    END IF;

    v_actor_id := workforce.bus_authenticate(p_project_id, p_token_hash);

    SELECT read_scope INTO v_read_scope
    FROM workforce.bus_member_capabilities
    WHERE project_id = p_project_id
      AND employee_id = v_actor_id
      AND capability_status = 'ACTIVE';

    IF p_scope = 'PROJECT' AND v_read_scope <> 'PROJECT' THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'BUS_PROJECT_READ_DENIED';
    END IF;

    RETURN QUERY
    SELECT h.*
    FROM workforce.bus_handoffs AS h
    WHERE h.project_id = p_project_id
      AND (
          (p_scope = 'INBOX' AND h.recipient_id = v_actor_id)
          OR (p_scope = 'OUTBOX' AND h.sender_id = v_actor_id)
          OR (p_scope = 'PROJECT' AND v_read_scope = 'PROJECT')
      )
    ORDER BY h.updated_at DESC, h.handoff_id DESC
    LIMIT p_limit;
END;
$$;

CREATE FUNCTION workforce.bus_transition_handoff(
    p_token_hash text,
    p_request_id text,
    p_project_id text,
    p_handoff_id text,
    p_new_status text,
    p_response_note text DEFAULT NULL
)
RETURNS workforce.bus_handoffs
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, workforce
AS $$
DECLARE
    v_actor_id text;
    v_handoff workforce.bus_handoffs%ROWTYPE;
    v_allowed boolean := false;
BEGIN
    IF p_request_id IS NULL OR char_length(p_request_id) NOT BETWEEN 1 AND 128 THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'BUS_REQUEST_ID_REQUIRED';
    END IF;

    v_actor_id := workforce.bus_authenticate(p_project_id, p_token_hash);

    SELECT * INTO v_handoff
    FROM workforce.bus_handoffs
    WHERE project_id = p_project_id
      AND handoff_id = p_handoff_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING ERRCODE = 'P0002', MESSAGE = 'BUS_HANDOFF_NOT_FOUND';
    END IF;

    IF v_handoff.handoff_status = p_new_status THEN
        IF v_handoff.response_note IS DISTINCT FROM p_response_note THEN
            RAISE EXCEPTION USING ERRCODE = '23505', MESSAGE = 'BUS_HANDOFF_IDEMPOTENCY_CONFLICT';
        END IF;
        RETURN v_handoff;
    END IF;

    v_allowed :=
        (v_actor_id = v_handoff.sender_id AND v_handoff.handoff_status = 'PENDING' AND p_new_status IN ('OPEN', 'CANCELLED'))
        OR (v_actor_id = v_handoff.sender_id AND v_handoff.handoff_status = 'OPEN' AND p_new_status = 'CANCELLED')
        OR (v_actor_id = v_handoff.recipient_id AND v_handoff.handoff_status = 'OPEN' AND p_new_status IN ('ACCEPTED', 'REJECTED'));

    IF NOT v_allowed THEN
        RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'BUS_HANDOFF_TRANSITION_DENIED';
    END IF;

    IF p_new_status = 'REJECTED' AND nullif(btrim(p_response_note), '') IS NULL THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'BUS_HANDOFF_REJECTION_REASON_REQUIRED';
    END IF;

    PERFORM set_config('app.actor_id', v_actor_id, true);
    PERFORM set_config('app.request_id', p_request_id, true);

    UPDATE workforce.bus_handoffs
    SET handoff_status = p_new_status,
        response_note = p_response_note,
        accepted_at = CASE WHEN p_new_status = 'ACCEPTED' THEN clock_timestamp() ELSE NULL END,
        rejected_at = CASE WHEN p_new_status = 'REJECTED' THEN clock_timestamp() ELSE NULL END,
        cancelled_at = CASE WHEN p_new_status = 'CANCELLED' THEN clock_timestamp() ELSE NULL END
    WHERE handoff_id = p_handoff_id
    RETURNING * INTO v_handoff;

    RETURN v_handoff;
END;
$$;

CREATE TRIGGER bus_channels_touch_version
BEFORE UPDATE ON workforce.bus_channels
FOR EACH ROW EXECUTE FUNCTION workforce.bus_touch_versioned_row();

CREATE TRIGGER bus_capabilities_touch_version
BEFORE UPDATE ON workforce.bus_member_capabilities
FOR EACH ROW EXECUTE FUNCTION workforce.bus_touch_versioned_row();

CREATE TRIGGER bus_routes_touch_version
BEFORE UPDATE ON workforce.bus_route_allowlist
FOR EACH ROW EXECUTE FUNCTION workforce.bus_touch_versioned_row();

CREATE TRIGGER bus_credentials_touch_version
BEFORE UPDATE ON workforce.bus_credentials
FOR EACH ROW EXECUTE FUNCTION workforce.bus_touch_versioned_row();

CREATE TRIGGER bus_tasks_touch_version
BEFORE UPDATE ON workforce.bus_tasks
FOR EACH ROW EXECUTE FUNCTION workforce.bus_touch_versioned_row();

CREATE TRIGGER bus_handoffs_touch_version
BEFORE UPDATE ON workforce.bus_handoffs
FOR EACH ROW EXECUTE FUNCTION workforce.bus_touch_versioned_row();

CREATE TRIGGER bus_channels_guard_update
BEFORE UPDATE ON workforce.bus_channels
FOR EACH ROW EXECUTE FUNCTION workforce.bus_guard_channel_update();

CREATE TRIGGER bus_capabilities_guard_update
BEFORE UPDATE ON workforce.bus_member_capabilities
FOR EACH ROW EXECUTE FUNCTION workforce.bus_guard_capability_update();

CREATE TRIGGER bus_routes_guard_update
BEFORE UPDATE ON workforce.bus_route_allowlist
FOR EACH ROW EXECUTE FUNCTION workforce.bus_guard_route_update();

CREATE TRIGGER bus_credentials_guard_update
BEFORE UPDATE ON workforce.bus_credentials
FOR EACH ROW EXECUTE FUNCTION workforce.bus_guard_credential_update();

CREATE TRIGGER bus_tasks_guard_update
BEFORE UPDATE ON workforce.bus_tasks
FOR EACH ROW EXECUTE FUNCTION workforce.bus_guard_task_update();

CREATE TRIGGER bus_handoffs_guard_update
BEFORE UPDATE ON workforce.bus_handoffs
FOR EACH ROW EXECUTE FUNCTION workforce.bus_guard_handoff_update();

CREATE TRIGGER bus_messages_guard_update
BEFORE UPDATE ON workforce.bus_messages
FOR EACH ROW EXECUTE FUNCTION workforce.bus_guard_message_update();

CREATE TRIGGER bus_channels_no_hard_delete
BEFORE DELETE ON workforce.bus_channels
FOR EACH ROW EXECUTE FUNCTION workforce.prevent_hard_delete();

CREATE TRIGGER bus_capabilities_no_hard_delete
BEFORE DELETE ON workforce.bus_member_capabilities
FOR EACH ROW EXECUTE FUNCTION workforce.prevent_hard_delete();

CREATE TRIGGER bus_routes_no_hard_delete
BEFORE DELETE ON workforce.bus_route_allowlist
FOR EACH ROW EXECUTE FUNCTION workforce.prevent_hard_delete();

CREATE TRIGGER bus_credentials_no_hard_delete
BEFORE DELETE ON workforce.bus_credentials
FOR EACH ROW EXECUTE FUNCTION workforce.prevent_hard_delete();

CREATE TRIGGER bus_tasks_no_hard_delete
BEFORE DELETE ON workforce.bus_tasks
FOR EACH ROW EXECUTE FUNCTION workforce.prevent_hard_delete();

CREATE TRIGGER bus_handoffs_no_hard_delete
BEFORE DELETE ON workforce.bus_handoffs
FOR EACH ROW EXECUTE FUNCTION workforce.prevent_hard_delete();

CREATE TRIGGER bus_messages_no_hard_delete
BEFORE DELETE ON workforce.bus_messages
FOR EACH ROW EXECUTE FUNCTION workforce.prevent_hard_delete();

CREATE TRIGGER bus_events_append_only
BEFORE UPDATE OR DELETE ON workforce.bus_events
FOR EACH ROW EXECUTE FUNCTION workforce.prevent_bus_event_mutation();

CREATE TRIGGER bus_channels_audit
AFTER INSERT OR UPDATE ON workforce.bus_channels
FOR EACH ROW EXECUTE FUNCTION workforce.bus_record_change();

CREATE TRIGGER bus_capabilities_audit
AFTER INSERT OR UPDATE ON workforce.bus_member_capabilities
FOR EACH ROW EXECUTE FUNCTION workforce.bus_record_change();

CREATE TRIGGER bus_routes_audit
AFTER INSERT OR UPDATE ON workforce.bus_route_allowlist
FOR EACH ROW EXECUTE FUNCTION workforce.bus_record_change();

CREATE TRIGGER bus_credentials_audit
AFTER INSERT OR UPDATE ON workforce.bus_credentials
FOR EACH ROW EXECUTE FUNCTION workforce.bus_record_change();

CREATE TRIGGER bus_tasks_audit
AFTER INSERT OR UPDATE ON workforce.bus_tasks
FOR EACH ROW EXECUTE FUNCTION workforce.bus_record_change();

CREATE TRIGGER bus_handoffs_audit
AFTER INSERT OR UPDATE ON workforce.bus_handoffs
FOR EACH ROW EXECUTE FUNCTION workforce.bus_record_change();

CREATE TRIGGER bus_messages_audit
AFTER INSERT OR UPDATE ON workforce.bus_messages
FOR EACH ROW EXECUTE FUNCTION workforce.bus_record_change();

INSERT INTO workforce.bus_channels (
    project_id,
    channel_status,
    max_hops,
    max_body_chars,
    source_ref
) VALUES (
    'START-UP',
    'DISABLED',
    4,
    8000,
    'DEC-016/ENG-003'
);

INSERT INTO workforce.bus_member_capabilities (
    project_id,
    employee_id,
    read_scope,
    task_authority,
    can_send,
    can_create_handoff,
    source_ref
)
SELECT
    'START-UP',
    employee_id,
    CASE WHEN employee_id IN ('SAO-001', 'EAC-001') THEN 'PROJECT' ELSE 'PARTICIPANT' END,
    CASE WHEN employee_id = 'SAO-001' THEN 'COORDINATE' ELSE 'PROPOSE' END,
    true,
    true,
    CASE
        WHEN employee_id IN ('SAO-001', 'EAC-001') THEN 'DEC-016'
        ELSE 'DEC-015'
    END
FROM workforce.active_project_members
WHERE project_id = 'START-UP'
  AND employee_id IN ('AI-ENG-001', 'RAS-001', 'PEO-001', 'SAO-001', 'EAC-001');

INSERT INTO workforce.bus_route_allowlist (
    route_id,
    project_id,
    sender_id,
    recipient_id,
    route_kind,
    source_ref
)
SELECT
    'ROUTE-' || replace(sender.employee_id, '-', '') || '-' || replace(recipient.employee_id, '-', '') || '-' || kind.route_kind,
    'START-UP',
    sender.employee_id,
    recipient.employee_id,
    kind.route_kind,
    CASE
        WHEN sender.employee_id IN ('SAO-001', 'EAC-001')
          OR recipient.employee_id IN ('SAO-001', 'EAC-001') THEN 'DEC-016'
        ELSE 'DEC-015'
    END
FROM workforce.active_project_members AS sender
CROSS JOIN workforce.active_project_members AS recipient
CROSS JOIN (VALUES ('MESSAGE'), ('TASK'), ('HANDOFF')) AS kind(route_kind)
WHERE sender.project_id = 'START-UP'
  AND recipient.project_id = 'START-UP'
  AND sender.employee_id IN ('AI-ENG-001', 'RAS-001', 'PEO-001', 'SAO-001', 'EAC-001')
  AND recipient.employee_id IN ('AI-ENG-001', 'RAS-001', 'PEO-001', 'SAO-001', 'EAC-001')
  AND sender.employee_id <> recipient.employee_id;

INSERT INTO workforce.schema_migrations (
    migration_id,
    description
) VALUES (
    '002_workforce_bus',
    'Project-scoped message, task and handoff bus with allowlists, acknowledgement, audit, revocation and loop protection'
);

COMMIT;
