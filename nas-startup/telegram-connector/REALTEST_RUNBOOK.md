# Telegram–NAS-Realtest – DSM-Schrittfolge

**Freigabe:** `DEC-024`  
**Ziel:** genau ein privater Telegram-Auftrag an `AI-ENG-001` mit Task-ID `ENG-TG-REALTEST-001`  
**Endzustand:** Connector gestoppt, Testzugang vollständig widerrufen, Bus `DISABLED`, Bot-Token widerrufen und lokal gelöscht

Diese Anleitung ist für einen einmaligen Test. Sie ist keine Freigabe für Dauerbetrieb.

## 1. Vorher prüfen

- Das laufende Container-Manager-Projekt `startup` ist grün.
- Über den bereits geprüften HTTPS-Weg antworten `/health`, `/db-check` und `/bus/v1/status` erfolgreich.
- `/bus/v1/status` zeigt vor dem Test `channel_status: DISABLED`.
- Im Ordner `Startup-Backups` liegt ein frischer Datenbank-Dump mit einer Größe größer als `0 Byte`.
- Auf Router und NAS werden keine neuen Ports geöffnet.

Wenn einer dieser Punkte nicht stimmt: nicht starten.

## 2. Bot sicher anlegen

1. In Telegram den verifizierten Bot `@BotFather` öffnen.
2. `/newbot` senden und genau einen neuen Testbot anlegen.
3. Das angezeigte Bot-Token **nicht in ChatGPT, Codex, E-Mail oder eine Projektdokumentation kopieren**.
4. Dem neuen Bot im privaten Chat `/start` senden.

## 3. Dateien auf der NAS vorbereiten

1. Den Paketordner `telegram-connector` vollständig nach `/docker/Startup/telegram-connector` kopieren.
2. Darin den Ordner `secrets` anlegen.
3. Im DSM-Texteditor die Datei `/docker/Startup/telegram-connector/secrets/telegram_bot_token` erstellen und ausschließlich das BotFather-Token einfügen. Keine Anführungszeichen und keine zweite Zeile.
4. `telegram-realtest.env.example` als `telegram-realtest.env` kopieren.
5. In dieser Datei zunächst unverändert lassen:

```text
TELEGRAM_CONNECTOR_ENABLED=false
TELEGRAM_KILL_SWITCH=true
```

Das Workforce-Token wird später automatisch lokal erzeugt. Es darf nicht manuell kopiert oder angezeigt werden.

## 4. Telegram-IDs ermitteln

1. In Container Manager ein neues temporäres Projekt `startup-telegram-identity` erstellen.
2. Als Pfad `/docker/Startup/telegram-connector` und als Compose-Datei `compose.identity.yaml` wählen.
3. Projekt bauen/starten und danach das Protokoll des einmaligen Containers öffnen.
4. Nur bei `chat_type: private` die beiden Zahlen `chat_id` und `user_id` übernehmen.
5. Diese Zahlen ausschließlich in `telegram-realtest.env` bei `TELEGRAM_ALLOWED_CHAT_ID` und `TELEGRAM_ALLOWED_USER_ID` einsetzen.

Das Protokoll zeigt weder Token noch Nachrichteninhalt. Werden keine IDs angezeigt, dem Bot erneut `/start` senden und den Identity-Probelauf wiederholen.

## 5. Kurzlebigen Testzugang vorbereiten

1. Noch einmal Backup und die drei Health-/Status-Endpunkte prüfen.
2. In Container Manager das temporäre Projekt `startup-telegram-prepare` mit `compose.prepare.yaml` erstellen und einmal starten.
3. Das Protokoll muss mit `PASS` bestätigen:
   - Kanal `TESTING`,
   - Identität `CEO-TG-001`,
   - `task_authority=PROPOSE`,
   - `can_create_handoff=false`,
   - genau zwei aktive Routen,
   - aktiver, noch nicht abgelaufener `ACCEPTANCE`-Zugang.

Der Vorbereitungslauf verweigert den Start automatisch, wenn der Kanal nicht `DISABLED` ist, bereits ein aktiver Zugang existiert, Migration 003 fehlt, Gerd nicht aktiv ist oder der Testtask schon vorhanden ist.

## 6. Einzigen Realtest starten

1. In `telegram-realtest.env` genau diese beiden Werte ändern:

```text
TELEGRAM_CONNECTOR_ENABLED=true
TELEGRAM_KILL_SWITCH=false
```

2. In Container Manager das Projekt `startup-telegram-run` mit `compose.run.yaml` erstellen und starten.
3. Im privaten Bot-Chat `/status` senden. Erwartet wird `Kanal=TESTING`.
4. Danach exakt einmal senden:

```text
/task AI-ENG-001 ENG-TG-REALTEST-001 | Telegram-NAS-Realtest | Technische PENDING-Bestätigung ohne automatische Bearbeitung
```

5. Erwartete Antwort:

```text
PENDING ENG-TG-REALTEST-001 für AI-ENG-001 registriert.
```

Keinen anderen Empfänger, keine andere Task-ID und keinen sensiblen Inhalt senden. Der Auftrag wird nicht automatisch angenommen oder bearbeitet.

## 7. Sofort bereinigen

1. Projekt `startup-telegram-run` stoppen.
2. In `telegram-realtest.env` wieder setzen:

```text
TELEGRAM_CONNECTOR_ENABLED=false
TELEGRAM_KILL_SWITCH=true
```

3. In Container Manager das temporäre Projekt `startup-telegram-cleanup` mit `compose.cleanup.yaml` erstellen und einmal starten.
4. Das Protokoll muss `PASS` zeigen für:
   - Kanal `DISABLED`,
   - Credential `REVOKED`,
   - Capability `REVOKED`,
   - Membership `REVOKED`,
   - Identity `REVOKED`,
   - aktive unverfallene Zugänge `0`,
   - lokale Workforce-Token-Datei entfernt.
5. Bei BotFather mit `/revoke` das Token dieses Testbots widerrufen oder den Testbot mit `/deletebot` löschen.
6. Erst danach die Datei `secrets/telegram_bot_token` auf der NAS löschen.
7. `/health`, `/db-check` und `/bus/v1/status` erneut prüfen; Status muss `DISABLED` bleiben.

Task, Nachricht und Auditspur bleiben absichtlich als Nachweis in PostgreSQL erhalten. Das ist kein aktives Recht.

## Abbruchregel

Bei jeder unerwarteten Antwort zuerst `startup-telegram-run` stoppen. Danach immer Schritt 7 ausführen. Wird der Cleanup nicht mit `PASS` beendet, keine weiteren Tests durchführen und den Zustand dokumentieren; keinesfalls Rechte manuell erweitern oder den Bus auf `ACTIVE` setzen.
