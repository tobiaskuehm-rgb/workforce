\set ON_ERROR_STOP on

BEGIN;

SELECT set_config('app.actor_id', 'SYSTEM-MIGRATION', true);
SELECT set_config('app.request_id', 'MIG-003-WORKFORCE-BUS-TRIGGER-FIX', true);

ALTER TABLE workforce.bus_credentials
    ADD COLUMN IF NOT EXISTS updated_at timestamptz;

UPDATE workforce.bus_credentials
SET updated_at = issued_at
WHERE updated_at IS NULL;

ALTER TABLE workforce.bus_credentials
    ALTER COLUMN updated_at SET DEFAULT clock_timestamp(),
    ALTER COLUMN updated_at SET NOT NULL;

INSERT INTO workforce.schema_migrations (
    migration_id,
    description
) VALUES (
    '003_workforce_bus_trigger_fix',
    'Adds the missing credential update timestamp required by the shared version trigger'
);

COMMIT;
