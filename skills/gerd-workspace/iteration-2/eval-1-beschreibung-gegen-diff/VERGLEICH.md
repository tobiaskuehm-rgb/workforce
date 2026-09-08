# Vergleich — eval-1 beschreibung-gegen-diff

| # | Kriterium (gekürzt) | with_skill | without_skill |
|---|---|---|---|
| 1 | Commit 7f3a9c2 genannt | bestanden | bestanden |
| 2 | Hauptbefund G-093, Reihe fortlaufend | bestanden | bestanden |
| 3 | Datei/Codestelle + Invariante 2 | bestanden | bestanden |
| 4 | Prüfung nur am Rundenanfang, Schleife ungeschützt | bestanden | bestanden |
| 5 | Test prüft nur Storewert, kann nie rot werden | bestanden | bestanden |
| 6 | „verify grün" als nicht gemessen geführt | bestanden | bestanden |
| 7 | Kleinste sichere Korrektur + Test mit Wechsel in der Schleife | bestanden | bestanden |
| 8 | Sichtbare Trennung geprüft / nicht gemessen / nicht blockierend / Gate | bestanden | bestanden |
| 9 | Gate stoppt eindeutig, mit Begründung und nächstem Schritt | bestanden | bestanden |
| 10 | Kein Codeeingriff durch Gerd, Korrektur als Auftrag | bestanden | bestanden |
| 11 | Schwere je Befund, blockierend vs. nachrangig | bestanden | bestanden |
| 12 | Grünes verify als Befund am Prüfwerkzeug | bestanden | bestanden |
| | **Summe** | **12 / 12** | **12 / 12** |

Ergänzend, nicht kriteriumsrelevant: with_skill 53.013 Token in 198,7 s, without_skill 88.207 Token in 180,5 s.

## Bewertung

Beide Ausgaben erfüllen alle zwölf Kriterien; die Kriterienliste trennt hier nicht. Der Unterschied liegt in der Qualität der Beweisführung, und er geht in beide Richtungen. **without_skill** ist inhaltlich schärfer: Es entscheidet den fachlich heikelsten Punkt, den Zustand zwischen `provider.complete()` und `telegram.send()` („eine bezahlte Antwort existiert, ist aber nicht zugestellt"), verlangt die Prüfung ausdrücklich an *beiden* Ausgängen und weist unter „Unabhängiger Nachweis" eine Tabelle aus, die je Befund angibt, ob er allein aus dem Diff trägt — G-096 ausdrücklich „nein", G-097 gespalten in belegten Nachweismangel und offene Ursache. Das ist die sauberste Trennung von Beobachtung und Vermutung in beiden Texten.

**with_skill** ist dafür disziplinierter im Umfang und in der Selbstprüfung: vier statt fünf Befunde ohne inhaltliche Überlappung (without_skill führt in G-095 im Kern noch einmal die Testlücke aus G-094), zu jeder Korrektur eine Gegenprobe mit Zahlen (`provider.calls == 1`, „mit der Prüfung nur vor der Schleife wird derselbe Test rot"), diese Gegenprobenlogik auch auf `verify` selbst angewandt („einmal absichtlich die Schleifenprüfung entfernen und zeigen, dass `verify` rot meldet — sonst ist auch `verify` ein Stempel"), und ein „Geprüft und nicht bestätigt", das eigene Verdachtsmomente widerlegt statt nur Unauffälliges aufzuzählen. Nur dort steht außerdem der Vorbehalt, der die eigene Korrektur relativiert: Liest `store.channel()` aus einem Cache der Rundeneröffnung, wäre auch die Iterationsprüfung wirkungslos. Ein Fehler nur in with_skill: Der Kopf datiert auf den 2026-09-08, der Auftrag nennt den 07.09.2026.

Insgesamt ist **without_skill** die stärkere Einzelausgabe, weil sie den entscheidenden Zwischenzustand entscheidet statt offenzulassen — bei 66 % mehr Token für dasselbe Kriterienergebnis. Übernehmen sollte man wechselseitig: nach with_skill gehören der Cache-Vorbehalt zu `store.channel()`, die Gegenprobe zu jeder vorgeschlagenen Korrektur samt der Anwendung auf `verify`, und die Zusammenfassung von G-094/G-095 zu einem Befund; nach without_skill gehören die Belastbarkeitstabelle je Befund, die Prüfung an beiden Ausgängen mit ausdrücklicher Entscheidung für den teureren Abbruch, und die Auflage, dass das Gate auch bei richtigem Code auf FAIL bleibt, solange die Nachweisdatei fehlt.

## Kritik an den Kriterien

Die Liste ist zu grob, um zwei sorgfältige Reviews zu unterscheiden — zwölf von zwölf auf beiden Seiten. Kriterium 2 unterscheidet nicht zwischen vier und fünf Befunden, obwohl genau das ein Qualitätsunterschied ist. Kriterien 6 und 12 werden von demselben Absatz erfüllt; 12 ist die schärfere Fassung, 6 damit fast redundant. Kriterium 8 bündelt vier Teilaussagen. Kriterium 10 ist negativ formuliert und kaum falsifizierbar. Es fehlen Kriterien zum korrekten Reviewdatum und zum Zwischenzustand zwischen Provideraufruf und Versand — beides hätte hier trennscharf gemessen.
