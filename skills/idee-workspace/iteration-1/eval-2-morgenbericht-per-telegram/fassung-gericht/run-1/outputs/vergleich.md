# Ideen-Vergleich: Morgenbericht von Marlene

## Frage und Annahmen

**Die Idee, wörtlich in ganzen Sätzen:** Marlene schickt Tobias jeden Morgen um 7 Uhr per Telegram einen Bericht darüber, was fällig ist und was sie am Vortag gemacht hat. Dann muss Tobias nicht mehr in den Ordner gucken.

**Die Frage dahinter:** Wie erfährt Tobias jeden Morgen ohne eigenes Nachsehen, was in seiner privaten Verwaltung fällig ist und was Marlene am Vortag erledigt hat?

**Widerspruch zu einer bestehenden Entscheidung — steht hier, wie Regel 8 es verlangt:** Am 04.09.2026 wurde entschieden, dass der Bericht vorerst als Datei in `_Berichte` liegt und die Telegram-Zustellung später kommt. Die Idee macht genau das jetzt. Das ist kein Ausschlussgrund, aber es ist eine Entscheidung, die neu getroffen werden müsste, nicht bloß eine offene Stelle.

**Annahmen, die die Idee voraussetzt und nicht sagt:**
- Der tägliche Berichtslauf soll unaufgefordert laufen, auch an Tagen ohne Fälligkeiten.
- „7 Uhr" heißt ein fester Zeitplan; im Skill ist der nicht einrichtbar, er muss außerhalb liegen.
- Der Dateibericht in `_Berichte` bleibt bestehen und wird nur zusätzlich zugestellt — die Idee sagt nicht, ob die Datei entfallen soll.
- Die tägliche Grundlast passt in die Deckel des Bots.

**Frage an Tobias, mit Empfehlung:** Soll die Datei in `_Berichte` bleiben, wenn der Telegram-Bericht kommt? Empfehlung: ja — sie ist der Nachweis, die Nachricht ist nur die Zustellung.

## Messung

| Sache | Wert | Herkunft |
|---|---|---|
| Berichtsablage | Datei in `_Berichte`, Telegram vertagt | Entscheidung 04.09.2026 |
| Deckel des Bots | 2 USD und 100 Aufrufe pro Tag | Entscheidung 08.09.2026 |
| Modell Marlenes im Bot | Sonnet | bekannte Lage |
| Zeitplan im Skill | nicht einrichtbar, nur außerhalb | bekannte Lage |
| Datum | 08.09.2026 | — |
| Kosten je Berichtslauf | **nicht gemessen**, alle Kostenangaben unten geschätzt | — |
| Füllstand des Tagesdeckels | **nicht gemessen** | — |
| Inhalt von `_Berichte` | **nicht gemessen** (kein Dateizugriff in diesem Lauf) | — |

## Die zehn Punkte

Die Standardliste des Verfahrens, unverändert, festgelegt vor dem Gegenvorschlag: Ziel, Zeit bis Nutzen, Aufwand, Kosten, Risiko, Rücknehmbarkeit, Passung, Messbarkeit, Abhängigkeiten, Nebenwirkungen.

## Vorschlag A

Kein Zeitplan, kein automatischer Versand. Der Bericht bleibt als Datei in `_Berichte`, wie am 04.09. entschieden. Zusätzlich beantwortet Marlene im Telegram-Bot auf Zuruf: Tobias schreibt „was ist fällig", Marlene antwortet mit derselben Gliederung wie der Dateibericht (fällig heute, fällig diese Woche, gestern erledigt).

