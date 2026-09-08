# Ideen-Vergleich (Fassung C, Synthese): Morgenbericht von Marlene

## 1. Die Frage und das Ziel

**Frage:** Tobias muss täglich selbst in einen Ordner sehen, um zu wissen, was fällig ist und was Marlene zuletzt getan hat. Wie kommt diese Information zu ihm, ohne dass er nachsieht?

**Die Idee, wörtlich:** „Marlene schickt mir jeden Morgen um 7 Uhr per Telegram einen Bericht, was fällig ist und was sie gestern gemacht hat. Dann muss ich nicht mehr in den Ordner gucken."

**Annahmen darin:** dass der Nutzen am Morgen entsteht; dass ein fester Termin nötig ist; dass Push besser ist als Abruf; dass Telegram der Weg ist.

**Gemessen** (übernommene Lage, in diesem Lauf nicht selbst nachgemessen — ich durfte keine Projektdateien öffnen, nur den Skill-Ordner):

| Tatsache | Quelle |
|---|---|
| Bericht liegt vorerst als Datei in `_Berichte`, Telegram später | Entscheidung 04.09.2026 |
| Bot deckelt bei 2 USD und 100 Aufrufen pro Tag | Entscheidung 08.09.2026 |
| Marlene läuft im Bot auf Sonnet | Lage |
| Zeitplan im Skill nicht einrichtbar, nur außerhalb | Lage |

**Geschätzt / offen:** Kosten eines Berichtslaufs, Laufzeit, Zustellquote von Telegram. Nichts davon liegt vor.

## 2. Der Gegenvorschlag

**B — Der Vorspann statt des Weckers.** Kein fester Termin, kein Push. Beim ersten Kontakt, den Tobias an einem Tag ohnehin mit dem Bot hat, stellt Marlene ihrer Antwort eine kurze Fälligkeitszeile voran: heute fällig, überfällig, zuletzt erledigt. Schreibt er nicht, kommt nichts. Kein Zeitplaner außerhalb, keine zusätzliche Auslösung.

Einseitig an anderer Stelle: A ist einseitig auf Verlässlichkeit ohne Zutun, B ist einseitig auf null Betriebsteile.

## 3. Die Zerlegung (zwanzig Zellen, ohne Wertung)

| Bestandteil | A — 7 Uhr, Push per Telegram | B — Vorspann beim ersten Kontakt |
|---|---|---|
| Ziel | Tobias erfährt es, ohne irgendetwas zu tun. Der Ordner wird überflüssig. | Tobias erfährt es beim ersten Mal, wenn er ohnehin schreibt. Der Ordner wird überflüssig, sobald er schreibt. |
| Zeit bis Nutzen | Erst nach Einrichtung eines Zeitplaners außerhalb und eines Versandpfads. | Sofort: eine Regel im Skill, ab dem nächsten Aufruf wirksam. |
| Aufwand | Zeitplaner außerhalb, Berichtsauftrag, Weg der Ausgabe nach Telegram, Fehlerfall bei Ausfall. | Ein Vorspann in einer Antwort, die ohnehin erzeugt wird. |
| Kosten | Ein zusätzlicher Sonnet-Lauf täglich gegen die 2-USD-Decke, auch an Tagen ohne Leser. | Kein zusätzlicher Aufruf; hängt sich an einen, der stattfindet. |
| Risiko | Kann still ausfallen: toter Zeitplaner, nicht zugestellte Nachricht. Beides unbemerkt. | Kann ausbleiben, wenn Tobias tagelang nicht schreibt — genau dann, wenn Fristen unbemerkt reifen. |
| Rücknehmbarkeit | Zeitplaner lebt außerhalb des Repos und muss aktiv abgeschaltet werden. | Skill-Änderung, wieder herausnehmbar. |
| Passung | Nimmt „Telegram später" vom 04.09. vorweg; die Decke vom 08.09. wird täglich belastet. | Bleibt innerhalb des bestehenden Bot-Betriebs; verlässt aber ebenfalls den Ordner. |
| Messbarkeit | Fester täglicher Lauf ergibt eine gleichmäßige Reihe: Kosten je Lauf, Laufzeit, Zustellquote messbar. | Messung hängt am unregelmäßigen Nutzerverhalten; keine Reihe. |
| Abhängigkeiten | Zeitplaner, Bot zur festen Uhrzeit erreichbar, Telegram-Versandweg. | Nichts, was nicht ohnehin läuft. |
| Nebenwirkungen | Knabbert früh am Tag an der 100-Aufrufe-/2-USD-Decke; schweigt trotzdem an Tagen, an denen Tobias arbeitet. | Längerer erster Antworttext; Vorspann kann bei kurzer Frage stören. |

## 4. Die zehn Wahlen

**Urheber der Wahlen: eine fremde Instanz** (Subagent, ohne Kenntnis der Herkunft von A und B; nur Frage, Messung, beide Vorschläge, die zehn Punkte).

