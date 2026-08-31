# Bus-Negativtests Karl ↔ Thorsten – Ergänzung zum Realtest-Runbook

**Zweck:** Aktivierungsgate Punkt 6 aus `WORKFORCE_BUS_ROLLOUT.md` schließen — Negativtests über die *echte* HTTPS-API statt nur transaktional in SQL.
**Bezug:** ergänzt `../BUS_REALTEST_KARL_THORSTEN_RUNBOOK.md`, ersetzt es nicht.
**Stand:** erstellt 2026-08-31, lokal getestet, auf der NAS noch nicht ausgeführt.

## Warum ein eigener Schritt

`postgres-tests/002_workforce_bus_acceptance.sql` prüft die Fail-Closed-Kontrollen bereits, aber innerhalb einer Transaktion mit `ROLLBACK` und direkt auf den SQL-Funktionen. Damit ist offen, ob dieselben Kontrollen auch über den realen Weg greifen: Reverse Proxy → FastAPI → Dependency-Kette → SQL. Genau diese Lücke schließt dieser Schritt.

## Einordnung in die Schrittfolge

Der Negativtest läuft **im selben `TESTING`-Fenster** wie der positive Realtest und benötigt weder neue Zugangsdaten noch eine zusätzliche Firewall-Regel — er nutzt dieselben zwei Tokens aus dem Prepare-Schritt und dieselbe feste Quelladresse `172.31.254.2`.

Reihenfolge im Runbook:

| Schritt | Compose-Datei | Neu? |
|---|---|---|
| 3 Vorbereiten | `compose.prepare.yaml` | bestehend |
| 4 Realtest (positiv) | `compose.run.yaml` | bestehend |
| **4b Negativtests** | **`compose.negtest.yaml`** | **neu** |
| 5 Bereinigen | `compose.cleanup.yaml` | bestehend |

Das bereits freigegebene Realtest-Paket bleibt unverändert: Der Negativtest hat ein eigenes Image (`startup-bus-negtest:v1`) und ein eigenes Dockerfile.

## Schritt 4b ausführen

1. Erst ausführen, wenn Schritt 4 mit `"result": "PASS"` beendet wurde. Bei `FAIL` oder `BLOCKED` in Schritt 4 diesen Schritt überspringen und direkt zu Schritt 5.
2. In Container Manager ein temporäres Projekt `startup-bus-realtest-negtest` mit Pfad `/docker/Startup/bus-realtest` und Compose-Datei `compose.negtest.yaml` anlegen.
3. Projekt einmal starten und das Protokoll des Einmalcontainers öffnen.
4. Erwartet: eine einzelne JSON-Zeile mit `"result": "PASS"`, `"cases_failed": 0` und `"cases_total": 20`.
5. Bei `"result": "FAIL"`: **nicht wiederholen.** Das Protokoll sichern, direkt zu Schritt 5 (Bereinigung) gehen und mir das Ergebnis schicken. Ein fehlgeschlagener Negativtest bedeutet, dass eine Sicherheitskontrolle über den realen Weg nicht greift — das blockiert die Aktivierung.
6. In Schritt 5 zusätzlich das Projekt `startup-bus-realtest-negtest` mit entfernen.

**Schick mir dieses Protokoll**, bevor du bereinigst.

## Wiederholungslauf

Wird der Test je erneut gebraucht, vorher `BUS_NEGTEST_RUN_ID` in `compose.negtest.yaml` hochzählen (`"001"` → `"002"`). Alle Request-IDs und Idempotency-Keys leiten sich davon ab; ohne Änderung kollidiert ein zweiter Lauf mit den Nachrichten des ersten und meldet fälschlich Fehler.

## Die 20 geprüften Fälle

**Authentifizierung**
1. `unknown_token_rejected` — unbekanntes Token → 401 `BUS_AUTH_FAILED`
2. `malformed_bearer_rejected` — zu kurzes Token → 401 `BUS_BEARER_TOKEN_REQUIRED`
3. `missing_authorization_rejected` — kein Header → 401 `BUS_BEARER_TOKEN_REQUIRED`

