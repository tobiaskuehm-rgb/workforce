\set ON_ERROR_STOP on

-- Audit reconstruction for one chain run: Telegram -> Connector -> Bus ->
-- Agent -> Bus -> Connector -> Telegram.
--
-- Gerd, Phase 5, Punkt 4: "Positive und negative Auditspur automatisiert aus
-- PostgreSQL rekonstruieren." core_audit.sql does that for the ENG-008
-- roundtrip; for the chain there was nothing, and I said so myself in
-- REVIEW_ANTWORTEN.md long before writing this.
--
-- Writing it is what found G-053. The last leg left no trace in the database
-- at all: the connector announced the reply to the CEO and recorded that in
-- its own SQLite file, never on the bus. This script would have reconstructed
-- two thirds of the chain and reported PASS. Since the connector acknowledges,
-- step 5 exists and means something precise - see the scope note below.
--
-- Unlike core_audit.sql, the request ids are not one family. Each leg names
-- itself, which is what makes the binding possible without trusting anything
-- in between:
--
--   TG-<update_id>-TASK        connector creates the task
--   TG-<update_id>-MESSAGE     connector sends the request to the agent
--   AGENT-REPLY-<derived>      agent answers, derived from the inbound id
--   AGENT-ACK-<derived>        agent acknowledges the request
--   TG-ACK-<message_id>        connector acknowledges the reply
--
-- The agent's two ids are derived from the inbound message id by SHA-256
-- (agent_worker.derived_key), so a repeated run produces the same ones. That
-- is why step 3 can be bound to the *specific* inbound message rather than to
-- "some reply by the agent".
--
-- Read-only by construction: BEGIN TRANSACTION READ ONLY and ROLLBACK, so it
-- may be pointed at production at any time.
--
--   psql -v run_suffix=CHAIN1 -v update_id=4711 -v task_id=CEO-TG-CHAIN-001 \
--        -f chain_audit.sql
--
-- **Was hier nicht rekonstruierbar ist.** Ob der Text tatsaechlich in Telegram
-- ankam, steht nicht in dieser Datenbank und kann es nicht. Was Schritt 5
-- belegt, ist praeziser und schwaecher zugleich: Der Connector bestaetigt
-- *nachdem* der Versand erfolgreich war (G-001-Reihenfolge), eine
-- Bestaetigung heisst also "an Telegram uebergeben". Der Beleg fuer die
-- Telegram-Seite selbst liegt im lokalen Audit des Connectors. Wer beides
-- braucht, braucht beide Quellen - und das ist eine Eigenschaft der Kette,
-- kein Mangel dieses Skripts.

BEGIN TRANSACTION READ ONLY;

SELECT set_config('chain.project_id', 'START-UP', false);
SELECT set_config('chain.connector', 'CEO-TG-' || :'run_suffix', false);
SELECT set_config('chain.agent', 'AGENT-ENG-001', false);
SELECT set_config('chain.task_id', :'task_id', false);
SELECT set_config('chain.tg_prefix', 'TG-' || :'update_id' || '-', false);

\echo '=== Voraussetzung: Ablehnungsprotokoll vorhanden ==='

SELECT CASE
    WHEN to_regclass('workforce.bus_denials') IS NULL
        THEN 'FEHLT - Migration 005_bus_denial_audit anwenden'
    ELSE 'vorhanden'
END AS bus_denials;

\echo ''
\echo '=== 1. Rekonstruierte Abfolge: erfolgreiche Vorgaenge ==='

-- Bound to the two identities of this run rather than to one request-id
-- family, because the legs name themselves differently. Identifiers only -
-- bus_events carries subject and body for MESSAGE rows, and an audit printout
-- has no business reproducing them.
SELECT
    row_number() OVER (ORDER BY ev.event_id) AS schritt,
    ev.actor_id,
    ev.record_type,
    ev.record_key,
    ev.event_type,
    ev.request_id,
    coalesce(ev.new_record ->> 'task_status',
             ev.new_record ->> 'delivery_status') AS status,
    coalesce(ev.new_record ->> 'recipient_id',
             ev.new_record ->> 'owner_id') AS gegenueber,
    ev.new_record ->> 'task_ref' AS task_ref,
    ev.occurred_at
FROM workforce.bus_events AS ev
WHERE ev.project_id = current_setting('chain.project_id')
  AND ev.actor_id IN (current_setting('chain.connector'),
                      current_setting('chain.agent'))
  AND (ev.request_id LIKE current_setting('chain.tg_prefix') || '%'
       OR ev.request_id LIKE 'TG-ACK-%'
       OR ev.request_id LIKE 'AGENT-REPLY-%'
       OR ev.request_id LIKE 'AGENT-ACK-%')
ORDER BY ev.event_id;

\echo ''
\echo '=== 2. Positiv-Audit: geforderte Sequenz, an feste Ids gebunden ==='

