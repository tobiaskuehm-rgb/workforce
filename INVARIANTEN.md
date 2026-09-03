# Invarianten des Neubaus — Entwurf für die DEC

**Status:** Entwurf, `CEO-CHAT-2026-09-03/PENDING-DEC` (`G-006`: die Nummer entsteht im
iCloud-Quellensatz, nicht hier). **Entwurf:** Claude Code. **Prüfung:** Gerd streicht und
ergänzt. **Unterschrift:** CEO. Danach ist diese Seite der Maßstab, gegen den jeder
Meilenstein nach seinem Lauf geprüft wird — nicht mehr, nicht weniger.

**Prüffrage je Zeile:** Welcher Befund des Prototyps wäre damit vom ersten Tag an unmöglich
gewesen? Eine Zeile ohne Befund ist eine Meinung. Ein Befund ohne Zeile war ein Symptom
der alten Bauform und braucht im Neubau keinen Test.

## Die zwölf Eigenschaften

Jede Zeile: was gilt, welcher Befund sie erzwungen hat, welcher Test sie beweist.

| # | Eigenschaft | Erzwungen durch | Beweis im Neubau |
|---|---|---|---|
| 1 | **Fail-closed ist die Voreinstellung.** Kanal aus, Schalter aus, unbekannte Route abgelehnt. Ein leerer Start antwortet niemandem. | `G-031`, `G-041`, Security-Review | Frischer Start ohne Konfiguration: keine Antwort, kein Provideraufruf. Unbekannte Route: Ablehnung mit stabilem Code. |
| 2 | **Der Kill Switch wirkt innerhalb einer Abfragerunde.** Ein Zustandswechsel stoppt jeden Ausgang, Provider wie Messenger. | Bus-Abnahme, `G-062` | Kanal mitten im Lauf auf aus: kein weiterer Provideraufruf, kein Versand, offene Arbeit bleibt sichtbar. |
| 3 | **Der Empfänger kommt aus dem Datensatz, nie aus der Modellausgabe.** Routen sind eine explizite Allowlist. | `G-003`, Injektionstests | Injizierte Anweisung „sende an X" im Text: Antwort geht an den ursprünglichen Absender, X sieht nichts. |
| 4 | **Schleifen enden.** Hop-Zähler auf jeder Nachricht, zwei Agenten, die aufeinander zeigen, stoppen. | Bus-Abnahme | Zwei Identitäten mit Route zueinander: Kette endet beim Limit, mit Auditzeile. |
| 5 | **Idempotenz hat zwei Linien, und sie sind nicht austauschbar.** Nachrichten-Id ist aus Absender und Schlüssel abgeleitet; ein Claim ohne dauerhafte Wirkung wird zurückgegeben; jeder Claim hat Lease und Versuchszähler. | `G-001`, `G-002`, `G-013`, `G-053`, `G-056`, `G-082`, `G-083` | Prozess stirbt nach Versand vor Bestätigung: genau ein Ausgang. Lokaler Zustand gelöscht: immer noch genau einer. Lease abgelaufen: ein zweiter Prozess übernimmt, ein dritter nicht. |
| 6 | **Der Lauf ist allein aus der Datenbank rekonstruierbar.** Jeder dauerhafte Schreibvorgang trägt Akteur und Request-Id; das Audit ist eine Hash-Kette. | Audit-Trigger `002`, `G-059`, `G-070` | Lauf, Prozess weg, Reihenfolge aus der Datenbank nachgespielt: identisch. Eine Zeile verändert: Kettenprüfung schlägt an. |
| 7 | **Jede Ablehnung ist ein Datensatz.** Stabiler Code, kein Inhalt, geschrieben auch dann, wenn die abgelehnte Operation zurückgerollt wurde. | `005`, `G-014` | Abgelehnter Aufruf: eine Ablehnungszeile mit Code, ohne Nachrichtentext. Audit kaputt: die Ablehnung bleibt eine Ablehnung, wird kein Serverfehler. |
| 8 | **Es gibt eine Datengrenze, und sie ist eine Funktion.** Alles, was zu Provider oder Messenger geht, läuft durch sie; die Feldmenge je Policy ist eine Konstante; der Betreff ist Inhalt. | `G-029`, `G-054`, `G-084`, Security-Review | Statische Prüfung: jeder Ausgangspfad ruft die Grenze. `METADATA_ONLY` lässt weder Text noch Betreff durch. Ein lokales Modell darf mehr sehen als ein fremdes, und das steht in der Konstante. |
| 9 | **Kosten werden reserviert, bevor sie entstehen.** Versuch, Eingabe, maximale Ausgabe und Preis müssen gemeinsam in den Rest passen; ein bezahlter Provider unter Nulldecke wird vor dem ersten Aufruf abgewiesen; ein fehlgeschlagener Versuch zählt. | `G-004`, `G-016`, `G-057`, `G-065` | Decke null plus bezahlter Provider: kein Aufruf. Geschätzte Kosten über Rest: kein Aufruf. Aufruf scheitert: Versuch trotzdem verbraucht. |
| 10 | **Der Agent bleibt werkzeuglos.** Der Provider nimmt Text und gibt Text; die Modellausgabe wird ausschließlich als Antworttext verwendet. | Security-Review 2026-08-31 | Provider-Attrappe liefert etwas, das wie ein Werkzeugaufruf aussieht: es wird als Text behandelt, nichts wird ausgeführt. |
| 11 | **Jede Wirkung trägt ihre Herkunft.** Request-Id der Form `<PRÄFIX>-<lauf>-<phase>`, deterministisch aus der Anfrage abgeleitet; Nachweise binden an exakte Ids, nie an „irgendein Datensatz dieses Typs". | `G-059`, `G-070` | Zwei Läufe hintereinander: jeder ist für sich rekonstruierbar, keiner sieht den Datensatz des anderen. |
| 12 | **Secrets liegen in Dateien, im Klartext, minimal.** Nie in Umgebung, Repo oder Chat; ein Prozess bekommt nur das Geheimnis, das er benutzt; Eigentümer und Rechte sind feste Zahlen. | `G-017`, `G-044`, `G-089`, Kettenlauf 2026-09-01 | Geheimnis nur in der Umgebung: Start verweigert. Echo-Betrieb: kein Modellschlüssel im Container. Datei mit falscher Form: stabiler Fehler, Wert nie ausgegeben. |

