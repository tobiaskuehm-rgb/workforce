# Paketinhalt – Telegram–NAS-Realtest

**Version:** 2026-08-21 v2 / `DEC-026`-Einmaltest  
**Freigabe:** genau ein zweiter Realtest nach `DEC-026`; sichere Vorbereitung ausstehend, Dauerbetrieb und jede weitere Wiederholung gesperrt

## Auf der NAS benötigte Dateien

| Datei | Zweck |
|---|---|
| `Dockerfile` | baut den Python-Connector ohne zusätzliche Pakete |
| `telegram_connector.py` | fail-closed Telegram-/Workforce-Transport |
| `identity_probe.py` | ermittelt ausschließlich numerische Chat-/Benutzer-ID |
| `network_probe.py` | tokenfreier, secretfreier HTTPS-Vorabtest mit stabilen Fehlercodes |
| `telegram-realtest.env.example` | secretfreie Konfigurationsvorlage |
| `compose.network-check.yaml` | isolierter Vorabtest mit fester Kandidaten-Quelladresse, ohne Ports und Tokens |
| `compose.identity.yaml` | einmalige ID-Ermittlung |
| `compose.prepare.yaml` | kurzlebige DB-Identität, Routen und Credential anlegen |
| `compose.run.yaml` | einmaligen Connector-Test starten |
| `compose.cleanup.yaml` | alle Testrechte widerrufen und Token-Datei entfernen |
| `prepare_realtest_once.sh` | erzeugt das lokale Kurzzeit-Token und startet die DB-Vorbereitung |
| `cleanup_realtest_once.sh` | führt den DB-Widerruf aus und löscht das Kurzzeit-Token |
| `realtest_prepare.sql` | sichere, vorbedingte Provisionierung nach `DEC-024` |
| `realtest_cleanup.sql` | append-only Widerruf und Rückkehr zu `DISABLED` |
| `REALTEST_RUNBOOK.md` | DSM-Schrittfolge und Abbruchregel |
| `compose.preflight2.yaml` | rein lesende NAS-Vorprüfung ohne Credential-Erzeugung |
| `preflight_realtest2_once.sh` | startet ausschließlich die lesende Vorprüfung |
| `realtest2_preflight.sql` | prüft `DISABLED`, Credentials `0`, alte Identität widerrufen und neue IDs frei |
| `telegram-realtest-2.env.example` | secretfreie, fail-closed Vorlage für den neuen `…-002`-Lauf |
| `compose.prepare2.yaml` | frische `CEO-TG-002`-Provisionierung |
| `compose.run2.yaml` | genau ein Connectorlauf aus `172.31.254.2` mit getrenntem v2-Volume |
| `compose.cleanup2.yaml` | vollständiger Widerruf der `…-002`-Rechte und Tokenlöschung |
| `realtest2_prepare.sql` | vorbedingte Provisionierung nach `DEC-026` |
| `realtest2_cleanup.sql` | append-only Widerruf der `…-002`-Identitäten und Rückkehr zu `DISABLED` |
| `REALTEST2_RUNBOOK.md` | aktuelle DSM-Schrittfolge und Pflicht-Cleanup nach `DEC-026` |
| `README.md` | Architektur und Sicherheitsgrenzen |

`compose.realtest.yaml`, `compose.pilot.yaml`, `telegram.env.example`, lokale Tests und Demo sind zusätzliche technische Referenzen. Nach `DEC-026` dürfen ausschließlich die ausdrücklich genannten `…2`-Artefakte in der dokumentierten Reihenfolge für genau einen Test verwendet werden. Der tokenfreie Netzwerkcheck ist bereits `PASS`; andere Compose-Dateien bleiben gesperrt.

## Absichtlich nicht enthalten

- Bot-Token oder Workforce-Token,
- `telegram-realtest.env`,
- `startup.env`,
- Datenbankpasswörter oder Hashes,
- Chat- oder Benutzer-ID des CEO,
- PostgreSQL-Dump oder Container-Volume,
- produktive Rechte oder Dauerbetriebsfreigabe.

Das historische v1-Archiv und die `…-001`-Artefakte bleiben unverändert als Input-/Ausführungssnapshot erhalten und dürfen nicht als aktueller Wiederholungsauftrag verwendet werden.
