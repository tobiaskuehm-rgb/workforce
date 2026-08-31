# Security-Review Workforce Bus v0.1

**Datum:** 2026-08-31
**Gegenstand:** `postgres-init/002_workforce_bus.sql`, `postgres-init/003_workforce_bus_trigger_fix.sql`, `workforce-api/app.py` (v6), `compose.yaml`, `bus-realtest/`, Laufzeitzustand der NAS
**Grundlage:** Codeanalyse plus der am selben Tag durchgeführte Realtest inklusive 20 Negativtests (`2026-08-31_bus_realtest_karl_thorsten.md`)
**Zweck:** Punkt 7 des Aktivierungsgates aus `WORKFORCE_BUS_ROLLOUT.md`

## Gesamturteil

Der Bus selbst ist solide gebaut. Die Zugriffskontrolle ist zweistufig und fällt in beiden Stufen geschlossen aus; die Negativtests haben das über den realen HTTPS-Weg bestätigt, nicht nur transaktional in SQL. Ich habe **keinen Weg gefunden, die Kanalsperre, die Routenfreigabe oder die Absenderidentität über die API zu umgehen.**

Die Befunde unten betreffen daher überwiegend nicht die Bus-Logik, sondern deren Umfeld: die mitlaufende Alt-API, Dateirechte und einen vergessenen Zugangsschlüssel. Zwei davon sollten vor einer Aktivierung behoben sein.

**Empfehlung:** Aktivierung auf `ACTIVE` weiterhin zurückstellen — nicht wegen der Bus-Implementierung, sondern wegen F1 und F2 und weil ein Negativtest noch fehlt (F7).

## Was nachweislich hält

| Kontrolle | Umsetzung | Nachweis |
|---|---|---|
| Kill Switch zweistufig | DB (`bus_resolve_credential`) und API (`require_bus_ready`) prüfen unabhängig | Kanal `DISABLED` ⇒ 503 vor jeder Tokenprüfung |
| Widerruf endgültig | Trigger `bus_guard_channel_update` verweigert Rückweg aus `REVOKED` | `002_workforce_bus.sql:415-421` |
| Absenderidentität | ausschließlich aus dem Credential, nie aus dem Request-Body | `app.py:466-496`; Negativtest `unknown_field_rejected` |
| Token-Handhabung | nur SHA-256 in der DB, Klartext nie gespeichert oder geloggt | `app.py:142` |
| API-Key-Vergleich | `hmac.compare_digest`, laufzeitkonstant | `app.py:286` |
| Fehlermeldungen | stabile Kennungen, kein SQL, keine Stacktraces, keine Tabellenstruktur | `bus_error()`, `app.py:49-81` |
| Existenz nicht verraten | unbekannte `message_id` ⇒ `BUS_ACK_DENIED` statt 404 | Negativtest bestätigt |
| HTTPS-Zwang für Bus | HTTP ⇒ `BUS_HTTPS_REQUIRED` | live geprüft: `{"detail":"BUS_HTTPS_REQUIRED"}` |
| Container-Härtung | `read_only`, `cap_drop: ALL`, `no-new-privileges`, UID 10001 | `compose.yaml`, `bus-realtest/Dockerfile` |
| Netzsegmentierung | `backend` ist `internal: true`, DB nicht von außen erreichbar | `compose.yaml:126` |

## Befunde

### F1 — Telegram-Bot-Token seit zehn Tagen unwiderrufen und für alle lesbar (hoch)

```text
/volume1/docker/Startup/telegram-connector/secrets/telegram_bot_token
-rwxrwxrwx+ 1 TOBKUM users 47  Aug 21 23:26
```

Die Datei enthält ein echtes Telegram-Bot-Token und liegt seit dem 2026-08-21 dort. `telegram-connector/README.md` schreibt für den Rückbau nach dem abgebrochenen `DEC-024`-Versuch ausdrücklich vor: „das Bot-Token bei BotFather widerrufen und die lokale Token-Datei löschen." Beides ist unterblieben.

Wer Lesezugriff auf die Freigabe hat, kann den Bot vollständig übernehmen: Nachrichten im CEO-Chat mitlesen und in seinem Namen senden. Die Rechte `rwxrwxrwx` schränken das auf niemanden ein.

**Empfehlung:** Token bei BotFather widerrufen (`/revoke`), Datei löschen. Für den kommenden `DEC-026`-Lauf ein frisches Token erzeugen und erst unmittelbar vor dem Test ablegen. Unabhängig von jeder Bus-Aktivierung sofort erledigen.

