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

`compose.yaml` ist der ganze Betrieb: `docker compose up -d --build`. Secrets liegen als
Dateien in `secrets/` mit `chgrp 10001` und `chmod 640`; `config.json` daneben. Ein
Bot-Token verträgt genau einen Abfrager — der Connector des Prototyps darf nicht
gleichzeitig laufen.