- **Ort:** Telegram-Bot, bestehende Marlene-Identität; Ablage unverändert in `_Berichte`.
- **Ablauf:** Tobias fragt, wenn er es wissen will, meist morgens. Marlene liest den zuletzt geschriebenen Dateibericht und ergänzt, was seither dazugekommen ist.
- **Kosten:** geschätzt ein Sonnet-Aufruf je Frage, also nur an Tagen, an denen gefragt wird; bei einer Frage am Tag ein Bruchteil des 2-USD-Deckels und 1 von 100 Aufrufen.
- **Aufwand:** einmalig gering, es entsteht nur eine feste Antwortgliederung für Marlene; laufend eine Nachricht von Tobias am Tag.
- **Risiko:** Tobias vergisst zu fragen und erfährt nichts. Kein technischer Ausfall möglich, weil nichts läuft.
- **Rücknahme:** sofort, es gibt nichts abzubauen.

## Vorschlag B

Marlene schickt jeden Morgen um 7:00 Uhr unaufgefordert per Telegram einen Bericht: was fällig ist und was sie am Vortag gemacht hat. Der Ordner muss dann nicht mehr geöffnet werden.

- **Ort:** Telegram-Bot, Marlene-Identität; Zeitplan außerhalb des Skills (Systemzeitplaner oder externer Dienst), weil er im Skill nicht einrichtbar ist.
- **Ablauf:** Um 7:00 löst der Zeitplan einen Marlene-Lauf aus; Marlene erzeugt den Bericht, legt ihn wie bisher in `_Berichte` ab und schickt ihn zusätzlich in den Telegram-Chat.
- **Kosten:** geschätzt ein bis mehrere Sonnet-Aufrufe je Morgen, jeden Tag, auch an Tagen ohne Fälligkeiten; feste tägliche Grundlast gegen den 2-USD- und 100-Aufrufe-Deckel.
- **Aufwand:** einmalig Einrichtung des Zeitplans außerhalb des Skills samt Anmeldedaten und Fehlerbehandlung; laufend null Aufwand für Tobias.
- **Risiko:** Zeitplan läuft nicht (Rechner aus, Fehler) und niemand merkt es, weil das Ausbleiben einer Nachricht wie „nichts fällig" aussieht; bei erschöpftem Tagesdeckel fällt der Bericht ebenfalls still aus. Widerspricht der Entscheidung vom 04.09.
- **Rücknahme:** Zeitplan abschalten, wenige Minuten.

## Bewertung

**Bewertet von einer fremden Instanz, blind.** Ein eigener Lauf, der Frage, Messung, beide Vorschläge und die zehn Punkte bekommen hat, ohne Herkunftsangabe und ohne Zugriff auf diese Datei.

