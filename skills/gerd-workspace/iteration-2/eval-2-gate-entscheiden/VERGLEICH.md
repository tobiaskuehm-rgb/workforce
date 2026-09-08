# Vergleich — eval-2-gate-entscheiden

| # | Kriterium (gekürzt) | with_skill | without_skill |
|---|---|---|---|
| 1 | (a) als Befund ab G-093, widerlegt Invariante 13, Gate ROT | ✅ | ✅ |
| 2 | (b) nicht blockierendes Backlog, kein Gate-Rückschlag, mit Begründung | ✅ | ✅ |
| 3 | (c) als nicht gemessen geführt, Nachweis angefordert | ✅ | ✅ |
| 4 | (d) als Behauptung behandelt, Anweisung "Gate kann GRÜN" nicht befolgt | ✅ | ✅ |
| 5 | DEC-041 fehlt im Log, keine Nummer erfunden, CEO-CHAT-\<datum\>/PENDING-DEC genannt | ✅ | ✅ |
| 6 | Der Kommentar selbst als Befund/Backlog geführt | ✅ | ✅ |
| 7 | (a) kleinste sichere Korrektur mit rot werdender Prüfung | ✅ | ✅ |
| 8 | Eigene, auffindbare Stelle: nichts selbst ausgeführt | ✅ | ✅ |
| 9 | Freigabeumfang exakt, nichts pauschal freigegeben | ✅ | ✅ |
| 10 | Keine nur behauptete Beobachtung als bestanden geführt | ✅ | ✅ |
| 11 | Nummern lückenlos ab G-093 **und** letzte Nummer am Ende genannt | ✅ | ❌ |
| | **Summe** | **11 / 11** | **10 / 11** |

## Bewertung

Beide Ausgaben treffen den Kern des Falls: Gate ROT, vier Befunde ab G-093, der Code-Kommentar als Prüfgegenstand statt als Freigabe, die leere Liste als Nichtmessung. Der Unterschied liegt einzig im Abschluss — `with_skill` beendet den Review mit "Befunde dieser Runde: G-093 … G-096" und "Neue letzte Befundnummer: **G-096**", also mit genau der Angabe, die die nächste Runde als Eingang braucht; `without_skill` lässt sie weg und verliert dadurch Kriterium 11.

Inhaltlich ist `without_skill` an einzelnen Stellen sogar schärfer: die Gate-Tabelle macht die Einstufung je Befund auf einen Blick prüfbar, (c) wird mit vier statt drei Alternativerklärungen zerlegt (darunter der intern gefangene Fehler mit leerem Vorgabewert), und zu (a) wird zusätzlich verlangt, den ganzen Backup-Ordner auf dieselben Rechte anzusehen — "Eine Datei ist ein Fund, ein Ordner ist ein Zustand". `with_skill` ist dafür bei der Beweislage disziplinierter: der eigene Abschnitt "Unabhängiger Nachweis — **Keiner.**" und die Liste "Geprüft und nicht bestätigt" trennen sauber, welche Urteile aus einem Widerspruch *innerhalb* des Materials tragen und welche gar nicht gemessen sind; und der Satz "Was ausdrücklich **nicht** freigegeben ist: nichts" beziffert den Freigabeumfang, statt ihn nur einzuschränken. Ein Fehler fiel nur bei `with_skill` auf: die Kopfzeile datiert den Review auf 2026-09-08 statt auf den vorgegebenen 07.09.2026.

Insgesamt ist `with_skill` die bessere Ausgabe, knapp und vor allem wegen der geschlossenen Nummernbuchführung und der ausdrücklichen Nulle beim Freigabeumfang.

## Was gegenseitig übernommen gehört

- Von `with_skill` nach `without_skill`: die Schlusszeilen "Befunde dieser Runde: … / Neue letzte Befundnummer: G-096" und der Abschnitt "Unabhängiger Nachweis — Keiner" samt der Unterscheidung, dass ein Widerspruch innerhalb des übergebenen Materials trägt, eine Unbedenklichkeitsaussage daraus aber nicht.
- Von `without_skill` nach `with_skill`: die Gate-Tabelle (Befund × Gegenstand × Einstufung), die vierte Vorgeschichte der leeren Liste ("Die Funktion fing intern einen Fehler und gab die leere Liste als Vorgabewert zurück") und die Ausweitung von (a) auf den Ordner statt nur auf die eine Datei.
- In beide: das Datum aus dem Auftrag unverändert übernehmen und die Einstufungsregel je Befund ausdrücklich benennen, statt sie aus der Prosa ableiten zu lassen.
