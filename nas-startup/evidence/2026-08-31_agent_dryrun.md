# Nachweis: Agenten-Trockenlauf mit Echo-Provider

**Datum:** 2026-08-31
**Quellreferenz:** `DEC-028/ENG-008`, Lauf-Suffix `20260831-DRY1`
**Identität:** `AI-ENG-001` (Gerd)
**Ergebnis:** `PASS` — vier Nachrichten bearbeitet, Kanal danach wieder `DISABLED`, 0 aktive Zugänge

Erster Lauf der Agenten-Schicht. Bewusst mit dem Echo-Provider: kein Modell, kein API-Schlüssel, keine Kosten, kein Byte verlässt die NAS. Der Lauf prüft den Bus-Weg, nicht die Antwortqualität.

## Was geprüft werden sollte

Ob der Worker den gesamten Weg bewältigt — Inbox lesen, bestätigen, antworten — und ob die Datengrenze im echten Betrieb hält.

## Ausgangslage

In Gerds Inbox lagen vier unbeantwortete Nachrichten aus früheren Tests. Drei davon waren vorab bekannt und für zwei war ein Fehlschlag zu erwarten; die vierte kam im Lauf dazu.

## Ergebnis

| Nachricht | Absender | Erwartet | Tatsächlich |
|---|---|---|---|
| `MSG-901159FE…` | `CEO-TG-002` | Fehler, Identität beim Telegram-Cleanup widerrufen | `BUS_RECIPIENT_NOT_ACTIVE` |
| `MSG-63A233A8…` | `SAO-001`, Hop 4 | Fehler, Antwort wäre Hop 5 | `BUS_LOOP_LIMIT_EXCEEDED` |
| `MSG-763AFEAF…` | `SAO-001`, Hop 2 | Antwort geht raus | Antwort `MSG-31ACB6B7…`, Hop 3 |
| `MSG-503F56F5…` | `EAC-001` | nicht vorhergesagt | Antwort `MSG-259600BE…`, Hop 1 |

`"handled": 4`, Exit-Code 0. Beide Fehlerpfade wurden abgefangen: Der Worker hat sie protokolliert, die betroffenen Nachrichten bestätigt und ist weitergelaufen — kein Absturz, keine Endlosschleife.

Dass die Fehlschläge nicht endlos wiederholt werden, ist eine Folge der Reihenfolge im Worker: Bestätigt wird **vor** der Bearbeitung. Eine Nachricht, deren Antwort scheitert, steht danach auf `ACCEPTED` und fällt aus dem `DELIVERED`-Filter des nächsten Durchlaufs. Das war so beabsichtigt, damit der Absender den Empfang auch dann sieht, wenn die Bearbeitung scheitert — dass es zugleich einen Wiederholungssturm verhindert, ist ein willkommener Nebeneffekt.

## Datengrenze

Der eigentliche Prüfpunkt. Alle vier Protokollzeilen:

```text
"data_policy": "METADATA_ONLY"
"body_included": false
"fields_sent": ["action_class", "message_id", "sender_id", "subject"]
"chars_sent": 83 … 103
```

Kein Nachrichtentext hat die NAS verlassen. Bei `METADATA_ONLY` ist das die Voreinstellung, und sie greift im echten Betrieb, nicht nur im Test. Jede Zeile trägt zusätzlich einen SHA-256-Fingerabdruck der übertragenen Felder, aber nie deren Inhalt.

## Rückbau

```text
 PASS | DISABLED | AI-ENG-001 | CRED-ACCEPT-AGENT-20260831-DRY1 | REVOKED | 0
```

Token-Datei gelöscht, alle drei Compose-Projekte und das Testnetz entfernt, temporäre Firewall-Regel zurückgenommen. Endprüfung: Kanal `DISABLED`, 0 aktive Credentials, Produktivstack unberührt.

Die zwei erzeugten Antwortnachrichten bleiben im Bus — sie sind Nachweis, kein aktives Recht.

## Ein Fehler unterwegs

Der erste Build scheiterte an einer erfundenen SDK-Version (`anthropic==1.4.0`; verfügbar ist `1.2.0`). Nachschlagen statt aus dem Gedächtnis schreiben — die eigene Vorgabe der API-Dokumentation, gegen die ich verstoßen habe. Nach der Korrektur lief der Build durch.

## Was dieser Lauf ausdrücklich nicht belegt

- **Keine Antwortqualität.** Der Echo-Provider gibt einen festen Text zurück. Über die Brauchbarkeit echter Modellantworten sagt der Lauf nichts.
- **Keine Freigabe für den Modellbetrieb.** `AGENT_PROVIDER=claude` braucht weiterhin die Entscheidung zur Datengrenze, ein Kostenlimit, eine Ratenbegrenzung und ein eigenes Security-Review.
- **Keine Injection-Prüfung im Echtbetrieb.** Dass Modellausgabe das Routing nicht beeinflussen kann, ist strukturell abgesichert und lokal getestet, aber hier nicht gegen ein echtes Modell erprobt — der Echo-Provider liest den Inhalt gar nicht.
