\set ON_ERROR_STOP on

-- Grants the API execute rights on the knowledge functions, by name.
--
-- Why a separate migration (review finding G-035): 007 removed the blanket
-- default grant, so functions from later migrations arrive with no rights at
-- all - which is correct, but means the knowledge functions need an explicit
-- decision. `004_knowledge_capability` comes from the authoritative source set
-- and is not edited here (see the canonical boundary in CLAUDE.md), so the
-- grant lives in an additive follow-up instead.
--
-- Applies only together with the knowledge gate. Without 004 there is nothing
-- to grant, and without the role there is nobody to grant to; both are
-- checked rather than assumed.

BEGIN;

SELECT set_config('app.actor_id', 'SYSTEM-MIGRATION', true);
SELECT set_config('app.request_id', 'MIG-008-KNOWLEDGE-API-GRANTS', true);

DO $$
DECLARE
    v_name text;
    v_signature text;
    v_granted integer := 0;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM workforce.schema_migrations
                   WHERE migration_id = '004_knowledge_capability') THEN
        RAISE EXCEPTION 'MIGRATION_008_REQUIRES_004: die Knowledge-Migration ist nicht angewendet';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'workforce_api') THEN
        RAISE EXCEPTION 'MIGRATION_008_ROLE_MISSING: workforce_api fehlt, 007 zuerst anwenden';
    END IF;

    -- Named, not wholesale. Every entry here is a function the API actually
    -- calls; anything else the knowledge migration created stays out of reach.
    FOREACH v_name IN ARRAY ARRAY[
        'knowledge_create_candidate', 'knowledge_submit_review',
        'knowledge_approve', 'knowledge_revoke', 'knowledge_retrieve',
        'knowledge_record_assessment'
    ] LOOP
        FOR v_signature IN
            SELECT format('workforce.%I(%s)', p.proname,
                          pg_get_function_identity_arguments(p.oid))
            FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'workforce' AND p.proname = v_name
        LOOP
            EXECUTE format('REVOKE EXECUTE ON FUNCTION %s FROM PUBLIC', v_signature);
            EXECUTE format('GRANT EXECUTE ON FUNCTION %s TO workforce_api', v_signature);
            v_granted := v_granted + 1;
        END LOOP;
    END LOOP;

    IF v_granted = 0 THEN
        RAISE EXCEPTION 'MIGRATION_008_NOTHING_GRANTED: keine Knowledge-Funktion gefunden';
    END IF;
    RAISE NOTICE 'workforce_api: EXECUTE auf % Knowledge-Funktion(en) erteilt', v_granted;
END;
$$;

INSERT INTO workforce.schema_migrations (
    migration_id,
    description
) VALUES (
    '008_knowledge_api_grants',
    'Grants the API named execute rights on the knowledge functions; no blanket default grant'
);

COMMIT;
