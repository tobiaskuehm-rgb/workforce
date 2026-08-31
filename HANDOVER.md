# Arbeitsstand und Prüfschleife

**Zuletzt aktualisiert:** 2026-08-31, 16:15 — von Claude Code

## Wie die Zusammenarbeit läuft

**Claude Code programmiert. Codex (Gerd) prüft.** Nur eine Seite ändert Code — damit kann nichts kollidieren.

| Datei | Wer schreibt | Wer liest | Wo |
|---|---|---|---|
| `REVIEW_GERD.md` | **nur Gerd** | Claude | NAS `/docker/Startup/` |
| `REVIEW_ANTWORTEN.md` | **nur Claude** | Gerd | NAS `/docker/Startup/` |
| `HANDOVER.md` (diese) | Claude | Gerd | NAS + Repo |
| Quellcode | **nur Claude** | Gerd | Repo, deployt auf NAS |

Jede Seite schreibt ausschließlich ihre eigene Datei. Niemand editiert die des anderen — deshalb braucht es keine Sperren und keine Absprache über Reihenfolge.

**Ablauf:** Gerd trägt Befunde in `REVIEW_GERD.md` ein → Claude liest sie beim nächsten Mal, arbeitet sie ab und antwortet in `REVIEW_ANTWORTEN.md` → offen bleibt, was der Nutzer entscheiden muss.

Ein Befund wird nie gelöscht, sondern beantwortet. Auch „stimmt nicht, weil …" ist ein Ergebnis.

## Wo die Wahrheit liegt

```
Mac-Repo  /Users/Tobi/Documents/Codex/workorce claude/nas-startup/   ← Quelle der Wahrheit
NAS       /volume1/docker/Startup/                                    ← Ziel, kein Git
```

Die NAS hat **kein Git**. Am Code wird im Repo gearbeitet, auf die NAS wird deployt. Ausnahme sind die beiden Review-Dateien: Die leben auf der NAS, weil Gerd nur dort hinkommt.

Deploy (`rsync` und `scp` funktionieren auf dieser DSM nicht):

```bash
cd "/Users/Tobi/Documents/Codex/workorce claude/nas-startup" && tar czf - <pfade> | ssh synology "cd /volume1/docker/Startup && tar xzf - && find . -name '._*' -delete"
```

---

## Stand der Arbeit

### Fertig und nachgewiesen

| Baustein | Zustand | Nachweis in `evidence/` |
|---|---|---|
| PostgreSQL-Schema (Migrationen 001–003) | produktiv | — |
| Workforce-API `v7` (FastAPI) | läuft, gesund | — |
| HTTPS über Reverse Proxy 8443 | verifiziert | — |
| Bus-Realtest Karl ↔ Thorsten | **PASS** | `2026-08-31_bus_realtest_karl_thorsten.md` |
| 20 Negativtests über die echte API | **PASS** | dito |
| Widerrufstest (Gate-Punkt 6 komplett) | **PASS** | `2026-08-31_telegram_realtest_2_und_widerrufstest.md` |
| Telegram-Realtest 2 | **PASS** | dito |
| Security-Review Bus | erledigt | `2026-08-31_security_review_workforce_bus.md` |
| Agenten-Trockenlauf (Echo) | **PASS** | `2026-08-31_agent_dryrun.md` |

Die Kette **Telegram → NAS → Bus → PostgreSQL** ist real belegt. Der Bus ist abgenommen.

### Gebaut, aber nie mit einem Modell gelaufen

`workforce-agent/` — Worker, Provider-Abstraktion, Datengrenze, Prepare-/Cleanup-Paket, 27 lokale Tests. Der Echo-Trockenlauf hat den Bus-Weg belegt; `AGENT_PROVIDER=claude` ist noch nie ausgeführt worden.

### Systemzustand

Kanal `DISABLED`, 0 aktive Credentials, keine Secrets abgelegt, keine temporären Firewall-Regeln, nur der Produktivstack läuft.

---

## Offene Punkte

### Entscheidungen beim Nutzer

1. **Datengrenze** — `AGENT_DATA_POLICY`. Voreinstellung `METADATA_ONLY` (kein Nachrichtentext verlässt die NAS). Für echte fachliche Arbeit braucht es `BODY`. **Das blockiert den Modellbetrieb.**
2. **sudo-Regel** (Befund F5) — `/etc/sudoers.d/tobkum-docker`, passwortloser Docker-Zugriff, faktisch Root. Wann zurücknehmen?

### Technisch offen

| Punkt | Warum es zählt |
|---|---|
| Security-Review der **Agentenschicht** | Gate für den ersten echten Modellbetrieb |
| Keine Ratenbegrenzung (Befund F8) | Beim Agenten schwerer als beim Menschen: ein fehlgeleiteter Agent wird nicht müde |
| Kein Kostenlimit | `AGENT_MAX_CYCLES` begrenzt Zyklen, nicht Nachrichten pro Zyklus |
| Rückrichtung Bus → Telegram | Nie zusammen mit der Agentenschicht erprobt |
| Freigabeentscheidung (`DEC-`Nummer) für Modellbetrieb | fehlt |

---

## Was zuletzt passiert ist

### 2026-08-31 — Claude Code

Bus abgenommen (alle sieben Gate-Punkte), Telegram-Kette real belegt, Agentenschicht gebaut und im Trockenlauf bewiesen. Security-Befunde F1–F4, F6, F7 behoben.

Vier Defekte gefunden und behoben, die den Betrieb blockiert hätten:

- Falscher Reverse-Proxy-Host (`-77` statt `-78`) in vier Telegram-Dateien
- Das Bus-Realtest-Paket war nur einmal ausführbar — widerrufene Credentials lassen sich per Trigger nie reaktivieren, also kollidierte ein zweiter Lauf am Primärschlüssel
- psql ersetzt `:'var'` **nicht** innerhalb von `DO`-Blöcken; umgestellt auf `set_config`/`current_setting`
- `cap_drop: ALL` entzieht `root` auch `CAP_DAC_OVERRIDE`, `CAP_FOWNER` und `CAP_CHOWN`. Fiel erst auf, nachdem die Verzeichnisrechte verschärft waren, in einer Kette von vier Fehlschlägen

Ein eigener Fehler: erfundene SDK-Version `anthropic==1.4.0` (real `1.2.0`) kostete einen Build.

**Als Nächstes:** Security-Review der Agentenschicht.
