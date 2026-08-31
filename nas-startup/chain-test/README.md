# Kettentest — Telegram → Bus → Agent → Bus → Telegram

**Status:** **Unfertig.** Angefangen am 2026-08-31, unterbrochen für Gerds zweite Prüfrunde. Nicht ausführen.

Bisher existiert nur `chain_prepare.sql`. Es fehlen: Cleanup, Compose-Dateien, Runbook und lokale Tests.

## Wozu

Jedes Stück der Zielkette ist einzeln belegt — Telegram-Realtest, Agenten-Trockenlauf, Core-Roundtrip. **Zusammen gelaufen sind sie nie.** Dieser Test soll die Kette einmal als Ganzes zeigen, mit dem Echo-Provider und damit ohne Kosten.

## Zwei Funde beim Durchdenken

Beide wären erst im Lauf aufgefallen und hätten je einen Anlauf gekostet.

**1. Die Rückrichtung war strukturell unmöglich.** `realtest2_prepare.sql` legt ausschließlich `ROUTE-CEOTG002-AIENG001-{TASK,MESSAGE}` an — nur ausgehend. Keine Route erlaubte je irgendjemandem, der Connector-Identität zu schreiben. `publish_inbox_notifications()` hätte also immer eine leere Inbox gefunden, unabhängig davon, wie oft man es versucht. Die Rückrichtung war nicht bloß ungetestet; sie konnte nicht funktionieren.

`chain_prepare.sql` legt beide Richtungen an.

**2. Die Agentenantwort trug keine Task-Referenz.** Der Connector gibt einen Nachrichtentext nur weiter, wenn dessen `task_ref` auf der Allowlist steht (Befund G-003, am selben Tag eingebaut). Die Antwort des Agenten hatte gar keine — meine eigene Sicherheitsprüfung hätte die Kette blockiert.

Behoben: `bus_client.send_message()` nimmt jetzt `task_ref`, und der Worker reicht die Referenz der eingehenden Nachricht durch. Eine Antwort zu Aufgabe X gehört zu Aufgabe X.

## Was noch fehlt

- `chain_cleanup.sql` — Identität, Routen, Credentials widerrufen, Kanal `DISABLED`
- Compose für Prepare, Connector-Lauf, Agenten-Lauf, Cleanup
- Lokale Tests gegen eine Attrappe, bevor irgendetwas läuft
- Runbook mit der Schrittfolge
- Entscheidung über `TELEGRAM_OUTBOUND_POLICY`: auf `METADATA_ONLY` siehst du nur die Ankündigung, nicht die Antwort

## Voraussetzungen für den Lauf

Ein neuer Testbot (alle wurden gelöscht), ein Firewall-Fenster, und die Freigabe aus `DEC-028` beziehungsweise eine eigene Entscheidung.
