# Telegram–NAS-Realtest 2 – DSM-Schrittfolge

**Freigabe:** `DEC-026` – genau ein Lauf  
**Technische Identität:** `CEO-TG-002` – kein Mitarbeiter und keine CEO-Imitation  
**Ziel:** `AI-ENG-001`  
**Task:** `ENG-TG-REALTEST-002`, zwingend `PENDING`  
**Endzustand:** Connector und temporäre Projekte entfernt, sämtliche `…-002`-Rechte widerrufen, Bus `DISABLED`, aktive Credentials `0`, Bot und lokale Token-Dateien widerrufen beziehungsweise gelöscht, temporäre Firewallregel entfernt

Diese Anleitung erlaubt keinen Dauerbetrieb und keinen zweiten Versuch.

## 1. Vorbedingungen

Vor jeder externen Nachricht müssen alle Punkte `PASS` sein:

1. lokale Connector-Tests und YAML-Prüfungen;
2. wegwerfbarer PostgreSQL-Lauf `realtest2_prepare.sql → PENDING/Dublette/Negativfälle → realtest2_cleanup.sql`;
3. laufendes Projekt `startup`, gesunde Datenbank/API und Bus `DISABLED`;
4. aktive unverfallene Bus-Credentials `0`;
5. frischer Datenbankdump größer als `0 Byte`;
6. keine Projekte `startup-telegram-identity2`, `startup-telegram-prepare2`, `startup-telegram-run2` oder `startup-telegram-cleanup2`;
7. kein altes Workforce-Token und noch kein laufendes v2-Testvolume.

Bei einer Abweichung: nicht starten.

## 2. Bot und Allowlist ausschließlich lokal vorbereiten

1. Genau einen neuen Testbot über den offiziellen `@BotFather` anlegen.
2. Token niemals in Chat, Prompt, Projektquelle, Evidenz oder Git einfügen.
3. Token ausschließlich in `/docker/Startup/telegram-connector/secrets/telegram_bot_token` speichern.
4. Dem Bot im privaten CEO-Chat `/start` senden.
5. `compose.identity.yaml` einmalig als Projekt `startup-telegram-identity2` ausführen.
6. Nur bei `chat_type=private` die ausgegebenen numerischen `chat_id` und `user_id` lokal in `telegram-realtest-2.env` eintragen.
7. Identity-Projekt wieder entfernen.

Die Datei bleibt zunächst fail-closed:

```text
TELEGRAM_CONNECTOR_ENABLED=false
TELEGRAM_KILL_SWITCH=true
TELEGRAM_ALLOWED_RECIPIENT_IDS=AI-ENG-001
TELEGRAM_ALLOWED_TASK_IDS=ENG-TG-REALTEST-002
TELEGRAM_SOURCE_REF=DEC-026/ENG-007
```

## 3. Frischen Kurzzeitzugang vorbereiten

1. Backup, Health, `DISABLED` und aktive Credentials `0` erneut prüfen.
2. Projekt `startup-telegram-prepare2` mit `compose.prepare2.yaml` einmal starten.
3. Das Protokoll muss `PASS` zeigen für `CEO-TG-002`, `PARTICIPANT`, `PROPOSE`, Senden=true, Handoff=false, genau zwei aktive Routen, `ACCEPTANCE`, unverfallen und Kanal `TESTING`.
4. Bei jedem anderen Ergebnis sofort `compose.cleanup2.yaml` ausführen und abbrechen.

## 4. Genau einen Connectorlauf ausführen

1. Temporär in der DSM-Firewall nur `172.31.254.2/32` auf TCP-Zielport `8443` oberhalb der allgemeinen 8443-Verweigerung zulassen.
2. In `telegram-realtest-2.env` genau diese Schalter setzen:

```text
TELEGRAM_CONNECTOR_ENABLED=true
TELEGRAM_KILL_SWITCH=false
```

3. Projekt `startup-telegram-run2` mit `compose.run2.yaml` starten.
4. Im privaten Bot-Chat genau einmal `/status` senden; erwartet wird `Kanal=TESTING`.
5. Danach exakt einmal senden:

```text
/task AI-ENG-001 ENG-TG-REALTEST-002 | Telegram-NAS-Realtest 2 | Technische PENDING-Bestätigung ohne automatische Bearbeitung
```

6. Erwartete Antwort:

```text
PENDING ENG-TG-REALTEST-002 für AI-ENG-001 registriert.
```

Keine freien Texte, weiteren Empfänger oder sensiblen Inhalte senden.

## 5. Unmittelbarer Pflicht-Cleanup

Erfolg, Fehler und Zeitablauf führen in dieselbe Bereinigung:

1. `startup-telegram-run2` stoppen.
2. Environment wieder auf `ENABLED=false` und Kill Switch=true setzen.
3. Projekt `startup-telegram-cleanup2` mit `compose.cleanup2.yaml` einmal ausführen.
4. Nur bei `PASS` für `DISABLED`, Credential/Capability/Membership/Identity `REVOKED` und aktive Credentials `0` fortfahren.
5. Run-, Prepare-, Cleanup- und Identity-Projekt sowie das Volume `telegram_realtest_state_v2` entfernen.
6. Workforce-Token-Datei und anschließend die Bot-Token-Datei löschen.
7. Den Testbot bei BotFather widerrufen beziehungsweise löschen.
8. Temporäre `/32 → TCP 8443`-Regel entfernen und die vier ursprünglichen Firewallregeln prüfen.
9. Projektliste, Netzliste, API/DB und Bus `DISABLED` nachprüfen.

Task-, Nachrichten- und Auditevidenz bleiben append-only erhalten. Erst nach dem vollständigen Rückbau darf der Lauf als abgeschlossen dokumentiert werden.