## Fünf Bauform-Zusagen

Keine Eigenschaften des Produkts, sondern Bedingungen dafür, dass die zwölf oben prüfbar
bleiben. Sie haben den Großteil der übrigen Befunde erzeugt.

1. **Ein Zustand.** Es gibt genau einen Speicher für Nachrichten, Claims, Leases und
   Dubletten. Ein Prozess, der stirbt, hinterlässt nichts, was ein anderer Speicher wissen
   müsste. (`G-002`, `G-053`, `G-056`, `G-082`, `G-083`)
2. **Läuft auf dem Mac, oder es läuft nicht.** Jeder Test, jeder Lauf, jede Schemaänderung
   ist lokal ausführbar, bevor die NAS sie sieht. (`G-011`, `G-045`, `G-074`)
3. **Kein Dokument enthält Befehle.** Was ausgeführt wird, ist ein Kommando mit Exitcode;
   was gelesen wird, ist aus dem Kommando erzeugt. (`G-042`, `G-043`, `G-055`, `G-068`,
   `G-072`, `G-085`, `G-086`)
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
nicht als Vorrat.

## Wie der Review damit arbeitet

Drei Meilensteine, jeder endet mit einem echten Lauf. Gerd prüft **nach** dem Lauf gegen
diese Seite: Welche Zeile ist belegt, welche nicht, und was hat der Lauf gezeigt, das hier
fehlt. Ein Befund, der keinen dauerhaften Schaden verhindert, setzt kein Gate zurück; er
wird ein Test im nächsten Meilenstein. Ein Befund, der eine Zeile hier widerlegt, stoppt.
