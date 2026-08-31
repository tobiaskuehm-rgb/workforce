# Telegram-CEO-Pilotconnector

**Status:** `DEC-025`-NAS-Netzcheck und Rückbau `PASS`; `DEC-026` gibt genau einen neuen Realtest mit frischen `…-002`-Identitäten frei. Sichere Vorbereitung und Ausführung stehen aus; Dauerbetrieb und jede weitere Wiederholung bleiben gesperrt.

## Zweck

Der Connector ist ein schmaler Transportadapter zwischen genau einem privaten Telegram-CEO-Chat und dem vorhandenen `START-UP`-Workforce-Bus. Er verwendet ausgehendes Long Polling und benötigt deshalb keinen eingehenden NAS- oder Router-Port. Telegram speichert nicht den verbindlichen Arbeitsstand; Aufgaben, Nachrichten und Status bleiben im Workforce-Bus.

## Sicherheitsgrenzen

- Start nur mit `TELEGRAM_CONNECTOR_ENABLED=true` **und** `TELEGRAM_KILL_SWITCH=false`.
- Genau eine numerische Chat-ID plus eine numerische Benutzer-ID; Gruppen werden abgewiesen.
- Nur die explizite Mitarbeiter-Allowlist ist adressierbar.
- Neue Aufgaben werden immer als `PENDING` erzeugt.
- Die Gegenrichtung liest nur die Inbox der später ausdrücklich genehmigten Connector-Identität und sendet eine kurze Metadaten-/Betreff-Zusammenfassung; der Nachrichtenbody bleibt auf der NAS.
- Telegram-`update_id` und Workforce-`Idempotency-Key` verhindern Doppelverarbeitung.
- SQLite speichert nur Zustell-/Verarbeitungsstatus und kurze Auditmetadaten, niemals Bot-/Bus-Token oder vollständige Auftragsinhalte.
- Workforce-Aufrufe sind ausschließlich über HTTPS zulässig.
- Kein Webhook, kein eingehender Port, keine Kundenkommunikation und keine automatische geschäftliche Entscheidung.

Telegram-Bot-Chats sind Cloud-Chats und keine Ende-zu-Ende-verschlüsselten Secret Chats. Deshalb gehören nur IDs, kurze Arbeitsaufträge, Zustände und kurze Ergebniszusammenfassungen in diesen Kanal. Secrets, sensible Volltexte, Employee Memory und höher geschütztes Knowledge bleiben auf der NAS.

## Lokaler Test

Im Ordner ausführen:

```text
python3 -m unittest discover -v
```

Die Tests verwenden ausschließlich simulierte Telegram- und Workforce-Gegenstellen. Sie benötigen keine Tokens und erzeugen keine Netzwerkverbindung.

Für ein kurzes sichtbares Protokoll ohne Netzwerkzugriff:

```text
python3 local_demo.py
```

## Vorgesehene Kommandos

```text
/help
/status
/task AI-ENG-001 ENG-TG-REALTEST-002 | Telegram-NAS-Realtest 2 | Technische PENDING-Bestätigung ohne automatische Bearbeitung
```

Im aktiven Testbetrieb prüft jeder Poll-Zyklus außerdem die Workforce-Inbox. Eine neue Nachricht wird höchstens einmal als kurze Telegram-Zusammenfassung zugestellt; sie wird dadurch nicht automatisch als fachlich angenommen bestätigt.

Freie Texte, Gruppen, andere Benutzer, nicht freigegebene Empfänger, unsicheres HTTP und unbekannte Kommandos werden verweigert.

## Historischer einmaliger Realtest nach DEC-024

Der CEO hatte den einmaligen Realtest freigegeben. Die Freigabe ist durch den abgebrochenen Versuch verbraucht. Der damalige Scope war ausschließlich:

1. technische Acceptance-Identität `CEO-TG-001` – ausdrücklich kein Mitarbeiter und keine CEO-Imitation,
2. Empfänger `AI-ENG-001` (Gerd),
3. Task `ENG-TG-REALTEST-001`, immer mit Status `PENDING`,
4. ein höchstens 30 Minuten gültiger Workforce-Zugang,
5. Bus-Kanal höchstens `TESTING`, niemals `ACTIVE`,
6. genau ein privater CEO-Bot-Chat und eine CEO-Benutzer-ID,
7. vollständiger Widerruf und Kanal `DISABLED` unmittelbar nach dem Test.

