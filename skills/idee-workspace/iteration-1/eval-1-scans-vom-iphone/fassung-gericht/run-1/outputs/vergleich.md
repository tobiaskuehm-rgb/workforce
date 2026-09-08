# Ideen-Vergleich: Scans vom iPhone über iCloud

Fassung A, das Gericht. 08.09.2026.

## Die Frage hinter der Idee

**Frage:** Wie kommen künftig alle Scans zuverlässig, vollständig und über genau einen Eingang zu Marlene, die lokal auf dem Mac liest und jede Datei vollständig braucht?

**Die Idee, wörtlich in ganze Sätze gebracht:** Alle Scans entstehen künftig mit dem iPhone. Sie landen direkt in einem Ordner „Eingang" in iCloud. Marlene holt sie sich von dort. Der Scanner am Mac wird abgeschafft.

**Berührung einer bestehenden Entscheidung:** Die Idee widerspricht keiner getroffenen Entscheidung, aber sie nimmt eine offene vorweg. Das Ablagekonzept vom 07.09.2026 sieht iCloud als Eingang bereits vor; die Entscheidung dazu ist offen. Die Entscheidung vom 07.09.2026 zum NAS-Ordner (Marlene nur lesend) wird durch die Idee gegenstandslos, weil dieser Weg entfällt.

**Annahmen, die die Idee voraussetzt und nicht sagt:**
- Dass eine Datei, die in iCloud sichtbar ist, auf dem Mac auch vollständig vorliegt.
- Dass das iPhone die Qualität liefert, die der Mac-Scanner heute liefert (mehrseitig, Duplex, Einzug).
- Dass Marlene ihren Lesepfad auf iCloud umstellen darf und der Ordner lokal materialisiert ist.
- Dass es nach der Abschaffung keinen zweiten Weg mehr braucht.

**Frage an Tobias, mit Empfehlung:** Steht iCloud Drive auf dem Mac auf „Mac-Speicher optimieren"? Empfehlung: nachsehen und ausschalten, bevor irgendetwas umgestellt wird — davon hängt ab, ob Marlene Dateien oder Platzhalter sieht.

## Messung

| Was | Wert | Herkunft |
|---|---|---|
| Eingänge heute | zwei Ordner, zwei Scanner | bekannte Lage |
| NAS-Ordner, Marlenes Zugriff | nur lesend | Entscheidung 07.09.2026 |
| Marlenes Leseort | lokal auf dem Mac, braucht jede Datei vollständig | bekannte Lage |
| iCloud als Eingang | im Ablagekonzept 07.09.2026 vorgesehen, Entscheidung offen | bekannte Lage |
| Scans pro Woche | **nicht gemessen** | `ls -1 <eingangsordner> \| wc -l` über vier Wochen |
| Dateigrößen typisch | **nicht gemessen** | `du -sh <eingangsordner>` |
| iCloud-Einstellung „Speicher optimieren" | **nicht gemessen** | `defaults read com.apple.bird` bzw. Systemeinstellungen → Apple-ID → iCloud Drive |
| Anschaffungs- oder Restwert Mac-Scanner | **nicht gemessen** | keine Quelle im Zugriff |

Alle Kosten- und Stundenangaben unten sind **geschätzt**.

## Vorschlag A

**Ort:** Das iPhone scannt, die Dateien landen in iCloud im Ordner „Eingang". Marlene liest aber nicht aus iCloud, sondern aus einem lokalen Ordner „Posteingang" auf dem Mac. Dazwischen liegt ein kleiner Übernahmeschritt auf dem Mac (Skript oder Ordneraktion, minütlich), der eine Datei erst dann lokal verschiebt, wenn sie vollständig heruntergeladen ist und ihre Größe zwei Durchläufe lang unverändert bleibt; danach wandert sie in iCloud nach „Übernommen".

**Ablauf:** Scannen am iPhone → iCloud/Eingang → Übernahmeschritt → lokaler Posteingang → Marlene sieht ausschließlich fertige Dateien. Der Mac-Scanner bleibt zunächst stehen und liefert in denselben lokalen Posteingang; abgeschafft wird er erst, wenn vier Wochen lang kein Scan verloren ging oder abgeschnitten ankam.

**Kosten:** keine laufenden, 0 Euro einmalig (geschätzt).

**Aufwand:** einmalig 2–3 Stunden für Übernahmeschritt, Protokoll und Ordner; laufend nichts außer dem Scannen (geschätzt).

**Risiko:** Der Übernahmeschritt ist zusätzliche Technik, die ausfallen kann; fällt er aus, stapeln sich Dateien sichtbar in iCloud/Eingang statt still verloren zu gehen. Zwei Eingänge bestehen vier Wochen länger fort.

## Vorschlag B

**Ort:** Alle Scans entstehen am iPhone und landen unmittelbar im iCloud-Ordner „Eingang". Marlene holt sie sich von dort. Der Scanner am Mac wird abgeschafft.

**Ablauf:** Scannen am iPhone → iCloud/Eingang → Marlene greift beim nächsten Lauf darauf zu und legt ab. Der bisherige NAS-Ordner und der Mac-Scanner entfallen; es gibt nur noch einen Eingang.

