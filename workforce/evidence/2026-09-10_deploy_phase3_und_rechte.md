# Nachweis: Deploy Phase 3 (`35e7ae3`) und Ordnerrechte auf der NAS, 2026-09-10

**Freigabe:** CEO im Chat, 2026-09-10, „ja" zu P-2 (Klasse Produktives, Deploy Phase 3) und R-2
(Klasse Rechte, Ordnerrechte), Vorlagen in `workforce/reviews/2026-09-10_donnerstag_vorlagen.md`.
Gerds Vorab-Freigabe für den Zeitplanbetrieb: `a15a129`; seither `G-107`, `G-110`, `G-111`
behoben und Skill-/Gedächtniscommits der Parallelsitzungen.

**Deploy (Karl, Claude Code, ca. 09:50 CEST):** `git status` leer, HEAD `35e7ae3`, 63 Tests
grün, `config.nas.json` mit `schedule` (Montag 06:00 UTC, Donnerstag 06:00 UTC, an KARL),
Decke 2,0. `sh workforce/deploy_nas.sh`:

```
RESULT: deployed 35e7ae3 config 3490e16af4cc
```

**Messung nach dem Start:**

```
STARTUP-35e7ae36717d-1789027349  commit 35e7ae36717d…, config_sha256 3490e16af4cc…, Kanal ACTIVE
status: Stand: 35e7ae36717d seit 2026-09-10, Konfiguration 3490e16af4cc / Kanal: ACTIVE
verify: Audit: intakt / RESULT: PASS / exit 0
```

**Der Donnerstagstermin hat sofort gefeuert** (06:00 UTC war vorbei, erster Lauf setzt die
Basis auf die vorige Fälligkeit, heute ist fällig): `SCHEDULED` `DONNERSTAG_ENTSCHEIDUNGEN`
2026-09-10, `CLAIM`, `BOUNDARY` (BODY, 195 Zeichen), `RESERVED` (worst 0,152 USD), `REPLIED`
(`claude-opus-5`, 4807/934 Token, 0,047385 USD), Antwort `SENT` mit externer Id `43`, 1295
Zeichen. `status`: 1 Aufruf, 0,0474 von 2,00 USD, 0 Ausgänge offen. `schedule_seen`:
Montag 2026-09-07 (Basis), Donnerstag 2026-09-10.

**R-2, Rechte (Wegwerf-Container, `alpine`):** `chgrp 10001` auf Ordner, `secrets/`,
`config.json`; `chmod 750` Ordner, `secrets/`, `deploy_nas.sh`; `chmod 640 config.json`.
Ergebnis: `drwxr-x--- 1026:10001` Ordner und `secrets/`, `-rw-r----- 1026:10001` `config.json`
und beide Secrets, `-rwxr-x--- 1026:users` `deploy_nas.sh`. Container neu gestartet (`restart`),
liest Konfiguration weiter (`status` gleich), `verify` PASS, zweite `STARTUP`-Zeile mit
demselben Hash, **kein zweites Feuern** des Termins (`SCHEDULED` bleibt 1). Schreibprobe des
SSH-Benutzers im Ordner: beschreibbar, also funktioniert `tar xzf` beim nächsten Deploy.

**Nicht gemessen:** die Montagsnachricht am 2026-09-14 (erster regulärer Termin); ob die
Donnerstagsantwort inhaltlich taugt, das liest der CEO; ein Deploy nach den neuen Rechten.
