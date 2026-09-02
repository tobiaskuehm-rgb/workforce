\set ON_ERROR_STOP on

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM workforce.schema_migrations
        WHERE migration_id = '004_knowledge_capability'
    ) THEN
        RAISE EXCEPTION 'Migration 004_knowledge_capability is missing.';
    END IF;

    IF EXISTS (SELECT 1 FROM workforce.knowledge_credentials) THEN
        RAISE EXCEPTION 'Migration must not seed Knowledge credentials.';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.knowledge_systems
        WHERE project_id = 'START-UP' AND system_status = 'DISABLED'
    ) THEN
        RAISE EXCEPTION 'Knowledge system must remain DISABLED after migration.';
    END IF;

    IF EXISTS (SELECT 1 FROM workforce.knowledge_member_permissions) THEN
        RAISE EXCEPTION 'Migration must not seed Knowledge member permissions.';
    END IF;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-ACCEPTANCE', true);
SELECT set_config('app.request_id', 'TEST-KNOWLEDGE-SETUP', true);

UPDATE workforce.knowledge_systems
SET system_status = 'TESTING'
WHERE project_id = 'START-UP';

INSERT INTO workforce.knowledge_member_permissions (
    project_id, employee_id, can_create_candidate, can_review_owned,
    can_assess, can_manage_role_packs, source_ref
)
SELECT
    member.project_id,
    member.employee_id,
    true,
    true,
    false,
    false,
    'ENG-004-ACCEPTANCE-ONLY'
FROM workforce.active_project_members AS member
WHERE member.project_id = 'START-UP'
  AND member.employee_id IN ('AI-ENG-001', 'RAS-001', 'PEO-001', 'SAO-001', 'EAC-001');

UPDATE workforce.knowledge_member_permissions
SET can_assess = true
WHERE project_id = 'START-UP'
  AND employee_id = 'PEO-001';

INSERT INTO workforce.knowledge_credentials (
    credential_id, project_id, employee_id, token_hash,
    credential_scope, source_ref, expires_at
) VALUES
    ('KCRED-ACCEPT-KARL-KC1', 'START-UP', 'SAO-001', repeat('a', 64),
        'ACCEPTANCE', 'ENG-004-TEST', clock_timestamp() + interval '1 hour'),
    ('KCRED-ACCEPT-GERD-KC1', 'START-UP', 'AI-ENG-001', repeat('b', 64),
        'ACCEPTANCE', 'ENG-004-TEST', clock_timestamp() + interval '1 hour'),
    ('KCRED-ACCEPT-THORSTEN-KC1', 'START-UP', 'RAS-001', repeat('c', 64),
        'ACCEPTANCE', 'ENG-004-TEST', clock_timestamp() + interval '1 hour'),
    ('KCRED-ACCEPT-ANASTASIA-KC1', 'START-UP', 'PEO-001', repeat('d', 64),
        'ACCEPTANCE', 'ENG-004-TEST', clock_timestamp() + interval '1 hour'),
    ('KCRED-ACCEPT-NORA-KC1', 'START-UP', 'EAC-001', repeat('e', 64),
        'ACCEPTANCE', 'ENG-004-TEST', clock_timestamp() + interval '1 hour');

-- Test 1: only explicitly reviewed and approved company knowledge is retrievable.
DO $$
DECLARE
    v_object workforce.knowledge_objects%ROWTYPE;
    v_count integer;
