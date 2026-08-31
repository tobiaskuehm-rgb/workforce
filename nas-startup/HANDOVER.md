# Arbeitsstand und Prüfschleife

**Zuletzt aktualisiert:** 2026-08-31, spät — von Claude Code

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

## Der maßgebliche Quellensatz

```
~/Library/Mobile Documents/com~apple~CloudDocs/Startup_Codex/
    START_UP_Codex_Projektquellen_2026-08-13/
```

Entscheidungen bis `DEC-027`, `ENG-008` vorhanden, Projektanweisung v1.2. **Das ist der gültige Stand.**

Nicht verwenden: `~/.codex/.chatgpt-projects/…/sources/` bzw. `/mnt/data/…` — Stand 10.08., nur bis `DEC-009`, `ENG-008` fehlt dort ganz.

Zwei Grenzen aus `DEC-027` und `ENG-008`, die gelten:

- **Kein externer kostenpflichtiger Dienst.** `AGENT_PROVIDER=claude` ist ohne neue Entscheidung nicht freigegeben.
- **Der Core sind Gerd, Karl und Anastasia.** Frühere Bus-Abnahmen sind Evidenz, ersetzen den Core-Roundtrip aber nicht.

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
| **ENG-008 Core-Roundtrip** | **CORE PASS** | `2026-08-31_eng008_core_roundtrip.md` |
| Security-Review Agentenschicht | erledigt | `2026-08-31_security_review_agent.md` |

Die Kette **Telegram → NAS → Bus → PostgreSQL** ist real belegt. Der Bus ist abgenommen.

### Gebaut, aber nie mit einem Modell gelaufen

`workforce-agent/` — Worker, Provider-Abstraktion, Datengrenze, Prepare-/Cleanup-Paket, Budget, 56 lokale Tests. Der Echo-Trockenlauf hat den Bus-Weg belegt; `AGENT_PROVIDER=claude` ist noch nie ausgeführt worden.

### Systemzustand

Kanal `DISABLED`, 0 aktive Credentials, keine Secrets abgelegt, keine temporären Firewall-Regeln, nur der Produktivstack läuft.

---

## Offene Punkte

### Entscheidungen beim Nutzer

1. **Datengrenze** — `AGENT_DATA_POLICY`. Voreinstellung `METADATA_ONLY` (kein Nachrichtentext verlässt die NAS). Für echte fachliche Arbeit braucht es `BODY`. **Das blockiert den Modellbetrieb.**
2. **sudo-Regel** (Befund F5) — `/etc/sudoers.d/tobkum-docker`, passwortloser Docker-Zugriff, faktisch Root. Wann zurücknehmen?

### Technisch offen

| Punkt | Stand |
|---|---|
| **A1 — Agent handelt unter Menschen-Identität** | **blockiert den Modellbetrieb.** `agent_identity_create.sql` liegt bereit, nicht ausgeführt |
| A2 Herkunftsvermerk | behoben |
| A3 Laufzeitgrenze | behoben |
| A5 Rückzug bei Busausfall | behoben |
| F8 Ratenbegrenzung / Kostenlimit | behoben, fünf Decken in `budget.py` |
| Rückrichtung Bus → Telegram | konfigurierbar, Voreinstellung unverändert `METADATA_ONLY` |
| Freigabeentscheidung (`DEC-`Nummer) für Modellbetrieb | fehlt |

---

## Hier weitermachen

**Stand:** Gerds zweite Prüfrunde ist eingegangen (Befunde `G-012` bis `G-019` in `REVIEW_GERD.md`). **Alle acht treffen zu.** Drei sind abgearbeitet, fünf offen.

### Erledigt aus Runde zwei

- **G-015** — `CORE PASS` war zu stark und ist zurückgenommen. Der Nachweis trägt jetzt `BUS LIFECYCLE PASS`, das Gate steht auf **`CORE ITERATE`**. `core_roundtrip.py` steuert Bus-Clients direkt und benutzt weder `agent_worker.py` noch `state_store.py`, Claim oder Retry — genau das verlangt `ENG-008` aber.
- **G-012** — `record_reply()` fehlte im `EXHAUSTED`-Zweig. Beim Testen zeigte sich mehr: Der Übergang nach `EXHAUSTED` wurde vom auslösenden Lauf verbraucht; starb der, ging die Schlussmeldung nie raus. `EXHAUSTED` bleibt jetzt beanspruchbar, bis die Meldung verbucht ist.
- **G-013** — Der Claim wird bis zum dauerhaften Ergebnis gehalten, nicht schon beim Providerfehler freigegeben.