| # | Punkt | A | A Grund | B | B Grund |
|---|---|---|---|---|---|
| 1 | Ziel | 3 | Liefert die Auskunft in der verlangten Gliederung, aber die Frage verlangt ausdrücklich „ohne eigenes Nachsehen", und Fragen ist eine Holhandlung. | 4 | Erfüllt den Bringschuld-Kern der Frage genau, verfehlt ihn aber an jedem Morgen, an dem der Zeitplan still ausfällt. |
| 2 | Zeit bis Nutzen | 5 | Nur eine Antwortgliederung nötig, ab der nächsten Nachricht nutzbar. | 3 | Erst nach Einrichtung von Zeitplan, Anmeldedaten und Fehlerbehandlung außerhalb des Skills. |
| 3 | Aufwand | 3 | Einmalig fast null, dafür laufend jeden Tag eine bewusste Handlung von Tobias. | 4 | Einmalige Einrichtung samt Fehlerbehandlung, danach null laufender Aufwand für Tobias, was die Frage genau will. |
| 4 | Kosten | 5 | Ein Aufruf nur an Tagen mit Frage, minimaler Anteil an beiden Deckeln. | 3 | Feste Tagesgrundlast von ein bis mehreren Aufrufen auch an Tagen ohne Fälligkeit, gegen einen ungemessenen Deckelfüllstand. |
| 5 | Risiko | 3 | Kein technischer Ausfall möglich, aber das Restrisiko „Tobias vergisst zu fragen" trifft genau den Zweck. | 2 | Stiller Ausfall durch Rechner aus, Fehler oder erschöpften Deckel ist ununterscheidbar von „nichts fällig". |
| 6 | Rücknehmbarkeit | 5 | Es läuft nichts, es gibt nichts abzubauen. | 4 | Zeitplan abschalten dauert Minuten, ist aber ein realer Rückbauschritt außerhalb des Skills. |
| 7 | Passung | 5 | Hält die Entscheidung vom 04.09. ein, weil die Ablage unverändert bleibt und nur auf Zuruf geantwortet wird. | 2 | Führt genau die Telegram-Zustellung ein, die am 04.09. ausdrücklich vertagt wurde, ohne dass eine neue Entscheidung dazu gemessen ist. |
| 8 | Messbarkeit | 3 | An der Zahl der Fragen im Chat ablesbar, aber ausbleibende Fragen sagen nicht, ob es am Verfahren oder an der Gewohnheit lag. | 3 | Empfangene Nachrichten sind zählbar, doch fehlende Morgen sind nicht von fälligkeitsfreien Tagen zu unterscheiden. |
| 9 | Abhängigkeiten | 4 | Braucht Telegram-Bot und den vorhandenen Dateibericht, nichts darüber hinaus. | 2 | Braucht zusätzlich einen laufenden Rechner oder externen Dienst, dessen Anmeldedaten und dessen Verfügbarkeit. |
| 10 | Nebenwirkungen | 4 | Zwei Auskunftswege (Datei und Chat) können bei Nachträgen auseinanderlaufen. | 3 | Tägliche Nachricht kann bei leerem Inhalt zur Gewohnheitsblindheit führen und verbraucht Deckel für andere Nutzung. |

**Summe A: 40 — Summe B: 30**

## Fazit

**Auflösung:** A war der Gegenvorschlag, B ist Tobias' Idee.

**Wer gewinnt, wo, und warum die Summe täuscht.** Nach Punkten gewinnt A mit 40 zu 30, und zwar in Kosten, Passung und Abhängigkeiten — also überall dort, wo die heutige Lage zählt. Genau da täuscht die Summe: Diese drei Punkte sind Zustände, keine Eigenschaften. Eine neue Entscheidung zur Telegram-Zustellung, eine gemessene Kostenzahl je Lauf und ein Zeitplan, der irgendwo läuft, würden B in allen dreien heben, während A in Punkt 1 — dem eigentlichen Zweck, „ohne eigenes Nachsehen" — dauerhaft schwächer bleibt, weil es die Zuverlässigkeit auf Tobias' Gedächtnis verlagert. Die Idee ist also nicht die schwächere Lösung, sondern die noch nicht zulässige.

**Was aus dem unterlegenen Vorschlag in den Gewinner gehört.** Aus A geht die Deckelrücksicht in B: ein Aufruf je Morgen, keine Kette. Aus A geht die Beibehaltung der Datei in `_Berichte` — die Nachricht ist Zustellung, nicht Ablage. Und aus A geht der Abruf selbst: „was ist fällig" auf Zuruf ist die Rückfallebene für jeden Morgen, an dem der Zeitplan nicht gelaufen ist, und kostet nichts, solange niemand fragt.

**Die eine Sache, die am ehesten noch falsch ist.** Beide Vorschläge stehen und fallen mit den geschätzten Kosten je Berichtslauf. Sie sind in diesem Lauf nicht gemessen worden. Liegt ein Marlene-Berichtslauf deutlich über der Schätzung, ist der Kostenpunkt von B kein Nachteil mehr, sondern ein Ausschlussgrund — und dann ist auch A nicht die Antwort, sondern ein Bericht, der ohne Modellaufruf aus der Datei vorgelesen wird.

**Keine Entscheidung. Die trifft Tobias.** Was ansteht, ist eine Entscheidung zur Telegram-Zustellung, die die vom 04.09. ablöst.
