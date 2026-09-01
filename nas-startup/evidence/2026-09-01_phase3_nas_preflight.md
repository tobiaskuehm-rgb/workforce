# Nachweis: Phase 3 — NAS-Preflight

**Datum:** 2026-09-01, 11:55–12:05
**Roadmap:** Phase 3 aus `REVIEW_GERD.md`
**Freigabe:** CEO im Chat („los phase 3")
**Ergebnis:** **`PREFLIGHT PASS`** — Iststand gemessen, Rückfallpunkte gesichert und verifiziert, keine unerwartete Datei, kein Secret im Deploypaket

**Kein Rollout.** Weder `compose.yaml` noch `postgres-init/` noch `workforce-api/` wurden auf die NAS gebracht. Keine Migration angewendet, kein Container verändert.

---

## 1. Iststand, gemessen

| | |
|---|---|
| Laufende API | `startup-workforce-api:v7`, `Up (healthy)`, meldet `api_version v7`, `channel_status DISABLED` |
| Datenbank | `postgres:17-alpine`, `Up (healthy)`, 9.646 kB |
| Angewendete Migrationen | `001_employee_registry`, `002_workforce_bus`, `003_workforce_bus_trigger_fix` |
| Kanal | `DISABLED` |
| Aktive Credentials | **0** |
| Knowledge (`004`) | nicht angewendet |
| Ablehnungs-Audit (`005`) | nicht angewendet |
| Rolle `workforce_api` (`007`) | fehlt — muss vor `007` angelegt werden |
| Alt-Registry-Tabellen (`006`) | alle 7 vorhanden — `006` wird ein No-op |

**Damit ist belegt:** Der Produktivstand ist unberührt von allem, was seit dem 2026-08-31 im Repo entstanden ist. Keines der neuen Gates hat versehentlich ausgelöst.

## 2. Provenienz

`verify_production_state.sh`: **6 von 6 Dateien stimmen byteweise mit `ff2d32a`** überein — `compose.yaml`, `app.py`, `Dockerfile` und die drei angewendeten Migrationen. Tag `produktiv-v7`, lokal und auf dem NAS-Remote.

## 3. Rückfallpunkte, gesichert **und** verifiziert

| Datei | Größe | Rechte |
|---|---|---|
| `preflight-2026-09-01_11-56-11.sql` | 357.575 B | `640 root:administrators` |
| `preflight-2026-09-01_11-56-11.globals.sql` | 681 B, 1 `CREATE ROLE` | `640 root:administrators` |
| `rollback-workforce-api-v7-2026-09-01_11-56-11.tar.gz` | 25 MB | `640 root:administrators` |

Image-ID des Rückfallstands: `sha256:6c9ef655f7f4d507f50202a9731499bf89c8ef4d784963fea37d17e02fab61bf`

**Der Rollen-Dump schließt die Lücke aus `G-024`.** Der nächtliche Job schreibt nur `pg_dump`, also ohne `CREATE ROLE` — deshalb war er nicht sauber einspielbar. Das Preflight-Paar ist beides.

**Verifiziert, nicht angenommen.** In einem isolierten Container mit `tmpfs`, ohne Verbindung zur Produktivdatenbank:

```
globals einspielen:   0 Fehler
Datenbank einspielen: 0 Fehler
Gegenprobe:           28 Nachrichten | 9 Tasks | 15 Tabellen | Eigentuemer workforce_app
```

Deckungsgleich mit der Produktion. **Das ist ein bekannter Rückfallpunkt, kein hoffentlich brauchbarer.** Container und Netz danach restlos entfernt.

## 4. Manifest und Secret-Hygiene

`verify_manifest.sh`: **126 Dateien, nichts fehlend, nichts abweichend, nichts unerwartet.**

`check_backup_permissions.sh` nach dem Schreiben der drei neuen Dateien: **56 Dateien, keine mit Welt-Lese- oder Welt-Schreibrecht, kein `everyone` in der ACL.** Die Härtung aus `G-022` hat das Schreiben überstanden, weil die neuen Dateien ausdrücklich auf `640 root:administrators` gesetzt wurden.

## 5. Ein Nebeneffekt der Härtung, der dokumentiert gehört

Der erste Versuch, das Rückfall-Image zu schreiben, scheiterte mit `Permission denied`. Grund: `Startup-Backups` gehört seit `G-022` `root:administrators` mit `750` — die Gruppe darf **lesen, nicht schreiben**. Die Shell-Umleitung lief als `TOBKUM`.

Das ist richtig so: In den Sicherungsordner schreibt nur Root, und der nächtliche Job läuft als Root. **Wer künftig dort etwas ablegen will, braucht `sudo` — eine Shell-Umleitung genügt nicht.**

## 6. Was Phase 3 ausdrücklich nicht getan hat

- **Kein Deployment von `compose.yaml`.** Die Datei im Repo zeigt auf `startup-workforce-api:v8`, ein Image, das auf der NAS nicht existiert. Ein unbeabsichtigter `docker compose up` würde es bauen und den laufenden v7-Container ersetzen — also ungewollt Phase 4 auslösen. Sie geht erst im Rollout-Fenster mit.
- **Keine Migration angewendet.** Alle vier Gates stehen auf `false`.
- **Kein Container verändert**, keine Rechte außerhalb der drei neu geschriebenen Dateien, kein Modellaufruf.

## 7. Voraussetzungen für Phase 4

1. **CEO-Freigabe für genau das Rollout-Fenster** — Phase 3 deckt sie nicht ab
2. `CREATE ROLE workforce_api` und `workforce_backup` mit Passwörtern aus dem Secret-Store, **vor** Migration `007`
3. Entscheidung, welche Gates im Fenster geöffnet werden. Nach Gerds Empfehlung: `005`, `006`, `007` — **ohne** `004` Knowledge, das hat ein eigenes Gate
4. Neues Passwort für `workforce_api` in `startup.env`, sonst spricht die API weiter als `workforce_app`
