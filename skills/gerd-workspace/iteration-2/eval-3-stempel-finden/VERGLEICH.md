# Vergleich — eval-3 "stempel-finden"

Bewertet wurden allein die Ausgaben unter `with_skill/run-1/outputs/review.md` und
`without_skill/run-1/outputs/review.md` gegen die zehn Kriterien aus `eval_metadata.json`.

| # | Kriterium (gekürzt) | with_skill | without_skill |
|---|---|---|---|
| 1 | Test A als Stempel, Begründung "nur Gutfall / leerer Rückgabewert" | bestanden | bestanden |
| 2 | Gegenprobe zu A: Fixture mit Verstoß, genau ein Fund erwartet | bestanden | bestanden |
| 3 | Test B als Stempel, Join entfernt grantee 0, Bedingung schließt sich selbst aus | bestanden | bestanden |
| 4 | Korrektur zu B: zwei Abfragen, eine ohne und eine mit Join | bestanden | bestanden |
| 5 | Test C nicht als Stempel; Positiv- und Negativfall benannt | bestanden | bestanden |
| 6 | Fortlaufende Nummern ab G-093, mit Laufzeit und Schwere | bestanden | **nicht bestanden** |
| 7 | Nichts ausgeführt, Urteil aus dem Lesen | bestanden | bestanden |
| 8 | Freigabe exakt (Gate ROT bzw. nur Test C, A und B ausgenommen) | bestanden | bestanden |
| 9 | Keine Zahl als Dauerwahrheit | bestanden | bestanden |
| 10 | Jede Korrektur besteht selbst die Gegenprobe | bestanden | bestanden |
| | **Summe** | **10 / 10** | **9 / 10** |

## Nachrechnung zu Kriterium 10

Beide Konfigurationen bestehen die verschärfte Prüfung. Nachgerechnet wurde, ob die
vorgeschlagene SQL-Korrektur selbst wieder eine leere Menge erzeugt:

- **Abfrage ohne Join** (with_skill: `... FROM aclexplode(...) a WHERE a.grantee = 0`;
  without_skill: `SELECT EXISTS (SELECT 1 FROM aclexplode(...) a WHERE a.grantee = 0)`):
  Ohne den Join auf `pg_roles` überlebt die Zeile mit `grantee = 0`. Die Menge ist nicht
  bauartbedingt leer, die Abfrage wird rot, wenn die PUBLIC-Vorgabe fehlt. Der Fehler ist
  nicht wiederholt.
- **Abfrage mit Join** (beide identisch im Prinzip: `JOIN pg_roles r ON r.oid = a.grantee
  WHERE r.rolname = 'workforce_owner'`): Der Filter bindet an eine in `pg_roles` real
  vorhandene Zeile, nicht an die Pseudorolle. Damit steht der Filter zwar hinter demselben
  Join, aber nicht hinter einer Bedingung, die der Join leert — genau die Unterscheidung, die
  das Kriterium verlangt. Auch hier keine Wiederholung.
- Zu Test A verlangen beide `assertEqual` auf **genau einen benannten Fund** statt
  `assertNotEqual([], …)`; ein Scanner, der immer `[]` liefert, und einer, der alles meldet,
  machen die Korrektur jeweils rot.

Ein Restmangel nur in `with_skill`: Die erste Korrekturabfrage enthält einen
`RAISE_NOTICE_PLACEHOLDER` und ist ausdrücklich als nicht ausführbar gekennzeichnet. Das
verletzt Kriterium 10 nicht — die drei geforderten Eigenschaften stehen darunter im Klartext —,
ist aber schwächer als das lauffähige SQL der anderen Konfiguration.

## Urteil

`with_skill` ist die bessere Ausgabe, und der Abstand liegt nicht in der Analyse, sondern in
der Form. Inhaltlich sind beide Reviews gleich treffsicher: dieselben zwei Stempel, dieselbe
Ursache beim Inner Join, dieselbe saubere Trennung in zwei Abfragen, dieselbe Einstufung von
Test C. Den Punkt gibt allein Kriterium 6: `with_skill` setzt über jeden Befund
"Laufzeit: Gerd via Claude Code … Schwere: hoch", `without_skill` nennt weder Laufzeit noch
eine Schwere für G-093 und G-094. Zusätzlich ist `with_skill` in der Freigabe schärfer — es
benennt ausdrücklich, wofür Test C freigegeben ist und wofür **nicht** (nicht für Lease-Verfall,
nicht für `max_attempts`), während `without_skill` ein "Gate: gelb" neben "Freigabe nicht
erteilt" stellt, ohne den Widerspruch aufzulösen.

Was aus `without_skill` in die andere Fassung gehört: die **Ergebnistabelle im Kopf** (Test →
Urteil → Befund), die den Leser in drei Zeilen orientiert; das **lauffähige SQL ohne
Platzhalter**; der dritte Gegenprobenfall zu Test A ("ein `boundary_scan`, der nichts findet,
weil er nichts liest … **lauter Fehlschlag**, nicht `PASS`"), der in `with_skill` fehlt; und die
zwei ausformulierten **Regelsätze für `CLAUDE.md`** am Schluss, die den Befund in eine dauerhafte
Regel überführen statt nur in einen Auftrag. Umgekehrt gehört aus `with_skill` nach drüben: der
Abschnitt **"Geprüft und nicht bestätigt"** samt dem Versuch, Test C selbst als Stempel zu
widerlegen ("Das ging nicht ohne einen Speicher, der `attempts` gar nicht führt"), der
**Befundkopf mit Laufzeit und Schwere**, und die **exakte Freigabeklausel** mit ihrer
Aufzählung dessen, was die Freigabe nicht abdeckt.

Eine Beobachtung zum Zuschnitt der Befunde: `without_skill` vergibt für die Lücke in Test C
eine eigene Nummer `G-095`, obwohl es den Test freigabefähig nennt; `with_skill` führt dieselben
Lücken als nicht blockierendes Backlog. Die Kriterien entscheiden das nicht — beide Wege sind
vertretbar, aber eine Befundnummer für etwas, das nicht blockiert, verwässert die Bedeutung der
Nummer.
