# Abnahmetests aller angewendeten Migrationen gegen die laufende Produktion

**2026-09-02, 11:55 CEST.** Lesend, jeder Test in einer Transaktion mit
`ROLLBACK`. Kein Schreibvorgang, kein Neustart, kein Containerwechsel.

## Warum dieser Nachweis existiert

`CLAUDE.md`, Abschnitt Migrationen, Punkt 6 verlangt für jede Migration einen
Abnahmetest, der „gegen die Produktion laufen darf". Bis zum 2026-09-02 war das
eine Behauptung: Vier Migrationen hatten gar keinen Test, und die beiden
großen — `001` und `002` — prüften Bestandszahlen aus dem August und wären
gegen die heutige Datenbank gescheitert (`G-049`). Belegt war der
Produktivstand deshalb nur über die Runbook-Nachweise des Phase-4-Fensters,
nicht über `postgres-tests/`.

Dieser Lauf ist der erste, in dem **alle angewendeten Migrationen** über ihren
eigenen Abnahmetest gegen die laufende Datenbank bestätigt sind.

## Umgebung

```
Zeitpunkt: 2026-09-02 11:55:23 CEST
Commit laut production_state.txt: PRODUCTION_COMMIT=672e0a7
startup-workforce-api-1 | startup-workforce-api:v9 | Up 5 hours (healthy)
startup-db-1 | postgres:17-alpine | Up 5 hours (healthy)
```

Ausgeführt aus `/volume1/docker/Startup` heraus über
`docker compose exec -T db psql -U workforce_app -d workforce -v ON_ERROR_STOP=1`,
Testdateien aus dem schreibgeschützten Mount `/opt/startup/tests`.

## Ergebnis

| Migration | Ergebnis | Exit |
|---|---|---|
| `001_employee_registry` | `PASS: Employee Registry schema, seed identities, project scope, versioning and audit controls` | 0 |
| `002_workforce_bus` | `PASS: Workforce Bus identity, project scope, inbox/outbox, tasks, handoffs, acknowledgement, immutable payloads, redacted audit, idempotency, loop protection, revocation and fail-closed controls` | 0 |
| `003_workforce_bus_trigger_fix` | `PASS (6 Tabellen am gemeinsamen Trigger)`, Selbstprüfung `PASS` | 0 |
| `005_bus_denial_audit` | `Bus denial audit acceptance: PASS` | 0 |
| `006_legacy_registry_tables` | `PASS (7 Tabellen in public)`, Selbstprüfung `PASS` | 0 |
| `007_least_privilege_roles` | `PASS`, Selbstprüfung `PASS` | 0 |

`004_knowledge_capability` und `008_knowledge_api_grants` sind **nicht**
angewendet und deshalb nicht Teil dieses Laufs. `008` hat weiterhin keinen
Abnahmetest; die Lücke steht mit Begründung in
`workforce-agent/test_migration_acceptance.py`.

## Gegenproben

Sechsmal `PASS` sagt für sich genommen auch dann nichts, wenn die Abfragen ins
Leere greifen. Zwei Prüfungen wurden deshalb mit **absichtlich falscher
Erwartung** gegen dieselbe Datenbank gefahren; beide mussten scheitern, und
beide taten es mit echten Zahlen aus der Produktion:

```
ERROR:  GEGENPROBE-001 Bootstrap identities incomplete: found 5 of 6
ERROR:  GEGENPROBE-002 Active self-routes: 68
```

Die erste belegt, dass die fünf Bootstrap-Identitäten wirklich gezählt werden;
die zweite, dass die Routentabelle wirklich gelesen wird — 68 aktive Routen,
keine davon auf sich selbst, sonst wäre der echte Test gescheitert.

## Was dieser Lauf nicht sagt

- Er sagt nichts über die **Laufzeit**. Es lief kein Agent, kein Telegram, kein
  Modell (`G-030` unverändert offen).
- Er sagt nichts über die **API**. Geprüft wurde das Datenbankschema; die
  Version im Kopf dieses Dokuments steht als Umgebungsangabe, nicht als
  Prüfergebnis.
- Er ersetzt **nicht** den Contract-Test und die Auditrekonstruktion. Die
  vorhandenen `PASS` dafür stammen vom 2026-08-31 und damit von einem älteren
  API-Stand mit nur `001`–`003`; beide brauchen echte Zugangsdaten und den
  Kanal auf `TESTING` und damit eine eigene Freigabe.
