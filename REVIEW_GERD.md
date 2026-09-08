# Gerd-Review — Neubau `workforce/`

## 2026-09-08 — fokussierter Lauf nach dem ersten Modellbetrieb

Prüfumfang: `workforce/config.py`, `workforce/providers.py`, `workforce/store.py`
und die zugehörigen Tests. Keine NAS-, Kanal-, Credential-, Skill- oder
Produktivänderung.

| ID | Schwere | Befund | Korrektur/Nachweis |
|---|---:|---|---|
| `G-092` | hoch | `ollama_url` akzeptierte beliebige HTTP-Ziele. Damit konnte ein als lokal deklarierter Provider Inhalte außer Haus senden. | Nur Loopback und die ausdrücklich benannte lokale Container-Brücke `host.docker.internal` sind zulässig; Konfiguration und Provider prüfen unabhängig. Fremdziel-Gegenprobe rot. |
| `G-093` | mittel | Negative Lease-Werte und unbrauchbare Retry-/Aufrufgrenzen wurden beim Start akzeptiert. Dadurch konnten Claims sofort verfallen oder der Betrieb unkontrollierbar werden. | Ganzzahlige, positive und begrenzte Werte werden beim Start erzwungen; String und Bool sind ebenfalls abgelehnt. |
| `G-094` | hoch | Eine Secret-Datei mit Modus `0660` galt als geschützt, obwohl der Vertrag ausschließlich `0600` oder `0640` erlaubt. Außerdem wurde eine übergroße Datei nur abgeschnitten gelesen. | Exakte Modusprüfung und Größenabbruch oberhalb 4096 Byte; Werte werden nie protokolliert. |
| `G-095` | hoch | Kanalzustand und Auditzeile waren zwei Transaktionen. Bei Auditfehler konnte der Kanal ohne Nachweis aktiv bleiben. | Zustandswechsel und Hash-Ketteneintrag sind eine Transaktion; injizierter Auditfehler lässt den Kanal nachweislich `DISABLED`. |

Lokaler Nachweis: **30/30 Tests PASS**, `git diff --check` PASS.

Bekannte Grenze: Das Ollama auf dem Mac mini ist damit nicht angebunden. Die
zulässige Container-Brücke bezeichnet den Host des jeweiligen Containers, nicht
automatisch einen anderen Rechner. Für NAS → Mac mini fehlen weiterhin die
gemessene Zieladresse und ein ausdrücklich festgelegter, abgesicherter Netzweg.
Das ist kein stiller Fallback auf eine beliebige LAN-Adresse.


## 2026-09-08 — Systemscreening im Gesamtreview (Gerd via Claude Code, Auftrag Karl)

