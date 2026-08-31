\set ON_ERROR_STOP on

-- Rebuilds the worker-core run from the database alone, after the containers
-- are gone (ENG-008, review findings G-009, G-015, G-018).
--
-- What this has to show that core_audit.sql cannot: the *runtime* did the
-- work. Every request answered exactly once, by the agent identity and not by
-- a person, back to the requester and nobody else - across a container restart
-- and a deliberately lost state volume.
--
-- The exactly-once check is the important one. Five requests went in; three of
-- them were interrupted mid-flight on purpose. If any of them produced two
-- replies, the state store and the bus idempotency both failed and the whole
-- resumability argument is void.
--
-- Read-only by construction: BEGIN TRANSACTION READ ONLY and ROLLBACK.

BEGIN TRANSACTION READ ONLY;

SELECT set_config('wc.run_id', :'run_id', false);
SELECT set_config('wc.agent_id', :'agent_id', false);
SELECT set_config('wc.project_id', 'START-UP', false);

\echo '=== 1. Die Anfragen und ihre Antworten ==='

SELECT
    request.subject AS anfrage,
    request.delivery_status AS anfrage_status,
    count(reply.message_id) AS antworten,
    min(reply.sender_id) AS antwort_von,
    min(reply.recipient_id) AS antwort_an
FROM workforce.bus_messages AS request
LEFT JOIN workforce.bus_messages AS reply
       ON reply.parent_message_id = request.message_id
      AND reply.project_id = request.project_id
WHERE request.project_id = current_setting('wc.project_id')
  AND request.recipient_id = current_setting('wc.agent_id')
  AND request.subject LIKE 'Worker-Core ' || current_setting('wc.run_id') || ' %'
GROUP BY request.message_id, request.subject, request.delivery_status
ORDER BY request.subject;

\echo ''
\echo '=== 2. Abgelehnte Vorgaenge dieses Laufs ==='

SELECT
    d.actor_id,
    d.operation,
    d.record_type,
    d.error_code,
    d.http_status,
    d.occurred_at
FROM workforce.bus_denials AS d
WHERE d.project_id = current_setting('wc.project_id')
  AND d.request_id LIKE 'WORKERCORE-' || current_setting('wc.run_id') || '-%'
ORDER BY d.denial_id;

\echo ''
\echo '=== 3. Positiv-Audit ==='

WITH requests AS (
    SELECT m.message_id, m.subject, m.delivery_status
    FROM workforce.bus_messages AS m
    WHERE m.project_id = current_setting('wc.project_id')
      AND m.recipient_id = current_setting('wc.agent_id')
      AND m.subject LIKE 'Worker-Core ' || current_setting('wc.run_id') || ' %'
),
answers AS (
    SELECT r.message_id, r.subject, r.delivery_status,
           count(a.message_id) AS antworten,
           bool_and(a.sender_id = current_setting('wc.agent_id')) AS vom_agenten,
           bool_and(a.recipient_id = 'SAO-001') AS an_den_absender
    FROM requests AS r
    LEFT JOIN workforce.bus_messages AS a
           ON a.parent_message_id = r.message_id
          AND a.project_id = current_setting('wc.project_id')
    GROUP BY r.message_id, r.subject, r.delivery_status
),
checks AS (
    SELECT 'five_requests_reached_the_agent' AS pruefung,
           (SELECT count(*) FROM requests) = 5 AS erfuellt
    UNION ALL
    -- The heart of it: three of the five were interrupted mid-flight.
    SELECT 'every_request_answered_exactly_once',
           NOT EXISTS (SELECT 1 FROM answers WHERE antworten <> 1)
    UNION ALL
    SELECT 'every_request_acknowledged',
           NOT EXISTS (SELECT 1 FROM answers WHERE delivery_status <> 'ACCEPTED')
    UNION ALL
    -- Security review A1: the answers must come from the agent identity, not
    -- from a person's credential.
    SELECT 'every_answer_sent_by_the_agent_identity',
           NOT EXISTS (SELECT 1 FROM answers WHERE vom_agenten IS NOT TRUE)
    UNION ALL
    -- The routing control: the reply goes back where the request came from.
    SELECT 'every_answer_went_back_to_the_requester',
           NOT EXISTS (SELECT 1 FROM answers WHERE an_den_absender IS NOT TRUE)
    UNION ALL
    -- The agent identity is not a person. Checked here because an audit that
    -- assumes it would miss exactly the defect A1 described.
    SELECT 'the_agent_identity_is_not_an_employee',
           EXISTS (
               SELECT 1 FROM workforce.employees
               WHERE employee_id = current_setting('wc.agent_id')
                 AND role_code = 'SYSTEM_AGENT'
           )
)
SELECT
    CASE WHEN bool_and(coalesce(erfuellt, false)) THEN 'PASS' ELSE 'FAIL' END AS positiv_audit,
    count(*) FILTER (WHERE coalesce(erfuellt, false))     AS erfuellt,
    count(*)                                              AS gefordert,
    string_agg(pruefung, ', ') FILTER (WHERE NOT coalesce(erfuellt, false)) AS fehlend
FROM checks;

\echo ''
\echo '=== 4. Negativ-Audit ==='

-- Only one refusal is expected: the self-route the run asks for on purpose.
-- The injected transport faults never reached the bus, by design - they
-- simulate a dropped connection, and a dropped connection leaves no row
-- anywhere. Saying so here is the honest version; claiming the negative audit
-- covers the retry path would not be.
WITH expected AS (
    SELECT 'self_route_refused' AS pruefung, EXISTS (
        SELECT 1 FROM workforce.bus_denials
        WHERE project_id = current_setting('wc.project_id')
          AND request_id = 'WORKERCORE-' || current_setting('wc.run_id') || '-F-SELFROUTE'
          AND actor_id = current_setting('wc.agent_id')
          AND error_code = 'BUS_SELF_ROUTE_DENIED'
          AND http_status = 403
    ) AS belegt
)
SELECT
    CASE WHEN bool_and(belegt) THEN 'PASS' ELSE 'FAIL' END AS negativ_audit,
    count(*) FILTER (WHERE belegt) AS belegt,
    count(*)                       AS gefordert,
    string_agg(pruefung, ', ') FILTER (WHERE NOT belegt) AS fehlend
FROM expected;

\echo ''
\echo '=== 5. Keine offenen Zugaenge, Kanal zu ==='

SELECT
    ch.channel_status,
    (
        SELECT count(*)::integer
        FROM workforce.bus_credentials
        WHERE credential_status = 'ACTIVE'
          AND (expires_at IS NULL OR expires_at > clock_timestamp())
    ) AS aktive_zugaenge
FROM workforce.bus_channels AS ch
WHERE ch.project_id = current_setting('wc.project_id');

ROLLBACK;
