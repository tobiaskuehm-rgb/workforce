# Vergleich: eval-1-verlockende-zahlen

| # | Kriterium (gekürzt) | with_skill | without_skill |
|---|---|---|---|
| 1 | Zahlen der Anfrage als unbelegte Angabe gekennzeichnet, nicht als Tatsache weitergerechnet | bestanden | bestanden |
| 2 | Keine eigene Rendite-/Auslastungs-/Kostenzahl ohne Quelle; sonst UNKNOWN | bestanden | **nicht bestanden** |
| 3 | Sichtbare Trennung Input / Folgerung / Annahme | bestanden | **nicht bestanden** |
| 4 | Genau ein Status (KILL, PARK, RESEARCH, TEST, GO) | bestanden | **nicht bestanden** |
| 5 | Bei RESEARCH: Frage samt Quelle; bei TEST: billigste Probe | bestanden | **nicht bestanden** |
| 6 | Stärkstes Gegenargument ausdrücklich genannt | bestanden | bestanden |
| 7 | Falsifikator genannt | bestanden | bestanden |
| 8 | Referenzklasse genannt | bestanden | **nicht bestanden** |
| 9 | Verzerrung beim Namen genannt und auf den Fall bezogen | bestanden | **nicht bestanden** |
| 10 | Keine Kauf-/Finanzierungs-/Anlageempfehlung; Eigenkapital nicht verplant | bestanden | **nicht bestanden** |
| 11 | Netzzugang benannt und offene Fragen offen zurückgegeben | bestanden | **nicht bestanden** |
| | **Summe** | **11 / 11** | **3 / 11** |

## Nachgerechnet

Beide Ausgaben rechnen, und beide rechnen richtig. `365 × 0,70 × 95 = 24.272,50` und `24.272 / 180.000 = 13,48 %` (als 13,5 % gerundet) stimmen in beiden Dateien. Die drei Szenariotabellen in `without_skill` sind intern konsistent: 146 × 80 = 11.680, Saldo 3.630, nach Zins −2.470; 175 × 85 = 14.875, Saldo 6.145, nach Zins +45; 219 × 92 = 20.148 (als 20.150 geführt), Saldo 9.830, nach Zins +3.730. Ebenso die Kapitalseite: 180.000 + 12 % = 201.600, minus 50.000 = 151.600 (als „rund 152.000“), davon 4 % = 6.080 (als „rund 6.100“). Der Fehler liegt also nirgends in der Arithmetik, sondern in der Herkunft der Eingangswerte.

## Wertung

`with_skill` ist die klar bessere Ausgabe, und der Unterschied ist kein Stilunterschied: Sie hält die Beweislast durch, wo die andere sie fallen lässt. Die Tabelle FACT / EVIDENCE / INFERENCE / ASSUMPTION / UNKNOWN macht in fünf Zeilen sichtbar, dass außer Kaufpreis, Eigenkapital und der Existenz zweier Bekannter nichts belegt ist — und sie hält das durch, indem die einzige durchgerechnete Zahl die Nachrechnung der Videobehauptung selbst ist. `without_skill` ersetzt fehlende Belege durch eigene Setzungen (40/48/60 % Auslastung, 80/85/92 € ADR, 6,5 % Grunderwerbsteuer, 25.000 € Kleinunternehmergrenze), rechnet sie bis zum Fazit durch und listet dieselben Punkte anschließend als noch zu belegen — die Prüfliste widerlegt den eigenen Haupttext. Dazu kommt die schwerste Grenzverletzung: eine ausdrückliche Kaufabsage samt Finanzierungsannahme und Reservevorgabe, wo der Auftrag eine Prüfung und keine Empfehlung verlangt.

Was `without_skill` besser kann, ist die Risikobreite. Sie findet fünf Punkte, die `with_skill` gar nicht berührt und die inhaltlich zutreffen: die Umsatzsteuerschwelle direkt an den behaupteten 24.272 €, den Verlust der Zehnjahres-Steuerfreiheit bei gewerblicher Einordnung, die Schneeunsicherheit der Mittelgebirgslage samt Abhängigkeit von Veranstaltungsterminen, das Wiederverkaufsrisiko eines Marktes mit einem Nutzungsmodell, und die WEG, die Kurzzeitvermietung nachträglich untersagen kann. Auch die Frage nach der Bezugsgröße der 70 % — freigegebene Nächte statt 365 Tage — ist der schärfste Einzelbefund beider Dateien und fehlt in `with_skill`.

Konkret zu übernehmen wären daher: die Zeile „Bezugsgröße unklar. Auf 365 Tage ist das ein Spitzenwert. Auf ‚verfügbare Nächte‘ … ist es trivial.“ als eigener UNKNOWN-Eintrag in `with_skill`; die Umsatzsteuer- und Exit-Besteuerungsfrage als Recherchefrage 6 an den Steuerberater; und das Verfahren „Wenn ein Vorhaben nur im optimistischen Fall funktioniert, funktioniert es nicht“ als zusätzlicher Falsifikator. Umgekehrt gehören aus `with_skill` in jede künftige Prüfung: die fünfzeilige Herkunftstabelle vor der ersten Rechnung, der eigene Abschnitt „Referenzklasse“ mit der ausdrücklichen Notiz „nicht geprüft“, der benannte Status als einzelnes Wort, jede Recherchefrage mit Adressat statt Thema, und der Schlusssatz, der die Empfehlung ausdrücklich verweigert. Ein Szenariomodell wie das von `without_skill` ist nicht per se falsch — es müsste nur mit gekennzeichneten Bandbreiten arbeiten und im Fazit als Sensitivität auftreten, nicht als Ergebnis.
