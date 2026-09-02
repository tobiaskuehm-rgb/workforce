# `G-053`: Die letzte Etappe der Kette steht nicht in der Datenbank

**2026-09-02, an der Produktion gemessen.** Lesend, `BEGIN TRANSACTION
READ ONLY` … `ROLLBACK`. Kein Schreibvorgang.

## Wie es gefunden wurde

Gerds Phase 5, Punkt 4 verlangt, die Auditspur automatisch aus PostgreSQL zu
rekonstruieren. Für den ENG-008-Roundtrip gibt es `core_audit.sql`; für die
Kette gab es nichts — eine Lücke, die ich selbst am 2026-09-01 in
`REVIEW_ANTWORTEN.md` benannt und dann nicht geschlossen hatte.

Beim Schreiben von `chain_audit.sql` fiel auf, dass die fünfte Etappe dort gar
nicht ankommen kann: `publish_inbox_notifications()` schickt die
Benachrichtigung an den CEO und schreibt das Ergebnis in **seinen eigenen**
SQLite-Speicher. Auf dem Bus passiert nichts.

## Gemessen am echten Kettenlauf

Der dokumentierte `CHAIN PASS`-Lauf vom 2026-09-01 liegt noch vollständig in
`workforce.bus_events`. Das neue Skript, gegen ihn gefahren:

```
psql -v run_suffix=CHAIN20260901 -v update_id=686780859 \
     -v task_id=ENG-CHAIN-20260901 -f chain_audit.sql
```

```
=== 2. Positiv-Audit: geforderte Sequenz, an feste Ids gebunden ===
 positiv_audit | belegt | gefordert |             fehlend              | reihenfolge_verletzungen
---------------+--------+-----------+----------------------------------+--------------------------
 FAIL          |      4 |         5 | connector_acknowledges_the_reply |                        0

=== 4. Nichts bleibt liegen ===
 nichts_offen | offene_nachrichten | liegengeblieben
--------------+--------------------+-----------------------------------------------
 FAIL         |                  2 | MSG-959271DA…AED1 an CEO-TG-CHAIN20260901,
                                     MSG-060DFD2A…6C13 an CEO-TG-CHAIN20260901
```

**Vier von fünf Etappen sind belegt, die Reihenfolge stimmt, und genau die
letzte fehlt.** Die beiden Antworten des Agenten stehen seit dem 2026-09-01 im
Posteingang der Connector-Identität auf `DELIVERED`.

## Was das heißt und was nicht

**Der `CHAIN PASS` ist nicht falsch.** Die Benachrichtigungen sind bei Telegram
angekommen; das steht im lokalen Audit des Connectors und stand auf dem Telefon
des CEO. Falsch ist etwas anderes: Es lässt sich **aus der Datenbank nicht
rekonstruieren**. Genau das verlangt Phase 5, und für die Kette wäre es
strukturell unmöglich gewesen.

Die zweite Folge wiegt schwerer, weil sie in die Zukunft reicht: Der
Dublettenschutz des Rückwegs hing an einem einzigen Ort. Geht der lokale
Speicher verloren — der Fall, den `worker_core_test.py` für den Agenten
ausdrücklich nachstellt —, liefert `get_inbox` alles zurück, was je an den
Connector ging, und bis zu zwanzig Benachrichtigungen gehen erneut hinaus. Der
Agent hat für genau diesen Fall zwei Linien; der Rückweg hatte eine.

## Was nachgesehen und **nicht** bestätigt wurde

Der naheliegende zweite Verdacht war Verhungern: Wenn nie bestätigt wird,
wächst der Posteingang, und bei `limit=20` sähe der Connector irgendwann nur
noch alte Nachrichten. **Stimmt nicht.** `bus_list_messages` sortiert
`ORDER BY m.created_at DESC, m.message_id DESC` — neueste zuerst. In der
Migration nachgelesen, bevor es in einen Befund gewandert wäre.

## Korrektur

Der Connector bestätigt jetzt, nachdem der Versand erfolgreich war
(`G-001`-Reihenfolge). Request-Id `TG-ACK-<message_id>`, damit die
Rekonstruktion Bestätigung und Nachricht ohne Zwischenschicht aneinanderbinden
kann. Ein fehlgeschlagenes Bestätigen beendet die Runde nicht — die Nachricht
*ist* beim CEO, nur der Bus weiß es noch nicht.

Belegt gegen Attrappen: sechs neue Tests im Connector, eine verschärfte
Zusicherung im Kettentest, Gegenprobe mit abgeschalteter Bestätigung schlägt
an. Am laufenden System belegt ist bisher nur der **Befund**, nicht die
Korrektur: Dafür braucht es einen neuen Kettenlauf.

## Offen

**Die beiden liegengebliebenen Nachrichten sind noch offen.** Sie gehören über
die Regeln des Busses geschlossen, nicht per `UPDATE` (Leitplanke 3) — also
über einen `ack`-Aufruf unter der Connector-Identität. Deren Zugang ist
widerrufen und der Kanal ist `DISABLED`; das gehört damit in dasselbe Fenster
wie der nächste Kettenlauf und braucht eine Freigabe.


---

## Nachtrag 2026-09-02, `G-059`

Das Skript hatte selbst zwei Bindungsfehler, gefunden beim erneuten Lesen.

**Abschnitt 1 zeigte vier Zeilen aus zwei verschiedenen Kettenläufen.** Er
klammerte auf die beiden Identitäten und ein `LIKE 'AGENT-REPLY-%'` — und die
Request-Ids des Agenten sind aus der Nachrichten-Id abgeleitet, tragen also
keine Laufkennung. Die Liste sah nach einer Abfolge aus und war eine Mischung.

**Schritt 5 hing an `min(record_key)` über alle Antworten des Agenten**, also
bei mehreren Läufen an einem fremden Datensatz. Aufgefallen ist das nur
deshalb nicht, weil vor der Korrektur nie bestätigt wurde und der Schritt so
oder so fehlte — ein Fehler, den ein zweiter Fehler verdeckt hat.

Beides klammert jetzt am Datensatz statt am Präfix: Die Anfrage kommt aus der
Request-Id mit Laufkennung, die Antwort hängt an ihrem `parent_message_id`.

Erneut gegen denselben Lauf gefahren, mit demselben Urteil und jetzt aus dem
richtigen Grund:

```
 schritt |       actor_id       | record_type | request_id
---------+----------------------+-------------+--------------------------------------
       1 | CEO-TG-CHAIN20260901 | TASK        | TG-686780859-TASK
       2 | CEO-TG-CHAIN20260901 | MESSAGE     | TG-686780859-MESSAGE
       3 | AGENT-ENG-001        | MESSAGE     | AGENT-REPLY-70159149F25AF239B3059AD4
       4 | AGENT-ENG-001        | MESSAGE     | AGENT-ACK-CCEA59043E3126352E5AF734

 positiv_audit | belegt | gefordert |             fehlend
---------------+--------+-----------+----------------------------------
 FAIL          |      4 |         5 | connector_acknowledges_the_reply
```

Vier Zeilen, aber diesmal die vier Etappen **eines** Laufs in ihrer
Reihenfolge.