BEGIN
    v_object := workforce.knowledge_create_candidate(
        repeat('b', 64),
        'REQ-KC-RULE-V1-CREATE',
        'START-UP',
        'KN-COMPANY-RULE-001',
        'Aktuelle Unternehmensregel',
        'K1',
        'Company Core',
        'SAO-001',
        'PROJECT_INTERNAL',
        'DEC-015',
        clock_timestamp() - interval '1 minute',
        clock_timestamp() + interval '30 days',
        clock_timestamp() + interval '60 days',
        ARRAY['Unternehmensregel', 'Freigabe'],
        'Aktuelle Unternehmensregel v1: Externe Aktionen benötigen Human Approval.',
        '[{"kind":"PROJECT","value":"START-UP"}]'::jsonb
    );

    IF v_object.knowledge_status <> 'DRAFT' OR v_object.version <> 1 THEN
        RAISE EXCEPTION 'Knowledge candidate was not created as DRAFT v1.';
    END IF;

    v_object := workforce.knowledge_submit_review(
        repeat('b', 64), 'REQ-KC-RULE-V1-REVIEW',
        'START-UP', 'KN-COMPANY-RULE-001', 1
    );
    IF v_object.knowledge_status <> 'REVIEW' THEN
        RAISE EXCEPTION 'Knowledge v1 did not enter REVIEW.';
    END IF;

    v_object := workforce.knowledge_approve(
        repeat('a', 64), 'REQ-KC-RULE-V1-APPROVE',
        'START-UP', 'KN-COMPANY-RULE-001', 1
    );
    IF v_object.knowledge_status <> 'APPROVED'
       OR v_object.approved_by <> 'SAO-001'
       OR v_object.content_hash <> encode(digest(v_object.content, 'sha256'), 'hex') THEN
        RAISE EXCEPTION 'Knowledge v1 approval or content hash is inconsistent.';
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.knowledge_retrieve(
        repeat('a', 64), 'KRUN-KARL-RULE-V1', 'START-UP',
        'Aktuelle Unternehmensregel', 'Company Core', 'GENERAL', 'ENG-004', 5
    )
    WHERE knowledge_id = 'KN-COMPANY-RULE-001'
      AND version = 1
      AND content_hash = encode(digest(content, 'sha256'), 'hex');

    IF v_count <> 1 THEN
        RAISE EXCEPTION 'Karl did not receive exactly approved company Knowledge v1.';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.knowledge_context_items
        WHERE run_id = 'KRUN-KARL-RULE-V1'
          AND knowledge_id = 'KN-COMPANY-RULE-001'
          AND version = 1
          AND chunk_ref = 'FULL'
    ) THEN
        RAISE EXCEPTION 'Context manifest for Knowledge v1 is missing.';
    END IF;
END;
$$;

-- Test 2: approval of v2 supersedes v1 and normal retrieval returns only v2.
DO $$
DECLARE
    v_object workforce.knowledge_objects%ROWTYPE;
    v_count integer;
BEGIN
    v_object := workforce.knowledge_create_candidate(
        repeat('b', 64), 'REQ-KC-RULE-V2-CREATE', 'START-UP',
        'KN-COMPANY-RULE-001', 'Aktuelle Unternehmensregel', 'K1', 'Company Core',
        'SAO-001', 'PROJECT_INTERNAL', 'DEC-015/Revision-2',
        clock_timestamp() - interval '1 minute',
        clock_timestamp() + interval '30 days',
        clock_timestamp() + interval '60 days',
        ARRAY['Unternehmensregel', 'Freigabe'],
        'Aktuelle Unternehmensregel v2: Externe und privilegierte Aktionen benötigen spezifisches Human Approval.',
        '[{"kind":"PROJECT","value":"START-UP"}]'::jsonb
    );

    PERFORM workforce.knowledge_submit_review(
        repeat('b', 64), 'REQ-KC-RULE-V2-REVIEW',
        'START-UP', 'KN-COMPANY-RULE-001', 2
    );
    v_object := workforce.knowledge_approve(
        repeat('a', 64), 'REQ-KC-RULE-V2-APPROVE',
        'START-UP', 'KN-COMPANY-RULE-001', 2
    );

    IF v_object.knowledge_status <> 'APPROVED' OR v_object.supersedes_version <> 1 THEN
        RAISE EXCEPTION 'Knowledge v2 did not supersede v1.';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.knowledge_objects
        WHERE knowledge_id = 'KN-COMPANY-RULE-001'
          AND version = 1 AND knowledge_status = 'SUPERSEDED'
    ) THEN
        RAISE EXCEPTION 'Knowledge v1 was not marked SUPERSEDED.';
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.knowledge_retrieve(
        repeat('a', 64), 'KRUN-KARL-RULE-V2', 'START-UP',
        'Aktuelle Unternehmensregel', 'Company Core', 'GENERAL', 'ENG-004', 5
    )
    WHERE knowledge_id = 'KN-COMPANY-RULE-001' AND version = 2;
    IF v_count <> 1 THEN
        RAISE EXCEPTION 'Normal retrieval did not return Knowledge v2.';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.knowledge_context_items
        WHERE run_id = 'KRUN-KARL-RULE-V2'
          AND knowledge_id = 'KN-COMPANY-RULE-001'
          AND version = 1
    ) THEN
        RAISE EXCEPTION 'SUPERSEDED Knowledge v1 reached the context manifest.';
    END IF;
