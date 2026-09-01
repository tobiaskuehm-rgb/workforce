\set ON_ERROR_STOP on

-- Durable record of *refused* API operations - bus and knowledge alike.
--
-- Numbered 005, not 004: the authoritative source set already had a
-- 004_knowledge_capability, and two different migrations under one number
-- would have been two competing technical truths (review finding G-021).
--
-- Review finding G-018: workforce.bus_events only ever holds successful INSERT
-- and UPDATE events, because a refused call raises and its transaction rolls
-- back - taking any audit row written inside it along. So the reconstruction
-- of a run could show what worked and never what was correctly denied. The
-- negative half of every acceptance test lived only in stdout and in
-- hand-written markdown, both of which disappear when the container does.
--
-- A rolled-back transaction cannot write its own audit row. The write
-- therefore happens one layer up, in workforce-api, on a fresh connection
-- after the failure - which is why this is a function called by the API and
-- not a trigger.
--
-- What may be stored is deliberately narrow: identities, identifiers, the
-- stable error code and the HTTP status. No message subject, no body, no note,
-- no token. The CHECK constraints below enforce that rather than asking for
-- it: an error code has to look like an error code, and a record key is capped
-- at the length of an identifier.

BEGIN;

SELECT set_config('app.actor_id', 'SYSTEM-MIGRATION', true);
SELECT set_config('app.request_id', 'MIG-005-BUS-DENIAL-AUDIT', true);

CREATE TABLE workforce.bus_denials (
    denial_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id text NOT NULL,
    -- Resolved from the credential, or 'UNKNOWN' when the token matches
    -- nothing. The token hash itself is never stored.
    actor_id text NOT NULL,
    operation text NOT NULL,
    record_type text NOT NULL,
    record_key text,
    error_code text NOT NULL,
    http_status integer NOT NULL,
    request_id text NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT bus_denials_actor_present
        CHECK (char_length(actor_id) BETWEEN 1 AND 128),
    CONSTRAINT bus_denials_operation_shape
        CHECK (operation ~ '^[A-Z0-9_]{1,64}$'),
    -- KNOWLEDGE is here because the denial log covers the whole API, not just
    -- the bus: the knowledge endpoints go through the same execute_bus_one and
    -- therefore through the same audit hook (review finding G-021 merged the
    -- two lineages, so there is one API and one audit path).
    CONSTRAINT bus_denials_record_type
        CHECK (record_type IN ('TASK', 'HANDOFF', 'MESSAGE', 'CHANNEL',
                               'KNOWLEDGE', 'UNKNOWN')),
    -- An identifier, never content. A body would not survive either test.
    CONSTRAINT bus_denials_record_key_shape
        CHECK (record_key IS NULL OR char_length(record_key) BETWEEN 1 AND 128),
    CONSTRAINT bus_denials_error_code_shape
        CHECK (error_code ~ '^[A-Z0-9_]{1,64}$'),
    CONSTRAINT bus_denials_http_status_range
        CHECK (http_status BETWEEN 100 AND 599),
    CONSTRAINT bus_denials_request_present
        CHECK (char_length(request_id) BETWEEN 1 AND 128)
);

CREATE INDEX bus_denials_run_idx
    ON workforce.bus_denials (project_id, request_id);

CREATE INDEX bus_denials_actor_idx
    ON workforce.bus_denials (project_id, actor_id, occurred_at DESC);

CREATE FUNCTION workforce.prevent_bus_denial_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION USING
        ERRCODE = '55000',
        MESSAGE = 'Workforce bus denials are append-only.';
END;
$$;

CREATE TRIGGER bus_denials_append_only
BEFORE UPDATE OR DELETE ON workforce.bus_denials
FOR EACH ROW EXECUTE FUNCTION workforce.prevent_bus_denial_mutation();

-- Resolves an identity for the audit trail without gating on it. Unlike
-- bus_authenticate this must not raise and must not care whether the
-- credential is still active: a call refused *because* the credential was
-- revoked is exactly the kind of event this table exists to keep.
CREATE FUNCTION workforce.bus_identify_for_audit(
    p_project_id text,
    p_token_hash text
)
RETURNS text
LANGUAGE sql
SECURITY DEFINER
SET search_path = pg_catalog, workforce
AS $$
    SELECT coalesce(
        (SELECT c.employee_id
         FROM workforce.bus_credentials AS c
         WHERE c.project_id = p_project_id
           AND c.token_hash = p_token_hash
         ORDER BY c.issued_at DESC
         LIMIT 1),
        'UNKNOWN'
    );
$$;

CREATE FUNCTION workforce.bus_record_denial(
    p_project_id text,
    p_token_hash text,
    p_request_id text,
    p_operation text,
    p_record_type text,
    p_record_key text,
    p_error_code text,
    p_http_status integer
)
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, workforce
AS $$
DECLARE
    v_denial_id bigint;
BEGIN
    INSERT INTO workforce.bus_denials (
        project_id, actor_id, operation, record_type, record_key,
        error_code, http_status, request_id
    ) VALUES (
        p_project_id,
        workforce.bus_identify_for_audit(p_project_id, p_token_hash),
        p_operation,
        p_record_type,
        nullif(btrim(coalesce(p_record_key, '')), ''),
        p_error_code,
        p_http_status,
        p_request_id
    )
    RETURNING denial_id INTO v_denial_id;

    RETURN v_denial_id;
END;
$$;

-- The API calls this function, so it needs EXECUTE by name. Conditional
-- because the gates are independent: this migration may run before 007 has
-- created the role, and it must not fail for that (review finding G-035).
-- 007 grants what already exists; this covers the other order.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'workforce_api') THEN
        REVOKE EXECUTE ON FUNCTION workforce.bus_record_denial(
            text, text, text, text, text, text, text, integer) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION workforce.bus_record_denial(
            text, text, text, text, text, text, text, integer) TO workforce_api;
        RAISE NOTICE 'workforce_api: EXECUTE auf bus_record_denial erteilt';
    ELSE
        RAISE NOTICE 'workforce_api existiert noch nicht - Grant folgt aus 007';
    END IF;
END;
$$;

INSERT INTO workforce.schema_migrations (
    migration_id,
    description
) VALUES (
    '005_bus_denial_audit',
    'Append-only record of refused bus operations; identifiers and error codes only'
);

COMMIT;
