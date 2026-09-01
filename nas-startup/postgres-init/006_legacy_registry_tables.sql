\set ON_ERROR_STOP on

-- The seven legacy registry tables, moved out of the API's startup path.
--
-- Review finding G-025 asks for a least-privilege runtime account. That was
-- impossible while `initialize_database()` ran CREATE TABLE at every start:
-- the API needed DDL rights permanently, which is why its role ended up as
-- SUPERUSER with CREATEROLE, CREATEDB and BYPASSRLS - and a superuser can
-- switch off the append-only triggers the whole audit argument rests on.
--
-- The statements below are the ones the API used to execute, unchanged and
-- still IF NOT EXISTS. On the running NAS every table already exists, so this
-- migration only records that the definition now lives here. On an empty
-- database it creates them, exactly as before.
--
-- The API no longer creates anything; it checks that these tables are present
-- and refuses to start if they are not.

BEGIN;

SELECT set_config('app.actor_id', 'SYSTEM-MIGRATION', true);
SELECT set_config('app.request_id', 'MIG-006-LEGACY-REGISTRY-TABLES', true);

    CREATE TABLE IF NOT EXISTS roles (
        id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        name text NOT NULL UNIQUE,
        description text NOT NULL DEFAULT '',
        created_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS workers (
        id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        name text NOT NULL,
        kind text NOT NULL CHECK (kind IN ('human', 'agent')),
        role_id bigint REFERENCES roles(id) ON DELETE SET NULL,
        active boolean NOT NULL DEFAULT true,
        created_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS tasks (
        id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        title text NOT NULL,
        description text NOT NULL DEFAULT '',
        status text NOT NULL DEFAULT 'open'
            CHECK (status IN ('open', 'in_progress', 'blocked', 'done')),
        assignee_id bigint REFERENCES workers(id) ON DELETE SET NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS activity_log (
        id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        event_type text NOT NULL,
        entity_type text NOT NULL,
        entity_id bigint,
        details jsonb NOT NULL DEFAULT '{}'::jsonb,
        created_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS task_notes (
        id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        task_id bigint NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
        note_type text NOT NULL CHECK (note_type IN ('note', 'result')),
        content text NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS documents (
        id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        title text NOT NULL UNIQUE,
        content text NOT NULL DEFAULT '',
        updated_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS document_versions (
        id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        document_id bigint NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        content text NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now()
    );

INSERT INTO workforce.schema_migrations (
    migration_id,
    description
) VALUES (
    '006_legacy_registry_tables',
    'Moves the seven legacy registry tables out of the API startup path so the runtime account needs no DDL'
);

COMMIT;