**Pflicht-Header**
4. `missing_idempotency_key_rejected` → 400 `BUS_IDEMPOTENCY_KEY_REQUIRED`
5. `missing_request_id_rejected` → 400 `BUS_REQUEST_ID_REQUIRED`

**Anfrageform**
6. `invalid_scope_rejected` — `scope=EVERYTHING` → 400 `BUS_REQUEST_INVALID`
7. `unknown_field_rejected` — untergeschobenes `sender_id` → 400 `BUS_REQUEST_INVALID`

**Routing und Identität**
8. `self_route_rejected` — Karl an Karl → 403 `BUS_SELF_ROUTE_DENIED`
9. `unlisted_recipient_rejected` — Empfänger außerhalb der Allowlist → 403
10. `project_scope_denied_for_specialist` — Thorsten liest `scope=PROJECT` → 403 `BUS_PROJECT_READ_DENIED`

**Bestätigungen**
11. `ack_seed_message` — Grundlage für 12–16
12. `ack_by_non_recipient_rejected` — Absender bestätigt sich selbst → 403 `BUS_ACK_DENIED`
13. `ack_unknown_message_does_not_leak_existence` — unbekannte `message_id` → 403 `BUS_ACK_DENIED`, **nicht** 404. Der Bus darf nicht verraten, ob eine ID existiert.
14. `ack_by_recipient_accepted` — regulärer Fall → 200
15. `ack_repeat_same_decision_is_idempotent` — gleiche Entscheidung erneut → 200
16. `conflicting_ack_decision_rejected` — `ACCEPTED` dann `REJECTED` → 409 `BUS_ACK_ALREADY_FINAL`

**Idempotenz**
17. `identical_replay_creates_no_duplicate` — gleicher Key, gleicher Inhalt → dieselbe `message_id`
18. `idempotency_key_reuse_with_different_body_rejected` → 409 `BUS_IDEMPOTENCY_CONFLICT`

**Grenzen**
19. `oversized_body_rejected` — 8001 Zeichen bei `max_body_chars` 8000 → 413 `BUS_BODY_TOO_LARGE`
20. `loop_limit_enforced` — Antwortkette bis `hop_count` 5 bei `max_hops` 4 → 422 `BUS_LOOP_LIMIT_EXCEEDED`

## Bewusst nicht enthalten

- **„Außerhalb `START-UP`"** — die API setzt `BUS_PROJECT_ID` fest im Code (`app.py:17`) und übernimmt keinen Projektwert aus dem Request. Ein fremdes Projekt ist über die API konstruktiv nicht adressierbar; ein Testfall dafür wäre eine Attrappe. Die Projektgrenze ist auf SQL-Ebene in `002_workforce_bus_acceptance.sql` geprüft.
- **„Nach Widerruf"** — nach dem Cleanup steht der Kanal auf `DISABLED`, und dann antwortet jeder Bus-Endpunkt schon vor der Tokenprüfung mit 503 `BUS_CHANNEL_NOT_ACTIVE`. Ein 401-Nachweis nach Widerruf braucht daher einen eigenen Zwischenschritt, der genau ein Credential widerruft, während der Kanal noch `TESTING` ist. Der ist in diesem Paket **noch nicht** enthalten und bleibt offen.

## Lokale Prüfung ohne Netzwerk

```text
python3 -m unittest discover -v
```

Neun Tests, davon fünf für den Negativtest. Der wichtigste ist `test_weakened_control_is_detected`: Er schaltet nacheinander acht Kontrollen in einer simulierten Bus-Gegenstelle ab (Selbst-Route, Allowlist, Projekt-Scope, Ack-Identität, Ack-Finalität, Idempotenz, Größenlimit, Schleifenlimit) und verlangt, dass der Negativtest jede einzelne Abschwächung meldet. Eine Testsuite, die eine fehlende Kontrolle nicht bemerkt, taugt nicht als Nachweis.
