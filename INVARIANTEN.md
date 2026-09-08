# Invarianten des Neubaus — Entwurf für die DEC

**Status:** Vorschlag hinter einem **offenen Entscheidungsgate.** Im maßgeblichen Decision Log
ist `DEC-037` der jüngste Eintrag, `PEO-007` und `HO-027` stehen offen; eine Chat-Zustimmung
ist keine Nummer (`G-006`). **Entwurf:** Claude Code, 2026-09-03. **Ergänzt** um die Zeilen
13–16, die Neufassung von Zeile 12 und Bauform-Zusage 3 auf Verlangen von Gerd am selben
Abend. **Unterschrift:** CEO. Danach ist diese Seite der Maßstab, gegen den geprüft wird —
beim Neubau je Meilenstein nach dem Lauf, bei der Weiterführung für Phase 5 und alles danach.

**Prüffrage je Zeile:** Welcher Befund des Prototyps wäre damit vom ersten Tag an unmöglich
gewesen? Eine Zeile ohne Befund ist eine Meinung. Ein Befund ohne Zeile war ein Symptom
der alten Bauform und braucht im Neubau keinen Test.

## Die sechzehn Eigenschaften

Jede Zeile: was gilt, welcher Befund sie erzwungen hat, welcher Test sie beweist.