Die vier getrennten Compose-Dateien bilden die sichere Reihenfolge ab: `compose.identity.yaml`, `compose.prepare.yaml`, `compose.run.yaml`, `compose.cleanup.yaml`. Die genaue DSM-Anleitung steht in `REALTEST_RUNBOOK.md`.

## v2-Fix und abgeschlossener tokenfreier Netzcheck

Der generische Fehlercode verdeckte bisher, ob DNS, TLS, Timeout, Verbindungsablehnung oder ein anderer Netzwerkfehler vorlag. Der v2-Kandidat ergänzt deshalb stabile, secretfreie Fehlercodes und einen tokenfreien HTTPS-Vorabtest über `compose.network-check.yaml`. Der Vorabtest prüft ausschließlich `/health`, `/db-check` und `/bus/v1/status` und akzeptiert standardmäßig nur den sicheren Kanalzustand `DISABLED`.

`DEC-025` hat genau einen tokenfreien NAS-Netzcheck mit der festen Quelladresse `172.31.254.2` im isolierten Netz `172.31.254.0/29` freigegeben. Die Kollisionsprüfung war frei. Der einmalige Containerlauf bestätigte bei `Exit Code: 0` alle drei HTTPS-Endpunkte, API `v6`, Projekt `START-UP`, Kanal `DISABLED`, `credential_used=false`, `transport=HTTPS_VERIFIED` und `result=PASS`. Danach wurden Projekt, Container, Netz und die ausschließlich für `172.31.254.2/32` auf TCP-Zielport `8443` angelegte Regel vollständig entfernt; die ursprünglichen Projekte, Netze und Firewallregeln wurden direkt bestätigt. Die Einmalfreigabe ist verbraucht. Ein Telegram-Realtest benötigt weiterhin eine neue ausdrückliche CEO-Entscheidung; ein kompletter Docker-Adressbereich und Port `8080` bleiben gesperrt.

## Historische NAS-Vorbereitung für `DEC-024`

- Den gesamten Ordner nach `/docker/Startup/telegram-connector` kopieren.
- `telegram-realtest.env.example` lokal auf der NAS als `telegram-realtest.env` kopieren und dort nur Chat-ID und Benutzer-ID eintragen; die echte Datei nicht zurück in den Projektordner übernehmen.
- Zunächst `TELEGRAM_CONNECTOR_ENABLED=false` und `TELEGRAM_KILL_SWITCH=true` lassen.
- Das Bot-Token ausschließlich als Datei `secrets/telegram_bot_token` auf der NAS hinterlegen. Das kurzlebige Workforce-Token wird bei der Vorbereitung automatisch lokal erzeugt und beim Cleanup wieder entfernt.
- Erst nach frischem, nicht leerem Datenbank-Backup sowie erfolgreichen Healthchecks vorbereiten und starten.
- Das Volume `telegram_realtest_state_v1` enthält nur Connector-Audit und Update-Deduplizierung; das Workforce-Datenvolume bleibt unberührt.
- Nach dem einzigen Test den Connector stoppen, `compose.cleanup.yaml` ausführen, beide Schalter wieder sperren, das Bot-Token bei BotFather widerrufen und die lokale Token-Datei löschen.

Die Compose-Datei ist eine isolierte Pilotvorlage und wird nicht automatisch in das laufende Projekt `startup` aufgenommen.

## Aktueller zweiter Einmaltest nach `DEC-026`

Die widerrufene Identität `CEO-TG-001` und sämtliche `…-001`-Belege bleiben unverändert. Der neue Lauf verwendet ausschließlich `CEO-TG-002`, `CRED-TG-CEO-REALTEST-002`, `ENG-TG-REALTEST-002`, `DEC-026/ENG-007`, `telegram-realtest-2.env` und die drei Compose-Dateien `compose.prepare2.yaml`, `compose.run2.yaml`, `compose.cleanup2.yaml`. Das getrennte Volume heißt `telegram_realtest_state_v2`.

Vor Ausführung sind die lokalen Tests, der wegwerfbare PostgreSQL-Probelauf, ein frisches NAS-Backup, gesunde Endpunkte, Bus `DISABLED`, aktive Credentials `0` und die ausschließlich lokale Bot-/Chat-/Benutzer-Allowlist nachzuweisen. Die vollständige Schrittfolge und der verpflichtende Rückbau stehen in `REALTEST2_RUNBOOK.md`. Diese Freigabe umfasst keinen Dauerbetrieb und keinen weiteren Test.
