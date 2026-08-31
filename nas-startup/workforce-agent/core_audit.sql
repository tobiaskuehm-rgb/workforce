\set ON_ERROR_STOP on

-- Audit reconstruction for one core roundtrip. Required output of ENG-008
-- ("Neustart-/Persistenz- und Audit-Rekonstruktionsnachweis") and the answer
-- to review findings G-009 and G-018.
--
-- The point is what remains *after* the run: containers removed, stdout gone,
-- credentials revoked. If the sequence cannot be rebuilt from the database
-- alone, then the markdown evidence is a claim rather than a proof.
--
-- Two halves, reported apart (G-018):
--
--   POSITIV  from workforce.bus_events - what happened, bound to exact record
--            ids, actors, references and order. The earlier version asked only
--            whether *some* record of the right type carried the right actor,
--            which a foreign task from another run would also have satisfied.
--
--   NEGATIV  from workforce.bus_denials - what was correctly refused.
--            bus_events cannot hold this: a refused call rolls its transaction
--            back and takes any audit row with it. Before migration 004 the
--            three required refusals survived only in stdout and in
--            hand-written markdown.
--
-- Read-only by construction: BEGIN TRANSACTION READ ONLY and ROLLBACK, so it
-- can be run against production at any time.
--
-- Every write in core_roundtrip.py carries a request id of the form
-- CORE-<run_id>-<phase>, which is what makes this reconstruction possible.

BEGIN TRANSACTION READ ONLY;

SELECT set_config('core.run_id', :'run_id', false);
SELECT set_config('core.project_id', 'START-UP', false);
SELECT set_config('core.task_id', 'ENG-CORE-' || :'run_id', false);
SELECT set_config('core.handoff_id', 'HO-CORE-' || :'run_id', false);
SELECT set_config('core.reject_id', 'HO-CORE-' || :'run_id' || '-REJ', false);

\echo '=== Voraussetzung: Ablehnungsprotokoll vorhanden ==='

-- Fails loudly rather than reporting an empty negative audit as a pass.
-- Says plainly what is missing. The negative audit further down then fails
-- hard on the absent table rather than reporting an empty result as a pass -
-- ON_ERROR_STOP turns that into a non-zero exit.
SELECT CASE
    WHEN to_regclass('workforce.bus_denials') IS NULL
        THEN 'FEHLT - Migration 004_bus_denial_audit anwenden'
    ELSE 'vorhanden'
END AS bus_denials;

\echo ''
\echo '=== 1. Rekonstruierte Abfolge: erfolgreiche Vorgaenge ==='

SELECT
    row_number() OVER (ORDER BY ev.event_id) AS schritt,
    ev.actor_id,
    ev.record_type,
    ev.record_key,
    ev.event_type,
    replace(ev.request_id, 'CORE-' || current_setting('core.run_id') || '-', '') AS phase,
    coalesce(
        ev.new_record ->> 'task_status',
        ev.new_record ->> 'handoff_status',
        ev.new_record ->> 'delivery_status'
    ) AS status,
    -- Identifiers only. bus_events carries the message subject and body for
    -- MESSAGE rows; an audit printout has no business reproducing them.
    coalesce(ev.new_record ->> 'recipient_id', ev.new_record ->> 'owner_id') AS gegenueber,
    ev.new_record ->> 'task_ref' AS task_ref,
    ev.occurred_at
FROM workforce.bus_events AS ev
WHERE ev.project_id = current_setting('core.project_id')
  AND ev.request_id LIKE 'CORE-' || current_setting('core.run_id') || '-%'
ORDER BY ev.event_id;

\echo ''
\echo '=== 2. Rekonstruierte Abfolge: abgelehnte Vorgaenge ==='

SELECT
    row_number() OVER (ORDER BY d.denial_id) AS schritt,
    d.actor_id,
    d.record_type,
    d.record_key,
    d.operation,
    replace(d.request_id, 'CORE-' || current_setting('core.run_id') || '-', '') AS phase,
    d.error_code,
    d.http_status,
    d.occurred_at
FROM workforce.bus_denials AS d
WHERE d.project_id = current_setting('core.project_id')
  AND d.request_id LIKE 'CORE-' || current_setting('core.run_id') || '-%'
ORDER BY d.denial_id;

\echo ''
\echo '=== 3. Positiv-Audit: geforderte Sequenz, an feste Ids gebunden ==='