| # | Eigenschaft | Erzwungen durch | Beweis |
|---|---|---|---|
| 1 | **Fail-closed ist die Voreinstellung.** Kanal aus, Schalter aus, unbekannte Route abgelehnt. Ein leerer Start antwortet niemandem. | `G-031`, `G-041`, Security-Review | Frischer Start ohne Konfiguration: keine Antwort, kein Provideraufruf. Unbekannte Route: Ablehnung mit stabilem Code. |
| 2 | **Der Kill Switch wirkt innerhalb einer Abfragerunde.** Ein Zustandswechsel stoppt jeden Ausgang, Provider wie Messenger. | Bus-Abnahme, `G-062` | Kanal mitten im Lauf auf aus: kein weiterer Provideraufruf, kein Versand, offene Arbeit bleibt sichtbar. |
| 3 | **Der Empfänger kommt aus dem Datensatz, nie aus der Modellausgabe.** Routen sind eine explizite Allowlist. | `G-003`, Injektionstests | Injizierte Anweisung „sende an X" im Text: Antwort geht an den ursprünglichen Absender, X sieht nichts. |
| 4 | **Schleifen enden.** Hop-Zähler auf jeder Nachricht; zwei Agenten, die aufeinander zeigen, stoppen. | Bus-Abnahme | Zwei Identitäten mit Route zueinander: Kette endet beim Limit, mit Auditzeile. |
| 5 | **Idempotenz hat zwei Linien, und sie sind nicht austauschbar.** Nachrichten-Id aus Absender und Schlüssel abgeleitet; ein Claim ohne dauerhafte Wirkung wird zurückgegeben; jeder Claim hat Lease und Versuchszähler. | `G-001`, `G-002`, `G-013`, `G-053`, `G-056`, `G-082`, `G-083` | Prozess stirbt nach Versand vor Bestätigung: genau ein Ausgang. Lokaler Zustand gelöscht: immer noch genau einer. Lease abgelaufen: ein zweiter Prozess übernimmt, ein dritter nicht. |
| 6 | **Der Lauf ist allein aus der Datenbank rekonstruierbar.** Jeder dauerhafte Schreibvorgang trägt Akteur und Request-Id; das Audit ist eine Hash-Kette. | Audit-Trigger `002`, `G-059`, `G-070` | Lauf, Prozess weg, Reihenfolge aus der Datenbank nachgespielt: identisch. Eine Zeile verändert: Kettenprüfung schlägt an. |
| 7 | **Jede Ablehnung ist ein Datensatz.** Stabiler Code, kein Inhalt, geschrieben auch dann, wenn die abgelehnte Operation zurückgerollt wurde. | `005`, `G-014` | Abgelehnter Aufruf: eine Ablehnungszeile mit Code, ohne Nachrichtentext. Audit kaputt: die Ablehnung bleibt eine Ablehnung, wird kein Serverfehler. |
| 8 | **Es gibt eine Datengrenze, und sie ist eine Funktion.** Alles, was zu Provider oder Messenger geht, läuft durch sie; die Feldmenge je Policy ist eine Konstante; der Betreff ist Inhalt. | `G-029`, `G-054`, `G-084`, Security-Review | Statische Prüfung: jeder Ausgangspfad ruft die Grenze. `METADATA_ONLY` lässt weder Text noch Betreff durch. Ein lokales Modell darf mehr sehen als ein fremdes, und das steht in der Konstante. |
| 9 | **Kosten werden reserviert, bevor sie entstehen.** Versuch, Eingabe, maximale Ausgabe und Preis müssen gemeinsam in den Rest passen; ein bezahlter Provider unter Nulldecke wird vor dem ersten Aufruf abgewiesen; ein fehlgeschlagener Versuch zählt. | `G-004`, `G-016`, `G-057`, `G-065` | Decke null plus bezahlter Provider: kein Aufruf. Geschätzte Kosten über Rest: kein Aufruf. Aufruf scheitert: Versuch trotzdem verbraucht. |
| 10 | **Der Agent bleibt werkzeuglos.** Der Provider nimmt Text und gibt Text; die Modellausgabe wird ausschließlich als Antworttext verwendet. | Security-Review 2026-08-31 | Provider-Attrappe liefert etwas, das wie ein Werkzeugaufruf aussieht: es wird als Text behandelt, nichts wird ausgeführt. |
| 11 | **Jede Wirkung trägt ihre Herkunft.** Request-Id der Form `<PRÄFIX>-<lauf>-<phase>`, deterministisch aus der Anfrage abgeleitet; Nachweise binden an exakte Ids, nie an „irgendein Datensatz dieses Typs". | `G-059`, `G-070` | Zwei Läufe hintereinander: jeder ist für sich rekonstruierbar, keiner sieht den Datensatz des anderen. |
| 12 | **Secrets sind dateibasiert und geschützt.** Jede Secret-Datei hat feste Eigentümer- und Rechtezahlen (`600` oder `640`, Gruppe nach Nummer) und reinen Textinhalt ohne Formatierung; nie in Umgebung, Repo oder Chat; ein Prozess bekommt nur das Geheimnis, das er benutzt. | `G-017`, `G-044`, `G-089`, Kettenlauf 2026-09-01 | Datei mit offenen Rechten: Start verweigert. Geheimnis nur in der Umgebung: Start verweigert. Echo-Betrieb: kein Modellschlüssel im Container. RTF statt Text: stabiler Fehler, Wert nie ausgegeben. |
| 13 | **Backup, Restore und Wiederanlauf sind geprobt, nicht beschrieben.** Der Zustand wird täglich gesichert, die Sicherung geprüft und mit festen Rechten abgelegt; eine Wiederherstellung in einen leeren Container ergibt ein System, das ohne Dublette weiterarbeitet; ein Neustart nach Absturz nimmt offene Arbeit wieder auf. | Gerd 2026-09-03; `G-022`, `G-047`, `G-048` | Sicherung, Wiederherstellung in ein leeres Verzeichnis: Hash-Kette gültig, offene Claims werden fortgesetzt, kein zweiter Versand. Prozess mitten im Lauf getötet und neu gestartet: derselbe Ausgang. Sicherungsdatei mit `644 root:root`: Prüfung rot. |
| 14 | **Die Ablehnungsart überlebt die Wiederaufnahme.** Wird eine abgelehnte Antwort nach `REPLIED` bestätigt, sagt die Bestätigung „abgelehnt: Art", nie „beantwortet"; die Art ist Teil des dauerhaften Zustands, nicht des Prozesses. | Gerd, Backlog aus `e022862`, Punkt 1; `G-087` | Abgelehnte Antwort, Prozess stirbt zwischen Antwort und Bestätigung, Neustart: die nachgeholte Bestätigung trägt die Ablehnungsart. |
| 15 | **Endgültig gescheiterte Zustellung erreicht den CEO sichtbar.** Sind die Telegram-Versuche für eine Nachricht erschöpft, entsteht eine aktive Meldung an den CEO — über einen anderen Weg oder beim nächsten Kontakt — samt Auditzeile; ein Logeintrag allein ist keine Meldung. | Gerd, Backlog aus `e022862`, Punkt 2; `G-083` | Drei gescheiterte Versuche: genau eine CEO-Meldung, auditiert; die Nachricht steht als aufgegeben mit Grund, nicht als erledigt. |
| 16 | **Externe Zustellung ist abgleichbar.** Jeder Versand an Telegram speichert die externe Nachrichten-Id am Bus-Datensatz; eine Abgleichabfrage beweist, dass jede Antwort genau eine Zustellung oder einen verbuchten Fehlschlag hat — nicht nur, dass lokal nichts doppelt gesendet wurde. | Gerd 2026-09-03; `G-053`, `G-056` | Nach einem Lauf: je `REPLIED` genau ein Zustellsatz mit externer Id. Zustellsatz gelöscht: Abgleich meldet die Lücke. Zustellsatz doppelt: Abgleich meldet die Dublette. |