END;
$$;

-- Test 3: a research candidate in REVIEW is not company truth and self-publishing fails.
DO $$
DECLARE
    v_count integer;
BEGIN
    PERFORM workforce.knowledge_create_candidate(
        repeat('c', 64), 'REQ-KC-WTP-CREATE', 'START-UP',
        'KN-RESEARCH-WTP-001', 'Research-Hypothese Zahlungsbereitschaft',
        'K4', 'Research & Strategy', 'RAS-001', 'PROJECT_INTERNAL',
        'RAS-001/Hypothese', clock_timestamp() - interval '1 minute',
        clock_timestamp() + interval '7 days', clock_timestamp() + interval '14 days',
        ARRAY['Research', 'Hypothese'],
        'Kunden zahlen wahrscheinlich X. Diese Aussage ist ungeprüft.',
        '[{"kind":"PROJECT","value":"START-UP"}]'::jsonb
    );
    PERFORM workforce.knowledge_submit_review(
        repeat('c', 64), 'REQ-KC-WTP-REVIEW',
        'START-UP', 'KN-RESEARCH-WTP-001', 1
    );

    BEGIN
        PERFORM workforce.knowledge_approve(
            repeat('c', 64), 'REQ-KC-WTP-SELF-APPROVE',
            'START-UP', 'KN-RESEARCH-WTP-001', 1
        );
        RAISE EXCEPTION 'Research owner self-published a candidate.';
    EXCEPTION
        WHEN insufficient_privilege THEN
            IF SQLERRM <> 'KNOWLEDGE_SELF_PUBLISH_DENIED' THEN RAISE; END IF;
    END;

    SELECT count(*) INTO v_count
    FROM workforce.knowledge_retrieve(
        repeat('a', 64), 'KRUN-KARL-WTP-DRAFT', 'START-UP',
        'Kunden zahlen wahrscheinlich X', NULL, 'GENERAL', 'ENG-004', 5
    );
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'DRAFT/REVIEW Research leaked as approved company Knowledge.';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.knowledge_context_items
        WHERE run_id = 'KRUN-KARL-WTP-DRAFT'
          AND knowledge_id = 'KN-RESEARCH-WTP-001'
    ) THEN
        RAISE EXCEPTION 'Research candidate reached the context manifest.';
    END IF;
END;
$$;

-- Test 4: permission filtering precedes ranking and context creation.
DO $$
DECLARE
    v_count integer;
