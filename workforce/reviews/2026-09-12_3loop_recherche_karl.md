# 3-Loop: Woher die Ideen kommen und wer sie recherchiert

Karl, 2026-09-12, auf `/3loop` des CEO. Sichten simuliert und so gekennzeichnet; Gerd und
Thorsten können sie im Review kippen.

## 1. Die Frage in einem Satz

Wie entstehen und reifen Kandidaten täglich ohne den CEO, wenn er selbst wenige Ideen
beisteuert, Recherche Quellen braucht und das Tagesbudget 2,0 USD beträgt; entscheidet der CEO
bis Donnerstag, 2026-09-17.

**Randbedingungen, schon entschieden:** `DEC-046` (Erzeugen offen, Marv benotet blind, Karl
gibt Filteränderungen frei, Probe ist der Maßstab). `DEC-042` (2,0 USD und 100 Aufrufe je Tag).
Invariante 10: Der Agent bleibt werkzeuglos, der Provider nimmt Text und gibt Text. Invariante
8: Alles nach draußen läuft durch die Datengrenze. Phase 5 (Werkzeuge hinter Freigabe) ist
nicht begonnen und braucht eine eigene Invariantenzeile.

## 2. Gemessen, nicht gemeint

| Was | Wert | Befehl oder Quelle |
|---|---|---|
| Kandidaten aus dem Chat des CEO | 11 Nennungen | `grep -c "Chat CEO" skills/gedaechtnis/thorsten.md` |
| Kandidaten aus Thorstens eigenen Läufen | 24 Nennungen | `grep -c "eigener Lauf"` |
| Kosten je Antwort, gemessen | 0,047385 USD (Opus, 4807/934 Token) | `evidence/2026-09-10_deploy_phase3_und_rechte.md` |
| Tagesdecke | 2,00 USD, 100 Aufrufe | `config.nas.json` |
| Zeitplan im Kern | vorhanden, zwei Einträge, Montag und Donnerstag | `config.nas.json`, Phase 3 |
| Netzzugriff im Kern | einer: der Provider selbst (`urlopen` zu Anthropic/Ollama). Keine Suche, kein Abruf | `grep -c urlopen workforce/` |
| Ollama | nicht erreichbar; Mac mini M1 vorhanden, Zustand nicht gemessen | `curl 127.0.0.1:11434` |
| Lokales Modell in der Allowlist | keins | `models.py` |

**Nicht gemessen:** Qualität eines lokalen Modells für Marktfragen; wie viele Ideen der CEO je
Woche wirklich hat; ob eine tägliche Nachricht gelesen wird.

## 3. Drei Sichten, jetzt festgelegt

**Tobias, Alltag:** Muss ich täglich etwas tun? Lese ich das? Merke ich nach zwei Wochen einen
Unterschied? Kostet es mehr als es bringt?

**Gerd, Nachweis (simuliert):** Bleibt der Agent werkzeuglos? Kommt jede Quelle als Daten
durch die Grenze oder holt das Modell sie selbst? Ist das Tagesbudget hart? Was passiert, wenn
eine Quelle lügt oder eine Anweisung enthält?

**Thorsten, Fach (simuliert):** Bekomme ich Material mit Quelle und Datum oder Behauptungen?
Kann ich eine Note belegen? Wird der Bestand tiefer oder nur länger? Erkenne ich, wenn ich
mich im Kreis drehe?

## 4. Der Vorschlag (A): täglicher Filterlauf, Modell später

Wörtlich vom CEO: „Thorsten macht unabhängig von mir jeden Tag einen Filterlauf. Am Modell
können wir später feilen. So viele Ideen kommen bei mir nicht zusammen."

In Sätzen: Ein Zeitplaneintrag ruft Thorsten täglich. Er nimmt den Bestand, arbeitet einen
Kandidaten weiter, ohne dass der CEO etwas liefern muss. Welches Modell und woher die Quellen
kommen, wird später entschieden.

**Annahmen, die A nicht sagt:** Ein täglicher Lauf hat täglich etwas zu tun. Ein Lauf ohne
neue Quelle bringt neue Erkenntnis. Der Bestand wird tiefer und nicht nur länger — genau die
Ratsche, die Anastasia gefunden hat, lief bisher ohne Zeitplan.

## 5. Drei Gegenvorschläge

