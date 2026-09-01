# Kettentest — Telegram → Bus → Agent → Bus → Telegram

**Status:** **startbereit.** Lokal grün, auf der NAS noch nie gelaufen. Der Lauf braucht eine Freigabe, ein Firewall-Fenster und einen Telegram-Testbot.

## Wozu

Jedes Stück der Zielkette ist einzeln belegt — Telegram-Realtest, Agenten-Trockenlauf, Core-Roundtrip. **Zusammen gelaufen sind sie nie.** Dieser Test zeigt die Kette einmal als Ganzes, mit dem Echo-Provider und damit ohne Kosten und ohne Modell.

```
Telegram  /task AGENT-ENG-001 ENG-CHAIN-… | Titel | Output
   ↓
Connector  legt Task PENDING an + Nachricht mit task_ref
   ↓
Bus        Routenprüfung, Idempotenz, Audit
   ↓
Agent      poll_once() → Echo-Provider → Antwort mit derselben task_ref
   ↓
Bus        Rückroute AGENT → Connector
   ↓
Connector  publish_inbox_notifications()
   ↓
Telegram   Benachrichtigung im Chat
```

## Drei Funde beim Durchdenken und Bauen

Jeder hätte im Fenster je einen Anlauf gekostet.

**1. Die Rückrichtung war strukturell unmöglich.** `realtest2_prepare.sql` legt ausschließlich `ROUTE-CEOTG002-AIENG001-{TASK,MESSAGE}` an — nur ausgehend. Keine Route erlaubte je irgendjemandem, der Connector-Identität zu schreiben. `publish_inbox_notifications()` hätte immer eine leere Inbox gefunden. `chain_prepare.sql` legt beide Richtungen an, und `test_chain.py` hält den Fall als Test fest, damit er nicht zurückkommt.

**2. Die Agentenantwort trug keine Task-Referenz.** Der Connector gibt einen Nachrichtentext nur weiter, wenn dessen `task_ref` auf der Allowlist steht (Befund `G-003`). Die Antwort des Agenten hatte gar keine — die eigene Sicherheitsprüfung hätte die Kette blockiert. Behoben: `bus_client.send_message()` nimmt `task_ref`, der Worker reicht sie durch.

**3. Der Connector kann die ehrliche Provenienz nicht schreiben.** `SOURCE_REF_PATTERN` verlangt `^DEC-\d{3}/ENG-\d{3}$` — der Platzhalter `CEO-CHAT-…/PENDING-DEC`, den der Rest des Projekts nach Befund `G-006` benutzt, passt nicht durch. **Aufgelöst, nicht umgangen:** Der Connector schreibt `DEC-023/ENG-007`, und das ist wahr — es ist die Entscheidung, die diesen Connector erlaubt. Die Provenienz des *Kettentests* ist eine andere und steht im SQL. Zwei Quellreferenzen, jede an ihrer Stelle korrekt.

## Lokale Prüfung — vor allem anderen

```bash
cd nas-startup/chain-test && python3 -m unittest discover -q
```

Kein Netz, kein Bot, keine Zugangsdaten, keine Kosten. **Echter Connector, echter Worker**, echte Zustandsdateien; Attrappen nur an den zwei Außenrändern, Telegram und Bus. Die Bus-Attrappe setzt die Routen-Allowlist durch, weil die unmögliche Rückrichtung genau der Defekt war, nach dem dieses Paket entstand.

Läuft seit dem 2026-09-01 auch mit Python 3.9: `telegram_connector.py` benutzt `timezone.utc` statt des 3.11er `datetime.UTC`. Eine Suite, die nur im Container läuft, wird nicht gelaufen (Befund `G-011`).

## Was der Lauf braucht

| | Wer |
|---|---|
| Ein **neuer Telegram-Testbot** samt Token in `secrets/telegram_bot_token` | du — alle alten wurden gelöscht |
| `TELEGRAM_ALLOWED_CHAT_ID` und `_USER_ID` aus `identity_probe.py` | du, einmal gegen den neuen Bot |
| Firewall-Regel für **`172.31.254.0/29`** auf TCP 8443 | du in DSM |
| `AGENT-ENG-001` in der Registry | prüft `chain_prepare.sql` und bricht sonst ab |
| `startup.db.env` | liegt seit 2026-08-31 auf der NAS |
| Freigabe im Chat | du |

**Die Firewall-Regel ist breiter als bei früheren Läufen.** Connector und Agent sind zwei Container und brauchen zwei Adressen (`.2` und `.3`); ein einzelnes `/32` reicht nicht mehr.

## Die Entscheidung ist gefallen: `METADATA_ONLY`

**Entschieden am 2026-09-01.** Der erste Lauf soll zeigen, dass die Kette sich schließt — nicht, dass eine Echo-Antwort lesbar ist. Eine Benachrichtigung im Chat belegt die Rückrichtung vollständig.

`TELEGRAM_OUTBOUND_POLICY` in `chain.env`:

- **`METADATA_ONLY`** (Voreinstellung, fail-closed) — du siehst *„eine Antwort ist da"*, nicht ihren Text. **Die Kette ist damit trotzdem bewiesen:** Eine Benachrichtigung im Chat heißt, dass die Rückrichtung funktioniert hat.
- **`BODY`** — der Antworttext selbst erscheint gekürzt im Chat, und nur für Nachrichten, deren Task auf der Allowlist steht.

Telegram-Bot-Chats sind Cloud-Chats ohne Ende-zu-Ende-Verschlüsselung. `BODY` heißt, dass interne Arbeitsinhalte bei Telegram liegen. Ein späterer Wechsel auf `BODY` ist eine eigene Entscheidung und gehört dokumentiert — es ist eine Datengrenze, kein Ausführlichkeitsschalter.

## Schrittfolge

```bash
# 1  Vorbereiten: Identität, beide Routen, zwei Zugänge, Kanal auf TESTING
sudo /usr/local/bin/docker compose -f compose.chain-prepare.yaml up --abort-on-container-exit

# 2  Firewall-Fenster in DSM öffnen: 172.31.254.0/29 auf TCP 8443

# 3  Kette starten, beide Container zusammen
sudo /usr/local/bin/docker compose -f compose.chain-run.yaml up --build

# 4  In Telegram senden:
#    /task AGENT-ENG-001 ENG-CHAIN-20260901 | Kurze Lagebeurteilung | Drei Saetze
#    Erwartung: "PENDING … registriert", dann eine NACHRICHT-Benachrichtigung

# 5  Rückbau — läuft in jedem Fall, auch nach Abbruch
sudo /usr/local/bin/docker compose -f compose.chain-run.yaml down
sudo /usr/local/bin/docker compose -f compose.chain-cleanup.yaml up --abort-on-container-exit

# 6  Firewall-Regel zurücknehmen, Token-Dateien löschen, nachmessen statt nachlesen
```

Der volle Docker-Pfad ist nicht kosmetisch: Die passwortlose sudo-Regel lautet auf `/usr/local/bin/docker`, und in einer nicht-interaktiven SSH-Sitzung liegt `docker` nicht im `PATH`.

## Was danach zu erwarten ist

Ein `PASS` heißt: Die Kette ist geschlossen. Es heißt **nicht**, dass ein Modell je geantwortet hat — der Provider ist Echo, und das ist so gewollt. Der bezahlte Lauf ist ein eigener Schritt mit eigener Entscheidung.

## Was noch fehlt

- `chain_audit.sql` — Rekonstruktion des Laufs aus `bus_events` und `bus_denials`, nach dem Muster von `workercore_audit.sql`. Sinnvoll erst, wenn Migration `004` auf der NAS ist.