BEGIN
    PERFORM workforce.knowledge_create_candidate(
        repeat('b', 64), 'REQ-KC-PEO-CREATE', 'START-UP',
        'KN-PEO-CONFIDENTIAL-001', 'Vertrauliche Probezeitbewertung',
        'K2', 'People & Organization', 'PEO-001', 'NEED_TO_KNOW',
        'PEO-001/Assessment', clock_timestamp() - interval '1 minute',
        clock_timestamp() + interval '30 days', clock_timestamp() + interval '60 days',
        ARRAY['Probezeitbewertung', 'vertraulich'],
        'Probezeitbewertung vertraulich: nur People & Organization.',
        '[{"kind":"ROLE","value":"PEOPLE_ORGANIZATION"}]'::jsonb
    );
    PERFORM workforce.knowledge_submit_review(
        repeat('b', 64), 'REQ-KC-PEO-REVIEW',
        'START-UP', 'KN-PEO-CONFIDENTIAL-001', 1
    );
    PERFORM workforce.knowledge_approve(
        repeat('d', 64), 'REQ-KC-PEO-APPROVE',
        'START-UP', 'KN-PEO-CONFIDENTIAL-001', 1
    );

    -- Even a role-pack entry cannot turn relevance into permission.
    PERFORM set_config('app.actor_id', 'SYSTEM-ACCEPTANCE', true);
    PERFORM set_config('app.request_id', 'TEST-KC-ROLE-PACK-NONTRANSITIVE', true);
    INSERT INTO workforce.knowledge_role_pack_entries (
        project_id, employee_id, knowledge_id, source_ref
    ) VALUES ('START-UP', 'AI-ENG-001', 'KN-PEO-CONFIDENTIAL-001', 'ENG-004-TEST');

    SELECT count(*) INTO v_count
    FROM workforce.knowledge_retrieve(
        repeat('a', 64), 'KRUN-KARL-PEO-DENIED', 'START-UP',
        'Probezeitbewertung vertraulich', 'People & Organization', 'GENERAL', 'ENG-004', 5
    );
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'Karl received Knowledge outside his audience.';
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.knowledge_retrieve(
        repeat('b', 64), 'KRUN-GERD-PEO-DENIED', 'START-UP',
        'Probezeitbewertung vertraulich', 'People & Organization', 'ROLE_PACK', 'ENG-004', 5
    );
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'Role Pack improperly granted Gerd P&O permission.';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.knowledge_context_items
        WHERE run_id IN ('KRUN-KARL-PEO-DENIED', 'KRUN-GERD-PEO-DENIED')
          AND knowledge_id = 'KN-PEO-CONFIDENTIAL-001'
    ) THEN
        RAISE EXCEPTION 'Unauthorized P&O content reached ranking/context output.';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.knowledge_retrieval_runs
        WHERE run_id IN ('KRUN-KARL-PEO-DENIED', 'KRUN-GERD-PEO-DENIED')
          AND eligible_count <> 0
    ) THEN
        RAISE EXCEPTION 'Unauthorized P&O content was counted as eligible before ranking.';
    END IF;
END;
$$;

-- Test 5: a Gerd role-pack request receives only permitted Engineering knowledge.
DO $$
DECLARE
    v_count integer;
BEGIN
    PERFORM workforce.knowledge_create_candidate(
        repeat('c', 64), 'REQ-KC-ENG-CREATE', 'START-UP',
        'KN-ENGINEERING-TLS-001', 'TLS Reverse Proxy Playbook',
        'K3', 'AI Engineering', 'AI-ENG-001', 'NEED_TO_KNOW',
        'ENG-004/Playbook', clock_timestamp() - interval '1 minute',
        clock_timestamp() + interval '30 days', clock_timestamp() + interval '60 days',
        ARRAY['TLS', 'Reverse Proxy', 'Engineering'],
        'TLS Reverse Proxy Engineering Playbook: geschützte Endpunkte nur über HTTPS.',
        '[{"kind":"ROLE","value":"AI_ENGINEERING"}]'::jsonb
    );
    PERFORM workforce.knowledge_submit_review(
        repeat('c', 64), 'REQ-KC-ENG-REVIEW',
        'START-UP', 'KN-ENGINEERING-TLS-001', 1
    );
    PERFORM workforce.knowledge_approve(
        repeat('b', 64), 'REQ-KC-ENG-APPROVE',
        'START-UP', 'KN-ENGINEERING-TLS-001', 1
    );

    PERFORM set_config('app.actor_id', 'SYSTEM-ACCEPTANCE', true);
    PERFORM set_config('app.request_id', 'TEST-KC-ROLE-PACK-GERD', true);
    INSERT INTO workforce.knowledge_role_pack_entries (
        project_id, employee_id, knowledge_id, source_ref
    ) VALUES ('START-UP', 'AI-ENG-001', 'KN-ENGINEERING-TLS-001', 'ENG-004-TEST');

    SELECT count(*) INTO v_count
    FROM workforce.knowledge_retrieve(
        repeat('b', 64), 'KRUN-GERD-ENGINEERING', 'START-UP',
        'TLS Reverse Proxy Engineering', NULL, 'ROLE_PACK', 'ENG-004', 5
    )
    WHERE knowledge_id = 'KN-ENGINEERING-TLS-001'
      AND knowledge_class = 'K3'
      AND domain = 'AI Engineering';

    IF v_count <> 1 THEN
        RAISE EXCEPTION 'Gerd role pack did not return the permitted Engineering playbook.';
    END IF;

    IF EXISTS (
        SELECT 1 FROM workforce.knowledge_context_items
        WHERE run_id = 'KRUN-GERD-ENGINEERING'
          AND knowledge_id = 'KN-PEO-CONFIDENTIAL-001'
    ) THEN
        RAISE EXCEPTION 'Gerd role pack loaded unnecessary/unauthorized P&O Knowledge.';
    END IF;
