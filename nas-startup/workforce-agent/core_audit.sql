\set ON_ERROR_STOP on

-- Audit reconstruction for one core roundtrip. Required output of ENG-008
-- ("Neustart-/Persistenz- und Audit-Rekonstruktionsnachweis") and the answer
-- to review finding G-009.
--
-- The point is what remains *after* the run: containers removed, stdout gone,
-- credentials revoked. If the sequence cannot be rebuilt from
-- workforce.bus_events alone, then the markdown evidence is a claim rather
-- than a proof.
--
-- Read-only by construction: BEGIN TRANSACTION READ ONLY and ROLLBACK, so it
-- can be run against production at any time.
--
-- Every write in core_roundtrip.py carries a request id of the form
-- CORE-<run_id>-<step>, which is what makes this reconstruction possible.

BEGIN TRANSACTION READ ONLY;

SELECT set_config('core.run_id', :'run_id', false);

\echo '=== Rekonstruierte Abfolge aus dem Audit ==='

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
    ev.occurred_at
FROM workforce.bus_events AS ev
WHERE ev.request_id LIKE 'CORE-' || current_setting('core.run_id') || '-%'
ORDER BY ev.event_id;

\echo ''
\echo '=== Pruefung der geforderten Sequenz ==='

WITH trail AS (
    SELECT
        ev.actor_id,
        ev.record_type,
        ev.record_key,
        ev.request_id,
        ev.new_record ->> 'task_status'    AS task_status,
        ev.new_record ->> 'handoff_status' AS handoff_status,
        ev.event_id
    FROM workforce.bus_events AS ev
    WHERE ev.request_id LIKE 'CORE-' || current_setting('core.run_id') || '-%'
),
checks AS (
    -- Task angelegt durch Karl
    SELECT 'task_created_by_karl' AS pruefung,
           EXISTS (SELECT 1 FROM trail
                   WHERE record_type = 'TASK' AND actor_id = 'SAO-001'
                     AND request_id LIKE '%TASK-CREATE') AS erfuellt
    UNION ALL
    -- Gerd hat den Task bearbeitet
    SELECT 'task_worked_by_gerd',
           EXISTS (SELECT 1 FROM trail
                   WHERE record_type = 'TASK' AND actor_id = 'AI-ENG-001'
                     AND task_status = 'IN_PROGRESS')
    UNION ALL
    -- Ergebnis von Gerd als Nachricht
    SELECT 'result_reported_by_gerd',
           EXISTS (SELECT 1 FROM trail
                   WHERE record_type = 'MESSAGE' AND actor_id = 'AI-ENG-001')
    UNION ALL
    -- Handoff durch Gerd erzeugt
    SELECT 'handoff_created_by_gerd',
           EXISTS (SELECT 1 FROM trail
                   WHERE record_type = 'HANDOFF' AND actor_id = 'AI-ENG-001')
    UNION ALL
    -- Handoff durch Anastasia angenommen
    SELECT 'handoff_accepted_by_anastasia',
           EXISTS (SELECT 1 FROM trail
                   WHERE record_type = 'HANDOFF' AND actor_id = 'PEO-001'
                     AND handoff_status = 'ACCEPTED')
    UNION ALL
    -- Ergebnis von Anastasia
    SELECT 'result_reported_by_anastasia',
           EXISTS (SELECT 1 FROM trail
                   WHERE record_type = 'MESSAGE' AND actor_id = 'PEO-001')
    UNION ALL
    -- Ablehnungspfad ebenfalls belegt
    SELECT 'rejection_path_recorded',
           EXISTS (SELECT 1 FROM trail
                   WHERE record_type = 'HANDOFF' AND actor_id = 'PEO-001'
                     AND handoff_status = 'REJECTED')
    UNION ALL
    -- Abschluss durch den Ersteller, mit Evidenz
    SELECT 'task_closed_by_creator',
           EXISTS (SELECT 1 FROM trail
                   WHERE record_type = 'TASK' AND actor_id = 'SAO-001'
                     AND task_status = 'DONE')
    UNION ALL
    -- Reihenfolge: Handoff nach Task, Abschluss nach Annahme
    SELECT 'order_task_before_handoff',
           (SELECT min(event_id) FROM trail WHERE record_type = 'TASK')
           < (SELECT min(event_id) FROM trail WHERE record_type = 'HANDOFF')
    UNION ALL
    SELECT 'order_acceptance_before_close',
           (SELECT min(event_id) FROM trail
            WHERE record_type = 'HANDOFF' AND handoff_status = 'ACCEPTED')
           < (SELECT max(event_id) FROM trail
              WHERE record_type = 'TASK' AND task_status = 'DONE')
)
SELECT
    CASE WHEN bool_and(coalesce(erfuellt, false)) THEN 'PASS' ELSE 'FAIL' END AS result,
    count(*) FILTER (WHERE coalesce(erfuellt, false))     AS erfuellt,
    count(*) FILTER (WHERE NOT coalesce(erfuellt, false)) AS offen,
    string_agg(pruefung, ', ') FILTER (WHERE NOT coalesce(erfuellt, false)) AS fehlend
FROM checks;

\echo ''
\echo '=== Endzustand der beruehrten Datensaetze ==='

SELECT 'TASK' AS art, task_id AS id, task_status AS status,
       (completion_evidence IS NOT NULL) AS mit_evidenz
FROM workforce.bus_tasks
WHERE task_id = 'ENG-CORE-' || current_setting('core.run_id')
UNION ALL
SELECT 'HANDOFF', handoff_id, handoff_status, NULL
FROM workforce.bus_handoffs
WHERE handoff_id LIKE 'HO-CORE-' || current_setting('core.run_id') || '%'
ORDER BY art, id;

ROLLBACK;