WITH trail AS (
    SELECT ev.event_id, ev.actor_id, ev.record_type, ev.record_key,
           ev.request_id, ev.new_record
    FROM workforce.bus_events AS ev
    WHERE ev.project_id = current_setting('chain.project_id')
),
-- The inbound message the agent answered. Everything after step 2 hangs off
-- this id, so a reply to some other message cannot satisfy the chain.
anfrage AS (
    SELECT record_key AS message_id
    FROM trail
    WHERE request_id = current_setting('chain.tg_prefix') || 'MESSAGE'
      AND record_type = 'MESSAGE'
    ORDER BY event_id
    LIMIT 1
),
steps AS (
SELECT 1 AS ord, 'connector_creates_task' AS schritt, (
    SELECT min(event_id) FROM trail
    WHERE request_id = current_setting('chain.tg_prefix') || 'TASK'
      AND record_type = 'TASK'
      AND record_key = current_setting('chain.task_id')
      AND actor_id = current_setting('chain.connector')
      AND new_record ->> 'owner_id' = current_setting('chain.agent')) AS event_id
UNION ALL
SELECT 2, 'connector_sends_request_to_agent', (
    SELECT min(event_id) FROM trail
    WHERE request_id = current_setting('chain.tg_prefix') || 'MESSAGE'
      AND record_type = 'MESSAGE'
      AND actor_id = current_setting('chain.connector')
      AND new_record ->> 'sender_id' = current_setting('chain.connector')
      AND new_record ->> 'recipient_id' = current_setting('chain.agent')
      -- G-003: ohne Task-Referenz haelt der Connector den Text spaeter zurueck.
      AND new_record ->> 'task_ref' = current_setting('chain.task_id'))
UNION ALL
SELECT 3, 'agent_replies_carrying_the_task_reference', (
    SELECT min(event_id) FROM trail
    WHERE request_id LIKE 'AGENT-REPLY-%'
      AND record_type = 'MESSAGE'
      AND actor_id = current_setting('chain.agent')
      AND new_record ->> 'sender_id' = current_setting('chain.agent')
      AND new_record ->> 'recipient_id' = current_setting('chain.connector')
      AND new_record ->> 'parent_message_id' = (SELECT message_id FROM anfrage)
      -- Die Antwort traegt die Referenz der Anfrage weiter (G-003). Fehlt sie,
      -- sieht die Kette komponentenweise gesund aus und liefert nichts.
      AND new_record ->> 'task_ref' = current_setting('chain.task_id'))
UNION ALL
SELECT 4, 'agent_acknowledges_the_request', (
    SELECT min(event_id) FROM trail
    WHERE request_id LIKE 'AGENT-ACK-%'
      AND record_type = 'MESSAGE'
      AND actor_id = current_setting('chain.agent')
      AND record_key = (SELECT message_id FROM anfrage))
UNION ALL
SELECT 5, 'connector_acknowledges_the_reply', (
    SELECT min(event_id) FROM trail
    WHERE request_id LIKE 'TG-ACK-%'
      AND record_type = 'MESSAGE'
      AND actor_id = current_setting('chain.connector')
      AND record_key = (SELECT min(record_key) FROM trail
                        WHERE request_id LIKE 'AGENT-REPLY-%'
                          AND actor_id = current_setting('chain.agent')))
),
-- Every adjacent pair, not two spot checks: step n must precede step n+1 for
-- all n. A partially reordered run passed the earlier form of this in
-- core_audit.sql, which is why it is written this way here from the start.
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
\echo '=== 3. Negativ-Audit: Ablehnungen dieses Laufs ==='

-- Was der Lauf an Ablehnungen erzeugt hat. Ein Kettenlauf, der durchlaeuft,
-- erzeugt keine - deshalb ist die Erwartung hier "keine im Erfolgspfad" und
-- nicht eine Liste geforderter Ablehnungen, die es nicht gibt. Wer einen
-- Ablehnungsfall absichtlich provoziert, sieht ihn in dieser Tabelle; das
-- Skript ist dafuer bereit, der Lauf tut es heute nicht.
SELECT
    row_number() OVER (ORDER BY d.denial_id) AS schritt,
    d.actor_id, d.record_type, d.record_key, d.operation,
    d.request_id, d.error_code, d.http_status, d.occurred_at
FROM workforce.bus_denials AS d
WHERE d.project_id = current_setting('chain.project_id')
  AND (d.request_id LIKE current_setting('chain.tg_prefix') || '%'
       OR d.request_id LIKE 'TG-ACK-%'
       OR d.request_id LIKE 'AGENT-REPLY-%'
       OR d.request_id LIKE 'AGENT-ACK-%')
ORDER BY d.denial_id;

\echo ''
\echo '=== 4. Nichts bleibt liegen ==='

-- Der Zustand, den G-053 unmoeglich gemacht hatte: eine Antwort, die fuer
-- immer DELIVERED im Posteingang des Connectors steht. Beide Richtungen
-- werden geprueft, weil eine offene Nachricht auf jeder Seite bedeutet, dass
-- die Kette an dieser Stelle stehengeblieben ist.
SELECT
    CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS nichts_offen,
    count(*) AS offene_nachrichten,
    string_agg(m.message_id || ' an ' || m.recipient_id, ', ') AS liegengeblieben
FROM workforce.bus_messages AS m
WHERE m.project_id = current_setting('chain.project_id')
  AND m.recipient_id IN (current_setting('chain.connector'),
                         current_setting('chain.agent'))
  AND m.delivery_status = 'DELIVERED';

ROLLBACK;