| Bestandteil | Wahl | Begründung |
|---|---|---|
| Ziel | **A** | Die Frage sagt „ohne dass er nachsehen muss"; B verlagert das Nachsehen vom Ordner in den Chat. |
| Zeit bis Nutzen | **B** | Sofort wirksam; A braucht erst einen Zeitplaner außerhalb. |
| Aufwand | **B** | Kein Zeitplaner, keine Auslösung, kein Versandpfad. |
| Kosten | **B** | A erzeugt täglich einen Lauf gegen die Decke, auch ohne Nutzen. |
| Risiko | **B** | A kann still ausfallen; ein fehlender Vorspann fällt sofort auf. |
| Rücknehmbarkeit | **B** | A hinterlässt einen Zeitplaner außerhalb, den jemand abschalten muss. |
| Passung | **Gleichstand → A** | 04.09. spricht für A, 08.09. für B. Nach Regel 3 geht Gleichstand an den Auftraggeber. |
| Messbarkeit | **A** | Nur ein fester Lauf ergibt eine Reihe, an der sich Kosten und Zustellung messen lassen. |
| Abhängigkeiten | **B** | A hängt an drei Teilen, B an keinem zusätzlichen. |
| Nebenwirkungen | **B** | A belastet die Decke und schweigt trotzdem an Arbeitstagen. |

Stand: A gewinnt Ziel, Passung (Gleichstand), Messbarkeit. B gewinnt die übrigen sieben.

## 5. Der dritte Vorschlag — C

**C — Der Bericht wird geschrieben, wo er hingehört, und wandert dann von selbst.**

Marlene erzeugt den Tagesbericht weiterhin als Datei in `_Berichte` — das ist der Zustand, der belegbar ist und den man später nachlesen kann. Ausgelöst wird er nicht von einem Wecker im Skill (den es dort nicht gibt), sondern von einem einzigen Zeitplaner außerhalb, der einmal morgens den Berichtsauftrag startet. Was Tobias per Telegram bekommt, ist **nicht** der Bericht, sondern eine kurze Zeile: „3 fällig, 1 überfällig, gestern: Rockhausen abgelegt" — mit dem Verweis auf die Datei. Zusätzlich stellt Marlene beim **ersten** Bot-Kontakt des Tages dieselbe Zeile ihrer Antwort voran, wenn der Morgenlauf nicht stattgefunden hat. Der Morgenlauf zählt gegen ein eigenes, kleines Kontingent innerhalb der 100 Aufrufe; reißt er die Decke, unterbleibt er und der Vorspann trägt allein.

| Teil von C | Herkunft |
|---|---|
| Fester Auslöser morgens, Zeitplaner außerhalb | A |
| Zustellung per Telegram | A |
| Fester Lauf als Messreihe (Kosten, Laufzeit, Zustellung) | A |
| Bericht bleibt Datei in `_Berichte` | Lage/04.09., von keinem der beiden aufgegeben |
| Kurze Zeile statt vollem Bericht in Telegram | neu — A wollte den ganzen Bericht pushen, B gar nichts pushen; die Kurzform hält beide Kosten klein |
| Vorspann beim ersten Kontakt | B |
| Vorspann nur als Rückfall, wenn der Morgenlauf ausblieb | neu — A und B lösen dasselbe doppelt aus; ungeglättet nebeneinander wäre es zweimal dieselbe Information |
| Eigenes Kontingent, Ausfall statt Deckenbruch | B |

**Wo sich zwei gewählte Teile nicht vertragen, und ich das nicht glätte:** Die Wahl bei „Risiko" ging an B, weil ein stiller Ausfall dort unmöglich ist. C nimmt den Zeitplaner aus A trotzdem mit und kann deshalb still ausfallen — der Vorspann fängt das ab, aber nur, wenn Tobias schreibt. An einem Tag ohne Zeitplaner **und** ohne Nachricht kommt nichts. Diese Lücke bleibt in C offen; sie ist nicht wegkonstruiert, sondern hingenommen.

## 6. Was weggefallen ist

- **Der volle Berichtstext in Telegram** (aus A). Grund: kostet Ausgabe-Token für etwas, das als Datei ohnehin vollständig vorliegt, und wird auf dem Telefon selten ganz gelesen.
- **Die feste Uhrzeit 7 Uhr als Zusage** (aus A). Grund: nicht gemessen, ob der Bot zu dieser Zeit erreichbar ist; C sagt „morgens", nicht „7:00", bis eine Zustellquote vorliegt.
- **Der Verzicht auf jeden Betriebsteil** (aus B). Grund: mit ihm fiele die Messreihe weg, und ohne Messreihe bleiben Kosten je Lauf für immer geschätzt.
- **Das Ausbleiben an schweigsamen Tagen** (aus B). Grund: genau dann reifen Fristen unbemerkt — der Fall, für den das Ganze gebaut wird.

**Was an C am ehesten falsch ist:** Der Zeitplaner außerhalb ist der einzige Teil, den niemand prüft. Fällt er aus, sieht C von innen gesund aus, und die einzige Sicherung ist, dass Tobias an dem Tag zufällig schreibt. Wer C baut, baut als Erstes die Meldung „seit N Tagen kein Morgenlauf" in den Vorspann — sonst hat C das Risiko von A geerbt, ohne es zu bemerken.

**Keine Entscheidung.** Tobias entscheidet, ob C gebaut wird, A bleibt oder B kommt.