END;
$$;

-- STALE is a computed actuality state; stale APPROVED content is excluded normally.
DO $$
DECLARE
    v_count integer;
BEGIN
    PERFORM workforce.knowledge_create_candidate(
        repeat('c', 64), 'REQ-KC-STALE-CREATE', 'START-UP',
        'KN-STALE-EXAMPLE-001', 'Veraltete Betriebsregel',
        'K3', 'AI Engineering', 'AI-ENG-001', 'NEED_TO_KNOW',
        'ENG-004/Stale-Test', clock_timestamp() - interval '2 days',
        clock_timestamp() - interval '12 hours', clock_timestamp() - interval '1 day',
        ARRAY['veraltet'], 'Veraltete Betriebsregel darf nicht regulär verwendet werden.',
        '[{"kind":"ROLE","value":"AI_ENGINEERING"}]'::jsonb
    );
    PERFORM workforce.knowledge_submit_review(
        repeat('c', 64), 'REQ-KC-STALE-REVIEW',
        'START-UP', 'KN-STALE-EXAMPLE-001', 1
    );
    PERFORM workforce.knowledge_approve(
        repeat('b', 64), 'REQ-KC-STALE-APPROVE',
        'START-UP', 'KN-STALE-EXAMPLE-001', 1
    );
    IF NOT EXISTS (
        SELECT 1 FROM workforce.knowledge_object_states
        WHERE knowledge_id = 'KN-STALE-EXAMPLE-001'
          AND version = 1
          AND knowledge_status = 'APPROVED'
          AND actuality_status = 'STALE'
    ) THEN
        RAISE EXCEPTION 'STALE actuality marker is missing.';
    END IF;
    SELECT count(*) INTO v_count
    FROM workforce.knowledge_retrieve(
        repeat('b', 64), 'KRUN-GERD-STALE', 'START-UP',
        'Veraltete Betriebsregel', 'AI Engineering', 'GENERAL', 'ENG-004', 5
    );
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'Non-current Knowledge was retrieved.';
    END IF;
END;
$$;

-- Test 6: assessment, error class, training action, capability record and retest persist.
DO $$
DECLARE
    v_record workforce.capability_records%ROWTYPE;