**Kosten:** keine laufenden (geschätzt); der Mac-Scanner entfällt, ein möglicher Verkaufserlös ist nicht gemessen.

**Aufwand:** einmalig etwa 1 Stunde (Ordner anlegen, Marlene auf den Pfad umstellen, alten Ordner stilllegen); laufend nichts außer dem Scannen (geschätzt).

**Risiko:** iCloud legt auf dem Mac je nach Einstellung Platzhalter statt vollständiger Dateien ab, und eine Datei kann während des Hochladens schon sichtbar sein; Marlene könnte eine unvollständige oder gar keine Datei lesen. Nach der Abschaffung des Mac-Scanners gibt es keinen zweiten Weg mehr.

## Die zehn Punkte

**Bewertet von einer fremden Instanz, blind** (eigener Lauf, kannte nur Frage, Messung, A und B und die zehn Punkte; Herkunft und Reihenfolge waren ihr nicht bekannt).

| # | Punkt | A | Grund A | B | Grund B |
|---|---|---|---|---|---|
| 1 | Ziel | 5 | erreicht Zuverlässigkeit und Vollständigkeit durch Prüfung vor Übergabe | 2 | erreicht „ein Eingang", aber nicht die geforderte Vollständigkeit |
| 2 | Zeit bis Nutzen | 4 | Nutzen ab erstem Scan, aber erst nach 2–3 h Einrichtung | 5 | Nutzen ab erstem Scan, Einrichtung in 1 h |
| 3 | Aufwand | 3 | mehr Einrichtung, danach nichts laufend | 5 | minimaler Aufwand, kein laufender Zusatz |
| 4 | Kosten | 5 | keine laufenden Kosten, 0 Euro einmalig | 4 | keine laufenden Kosten, Verkaufserlös unbeziffert verschenkt |
| 5 | Risiko | 4 | Ausfall ist sichtbar (Stapel in iCloud), kein stiller Verlust | 1 | das gemessene Risiko bleibt ungeprüft, Rückweg bereits abgeschafft |
| 6 | Rücknehmbarkeit | 4 | Mac-Scanner bleibt vier Wochen als Rückfall | 1 | Abschaffung in derselben Stunde ist eine Einbahnstraße |
| 7 | Passung | 5 | testet die offene Entscheidung, statt sie vorwegzunehmen | 2 | nimmt die offene iCloud-Entscheidung vorweg und schafft sofort Fakten |
| 8 | Messbarkeit | 5 | klares Kriterium: vier Wochen ohne Verlust oder Abschnitt | 2 | kein Kriterium genannt |
| 9 | Abhängigkeiten | 4 | braucht Übernahmeskript und dessen Pflege | 5 | braucht nur Ordner und Pfadumstellung |
| 10 | Nebenwirkungen | 4 | vorübergehend zwei Eingänge, kontrolliert befristet | 2 | Scannerabschaffung ist eine ungefragte Zusatzentscheidung |
| | **Summe** | **43** | | **29** | |

Urteil der Instanz: A ist klar stärker, weil er die eigentliche Frage — zuverlässig und **vollständig** — durch eine echte Prüfung beantwortet und den riskantesten Schritt erst nach einer gemessenen Frist macht. Die Summe täuscht bei 3 und 9, wo B vorn liegt: B zahlt kurzfristig weniger und kauft sich das mit genau dem Risiko, das die Messung schon als offene Frage benennt.

## Fazit

**Auflösung:** **B war Tobias' Idee, A der Gegenvorschlag.**

**Wer gewinnt:** Der Gegenvorschlag gewinnt, 43 zu 29, und der Abstand kommt aus vier Punkten: Vollständigkeit, Risiko, Rücknehmbarkeit, Messbarkeit. Er gewinnt aber nicht gegen die Idee, sondern gegen ihr Tempo — beide wollen dasselbe Ziel, iPhone scannt, iCloud ist der eine Eingang. Die Summe stimmt hier, weil die vier Punkte, in denen A führt, genau die sind, die die Frage stellt („zuverlässig, vollständig"), während B in Aufwand und Abhängigkeiten führt, also in Punkten, die nur den Weg dorthin betreffen.

**Was aus B in den Gewinner gehört:** Die Klarheit. B hat recht damit, dass das Ziel **ein** Eingang ist und nicht dauerhaft zwei; A darf die Übergangsfrist nicht zur Dauerlösung werden lassen, deshalb bekommt sie ein Enddatum, den 06.10.2026. Und B hat recht damit, dass der Mac-Scanner weg soll — das bleibt der Plan, nur mit einem Datum statt sofort. Der Verkauf des Scanners ist dabei eine eigene, kleine Frage, die niemand gestellt hat.

**Die eine Sache, die am ehesten noch falsch ist:** Dass das Problem überhaupt bei der Vollständigkeit liegt. Wenn iCloud Drive auf dem Mac ohnehin auf „alle Dateien behalten" steht und die Scans klein sind, ist der Übernahmeschritt in A überflüssige Technik und B war von Anfang an richtig. Das ist ungemessen und in fünf Minuten zu klären — vor jeder Entscheidung nachsehen.