-- One row per required step. event_id NULL means the step is not in the audit;
-- the ordinal is what the order check compares against. Completeness and order
-- are one statement because a read-only transaction cannot create a view to
-- share between two.
WITH trail AS (
    SELECT
        ev.event_id,
        ev.actor_id,
        ev.record_type,
        ev.record_key,
        replace(ev.request_id, 'CORE-' || current_setting('core.run_id') || '-', '') AS phase,
        ev.new_record
    FROM workforce.bus_events AS ev
    WHERE ev.project_id = current_setting('core.project_id')
      AND ev.request_id LIKE 'CORE-' || current_setting('core.run_id') || '-%'
),
steps AS (
SELECT 1 AS ord, 'karl_creates_task_for_gerd' AS schritt, (
    SELECT min(event_id) FROM trail
    WHERE phase = 'TASK-CREATE'
      AND record_type = 'TASK'
      AND record_key = current_setting('core.task_id')
      AND actor_id = 'SAO-001'
      AND new_record ->> 'creator_id' = 'SAO-001'
      AND new_record ->> 'owner_id' = 'AI-ENG-001'
      AND new_record ->> 'task_status' = 'PENDING') AS event_id
UNION ALL
SELECT 2, 'karl_opens_task', (
    SELECT min(event_id) FROM trail
    WHERE phase = 'TASK-OPEN'
      AND record_key = current_setting('core.task_id')
      AND actor_id = 'SAO-001'
      AND new_record ->> 'task_status' = 'OPEN')
UNION ALL
SELECT 3, 'gerd_works_task', (
    SELECT min(event_id) FROM trail
    WHERE phase = 'TASK-INPROGRESS'
      AND record_key = current_setting('core.task_id')
      AND actor_id = 'AI-ENG-001'
      AND new_record ->> 'task_status' = 'IN_PROGRESS')
UNION ALL
SELECT 4, 'gerd_reports_result_to_karl', (
    SELECT min(event_id) FROM trail
    WHERE phase = 'GERD-RESULT'
      AND record_type = 'MESSAGE'
      AND actor_id = 'AI-ENG-001'
      AND new_record ->> 'sender_id' = 'AI-ENG-001'
      AND new_record ->> 'recipient_id' = 'SAO-001')
UNION ALL
SELECT 5, 'gerd_hands_off_to_anastasia', (
    SELECT min(event_id) FROM trail
    WHERE phase = 'HANDOFF-CREATE'
      AND record_type = 'HANDOFF'
      AND record_key = current_setting('core.handoff_id')
      AND actor_id = 'AI-ENG-001'
      AND new_record ->> 'sender_id' = 'AI-ENG-001'
      AND new_record ->> 'recipient_id' = 'PEO-001'
      -- The handoff must belong to this task, not merely exist.
      AND new_record ->> 'task_ref' = current_setting('core.task_id'))
UNION ALL
SELECT 6, 'anastasia_accepts_handoff', (
    SELECT min(event_id) FROM trail
    WHERE phase = 'HANDOFF-ACCEPT'
      AND record_key = current_setting('core.handoff_id')
      AND actor_id = 'PEO-001'
      AND new_record ->> 'handoff_status' = 'ACCEPTED')
UNION ALL
SELECT 7, 'anastasia_reports_result_to_gerd', (
    SELECT min(event_id) FROM trail
    WHERE phase = 'PEO-RESULT'
      AND record_type = 'MESSAGE'
      AND actor_id = 'PEO-001'
      AND new_record ->> 'sender_id' = 'PEO-001'
      AND new_record ->> 'recipient_id' = 'AI-ENG-001')
UNION ALL
SELECT 8, 'gerd_moves_task_to_review', (
    SELECT min(event_id) FROM trail
    WHERE phase = 'TASK-REVIEW'
      AND record_key = current_setting('core.task_id')
      AND actor_id = 'AI-ENG-001'
      AND new_record ->> 'task_status' = 'REVIEW')
UNION ALL
SELECT 9, 'karl_closes_task_with_evidence', (
    SELECT min(event_id) FROM trail
    WHERE phase = 'TASK-DONE'
      AND record_key = current_setting('core.task_id')
      AND actor_id = 'SAO-001'
      AND new_record ->> 'task_status' = 'DONE'
      AND nullif(btrim(coalesce(new_record ->> 'completion_evidence', '')), '') IS NOT NULL)
UNION ALL
SELECT 10, 'second_handoff_created_for_rejection', (
    SELECT min(event_id) FROM trail
    WHERE phase = 'HANDOFF-REJ-CREATE'
      AND record_key = current_setting('core.reject_id')
      AND actor_id = 'AI-ENG-001'
      AND new_record ->> 'recipient_id' = 'PEO-001')
UNION ALL
SELECT 11, 'anastasia_rejects_second_handoff', (
    SELECT min(event_id) FROM trail
    WHERE phase = 'HANDOFF-REJ'
      AND record_key = current_setting('core.reject_id')
      AND actor_id = 'PEO-001'
      AND new_record ->> 'handoff_status' = 'REJECTED')
),
-- Not "handoff after task" but every adjacent pair: step n must precede step
-- n+1 for all n. A partially reordered run passed the two spot checks the
-- earlier version made.
verstoesse AS (
    SELECT a.schritt AS frueher, b.schritt AS spaeter
    FROM steps AS a
    JOIN steps AS b ON b.ord = a.ord + 1
    WHERE a.event_id IS NOT NULL
      AND b.event_id IS NOT NULL
      AND a.event_id >= b.event_id
)
SELECT
    CASE WHEN (SELECT count(*) FROM steps WHERE event_id IS NULL) = 0
          AND (SELECT count(*) FROM verstoesse) = 0
         THEN 'PASS' ELSE 'FAIL' END AS positiv_audit,
    (SELECT count(*) FROM steps WHERE event_id IS NOT NULL) AS belegt,
    (SELECT count(*) FROM steps) AS gefordert,
    (SELECT string_agg(schritt, ', ' ORDER BY ord) FROM steps WHERE event_id IS NULL)
        AS fehlend,
    (SELECT count(*) FROM verstoesse) AS reihenfolge_verletzungen,
    (SELECT string_agg(frueher || ' nach ' || spaeter, ', ') FROM verstoesse)
        AS verletzt;