BEGIN
    PERFORM set_config('app.actor_id', 'SYSTEM-ACCEPTANCE', true);
    PERFORM set_config('app.request_id', 'TEST-KC-CAPABILITY-DEFINITION', true);
    INSERT INTO workforce.capability_definitions (
        capability_id, project_id, title, description, owner_id, source_ref
    ) VALUES (
        'CAP-KNOWLEDGE-APPLICATION', 'START-UP', 'Knowledge anwenden',
        'Freigegebenes Wissen korrekt abrufen, belegen und anwenden.',
        'PEO-001', 'PEO-KCS-v1'
    );

    v_record := workforce.knowledge_record_assessment(
        repeat('d', 64), 'REQ-KC-ASMT-001', 'START-UP',
        'ASMT-KARL-KC-001', 'SAO-001', 'CAP-KNOWLEDGE-APPLICATION',
        2, 4, 'E2', 'Abruf war unvollständig.',
        'Permission-first Retrieval und Quellenmanifest wiederholen.',
        'KRUN-KARL-RULE-V2', NULL, NULL
    );

    IF v_record.current_level <> 2 OR v_record.target_level <> 4
       OR v_record.latest_assessment_id <> 'ASMT-KARL-KC-001' THEN
        RAISE EXCEPTION 'Initial capability record is inconsistent.';
    END IF;

    v_record := workforce.knowledge_record_assessment(
        repeat('d', 64), 'REQ-KC-ASMT-RETEST-001', 'START-UP',
        'ASMT-KARL-KC-RETEST-001', 'SAO-001', 'CAP-KNOWLEDGE-APPLICATION',
        3, 4, 'E3', 'Standardfall jetzt zuverlässig.',
        'Komplexen Need-to-know-Fall trainieren.',
        'KRUN-KARL-RULE-V2', 'ASMT-KARL-KC-001', 'BESTANDEN_LEVEL_3'
    );

    IF v_record.current_level <> 3
       OR v_record.latest_assessment_id <> 'ASMT-KARL-KC-RETEST-001'
       OR cardinality(v_record.evidence_assessment_refs) <> 2 THEN
        RAISE EXCEPTION 'Retest did not update the capability record correctly.';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.training_assessments
        WHERE assessment_id = 'ASMT-KARL-KC-RETEST-001'
          AND retest_of = 'ASMT-KARL-KC-001'
          AND error_class = 'E3'
          AND context_run_id = 'KRUN-KARL-RULE-V2'
    ) THEN
        RAISE EXCEPTION 'Retest linkage or context version reference is missing.';
    END IF;
END;
$$;

-- Audit, redaction, kill switch and hard-delete boundaries.
DO $$
DECLARE
    v_count integer;
BEGIN
    SELECT count(*) INTO v_count
    FROM workforce.knowledge_events
    WHERE actor_id = 'SYSTEM-UNATTRIBUTED'
       OR request_id = 'REQUEST-UNATTRIBUTED';
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'Knowledge audit contains unattributed events.';
    END IF;

    SELECT count(*) INTO v_count
    FROM workforce.knowledge_events
    WHERE record_type = 'CREDENTIAL'
      AND (
          COALESCE(old_record, '{}'::jsonb) ? 'token_hash'
          OR COALESCE(new_record, '{}'::jsonb) ? 'token_hash'
      );
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'Knowledge credential hashes leaked into general audit.';
    END IF;

    BEGIN
        DELETE FROM workforce.knowledge_objects
        WHERE knowledge_id = 'KN-COMPANY-RULE-001' AND version = 1;
        RAISE EXCEPTION 'Knowledge hard delete was accepted.';
    EXCEPTION
        WHEN object_not_in_prerequisite_state THEN
            IF SQLERRM <> 'KNOWLEDGE_HARD_DELETE_DENIED' THEN RAISE; END IF;
    END;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-ACCEPTANCE', true);
SELECT set_config('app.request_id', 'TEST-KC-KILL-SWITCH', true);
UPDATE workforce.knowledge_systems
SET system_status = 'DISABLED'
WHERE project_id = 'START-UP';

DO $$
BEGIN
    BEGIN
        PERFORM * FROM workforce.knowledge_retrieve(
            repeat('a', 64), 'KRUN-KARL-AFTER-KILL', 'START-UP',
            'Aktuelle Unternehmensregel', NULL, 'GENERAL', 'ENG-004', 5
        );
        RAISE EXCEPTION 'Knowledge kill switch was bypassed.';
    EXCEPTION
        WHEN insufficient_privilege THEN
            IF SQLERRM <> 'KNOWLEDGE_AUTH_FAILED' THEN RAISE; END IF;
    END;
END;
$$;

SELECT 'PASS: Knowledge lifecycle, versioning, draft protection, permission-first retrieval, context manifest, non-transitive role packs, assessment, capability, retest, audit and kill switch' AS acceptance_result;

ROLLBACK;