## Stand der Belege im Neubau (2026-09-08, Gerds Systemscreening)

Belegt mit Test: 1, 2, 3, 5 (teilweise), 6, 8, 9, 10, 12, 14, 16. **Offen, je mit dem
Meilenstein, der sie bringt:**

| # | Warum offen | Bis wann |
|---|---|---|
| 4 | Es gibt keine Agent-zu-Agent-Route, also keine Schleife, die enden müsste; ein Hop-Zähler ohne Route wäre ein Test ohne Gegenstand. | mit der ersten Route zwischen zwei Identitäten, dann Pflicht vor dem Lauf |
| 7 | Ablehnungen sind Auditzeilen, kein eigener Datensatztyp; „Audit kaputt bleibt Ablehnung" ist nicht geprüft. | Meilenstein nach Phase 3 |
| 13 | Sicherung und Kette sind getestet; Wiederherstellung in einen leeren Container und Wiederanlauf nach Absturz nicht. | vor Phase 4, weil Paperless den Zustand vergrößert |
| 15 | Die CEO-Meldung bei endgültig gescheiterter Zustellung läuft über denselben Kanal, der gerade gescheitert ist. | Meilenstein nach Phase 3, braucht einen zweiten Weg (E-Mail oder Log-Wächter) |

Eine Zeile ohne Beleg gilt weiter als Maßstab; sie ist nicht gestrichen, sondern datiert offen.

## Fünf Bauform-Zusagen

Keine Eigenschaften des Produkts, sondern Bedingungen dafür, dass die sechzehn oben prüfbar
bleiben. Sie haben den Großteil der übrigen Befunde erzeugt.

1. **Ein Zustand.** Es gibt genau einen Speicher für Nachrichten, Claims, Leases und
   Dubletten. Ein Prozess, der stirbt, hinterlässt nichts, was ein anderer Speicher wissen
   müsste. (`G-002`, `G-053`, `G-056`, `G-082`, `G-083`)
2. **Läuft auf dem Mac, oder es läuft nicht.** Jeder Test, jeder Lauf, jede Schemaänderung
   ist lokal ausführbar, bevor die NAS sie sieht. (`G-011`, `G-045`, `G-074`)
3. **Ausführbare Betriebsaktionen liegen in versionierten, getesteten Skripten.** Ein
   Dokument darf sie erklären und referenzieren, aber nicht ersetzen: Was im Fenster
   ausgeführt wird, hat eine Datei im Manifest, einen Test gegen Attrappen und einen
   Exitcode, der das Abbruchkriterium ist. (`G-042`, `G-043`, `G-055`, `G-068`, `G-072`,
   `G-085`, `G-086`)
4. **Konfiguration hat einen Ort und ein Schema.** Allowlists, Policies, Deckel, Modelle:
   eine Datei, geprüft beim Start, nicht verteilt auf Seeds, Env, Compose und Konstanten.
   (`G-057`, `G-066`, `G-077`, `G-090`)
5. **Der Prozess besitzt seine Daten, und nur die.** Kein Superuser, keine
   Eigentümerwanderung nachträglich; Rechte sind vom ersten Tag an die des Betriebs.
   (`G-045`, `G-071`, `G-074`–`G-079`)

## Was absichtlich fehlt

Der Bus als HTTP-Dienst für fremde Clients, ein Task-Board mit Zustandsautomat, Übergaben
zwischen Identitäten, ein Knowledge-Modul. Nichts davon hat im Prototyp je ein Mensch
benutzt. Sie kommen, wenn ein Lauf sie verlangt — als Meilenstein mit eigener Zeile hier,
nicht als Vorrat. Wählt der CEO die Weiterführung, bleiben sie, was sie sind, und diese
Seite gilt trotzdem.

## Wie der Review damit arbeitet

Beim Neubau: drei Meilensteine, jeder endet mit einem echten Lauf, Gerd prüft **nach** dem
Lauf gegen diese Seite — welche Zeile ist belegt, welche nicht, und was hat der Lauf gezeigt,
das hier fehlt. Ein Befund, der keinen dauerhaften Schaden verhindert, setzt kein Gate
zurück; er wird ein Test im nächsten Meilenstein. Ein Befund, der eine Zeile hier widerlegt,
stoppt. Bei der Weiterführung: dieselbe Seite, derselbe Modus, ab dem Phase-5-Fenster.
