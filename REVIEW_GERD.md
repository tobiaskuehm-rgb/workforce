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