**B, das Gegenteil an der teuersten Stelle: nicht täglich, sondern je Kandidat einmal tief.**
Die teuerste Stelle ist die Wiederholung ohne neues Material. Also kein Tagestakt, sondern ein
Ereignistakt: Ein Kandidat bekommt genau einen Recherchelauf, der so lang ist wie nötig, und
danach passiert mit ihm nichts mehr, bis eine Quelle oder eine Probe neu ist. Zwei Kandidaten
gleichzeitig, höchstens.

**C, dasselbe Ziel mit dem, was da ist: der Abrufer liefert, das Modell liest.** Ein getrenntes
Programm holt Quellen (Suche, Seiten, Register), speichert sie als Datei, und Thorsten bekommt
sie als Text durch die Datengrenze. Der Agent bleibt werkzeuglos, die Quelle ist zitierbar und
liegt im Repo. Das ist Phase 5 in ihrer kleinsten, lesenden Form.

**D, die einfachste Form: der Bestand wird gepflegt, nicht erweitert.** Kein neuer Kandidat,
keine neue Quelle. Thorsten geht täglich eine Zeile durch und beantwortet eine einzige Frage:
Was müsste wahr sein, damit das trägt, und wie fände man es heraus? Ergebnis ist eine
Fragenliste, die der CEO oder ein Abrufer später beantwortet.

| | A täglich | B je Kandidat tief | C Abrufer liefert | D Bestand pflegen |
|---|---|---|---|---|
| Ort | Bot, Zeitplan | Bot, auf Anstoß | Abrufer plus Bot | Bot, Zeitplan |
| Ablauf | ein Lauf je Tag über den Bestand | ein langer Lauf je Kandidat | Quellen holen, dann lesen und benoten | eine Zeile je Tag, nur Fragen |
| Kosten | rund 0,05 USD je Lauf, 1,50 im Monat | wie A, seltener | wie A plus Abrufer, Suche ggf. kostenpflichtig | wie A |
| Aufwand bis es läuft | eine Zeile in der Konfiguration | eine Zeile plus Auslöser | Abrufer bauen, Invariantenzeile, Gerds Review, ein bis zwei Wochen | eine Zeile |
| Risiko | Ratsche: der Bestand wächst ohne Tiefe | Anstoß fehlt, nichts passiert | neue Angriffsfläche; eine Seite kann Anweisungen enthalten | bleibt folgenlos ohne Antworten |

## 6. Die Matrix

| Sicht und Frage | A | B | C | D |
|---|---|---|---|---|
| Tobias: täglich etwas tun | 5, nichts | 3, er stößt an | 5, nichts | 5, nichts |
| Tobias: lese ich das | 3, täglich ermüdet | 4, selten und dann gehaltvoll | 4 | 2, Fragen ohne Antworten liest niemand zweimal |
| Tobias: Unterschied nach zwei Wochen | 3, mehr Zeilen, nicht mehr Wissen | 4, zwei Kandidaten wirklich geklärt | 5, belegte Noten | 2 |
| Tobias: Kosten gegen Nutzen | 4, 1,50 USD im Monat | 5, weniger Läufe | 3, Abrufer kostet Bauzeit | 4 |
| Gerd: Agent bleibt werkzeuglos | 5, unverändert | 5 | 4, nur wenn der Abrufer getrennt bleibt und sein Ergebnis Daten sind | 5 |
| Gerd: Quelle durch die Grenze | 1, es gibt keine Quelle, das Modell erfindet aus dem Gedächtnis | 2, dasselbe, nur seltener | 5, Quelle ist eine Datei mit Datum | 5, es wird nichts behauptet |
| Gerd: Budget hart | 5, Decke greift | 5 | 4, Suchdienst kann eigene Kosten haben | 5 |
| Gerd: Quelle lügt oder weist an | 3, keine Quelle, dafür Erfindung | 3 | 3, Injektion möglich, Grenze und Werkzeuglosigkeit halten dagegen | 5, nichts kommt herein |
| Thorsten: Material mit Quelle | 1, keins | 2 | 5 | 3, er sagt wenigstens, welche fehlt |
| Thorsten: Note belegbar | 1 | 2 | 5 | 3 |
| Thorsten: Bestand tiefer statt länger | 2, Tagestakt drängt zu Neuem | 5, ein Kandidat bis zum Ende | 4 | 4 |
| Thorsten: Kreis erkennbar | 3 | 4 | 4 | 5, Fragen wiederholen sich sichtbar |
| **Summe** | **36** | **44** | **51** | **48** |

