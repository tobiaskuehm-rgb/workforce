# Nachweis: Kettentest Telegram → Bus → Agent → Bus → Telegram

**Datum:** 2026-09-01
**Quellreferenz:** `CEO-CHAT-2026-09-01/PENDING-DEC` (Prepare/Cleanup), `DEC-023/ENG-007` (Connector)
**Lauf-Suffix:** `CHAIN20260901` · **Identitäten:** `CEO-TG-CHAIN20260901`, `AGENT-ENG-001`
**Provider:** `echo` — kein Modell, keine Kosten (`AGENT_MAX_COST_USD=0`)
**Ergebnis:** **`CHAIN PASS`** — zwei vollständige Durchläufe, je genau eine Anfrage und genau eine Antwort

**Das ist der erste Lauf, in dem das System das getan hat, wofür es existiert.** Alle bisherigen Nachweise belegten einzelne Glieder; zusammen gelaufen waren sie nie.

---

## Was belegt ist

```
Telegram  /task AGENT-ENG-001 ENG-CHAIN-… | Titel | Output
   → Connector legt Task PENDING an und schickt eine Nachricht mit task_ref
   → Bus prüft Route, Idempotenz, schreibt Audit
   → Agent poll_once() → Echo-Provider → Antwort mit derselben task_ref
   → Bus Rückroute AGENT-ENG-001 → CEO-TG-CHAIN20260901
   → Connector publish_inbox_notifications()
   → Telegram: Benachrichtigung im Chat
```

Aus der Datenbank rekonstruiert, nach dem Lauf:

| Zeit (UTC) | Absender | Empfänger | Status | `task_ref` | Art |
|---|---|---|---|---|---|
| 05:04:49 | `CEO-TG-CHAIN20260901` | `AGENT-ENG-001` | `ACCEPTED` | `ENG-CHAIN-20260901` | Anfrage |
| 05:07:18 | `AGENT-ENG-001` | `CEO-TG-CHAIN20260901` | `DELIVERED` | `ENG-CHAIN-20260901` | Antwort |
| 05:13:56 | `CEO-TG-CHAIN20260901` | `AGENT-ENG-001` | `ACCEPTED` | `ENG-CHAIN-20260902` | Anfrage |
| 05:13:57 | `AGENT-ENG-001` | `CEO-TG-CHAIN20260901` | `DELIVERED` | `ENG-CHAIN-20260902` | Antwort |

Je Task **eine** Anfrage, **eine** Antwort, Task-Bezug in beide Richtungen erhalten. Der Nutzer hat beide Benachrichtigungen im Telegram-Chat gesehen — das ist das Ende der Kette, und nur dort ist es sichtbar.

Die 2,5 Minuten Latenz im ersten Durchlauf sind der Zeitraum, in dem der Agent wegen des unten beschriebenen Volume-Defekts unten lag. Der zweite Durchlauf zeigt die echte Latenz: **eine Sekunde**.

## Was nicht belegt ist

- **Kein Modell war beteiligt.** Der Provider ist `echo`. `DEC-027` und `ENG-008` schließen einen externen kostenpflichtigen Dienst aus; der Echo-Provider ist hier die Anforderung, nicht die Abkürzung.
- **Der Antworttext hat die NAS nie verlassen.** `TELEGRAM_OUTBOUND_POLICY=METADATA_ONLY`, `AGENT_DATA_POLICY=METADATA_ONLY`. Im Chat steht, *dass* eine Antwort da ist, nicht *was* sie sagt.
- **Die Antwort bleibt `DELIVERED`.** Der Connector benachrichtigt, er bestätigt Bus-Nachrichten nicht — er ist keine bearbeitende Instanz. Das ist so gewollt und kein offener Rest.
- **Keine Audit-Rekonstruktion per SQL.** Migration `004` (Ablehnungs-Audit) ist auf der NAS **nicht** angewendet; `chain_audit.sql` gibt es noch nicht. Die Tabelle oben ist eine Abfrage von Hand, kein automatisierter Nachweis.

## Drei Defekte, die nur der echte Lauf finden konnte

