# workforce — der Neubau

Ein Prozess, eine SQLite-Datei, ein Container. Telegram rein, Modell raus, alles
protokolliert in einer Hash-Kette. Nur Standardbibliothek; läuft mit Python 3.9 auf dem
Mac und 3.13 im Container. Maßstab ist [INVARIANTEN.md](../INVARIANTEN.md).

## Auf dem Mac starten

```bash
cd "/Users/Tobi/Documents/Codex/workorce claude"
python3 -m unittest discover -s workforce/tests -t . -q
```

Dann drei Dinge, die nur du hast:

1. `workforce/secrets/telegram_bot_token` — eine Zeile, `chmod 600`.
2. `workforce/secrets/anthropic_api_key` — nur wenn eine Identität `claude` nutzt; sonst weglassen.
3. `workforce/config.json` — Kopie von `config.example.json` mit deiner `allowed_chat_id`,
   `db_path` und `secrets_dir` als lokale Pfade.

```bash
python3 -m workforce run --config workforce/config.json
```

Der Kanal ist nach dem ersten Start **aus**. `/start` im Telegram-Chat schaltet ihn an,
`/stop` aus, `/status` zeigt Kanal, Tagesbudget, offene Ausgänge und Audit. `@NAME text`
spricht eine andere konfigurierte Identität an.

## Der Kern meldet sich (Phase 3)

`config.json` kann einen `schedule` tragen: eine Liste von Terminen, jeder mit `id`, `weekday`
(1 Montag bis 7 Sonntag), `hour` (0–23, UTC — dieselbe Zeitbasis wie der Budgettag, keine
zweite Uhr), `identity` (muss eine Route von `CEO` haben) und `prompt`. Fällig ist ein Termin ab
seiner Stunde am richtigen Tag, einmal je Kalendertag; die Nachricht läuft danach wie jede
echte — Budget, Wiederaufnahme bei erschöpftem Tag (`G-100`), Audit. Beispiel in
`config.example.json`, `config.nas.json`: Montag Wochenlage, Donnerstag Entscheidungstermin.

## Befehle

| | |
|---|---|
| `run` | Endlosschleife |
| `once` | eine Abfragerunde, für Cron und Tests |
| `status` | wie `/status` |
| `channel on\|off` | Kill Switch von der Kommandozeile |
| `verify` | Hash-Kette und Zustellabgleich; Exit 1 bei jedem Fund |
| `backup <pfad>` | konsistente Kopie der Zustandsdatei, Rechte 600 |

## Auf der NAS

Ausgerollt wird nur über `deploy_nas.sh` aus sauberem Baum; es wählt die Compose-Dateien aus `config.nas.json`. Ein Neustart von Hand auf der NAS nimmt dieselbe Liste, sonst fehlt der Schlüssel-Mount und der Start bricht ab: Echo oder Ollama `docker compose -f compose.yaml up -d`, mit einer Identität `claude` `docker compose -f compose.yaml -f compose.claude.yaml up -d` (Invariante 12, `G-104`). Secrets liegen als
Dateien in `secrets/` mit `chgrp 10001` und `chmod 640`; `config.json` daneben. Ein
Bot-Token verträgt genau einen Abfrager — der Connector des Prototyps darf nicht
gleichzeitig laufen.