### Offen, in dieser Reihenfolge

| # | Was | NAS nötig |
|---|---|---|
| **G-017** | `startup.env` wird komplett gemountet; der nach außen vernetzte `core.run`-Container liest DB-Passwort und API-Schlüssel, **obwohl er die Datenbank gar nicht anfasst**. Mein Kommentar behauptet das Gegenteil. | nein |
| **G-014** | Der Contract-Test zählt **jeden** `BusError` als korrekte Ablehnung — ein 401 oder 500 bestünde. „107/107" ist eine einseitige Ablehnungsmatrix, keine Übereinstimmung. | nein |
| **G-016** | Der Abo-Provider startet die CLI **im Worker-Container** — mit Bus-Token, State-Mount und Bus-Route. Sein eigener Docstring verlangt einen Container ohne all das. | nein |
| **G-018** | `bus_events` enthält nur erfolgreiche Vorgänge; die Audit-Rekonstruktion deckt Ablehnungen nicht ab. | nein |
| **G-019** | Provenienz widersprüchlich: Entwürfe sind keine Entscheidungen, deployter Commit-Hash nicht dokumentiert. | teils CEO |

**Ein Muster, das beim Weiterarbeiten zählt:** G-014, G-016 und G-017 sind alle vom Typ *„Kommentar behauptet eine Absicherung, die der Code nicht herstellt"*. Das ist gefährlicher als ein Bug — ein solcher Kommentar hält den nächsten Leser vom Nachprüfen ab.

### Danach

Gerds Empfehlung, der ich zustimme: **nicht** ein echter Modell- oder Telegram-Lauf, sondern ein **integrierter Worker-Core-Test** mit Echo-Provider, echten Claim-/Retry-Fehlern, Neustart und vollständigem Audit. Erst danach den begonnenen `chain-test/` fertigbauen.

### Beim CEO

- `DEC-028` und `DEC-029` aus `DEC_ENTWUERFE_2026-08-31.md` prüfen und ins Log übernehmen — bis dahin bleibt das Gate formal offen
- sudo-Regel `/etc/sudoers.d/tobkum-docker` entfernen, wenn nicht gebraucht (faktisch Root)

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

**Nachmittag, autonom weitergearbeitet:** Budget mit fünf Decken (F8), zweite Datengrenze zu Telegram, Security-Review der Agentenschicht mit sieben Befunden, davon A2/A3/A5 direkt behoben.

Der wichtigste Fund ist A1: Der Agent nutzt das Credential von `AI-ENG-001` — und dessen Registry-Eintrag ist eine **Person** (`Gerd`, `AI Engineer`, `PROBATION`). Jede Antwort erscheint als Nachricht eines Menschen. Der Telegram-Connector hatte für genau dieses Problem bereits eine eigene technische Identität bekommen (`CEO-TG-002`, Titel „not an employee"); beim Agenten war dieselbe Sorgfalt nicht angewendet worden. `agent_identity_create.sql` legt `AGENT-ENG-001` nach diesem Muster an — nicht ausgeführt, weil eine dauerhafte Registry-Änderung eine Freigabe braucht.

**Abend:** Alle elf Review-Befunde beantwortet, sechs behoben. Der maßgebliche Quellensatz wurde gefunden — und er ändert die Richtung: `DEC-027` und `ENG-008` schließen den bezahlten Modellbetrieb aus, auf den ich hingearbeitet hatte. Der Echo-Provider ist das Geforderte, nicht die Notlösung.

`ENG-008` ist gebaut: Bus-Client um Tasks und Handoffs erweitert, `core_roundtrip.py` fährt die von `DEC-027` verlangte Sequenz in 18 Schritten inklusive Negativfällen, `core_audit.sql` rekonstruiert den Lauf allein aus der Audit-Spur. Prepare für drei Zugänge, Cleanup, Compose-Dateien.

**Als Nächstes:** Core-Roundtrip ausführen — braucht die temporäre Firewall-Regel und eine Freigabe. 89 Agenten-Tests, 35 Connector-Tests.