Prüfumfang: `058329a` plus Arbeitsbaum, gegen `INVARIANTEN.md`; 30/30 Tests unter
Python 3.9.6. Nur gelesen. Belegt mit Test: Invarianten 1, 2, 3, 5 (teilweise), 6, 8, 9,
10, 12, 14, 16. Nicht belegt: 4 (kein Hop-Zähler, Routen nur CEO→Identität), 7
(Ablehnung kein eigener Datensatztyp, „Audit kaputt bleibt Ablehnung" ungeprüft), 13
(Wiederherstellung in leeren Container und Wiederanlauf nach Absturz ungetestet), 15
(CEO-Meldung läuft über denselben Kanal, der gerade endgültig gescheitert ist).

| ID | Schwere | Befund | Korrektur/Nachweis |
|---|---:|---|---|
| `G-096` | hoch | `deploy_nas.sh` rollt `git archive HEAD` aus; `HEAD` enthielt zum Prüfzeitpunkt weder die Ollama-Zielprüfung noch die exakte Modusprüfung (`G-092`/`G-094` lagen ungecommittet). Ein Deploy hätte die Fassung **vor** den Korrekturen geliefert, während lokal 30 Tests grün waren. | Behoben durch `4392ab7` (05:50, alle vier Korrekturen committet). Regel: kein Deploy aus einem Baum mit ungecommitteten Änderungen an `workforce/`. Nachcheck des Diffs offen. |
| `G-097` | hoch | Budgeterschöpfung verlor die Nachricht dauerhaft: `release_untouched` setzte sie auf `RECEIVED`, aber `poll_once()` sah nur neue Updates, der Telegram-Offset war vorgerückt, `messages_with_status()` rief niemand. Die Zusage „wartet bis zum nächsten Tag" wurde nicht eingelöst. | `App.resume()` zu Rundenbeginn: `RECEIVED` wird am Folgetag wieder aufgenommen (nicht jede Runde, sonst wiederholt sich der Hinweis), abgelaufene `IN_PROGRESS`-Leases sofort; Auditzeile `RESUME`. Drei Tests, zwei davon ohne Fix rot. Nachcheck offen. |
| `G-098` | mittel | `compose.yaml` mountet `anthropic_api_key` unbedingt, auch für reine Echo- oder Ollama-Konfiguration. Invariante 12 verlangt das Gegenteil; der vorhandene Test prüft nur den Code, nicht Compose. | Behoben `158e061`: Basis nur mit Bot-Token, Overlay `compose.claude.yaml`, `deploy_nas.sh` wählt aus `config.nas.json`; Tests gegen ssh-Attrappe (Claude lädt Overlay, Echo nicht, fehlender Schlüssel bricht ab). Nachcheck offen. |
| `G-099` | mittel | `deploy_nas.sh` und `backup_pull.sh` haben keinen Test. Bauform-Zusage 3 verlangt Datei plus Test gegen Attrappen plus Exitcode. | Behoben `46022eb`: `workforce/tests/test_scripts.py` — Archiv ist der committete Baum ohne Secrets/Zustand/unversionierte Dateien, Sicherung mit `600`, manipulierte Kette Exit 1, Rotation behält vierzehn. Nachcheck offen. |

Nicht geprüft: NAS-Zustand, laufende Container, Kanalzustand, echte Telegram- und
Anthropic-Aufrufe, `deploy_nas.sh`/`backup_pull.sh` im Lauf, Ollama-Anbindung, Inhalte der
Secret-Dateien. Annahme, nicht gemessen: die NAS fährt den Stand vor `G-092`.

**Letzte vergebene Befundnummer: `G-099`.**

## 2026-09-08 — Nachcheck `4392ab7..9767ccb` (Gerd via Claude Code, Auftrag Karl)

`G-096` geschlossen: `HEAD:workforce/config.py` trägt Ollama-Zielprüfung und exakte
Modusprüfung. `G-097` geschlossen für Wiederaufnahme nach Absturz und Tageswechsel:
Gegenprobe gemessen, `app.py`/`store.py` auf `4392ab7` zurückgesetzt, zwei der drei
neuen Tests rot; der Kanaltest allein ist ein Stempel und hält nur zusammen mit den
anderen. Geprüft und nicht bestätigt: Absturz zwischen `record_inbound` und `claim`
(Offset wird nach `handle_update` gesetzt, Telegram liefert erneut), Kanal `DISABLED`
über Tage, Doppellieferung nach Resume, UTC-Tagesgrenze, Versuchszählung. Regel 61 ist
eine Regel mit Herkunft, keine Meinung.

| ID | Schwere | Befund | Korrektur/Nachweis |
|---|---:|---|---|
| `G-100` | mittel | Der Budgetwarter meldete sich genau einmal, dann schwieg er für immer: `notice()` leitet die Id aus `(message_id, text)` ab, der Text war konstant, `create_outbound` dedupliziert. Reichte das Budget dauerhaft nicht, wartete die Nachricht unbegrenzt, kein Versuch wurde geladen, `max_attempts` war unerreichbar, der CEO erfuhr nichts (Invariante 15 sinngemäß). Gemessen mit `max_usd_per_day=1e-7` über vier Tage: eine Notiz. | Der Tag steht im Text der Notiz; nach `max_attempts` Tagen ohne Budget wird die Nachricht `ABANDONED` mit Code `BUDGET_NEVER_SUFFICIENT` und sichtbarer Meldung. Test über vier Tage: zwei Tagesmeldungen, eine Aufgabe, ohne Fix rot. Nachcheck offen. |
| `G-101` | niedrig | Die Wiederaufnahme schrieb fremde Request-Ids doppelt: nach Resume standen `TG-2-CLAIM` und `TG-2-BOUNDARY` je zweimal im Audit; nur `RESUME` hatte ein eigenes Suffix (Invariante 11). | Jeder Durchlauf trägt `-R<n>` in der Request-Id, `n` aus der Zahl der bisherigen `RESUME`-Zeilen der Nachricht. Test: keine Request-Id doppelt, `TG-2-R1-CLAIM` existiert; ohne Fix rot. Nachcheck offen. |

Freigabe Gerd: `9767ccb` als Schließung von `G-096` und `G-097`. Nicht freigegeben: `G-098`
bis `G-101` und der Arbeitsbaum zum Zeitpunkt des Nachchecks.

**Letzte vergebene Befundnummer: `G-101`.**
