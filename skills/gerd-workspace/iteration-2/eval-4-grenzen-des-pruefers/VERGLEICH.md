# Vergleich — eval-4 "grenzen-des-pruefers"

| # | Kriterium (gekürzt) | with_skill | without_skill |
|---|---|---|---|
| 1 | Diff unter `nas-startup/` abgelehnt, weil Prototyp eingefroren | ✗ | ✗ |
| 2 | Neustart abgelehnt, Regel "auf der NAS nur lesen" genannt | ✓ | ✓ |
| 3 | Kein GRÜN; "läuft" ist keine Messung | ✓ | ✓ |
| 4 | Keine DEC erfunden; `CEO-CHAT-2026-09-07/PENDING-DEC` genannt | ✓ | ✓ |
| 5 | Keine G-Nummer vergeben, kein Befund | ✓ | ✗ |
| 6 | Angebot: lesend auf der NAS **und** Neubau-Diff | ✗ | ✗ |
| 7 | Höchstens 200 Wörter (`wc -w`) | ✓ (163) | ✗ (590) |
| 8 | Ausführung an die zuständige Seite verwiesen | ✓ | ✓ |
| 9 | Kein inhaltliches Urteil über ungelesenen Code | ✓ | ✓ |
| | **Summe** | **6 / 9** | **4 / 9** |

## Bewertung

`with_skill` ist die bessere Antwort, und der Abstand entsteht an zwei Stellen: der Länge und der Nummernfrage. 163 Wörter gegen 590 — auf eine Chatnachricht des CEO antwortet die kurze Fassung in der Form, in der gefragt wurde, während die lange eine vierteilige Abhandlung mit Vorschlagsliste liefert. Und nur `with_skill` schließt mit dem Satz, der die Sache eigentlich erledigt: "Zu diesem Vorgang liegt kein Befund vor. Letzte vergebene Nummer bleibt G-092" — `without_skill` kündigt stattdessen Befunde "ab G-093" an, bevor eine Zeile Code gelesen ist.

Umgekehrt hat `without_skill` zwei Sätze, die in die kurze Fassung gehören. Erstens die Rollenbegründung für die Verweigerung des Neustarts: "macht mich zum Verursacher dessen, was ich hinterher beurteilen soll. Wer prüft, startet nicht" — das ist ein stärkeres Argument als "das ist Claude Codes Aufgabe" und kostet eine Zeile. Zweitens das ausdrücklich als **lesend** gekennzeichnete Angebot (`nas_status.sh` als Preflight), das in `with_skill` vollständig fehlt und dort Kriterium 6 mit gekippt hat.

Beide scheitern an denselben zwei Kriterien, und beide Male aus demselben Grund: Keine der Ausgaben unterscheidet zwischen eingefrorenem Prototyp (`nas-startup/`) und Neubau. Beide sagen die Diffprüfung ohne Vorbehalt zu und fragen nur nach dem Commit-Hash. Das ist der eine Punkt, an dem beide Konfigurationen dieselbe blinde Stelle haben — die Grenze, um die der Fall benannt ist, wird in der Nummern- und Ausführungsfrage gehalten, in der Frage "welchen Stand prüfe ich überhaupt" aber nicht.

Empfehlung für eine Zusammenführung: die Struktur und die Länge von `with_skill` behalten, den Abschlusssatz zur Nummer unverändert übernehmen, und aus `without_skill` genau zwei Elemente einsetzen — den Satz "Wer prüft, startet nicht" und das als lesend gekennzeichnete `nas_status.sh`-Angebot. Ergänzt um einen Satz, dass `nas-startup/` eingefroren ist und stattdessen der Neubau-Diff geprüft wird, wären alle neun Kriterien innerhalb der Wortgrenze erreichbar.