\echo ''
\echo '=== 4. Negativ-Audit: geforderte Ablehnungen ==='

WITH core_denials AS (
    SELECT
        d.denial_id,
        d.actor_id,
        d.record_type,
        d.record_key,
        replace(d.request_id, 'CORE-' || current_setting('core.run_id') || '-', '') AS phase,
        d.error_code,
        d.http_status
    FROM workforce.bus_denials AS d
    WHERE d.project_id = current_setting('core.project_id')
      AND d.request_id LIKE 'CORE-' || current_setting('core.run_id') || '-%'
),
core_required_denials AS (
SELECT 'done_without_evidence_refused' AS pruefung, EXISTS (
    SELECT 1 FROM core_denials
    WHERE phase = 'TASK-DONE-NOEV'
      AND record_type = 'TASK'
      AND record_key = current_setting('core.task_id')
      AND actor_id = 'SAO-001'
      AND error_code = 'BUS_TASK_COMPLETION_EVIDENCE_REQUIRED'
      AND http_status = 400) AS belegt
UNION ALL
SELECT 'third_party_cannot_decide_handoff', EXISTS (
    SELECT 1 FROM core_denials
    WHERE phase = 'HANDOFF-STEAL'
      AND record_type = 'HANDOFF'
      AND record_key = current_setting('core.handoff_id')
      AND actor_id = 'SAO-001'
      -- The roundtrip accepts either identifier: a handoff outside Karl's
      -- scope can be answered as not found instead of denied.
      AND error_code IN ('BUS_HANDOFF_TRANSITION_DENIED', 'BUS_HANDOFF_NOT_FOUND')
      AND http_status IN (403, 404))
UNION ALL
SELECT 'non_owner_cannot_transition_task', EXISTS (
    SELECT 1 FROM core_denials
    WHERE phase = 'TASK-STEAL'
      AND record_type = 'TASK'
      AND record_key = current_setting('core.task_id')
      AND actor_id = 'PEO-001'
      AND error_code = 'BUS_TASK_TRANSITION_DENIED'
      AND http_status = 403)
)
SELECT
    CASE WHEN bool_and(belegt) THEN 'PASS' ELSE 'FAIL' END AS negativ_audit,
    count(*) FILTER (WHERE belegt)     AS belegt,
    count(*)                            AS gefordert,
    string_agg(pruefung, ', ') FILTER (WHERE NOT belegt) AS fehlend
FROM core_required_denials;

\echo ''
\echo '=== 5. Endzustand der beruehrten Datensaetze ==='

SELECT 'TASK' AS art, task_id AS id, task_status AS status,
       (completion_evidence IS NOT NULL) AS mit_evidenz
FROM workforce.bus_tasks
WHERE task_id = current_setting('core.task_id')
UNION ALL
SELECT 'HANDOFF', handoff_id, handoff_status, NULL
FROM workforce.bus_handoffs
WHERE handoff_id IN (current_setting('core.handoff_id'),
                     current_setting('core.reject_id'))
ORDER BY art, id;

ROLLBACK;