## 7. Fazit

**Empfehlung: C als Ziel, D als Sofortmaßnahme, B als Takt. A nicht in Reinform.**

Der tägliche Lauf ist richtig gedacht und an einer Stelle falsch: Ohne neue Quelle wiederholt
sich ein Modell. Zwölf von zwölf Noten im Bestand stammen heute aus dem Gedächtnis des Modells,
keine aus einer Quelle mit Datum — genau deshalb hat Anastasia die Ratsche gefunden. Ein
Tagestakt ohne Quelle beschleunigt sie.

1. **Sofort, kostet nichts: der tägliche Lauf im Modus D.** Ein Zeitplaneintrag, Montag bis
   Freitag, Thorsten nimmt eine Zeile des Bestands und liefert genau eine Sache: die Frage,
   deren Antwort den Kandidaten kippen oder tragen würde, und wo sie steht. Keine Note, kein
   neuer Kandidat. Kosten rund 1,50 USD im Monat. Das füllt die Fragenliste, die C später
   abarbeitet.
2. **Als Takt: B.** Wenn eine Quelle da ist, bekommt der Kandidat einen langen Lauf, und dann
   ruht er. Höchstens zwei gleichzeitig.
3. **Als Ziel: C, der Abrufer.** Getrenntes Programm holt Quellen, legt sie als Datei ab,
   Thorsten liest sie als Daten. Das braucht eine neue Zeile in `INVARIANTEN.md`, Gerds Review
   vorher, und ist der erste Schritt in Phase 5. Ein bis zwei Wochen.

**Zur Frage „Ollama ans Netz":** Nicht das Modell bekommt Netz, sondern der Abrufer. Ein Modell
mit eigenem Netzzugriff wäre ein Werkzeug und kippt Invariante 10; ein Abrufer, dessen Ergebnis
als Daten durch die Grenze geht, kippt sie nicht. Damit ist Ollama für Recherche erst dann
interessant, wenn C steht — dann aber richtig: lange Läufe über viel Text kosten lokal nichts.
Vorher lohnt der Aufbau nicht.

**Der Test, der die Entscheidung hält:** Ein Wächter verlangt, dass jede Note im Bestand eine
Quelle mit Datum trägt oder als `UNKNOWN` gekennzeichnet ist; ohne Quelle keine Note. Er wird
rot, sobald wieder aus dem Gedächtnis benotet wird.

**Offene Fragen, nur der CEO:**

- **Der tägliche Lauf: an wen?** Empfehlung: an dich als Nachricht, aber nur freitags
  gesammelt; täglich im Gedächtnis, nicht täglich im Telefon. Optionen: (a) täglich schreiben,
  freitags melden; (b) täglich melden; (c) nur ins Gedächtnis, du liest bei Bedarf.
- **Der Abrufer, Phase 5:** Empfehlung: ja, als nächster Meilenstein nach den offenen Befunden,
  lesend, mit eigener Invariantenzeile. Optionen: (a) bauen; (b) warten bis der Bestand mehr
  Fragen hat; (c) nicht bauen, Quellen bringst du selbst.
- **Ideenmenge:** Dein Satz „so viele Ideen kommen bei mir nicht zusammen" ist kein Mangel.
  Gemessen: 11 von dir, 24 von Thorsten. Empfehlung: Der Montagstermin fragt dich nach genau
  einer Beobachtung aus der Woche, keine Idee, nur etwas, das dir aufgefallen ist; daraus macht
  Thorsten Kandidaten. Optionen: (a) so; (b) gar nichts von dir erwarten; (c) drei je Woche
  wie im Battle vorgesehen.

**Die eine Sache, die am ehesten noch falsch ist:** dass ein Abrufer die Notenqualität hebt.
Vielleicht ist das Problem nicht die fehlende Quelle, sondern dass niemand kauft — und das
beantwortet nur die Probe, nicht die Recherche. C verschiebt die Probe nach hinten; das ist
richtig, solange es Wochen sind und nicht Monate.

Nächster Schritt: Der CEO beantwortet die drei Fragen bis Donnerstag, 2026-09-17; Owner Tobias.