### F2 — Alt-API und Web-UI über unverschlüsseltes HTTP erreichbar (mittel)

`compose.yaml:105-106` veröffentlicht Port 8080 im Klartext. Live geprüft:

```text
GET http://192.168.68.78:8080/kernel  -> 401   (aktiv, verlangt nur den Schlüssel)
GET http://192.168.68.78:8080/        -> 200   (Web-UI mit Schlüsseleingabe)
```

Die Bus-Endpunkte sind korrekt geschützt — dort greift `BUS_REQUIRE_HTTPS`. Die **Alt-Endpunkte** (`/kernel`, `/roles`, `/workers`, `/tasks`, `/documents`, `/activities`) hängen aber an `require_api_key` ohne jede Transportprüfung. Wer die Web-UI über 8080 benutzt, überträgt `WORKFORCE_API_KEY` im Klartext durchs LAN, ebenso alle Dokumenteninhalte.

`WORKFORCE_BUS_API_CONTRACT.md` formuliert die Absicht bereits: „Der bisherige HTTP-Port 8080 bleibt bis dahin auf Health-/Datenbankprüfungen begrenzt." Umgesetzt ist das nicht.

**Empfehlung:** Entweder `require_bus_transport` auch an die Alt-Endpunkte und an `/` hängen, oder Port 8080 nicht mehr veröffentlichen und ausschließlich über den Reverse Proxy erreichbar machen. Die zweite Variante ist die sauberere.

### F3 — Der gesamte Projektbaum ist world-writable (mittel)

Alles unterhalb von `/volume1/docker/Startup` steht auf `rwxrwxrwx`, einschließlich `secrets/`, `startup.env` (enthält das Datenbankpasswort) und der Migrationsdateien.

Beim Realtest zeigte sich die praktische Folge: `prepare_realtest_once.sh` setzt vor dem Schreiben korrekt `umask 077`, die erzeugten Token-Dateien landeten trotzdem als `-rwxrwxrwx`. Die DSM-ACL überstimmt den umask. Die Schutzmaßnahme im Skript läuft damit ins Leere.

Zusätzlich sind die Migrationsdateien beschreibbar, die `registry-migrate` als `postgres` gegen die Produktivdatenbank ausführt.

**Empfehlung:** Rechte auf der Freigabe einschränken — `startup.env` und `secrets/` auf `600`, Verzeichnisse auf `750`, und die DSM-ACL prüfen, damit sie den umask nicht wieder aufhebt. Ohne das ist jede dateibasierte Secret-Ablage in diesem Baum wirkungslos.

### F4 — Vertrauenswürdiger Proxy an eine dynamische Bridge-Adresse gebunden (niedrig)

`compose.yaml:99` setzt `BUS_TRUSTED_PROXY_CIDRS: "172.20.0.1/32"`. Aktuell korrekt — das Gateway von `startup_frontend` ist tatsächlich `172.20.0.1` bei Subnetz `172.20.0.0/16`. Docker vergibt Bridge-Subnetze aber der Reihe nach; wird das Netz neu angelegt, während ein anderes `172.20.0.0/16` belegt, verschiebt sich das Gateway.

Die Folge wäre kein Sicherheitsloch, sondern ein Ausfall: `trusted_https_proxy` liefert `False`, und alle Bus-Aufrufe enden in 503 `BUS_HTTPS_REQUIRED`. Das Verhalten ist fail-closed und damit richtig herum — die Fehlersuche wäre nur unangenehm.

**Empfehlung:** Subnetz für `startup_frontend` in `compose.yaml` fest vergeben, damit Gateway und CIDR nicht auseinanderlaufen können.

### F5 — Passwortloses `sudo` für Docker eingerichtet (informativ, bewusst)

Auf Wunsch des Betreibers wurde am 2026-08-31 `/etc/sudoers.d/tobkum-docker` mit `NOPASSWD` für `/usr/local/bin/docker` angelegt, damit die Testsequenz ohne interaktive Passworteingabe laufen konnte.

Das ist faktisch Root-Zugriff: Docker kann beliebige Hostpfade in Container einhängen. Die Beschränkung auf den Docker-Pfad verhindert Versehen, keine Absicht. Wer den SSH-Schlüssel `~/.ssh/id_ed25519_synology` besitzt, hat damit die volle Kontrolle über die NAS.

