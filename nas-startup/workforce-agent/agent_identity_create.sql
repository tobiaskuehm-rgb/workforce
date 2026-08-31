\set ON_ERROR_STOP on

-- Creates a dedicated technical identity for the agent.
--
-- Security review 2026-08-31, A1: the agent currently borrows AI-ENG-001,
-- whose registry entry is a person - display_name "Gerd", role_title
-- "AI Engineer / KI-Systemarchitekt", employment_status PROBATION. Every
-- answer the agent produces therefore appears in the bus as a message from a
-- human colleague, indistinguishable from one Gerd wrote himself.
--
-- The project already solved this correctly elsewhere. CEO-TG-002 carries
-- role_code SYSTEM_CONNECTOR and the role_title "Technical Acceptance
-- Connector – not an employee". This script applies the same pattern to the
-- agent, so attribution stays honest and no person is answerable for text a
-- model produced.
--
-- NOT YET RUN. Needs an approval decision and a DEC number; pass it as
-- :source_ref. Unlike the prepare script this is a *permanent* change to the
-- registry, not a short-lived credential - which is why it is a separate,
-- explicitly invoked file.
--
-- Routes mirror AI-ENG-001's existing MESSAGE routes, because the agent
-- answers the same people Gerd would. Deliberately NOT granted: task
-- authority beyond PROPOSE, handoff creation, and any route AI-ENG-001 does
-- not already have. The agent must never be able to reach further than the
-- person whose work it takes over.

BEGIN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM workforce.employees WHERE employee_id = 'AGENT-ENG-001'
    ) THEN
        RAISE EXCEPTION 'AGENT_IDENTITY_ALREADY_EXISTS';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM workforce.active_project_members
        WHERE project_id = 'START-UP' AND employee_id = 'AI-ENG-001'
    ) THEN
        RAISE EXCEPTION 'AGENT_IDENTITY_TEMPLATE_MISSING';
    END IF;
END;
$$;

SELECT set_config('app.actor_id', 'SYSTEM-WORKFORCE-AGENT', true);
SELECT set_config('app.request_id', 'AGENT-IDENTITY-CREATE', true);

INSERT INTO workforce.employees (
    employee_id,
    display_name,
    role_code,
    role_title,
    organizational_area,
    employment_status,
    source_ref
) VALUES (
    'AGENT-ENG-001',
    'Workforce Agent – AI Engineering',
    'SYSTEM_AGENT',
    'Automated agent – not an employee, answers are machine generated',
    'AI Engineering / Technical Integration',
    'ACTIVE',
    :'source_ref'
);

INSERT INTO workforce.employee_project_memberships (
    employee_id,
    project_id,
    membership_status,
    source_ref
) VALUES (
    'AGENT-ENG-001',
    'START-UP',
    'ACTIVE',
    :'source_ref'
);

-- PARTICIPANT read scope: the agent sees what it is party to, never the whole
-- project. PROPOSE only: it may suggest, never decide. No handoff creation -
-- a handoff transfers responsibility, and a machine cannot carry it.
INSERT INTO workforce.bus_member_capabilities (
    project_id,
    employee_id,
    capability_status,
    read_scope,
    task_authority,
    can_send,
    can_create_handoff,
    source_ref
) VALUES (
    'START-UP',
    'AGENT-ENG-001',
    'ACTIVE',
    'PARTICIPANT',
    'PROPOSE',
    true,
    false,
    :'source_ref'
);

-- Mirror exactly the MESSAGE routes AI-ENG-001 already has, in both
-- directions, and nothing beyond them.
INSERT INTO workforce.bus_route_allowlist (
    route_id,
    project_id,
    sender_id,
    recipient_id,
    route_kind,
    route_status,
    source_ref
)
SELECT
    'ROUTE-AGENTENG001-' || replace(existing.recipient_id, '-', '') || '-MESSAGE',
    'START-UP',
    'AGENT-ENG-001',
    existing.recipient_id,
    'MESSAGE',
    'ACTIVE',
    :'source_ref'
FROM workforce.bus_route_allowlist AS existing
WHERE existing.project_id = 'START-UP'
  AND existing.sender_id = 'AI-ENG-001'
  AND existing.route_kind = 'MESSAGE'
  AND existing.route_status = 'ACTIVE';

INSERT INTO workforce.bus_route_allowlist (
    route_id,
    project_id,
    sender_id,
    recipient_id,
    route_kind,
    route_status,
    source_ref
)
SELECT
    'ROUTE-' || replace(existing.sender_id, '-', '') || '-AGENTENG001-MESSAGE',
    'START-UP',
    existing.sender_id,
    'AGENT-ENG-001',
    'MESSAGE',
    'ACTIVE',
    :'source_ref'
FROM workforce.bus_route_allowlist AS existing
WHERE existing.project_id = 'START-UP'
  AND existing.recipient_id = 'AI-ENG-001'
  AND existing.route_kind = 'MESSAGE'
  AND existing.route_status = 'ACTIVE';

COMMIT;

SELECT
    'PASS' AS result,
    e.employee_id,
    e.role_code,
    e.role_title,
    c.read_scope,
    c.task_authority,
    c.can_send,
    c.can_create_handoff,
    (
        SELECT count(*)::integer
        FROM workforce.bus_route_allowlist
        WHERE project_id = 'START-UP'
          AND route_status = 'ACTIVE'
          AND (sender_id = 'AGENT-ENG-001' OR recipient_id = 'AGENT-ENG-001')
    ) AS active_routes
FROM workforce.employees AS e
JOIN workforce.bus_member_capabilities AS c
  ON c.employee_id = e.employee_id AND c.project_id = 'START-UP'
WHERE e.employee_id = 'AGENT-ENG-001';
