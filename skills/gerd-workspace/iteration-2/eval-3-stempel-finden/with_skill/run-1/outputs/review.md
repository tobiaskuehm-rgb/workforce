# Review: drei eingereichte Tests

Laufzeit: Gerd via Claude Code. Datum: 2026-09-08. Letzte vergebene Nummer vorher: `G-092`.

Vorbemerkung zur Beweislage: Ich habe **nichts ausgeführt** — kein Test gelaufen, keine
Datenbank befragt, kein `verify`. Was hier steht, ist am Text der drei Einreichungen gemessen,
und die Frage an jeden lautet: **Gibt es einen Zustand, in dem er rot wird?** Wo die Antwort
nur unter einer Annahme über nicht vorgelegten Code („was tut `boundary_scan` bei einem
Verstoß?") gilt, sage ich das dazu, statt sie zu bestehen.

---

## `G-093` – Test A prüft nur die gute Fixture und kann eine stillgelegte Datengrenze nicht von einer wirksamen unterscheiden

Laufzeit: Gerd via Claude Code. Geprüft: eingereichter Ausschnitt
`workforce/tests/test_workforce.py::test_boundary_covers_all_outbound`. Schwere: hoch.

Beobachtung: Der Test besteht aus genau einer Zusicherung der Form
`self.assertEqual([], boundary_scan(GOOD_FIXTURE))`. Eingabe ist eine Fixture, die per Namen
als konform deklariert ist; erwartet wird die leere Liste. Ein `boundary_scan`, das
bedingungslos `[]` zurückgibt — auskommentierter Rumpf, verschluckte Exception, leergelaufene
Regelliste, falscher Pfad in der Fixture-Auflösung — besteht diesen Test unverändert. Der Test
misst damit nicht, ob die Datengrenze deckt, sondern nur, dass der Scanner auf einem konformen
Eingang nicht fälschlich anschlägt. Der Name behauptet das Gegenteil: „covers all outbound".

Warum es zählt: Die Datengrenze ist die Stelle, an der alles vorbeimuss, was einen
Modellanbieter erreicht — die Zusage, dass es keinen zweiten Weg nach draußen gibt. Ein
Wächter, der diese Zusage hält, ohne rot werden zu können, ist ein Stempel; und ein Stempel an
dieser Stelle ist teurer als kein Test, weil er die Prüfung besetzt, die den Verstoß gefunden
hätte. Das Muster ist im Projekt bereits benannt: `test_guard_counterprobes.py` verlangt
ausdrücklich, dass über jedem Scanner mindestens eine Zusicherung steht, die **nicht** die Form
`assertEqual([], scanner(...))` hat. Test A hat genau diese Form und sonst keine — er ist der
Fall, gegen den dieser Wächter gebaut wurde. Ob `test_guard_counterprobes.py` im Neubau
`workforce/` überhaupt mitläuft, habe ich nicht gemessen; fällt er dort weg, fehlt auch die
automatische Meldung.

### Kleinste sichere Korrektur

Eine zweite Zusicherung im selben Test, gegen eine Fixture mit **einem** bekannten Verstoß, und
zwar gebunden an die Kennung des Verstoßes, nicht an „Liste nicht leer":

```python
offenders = boundary_scan(GOOD_FIXTURE)
self.assertEqual([], offenders)
# Gegenprobe: ein einziger, benannter Verstoss muss genau einmal gemeldet werden.
bad = boundary_scan(FIXTURE_WITH_RAW_SUBJECT)
self.assertEqual(['raw_subject_bypasses_prepare_outbound'], bad)
```

Gegenprobe der Korrektur — welcher Zustand macht sie rot: ein `boundary_scan`, das immer `[]`
liefert (zweite Zeile schlägt fehl); eines, das immer alles meldet (erste Zeile schlägt fehl);
eines, das den Verstoß findet, aber unter falschem Bezeichner oder doppelt (Gleichheit auf die
exakte Liste schlägt fehl). Bewusst `assertEqual` auf die vollständige Liste statt
`assertIn` oder `assertTrue(bad)`: „irgendein Fund" ist im Projekt schon einmal als
bestandener Negativtest durchgegangen. Die Verstoß-Fixture muss aus dem realen Ausgangspfad
gebaut sein, nicht aus meiner Vorstellung davon.

---

## `G-094` – Test B ist selbstausschließend: der Join entfernt genau die Zeile, deren Abwesenheit er belegen soll

Laufzeit: Gerd via Claude Code. Geprüft: eingereichter SQL-Abnahmetest. Schwere: hoch.

Beobachtung: Die Abfrage joint `aclexplode(...) a` auf `pg_roles r ON r.oid = a.grantee` und
filtert danach `WHERE a.grantee = 0`. Zur OID `0` — der Pseudorolle `PUBLIC` — gibt es in
`pg_roles` keine Zeile. Der Inner Join entfernt sie also, bevor der Filter greift; die
Ergebnismenge ist **unter jeder denkbaren ACL leer**, und `count(*) = 0` ist konstant wahr.
Der Test kann nicht rot werden. Ausgerechnet die Zusicherung „die Pseudorolle PUBLIC ist
ausgeblendet" belegt damit nichts: Sie wäre genauso wahr, wenn `aclexplode` gar nichts
zurückgäbe, wenn `nspacl` `NULL` ist (dann ist die Menge ohnehin leer), oder wenn die
Ausblendung nie implementiert worden wäre.

Zweiter Punkt an derselben Zeile: Die Abfrage **liefert** `ok`, sie **erzwingt** nichts. Ein
`SELECT`, dessen Ergebnis niemand liest, ist in einem Abnahmetest kein Fehlschlagpfad — ohne
`RAISE EXCEPTION` bei falschem Wert läuft die Datei durch, egal was herauskommt. Auch das ist
ein Zustand, in dem der Test nicht rot werden kann, unabhängig vom Join.

Warum es zählt: Das ist keine neue Fehlerklasse, sondern eine Wiederholung. Der Nachcheck vom
2026-09-02 hat exakt dieses Konstrukt im `009`-Abnahmetest gefunden und daraus die Regel
gemacht, dass zwei Tatsachen zwei Abfragen brauchen: eine **ohne** den Join (die Vorgabe für
`PUBLIC` existiert überhaupt) und eine **mit** ihm (genau sie wird ausgeblendet). Der
eingereichte Test hat die beiden wieder in eine Abfrage gezogen und damit den Fehler
reproduziert. Dass eine bereits aufgeschriebene Regel ein zweites Mal verletzt wird, ist der
schwerere Teil des Befunds: Die Regel steht, aber nichts misst sie.

### Kleinste sichere Korrektur

Zwei Abfragen, jede mit eigenem Fehlschlagpfad:

```sql
-- 1) Die PUBLIC-Vorgabe existiert ueberhaupt (ohne Join).
--    Rot, wenn jemand sie global entzogen hat -> die zweite Aussage waere dann leer-wahr.
SELECT CASE WHEN count(*) = 1 THEN true
  ELSE (SELECT false FROM (SELECT 1) x WHERE (RAISE_NOTICE_PLACEHOLDER)) END
FROM aclexplode((SELECT nspacl FROM pg_namespace WHERE nspname = 'public')) a
WHERE a.grantee = 0;

-- 2) Genau diese Zeile faellt beim Join auf pg_roles heraus (mit Join).
SELECT count(*) = 0
FROM aclexplode((SELECT nspacl FROM pg_namespace WHERE nspname = 'public')) a
JOIN pg_roles r ON r.oid = a.grantee
WHERE r.rolname = 'workforce_owner';
```

In der Projektform steht das Urteil in einem `DO`-Block mit `RAISE EXCEPTION` je Bedingung
(der Platzhalter oben ist keine ausführbare Zeile, sondern markiert die Stelle) — ich schreibe
hier keinen Code in das Repo, der Test gehört Claude Code. Wesentlich sind drei Eigenschaften,
nicht meine Formulierung: **(a)** Abfrage 1 ohne Join, sonst wiederholt die Korrektur den
Fehler, den sie behebt; **(b)** Abfrage 2 bindet an einen benannten, echt existierenden
Grantee, damit sie bei einem unerwünschten Grant rot wird und nicht nur bei `PUBLIC`;
**(c)** jede Bedingung wirft, statt einen Wert zu drucken.

Gegenprobe der Korrektur: Abfrage 1 wird rot, wenn die `PUBLIC`-Vorgabe auf `public` fehlt —
dann ist Abfrage 2 leer-wahr und die Gesamtaussage wertlos, genau der Zustand, den sie melden
soll. Abfrage 2 wird rot, sobald `workforce_owner` einen direkten Grant auf `public` bekommt.

---

## Test C – kein Befund, er kann rot werden

`test_claim_release_returns_attempt` ist kein Stempel. Ich habe vier unabhängige Zustände
gefunden, die ihn rot machen, und keine Zeile ohne Fehlschlagpfad:

| Zusicherung | Wird rot, wenn |
|---|---|
| `claim(...) == 'CLAIMED'` | Claim schlägt fehl, liefert `None`/`ALREADY_CLAIMED`, oder die Lease-Parameter werden ignoriert und die Signatur bricht |
| `release_untouched('M1') is True` | Freigabe nicht implementiert, findet den Datensatz nicht, oder verweigert sie fälschlich |
| `attempts == 0` | Freigabe lässt den Versuchszähler stehen — der eigentliche Regressionsfall, der Zustand aus dem der Regel zugrunde liegenden Vorfall |
| zweiter `release_untouched` ist `False` | Freigabe ist nicht idempotent-erkennend und gibt einen nicht gehaltenen Claim erneut frei |

Die dritte Zeile ist die tragende: Sie misst genau die Eigenschaft, um die es geht — ein Claim
ohne dauerhafte Wirkung kostet keinen Versuch —, und sie ist unter einer naiven
Implementierung (Status zurücksetzen, Zähler stehen lassen) rot. Das ist der Unterschied zu A
und B.

Zwei Lücken, die den Test nicht zum Stempel machen, aber offen bleiben; ich führe sie unten als
Backlog, nicht als Befund:

- **`max_attempts=3` wird übergeben und nirgends ausgeübt.** Ein Parameter, der in keiner
  Zusicherung vorkommt, ist eine Zusage ohne Deckung — dieselbe Form wie ein Allowlist-Feld,
  das niemand liest. Kein Zustand dieses Tests unterscheidet `max_attempts=3` von `=0`.
- **Die Gegenrichtung fehlt.** Der Test belegt, dass ein *unberührter* Claim zurückgegeben
  wird. Er belegt nicht, dass ein Claim **mit** dauerhafter Wirkung *nicht* zurückgegeben wird
  — die andere Hälfte derselben Regel. Eine Implementierung, die `release_untouched` immer
  freigibt, besteht Test C vollständig und wäre der teurere Fehler: zwei Prozesse an derselben
  Nachricht, zwei Provideraufrufe.
- **Die Lease ist nicht gemessen.** `lease_seconds=60` wird gesetzt; dass ein Claim nach
  Ablauf verfällt und dass der Verfall den Versuchszähler behandelt wie vorgesehen, prüft
  dieser Test nicht.

---

## Geprüft und nicht bestätigt

- Ob `boundary_scan` tatsächlich immer `[]` liefert, habe ich **nicht gemessen** — die
  Implementierung lag nicht vor und ich habe keine Datei außer meinem Skill gelesen. `G-093`
  hängt nicht daran: Der Befund ist, dass der Test diesen Zustand nicht unterscheiden kann,
  nicht dass er vorliegt.
- Ob `test_guard_counterprobes.py` im Neubau `workforce/` mitläuft und Test A von selbst
  melden würde: nicht gemessen. Falls ja, ist zusätzlich zu klären, warum er nicht angeschlagen
  hat — dann läge ein zweiter Befund am Wächter, und der wöge schwerer als `G-093`.
- Für `G-094` habe ich das Verhalten von `aclexplode`/`pg_roles` **nicht gegen eine laufende
  Instanz gemessen**, sondern aus der bereits im Projekt belegten Beobachtung desselben
  Konstrukts abgeleitet (Nachcheck 2026-09-02). Ein Lauf, der es endgültig entscheidet, steht
  unten.
- Die Implementierung hinter Test C (`make_store`, `release_untouched`) habe ich nicht
  gesehen. Beurteilt ist der Test, nicht der Speicher. Dass Test C rot werden **kann**, folgt
  aus seiner Form; dass die Implementierung korrekt ist, folgt daraus nicht.
- Ich habe versucht, Test C ebenfalls als Stempel zu widerlegen — eine Implementierung zu
  konstruieren, die alle vier Zusicherungen bedingungslos besteht. Das ging nicht ohne einen
  Speicher, der `attempts` gar nicht führt; dann bricht die dritte Zeile am fehlenden Schlüssel.
  Der Test hat gehalten.

---

## Unabhängiger Nachweis

Keiner. Ich habe in dieser Runde nichts ausgeführt: kein Test, keine Abfrage, kein `verify`,
kein Zugriff auf die NAS. Alle drei Urteile sind am vorgelegten Text gemessen. Das ist bei
`G-093` und Test C tragfähig, weil dort die **Form** des Tests den Befund ergibt; bei `G-094`
bleibt der Rest offen, den der Lauf unten schließt.

---

## Läufe, die die offenen Punkte schließen würden

Ich führe sie nicht aus. Wer sie freigibt, steht dabei.

1. **`G-094` endgültig:** die eingereichte Abfrage gegen eine **Wegwerf-Instanz** laufen lassen,
   einmal unverändert und einmal, nachdem ein direkter Grant auf `public` gesetzt wurde. Bleibt
   `ok = true` in beiden Fällen, ist der Stempel gemessen. Nur lesend geht das nicht — der
   zweite Teil ändert Zustand, also **nicht auf der Produktion**, sondern in einem
   `--rm`-Container mit `POSTGRES_USER` wie im Ziel (eine Probe mit anderem Bootstrap-Superuser
   prüft eine Lage, die es nicht gibt). Freigabe: CEO im Chat, ausgeführt von Claude Code.
2. **`G-093` ergänzend:** `boundary_scan` gegen eine Verstoß-Fixture aufrufen und sehen, ob
   überhaupt etwas gemeldet wird. Lokal, ohne Netz, ohne Kosten, kein Zustandswechsel —
   braucht keine Freigabe, aber es ist Claude Codes Lauf, nicht meiner.
3. **Test C ergänzend:** die drei Lücken als eigene Tests, insbesondere die Gegenrichtung
   (Claim mit dauerhafter Wirkung wird **nicht** freigegeben). Lokal.

---

## Nicht blockierendes Backlog nach dem Lauf

- Test C um `max_attempts`, Gegenrichtung und Lease-Ablauf erweitern (drei eigene Tests, siehe
  oben). Keiner davon verhindert dauerhaften Schaden im nächsten Meilenstein; sie gehören in
  den übernächsten.
- Prüfen, ob der Neubau `workforce/` einen Gegenwächter im Sinne von
  `test_guard_counterprobes.py` überhaupt besitzt. Falls nicht, ist das eine eigene Aufgabe —
  die Regel „jede Kontrolle braucht einen Test, der sie absichtlich schwächt" gilt auch für die
  Wächter selbst, und ohne den Gegenwächter wird `G-093` beim nächsten Scanner wiederkommen.

---

## Gate und Auftrag an Claude Code

**Status: ROT.**

Zwei der drei eingereichten Tests können in keinem Zustand rot werden. Beide sitzen an einer
Stelle, an der das Projekt eine Sicherheitszusage macht — die Datengrenze und ein
Rechte-Abnahmetest —, und beide besetzen die Prüfung, die den Verstoß gefunden hätte. Eine
Freigabe „gegen grüne Tests" wäre hier eine Freigabe gegen zwei Stempel.

Verbindlicher nächster Schritt, in dieser Reihenfolge:

1. `G-093` und `G-094` mit der jeweils angegebenen kleinsten Korrektur schließen. Jede
   Korrektur bringt ihre eigene Gegenprobe mit — die Frage „in welchem Zustand wird der **neue**
   Test rot" wird in `REVIEW_ANTWORTEN.md` beantwortet, nicht vorausgesetzt.
2. Lauf 1 und 2 oben ausführen und das Ergebnis nennen, mit Kommando und Datum.
3. Beide Befunde hinterlassen eine Regel in `CLAUDE.md`/`AGENTS.md` — `G-094` ist die
   Wiederholung einer bereits geschriebenen Regel, also gehört dort nicht noch einmal derselbe
   Satz hin, sondern der Wächter, der sie misst.

**Was ich ausdrücklich nicht freigebe:** Test A und Test B in ihrer eingereichten Form, in
keinem Umfang. Test C gebe ich frei als Beleg dafür, dass ein unberührter Claim zurückgegeben
wird, ohne einen Versuch zu kosten, und dass die Freigabe nicht doppelt greift — **nicht** als
Beleg für Lease-Verfall, für `max_attempts` und **nicht** dafür, dass ein Claim mit dauerhafter
Wirkung gehalten wird. Nichts an dieser Freigabe betrifft einen Deploy, einen Lauf auf der NAS
oder einen Provideraufruf.

---

Befunde dieser Runde: `G-093`, `G-094`.
Neue letzte vergebene Nummer: **`G-094`**.
