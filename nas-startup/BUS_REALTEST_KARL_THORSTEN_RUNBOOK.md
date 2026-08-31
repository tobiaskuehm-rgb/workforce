# Bus-Realtest Karl ↔ Thorsten – DSM-Schrittfolge

**Freigabe:** durch dich erteilt (eine Freigabe für die komplette Testsequenz, 2026-08-31)
**Ziel:** genau ein bidirektionaler Nachrichtenwechsel über den echten HTTPS-Weg zwischen Karl (`SAO-001`) und Thorsten (`RAS-001`)
**Endzustand:** beide Testzugänge widerrufen, Kanal `DISABLED`, Nachrichten/Audit bleiben als Nachweis in PostgreSQL erhalten

Diese Anleitung ist für einen einmaligen Test. Sie ist keine Freigabe für Dauerbetrieb oder `ACTIVE`.

Alle Dateien liegen in `bus-realtest/`. Details/Sicherheitsgrenzen: `bus-realtest/README.md`.

## 0. Was ich (Claude) nicht kann

Ich habe aus meiner Umgebung keinen Zugriff auf deine NAS. Jeden der folgenden Schritte musst du selbst in Container Manager/DSM ausführen und mir danach das Protokoll (Copy-Paste) zurückgeben, bevor wir zum nächsten Schritt gehen.

## 1. Vorher prüfen

- Container-Manager-Projekt `startup` ist grün (`db` und `workforce-api` gesund).
- `/health`, `/db-check`, `/bus/v1/status` antworten über den bereits geprüften HTTPS-Weg erfolgreich.
- `/bus/v1/status` zeigt vor dem Test `channel_status: DISABLED`.
- Ein frischer Datenbank-Dump liegt in `Startup-Backups` und ist größer als 0 Byte.
- Auf Router/NAS werden keine neuen Ports geöffnet.

Wenn einer dieser Punkte nicht stimmt: nicht starten, mir stattdessen Bescheid geben.

## 2. Dateien auf die NAS kopieren

1. Den kompletten Ordner `bus-realtest/` nach `/docker/Startup/bus-realtest` kopieren.
2. Darin existiert bereits ein leerer Unterordner `secrets/` — lokal auf der NAS lassen, nicht mit Inhalt aus diesem Repository befüllen.
3. Adresse und Referenz sind bereits fest in `compose.prepare.yaml` und `compose.run.yaml` eingetragen (`https://192-168-68-78.k30068872219.direct.quickconnect.to:8443` bzw. `DEC-027/ENG-003`, beides am 2026-08-31 bestätigt). Es muss nichts mehr von Hand ausgefüllt werden; `bus-realtest.env` dient nur noch als Notiz.

## 3. Testzugänge vorbereiten (`TESTING` + 2 Credentials)

1. In Container Manager ein temporäres Projekt `startup-bus-realtest-prepare` mit Pfad `/docker/Startup/bus-realtest` und Compose-Datei `compose.prepare.yaml` anlegen.
2. Projekt einmal starten und das Protokoll des Einmalcontainers öffnen.
4. Erwartet: `result | PASS`, `channel_status | TESTING`, für `SAO-001` und `RAS-001` je eine Zeile mit `credential_status | ACTIVE` und `credential_unexpired | t`.
5. Der Lauf verweigert sich automatisch, wenn der Kanal nicht `DISABLED` war, bereits ein aktiver Zugang existiert, Migration 003 fehlt oder Karl/Thorsten nicht aktiv sind.

**Schick mir dieses Protokoll**, bevor du weitermachst.

## 4. Realtest ausführen

1. In Container Manager ein temporäres Projekt `startup-bus-realtest-run` mit Pfad `/docker/Startup/bus-realtest` und Compose-Datei `compose.run.yaml` anlegen.
2. **DSM-Firewall vorbereiten:** Der Testcontainer bekommt die feste Adresse `172.31.254.2` im isolierten Netz `172.31.254.0/29` — dasselbe Muster, das `DEC-025` beim Netzcheck bereits erfolgreich verwendet hat. In **Systemsteuerung → Sicherheit → Firewall** eine temporäre Regel anlegen: TCP-Zielport `8443`, Quelle ausschließlich `172.31.254.2/32`, Aktion `Zulassen`. Die Regel muss über den bestehenden Verweigern-Regeln stehen. Sie wird in Schritt 5 wieder entfernt.
3. Projekt einmal starten und das Protokoll öffnen.
4. Erwartet: eine einzelne JSON-Zeile mit `"result": "PASS"`, einer `outbound_message_id`, einer `reply_message_id` und einem siebenteiligen `transcript` (Statuscheck, Karl sendet, Thorsten liest, Thorsten bestätigt, Thorsten antwortet, Karl liest, Karl bestätigt).
5. Bei `"result": "FAIL"` oder `"result": "BLOCKED"`: nicht wiederholen, direkt zu Schritt 5 (Bereinigung) gehen und mir das Protokoll schicken.

**Schick mir dieses Protokoll**, bevor du weitermachst.

## 5. Sofort bereinigen (immer, auch nach einem Fehler)

1. Projekt `startup-bus-realtest-run` stoppen.
2. In Container Manager ein temporäres Projekt `startup-bus-realtest-cleanup` mit Pfad `/docker/Startup/bus-realtest` und Compose-Datei `compose.cleanup.yaml` anlegen und einmal starten.
3. Erwartet: `result | PASS`, `channel_status | DISABLED`, beide `credential_status | REVOKED`, `active_unexpired_credentials_total | 0`.
4. Danach `/health`, `/db-check`, `/bus/v1/status` erneut prüfen — Status muss wieder `DISABLED` sein.
5. Die beiden Token-Dateien in `bus-realtest/secrets/` auf der NAS manuell löschen.
6. Die drei temporären Container-Manager-Projekte (`prepare`, `run`, `cleanup`) entfernen.
7. Die in Schritt 4 angelegte Firewall-Regel für `172.31.254.2/32` auf TCP `8443` wieder löschen und danach kontrollieren, dass die ursprünglichen Regeln unverändert sind.

**Schick mir dieses Protokoll ebenfalls.**

Nachrichten, Bestätigungen und Audit-Einträge aus dem Test bleiben absichtlich als Nachweis in PostgreSQL erhalten. Das ist kein aktives Recht.

## Abbruchregel

Bei jeder unerwarteten Antwort in Schritt 3 oder 4 sofort zu Schritt 5 springen. Kein Wiederholen mit denselben Credentials. Wird der Cleanup nicht mit `PASS` beendet: keine weiteren Tests durchführen, mir den Zustand schicken, keinesfalls den Kanal manuell auf `ACTIVE` setzen oder Rechte erweitern.

## Danach

Nach einem sauberen `PASS` in Schritt 4 und `PASS` in Schritt 5 ist der reale bidirektionale Test aus `WORKFORCE_BUS_ROLLOUT.md` (Aktivierungsgate, Punkt 4) erbracht. Offen bleiben laut diesem Gate weiterhin: Negativtests außerhalb `START-UP`/nach Widerruf/jenseits Schleifenlimit über die echte API, sowie das dokumentierte Security-Review — dazu machen wir im nächsten Schritt weiter.
