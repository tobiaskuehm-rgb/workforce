# Bus-Realtest Karl ↔ Thorsten

**Zweck:** genau ein bidirektionaler Realtest über den bestehenden `START-UP`-Workforce-Bus zwischen den beiden bereits aktiven Identitäten Karl (`SAO-001`) und Thorsten (`RAS-001`). Kein neuer Mitarbeiter, keine neue Route, keine dauerhafte Rechteänderung — nur zwei kurzlebige `ACCEPTANCE`-Zugänge und ein zeitlich begrenztes `TESTING`-Fenster.

Ausführliche Schrittfolge: `../BUS_REALTEST_KARL_THORSTEN_RUNBOOK.md`.

## Sicherheitsgrenzen

- Betrifft ausschließlich `SAO-001` und `RAS-001`, Projekt `START-UP`.
- Kanal wird höchstens auf `TESTING` gesetzt, niemals auf `ACTIVE`.
- Beide Zugänge laufen automatisch nach 30 Minuten ab und werden zusätzlich am Ende explizit widerrufen.
- Karls und Thorstens Mitarbeiter-, Mitgliedschafts-, Capability- und Routendaten sind bereits vorhanden (Migration `002_workforce_bus.sql`) und werden von diesem Paket nicht verändert — nur die zwei Test-Credentials und der Kanalstatus.
- Nachrichteninhalte im Testlauf sind bewusst neutral und enthalten keine echten Betriebsgeheimnisse.
- Kein neuer eingehender Port, kein neues Docker-Netz, kein Eingriff in bestehende Container außer den drei hier definierten Einmaldiensten.
- Rohes Tokenmaterial verlässt `./secrets/` nie in ein Protokoll; nur SHA-256-Hashes werden in die Datenbank geschrieben.

## Dateien

| Datei | Zweck |
|---|---|
| `compose.prepare.yaml` + `prepare_realtest_once.sh` + `bus_realtest_prepare.sql` | erzeugt zwei lokale Tokens, setzt Kanal auf `TESTING`, legt zwei `ACCEPTANCE`-Credentials an |
| `compose.run.yaml` + `bus_realtest_run.py` (+ `Dockerfile`) | führt den echten HTTPS-Nachrichtenwechsel Karl → Thorsten → Karl aus |
| `compose.cleanup.yaml` + `cleanup_realtest_once.sh` + `bus_realtest_cleanup.sql` | widerruft beide Credentials, setzt Kanal zurück auf `DISABLED` |
| `bus-realtest.env.example` | Vorlage für `BUS_REALTEST_BASE_URL` und `BUS_REALTEST_SOURCE_REF` |
| `test_bus_realtest_run.py` | lokaler, secretfreier Test der Ablauflogik ohne echte Netzwerkverbindung |

## Lokaler Test ohne Netzwerkzugriff

```text
python3 -m unittest discover -v
```

Verwendet ausschließlich simulierte HTTP-Antworten, benötigt keine Tokens und baut keine Verbindung auf.