Alle drei waren durch lokale Tests nicht erreichbar. Das ist das Argument für diesen Lauf.

**1. Das Bot-Token war eine RTF-Datei.** Mit TextEdit geschrieben, das speichert Rich Text: 433 Bytes RTF-Auszeichnung statt 46 Zeichen Token. Der Connector hätte die Auszeichnung als Token gelesen. Maschinell extrahiert, Original gesichert, beides beim Rückbau gelöscht. **Lehre für das Runbook:** „Text Editor" ist zu ungenau — es muss Klartext sein, und die Länge ist prüfbar.

**2. Das Agenten-Image legte sein Zustandsverzeichnis nicht an.** `Dockerfile` erzeugte `/var/lib/startup-agent` nicht, also wurde das benannte Volume beim ersten Mounten mit Root als Eigentümer erzeugt — und der Container läuft als UID 10001. Ergebnis: `sqlite3.OperationalError: unable to open database file`, sofortiger Absturz. Das Connector-Image macht es seit jeher richtig (`mkdir` plus `chown` auf `startup`).

**Dieser Defekt hätte jeden künftigen Agentenlauf getroffen**, auch den Worker-Core-Test. Behoben im `Dockerfile`; das bestehende Volume wurde übergeben statt gelöscht.

**3. Das Cleanup setzte `REVOKED` ohne Widerrufsmetadaten.** `chain_cleanup.sql` schrieb nur den Status. Jede Bus-Tabelle hat ein `CHECK`, das `REVOKED` an `revoked_at` und einen nicht leeren `revocation_reason` bindet; die Registry-Tabellen an `revoked_at`. Die Transaktion brach ab — **die Bedingung hat genau ihre Aufgabe erfüllt**: Ein widerrufener Datensatz ohne Grund wäre ein Loch in der Audit-Spur. Korrigiert und erneut gelaufen.

## Rückbau

```
 result | channel_status | connector_identity | active_chain_routes | active_credentials
--------+----------------+--------------------+---------------------+--------------------
 PASS   | DISABLED       | REVOKED            |                   0 |                  0
```

Nachgemessen statt protokolliert: Kanal `DISABLED`, null aktive Zugänge im ganzen Projekt, null aktive Kettenrouten, Connector-Identität `REVOKED`, `AGENT-ENG-001` unverändert `ACTIVE` (dauerhaft, gehört nicht zu diesem Lauf). Alle vier Token-Dateien gelöscht. Keine Testcontainer mehr vorhanden. Produktivstack durchgehend `Up (healthy)`, nicht angefasst.

Die vier Nachrichten und beide Tasks bleiben — sie sind der Nachweis, keine Berechtigung.

**Offen beim Nutzer:** die temporäre DSM-Firewall-Regel für `172.31.254.0/29` auf TCP 8443 zurücknehmen, und im BotFather entscheiden, ob der Testbot `@Thorsten_workforcebot` bestehen bleibt oder sein Token widerrufen wird.

## Nebenbefund

`AGENT-ENG-001` **existiert und ist aktives Projektmitglied** — vor dem Lauf gegen die Registry geprüft. `HANDOVER.md` führte das bis dahin als „nicht belegt" (Befund `G-019`). Damit ist der Punkt nachgemessen.

## Deployter Stand

Der Lauf begann auf Commit `f59e757`, Manifest verifiziert: 99 Dateien, keine Abweichung — der erste Einsatz von `deploy_manifest.sh`/`verify_manifest.sh`.

**Während des Laufs wurden zwei Korrekturen nachdeployt:** `workforce-agent/Dockerfile` (Defekt 2) und `chain-test/chain_cleanup.sql` (Defekt 3). Der Stand am Ende des Laufs ist deshalb **nicht** `f59e757`. Der genaue Endstand steht unten und ist nach dem Lauf erneut gegen die NAS verifiziert — genau die Angabe, die dem `ENG-008`-Nachweis gefehlt hat.

**Endstand:** siehe `DEPLOY_MANIFEST.txt` auf der NAS, eingetragen im Anschluss an diesen Nachweis.
