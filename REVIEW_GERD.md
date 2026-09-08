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
| `G-098` | mittel | `compose.yaml` mountet `anthropic_api_key` unbedingt, auch für reine Echo- oder Ollama-Konfiguration. Invariante 12 verlangt das Gegenteil; der vorhandene Test prüft nur den Code, nicht Compose. | offen |
| `G-099` | mittel | `deploy_nas.sh` und `backup_pull.sh` haben keinen Test. Bauform-Zusage 3 verlangt Datei plus Test gegen Attrappen plus Exitcode. | offen |

Nicht geprüft: NAS-Zustand, laufende Container, Kanalzustand, echte Telegram- und
Anthropic-Aufrufe, `deploy_nas.sh`/`backup_pull.sh` im Lauf, Ollama-Anbindung, Inhalte der
Secret-Dateien. Annahme, nicht gemessen: die NAS fährt den Stand vor `G-092`.

**Letzte vergebene Befundnummer: `G-099`.**