**Empfehlung:** Nach Abschluss der Arbeiten entfernen (`sudo rm /etc/sudoers.d/tobkum-docker`). Solange sie besteht, ist der private SSH-Schlüssel auf dem Mac wie ein Root-Passwort zu behandeln.

### F6 — Container `claude-agent` läuft als root mit Projekt-Mount (informativ)

Der Container `claude-agent` (Image `claude-nas`) läuft seit dem 2026-08-30 mit `/volume1/docker/Startup` und `/volume1/docker/Startup-Backups` als Schreib-Mounts, als `root`, ohne `read_only`, ohne `cap_drop`. Darin lief eine interaktive Sitzung.

Für die Bus-Sicherheit unmittelbar irrelevant, aber er umgeht die Härtung, die für alle anderen Container gilt, und hat Schreibzugriff auf Migrationen und Backups.

**Empfehlung:** Entfernen, wenn nicht mehr gebraucht. Falls er als Arbeitsumgebung bleiben soll, die Mounts auf `ro` setzen, wo Schreiben nicht nötig ist.

### F7 — Negativtest nach Widerruf fehlt weiterhin (offen)

Der Nachweis „widerrufenes Credential ⇒ 401" ist nicht erbracht. Nach dem Cleanup steht der Kanal auf `DISABLED`, und dann greift schon vorher 503 `BUS_CHANNEL_NOT_ACTIVE` — die Tokenprüfung wird gar nicht mehr erreicht.

Auf SQL-Ebene ist der Widerruf in `002_workforce_bus_acceptance.sql` geprüft, über die reale API nicht.

**Empfehlung:** Einen Zwischenschritt ergänzen, der genau ein Credential widerruft, während der Kanal noch `TESTING` ist, und dann mit dem widerrufenen Token einen 401 nachweist. Das schließt die letzte Lücke in Gate-Punkt 6.

### F8 — Keine Ratenbegrenzung (niedrig)

Weder API noch Datenbank begrenzen die Anzahl der Anfragen pro Credential und Zeitraum. Der Schleifenschutz (`max_hops`) begrenzt die Tiefe einer Antwortkette, nicht die Frequenz. Ein gültiges Credential kann beliebig viele Nachrichten erzeugen, bis `max_body_chars` mal Anzahl die Datenbank füllt.

Bei kurzlebigen `ACCEPTANCE`-Zugängen ist das Risiko gering. Vor `ACTIVE` mit `PRODUCTION`-Credentials sollte eine Begrenzung stehen — besonders wenn später ein KI-Agent autonom sendet und eine Fehlfunktion nicht ermüdet.

## Bewertung des Aktivierungsgates

| # | Anforderung | Stand |
|---:|---|---|
| 1 | Erweiterung und Review der API | **erfüllt** (dieses Dokument) |
| 2 | Projektbezogener HTTPS-Zugang | **erfüllt**, mit Einschränkung F2 |
| 3 | Getrennte, lokal gespeicherte Testzugänge | **erfüllt** |
| 4 | Realer bidirektionaler API-Test | **erfüllt** 2026-08-31 |
| 5 | Nachweis Projektgrenze, Zustellung, Annahme, Antwort, Audit | **erfüllt** |
| 6 | Negativtests | **weitgehend erfüllt** — 20 Fälle bestanden, F7 offen |
| 7 | Dokumentiertes Security-Review | **erfüllt** (dieses Dokument) |

Vor einer Entscheidung über `ACTIVE`: F1 sofort, F2 und F3 vorher, F7 als letzter fehlender Testnachweis. F4, F5, F6 und F8 sind vertretbar, sollten aber vor Dauerbetrieb adressiert sein.

## Hinweis zur nächsten Ausbaustufe

Die geplante KI-Agenten-Schicht verschiebt die Bedrohungslage deutlich. Der Bus ist heute sicher, *weil* an beiden Enden Menschen sitzen und ausschließlich innerhalb einer festen Allowlist geroutet wird. Sobald ein Agent autonom Nachrichteninhalte liest und daraufhin selbst sendet, kommt eine Klasse hinzu, die dieses Review nicht abdeckt: Ein Nachrichtentext kann dann Anweisungen an den Agenten enthalten. Die Allowlist begrenzt weiterhin, *wer* mit *wem* spricht — nicht, *wozu* sich ein Agent durch den Inhalt einer Nachricht bewegen lässt. Dafür ist ein eigenes Review nötig, bevor die Agentenschicht produktiv geht.
