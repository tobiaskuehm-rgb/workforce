# Review Gerd — Freigabeprüfung dreier Tests

Datum: 2026-09-07 · Prüfer: Gerd (AI-ENG-001) · Letzte vergebene Nummer vorher: G-092
Umfang: die drei eingereichten Tests, wie sie im Auftrag zitiert sind. Nichts ausgeführt, nichts gelesen außer dem Zitat — Aussagen über den umgebenden Code sind entsprechend als Annahme gekennzeichnet.

Prüffrage, überall dieselbe (Regel 47): **Gibt es einen Zustand, in dem dieser Test rot wird?** Wenn nein, ist er ein Stempel.

Ergebnis vorweg:

| Test | Urteil | Befund |
|---|---|---|
| A — `test_boundary_covers_all_outbound` | Stempel | `G-093` |
| B — `aclexplode`-Abnahme auf `public` | Stempel, und zwar ein selbstausschließender | `G-094` |
| C — `test_claim_release_returns_attempt` | kein Stempel, eine Lücke | `G-095` (klein) |

---

## G-093 — Ein Scanner, der nur gegen die gute Vorlage läuft, misst nicht den Scanner, sondern die Vorlage

**Zustand:** Test A ruft `boundary_scan(GOOD_FIXTURE)` und verlangt eine leere Liste. Die einzige Eingabe ist die, die per Konstruktion sauber ist.

**Wird er je rot?** Ja — aber nur, wenn jemand `GOOD_FIXTURE` verschlechtert. Für die Sache, die er zu prüfen behauptet („die Datengrenze deckt jeden ausgehenden Pfad ab"), wird er **nie** rot. Ein `boundary_scan`, der stumpf `return []` schreibt, ein Scanner, dessen Glob ins Leere geht, ein Scanner, der nach `G-084` die falsche Feldmenge kennt — alle drei bestehen ihn. Das ist genau die Form `assertEqual([], scanner(...))`, die `test_guard_counterprobes.py` seit 2026-09-03 als alleinige Zusicherung über einem Scanner verbietet. Der Test verletzt also nicht bloß eine allgemeine Regel, er verletzt eine Regel, für die dieses Projekt bereits einen Wächter hat; entweder greift der Wächter im Paket `workforce/` nicht, oder er wurde nicht mitgezogen. Das gehört mitgeprüft.

Zweiter Punkt, unabhängig davon: Der Name verspricht „covers **all** outbound". Eine Vollständigkeitsaussage lässt sich an einer einzelnen Vorlage grundsätzlich nicht belegen — das ist Leitplanke 7 in Testform, ein Name behauptet eine Absicherung, die der Rumpf nicht einlösen kann (`G-047`, `G-054`).

**Gegenprobe (welcher Zustand müsste ihn rot machen):**
1. Eine Vorlage mit einem ausgehenden Aufruf, der an `prepare_outbound()` vorbeigeht → mindestens ein Fund, mit dem erwarteten Pfad und Grund, nicht nur „nicht leer".
2. Eine absichtlich geschwächte Grenze (ein Feld mehr in der Policy-Feldmenge, ein zweiter Weg nach draußen) → Fund. Das ist das Muster `test_weakened_control_is_detected`.
3. Ein `boundary_scan`, der nichts findet, weil er nichts liest (leeres Verzeichnis, unlesbare Datei) → **lauter Fehlschlag**, nicht `PASS`; dieselbe Zusage wie bei `compose_scan.py`.

**Kleinste sichere Korrektur:** Den bestehenden Test behalten und **einen** Negativtest danebenstellen, der eine `BAD_FIXTURE` mit genau einem eingebauten Verstoß prüft und **genau einen** Fund verlangt, gebunden an Pfad und Kennung — nicht `assertNotEqual([], …)`. Dazu einen dritten, sehr kurzen: leere Eingabemenge → Ausnahme statt leerer Liste. Drei kleine Tests, kein Umbau am Scanner.

**Gate:** rot. Freigabe erst, wenn die Gegenprobe existiert und `test_guard_counterprobes.py` (oder sein Gegenstück in `workforce/`) diesen Scanner nachweislich erfasst.

---

## G-094 — Der Wächter schließt sich selbst aus und kann nie anschlagen

**Zustand:** Test B fragt

```
count(*) = 0
  FROM aclexplode(nspacl) a JOIN pg_roles r ON r.oid = a.grantee
 WHERE a.grantee = 0
```

Zur OID `0` gibt es in `pg_roles` keine Zeile — das ist gerade die Eigenschaft, auf der die Pseudorolle `PUBLIC` beruht. Der Join entfernt jede Zeile mit `grantee = 0`, bevor das `WHERE` überhaupt etwas zu tun hat. `count(*)` ist damit **immer** 0 und `ok` **immer** wahr: bei korrekt ausgeblendetem `PUBLIC`, bei fehlendem Ausblenden, bei leerem `nspacl`, bei einem Schema `public`, das gar nicht existiert (dann liefert das Subquery `NULL`, `aclexplode(NULL)` null Zeilen, und der Test ist wieder grün).

Das ist wortwörtlich der Fall aus Regel 47 (Nachcheck 2026-09-02) — dieselbe Abfrage, dieselbe Stelle, dieselbe falsche Grünmeldung. Ein Befund, der schon eine Regel hat und trotzdem wieder eingereicht wird, ist der teuerste: Er sieht wie eine bestandene Kontrolle aus und steht ausgerechnet dort, wo die Rechtelage begründet wird (`G-074`, `G-071`).

Dazu ein zweiter, kleinerer Mangel in derselben Zeile: Der Kommentar sagt „die Pseudorolle PUBLIC ist ausgeblendet", die Abfrage prüft aber gar nicht, dass **etwas** ausgeblendet wurde — sie prüft eine leere Menge. Eine Zusicherung über einen Filter braucht zwei Tatsachen und deshalb zwei Abfragen.

**Gegenprobe (welcher Zustand müsste ihn rot machen):**
1. `nspacl` enthält **keinen** `PUBLIC`-Eintrag → die erste Abfrage („die Vorgabe existiert überhaupt") muss rot werden. Beim heutigen PostgreSQL 17 ist der Eintrag da; fehlt er, ist die Datenbank nicht die, gegen die die Regel geschrieben wurde, und der Test muss das sagen statt zu schweigen.
2. Der Join wird entfernt → die zweite Abfolge („genau dieser Eintrag fällt beim Join heraus") muss die Differenz zeigen. Wird sie nicht rot, blendet der Join nichts aus und die Begründung aus `G-074` trägt nicht.
3. Ein **direkter** Grant auf `workforce_owner` auf `public` → muss rot werden. Das ist die eigentliche Zusicherung von `009`, und der eingereichte Test berührt sie überhaupt nicht.

**Kleinste sichere Korrektur:** Die eine Abfrage durch zwei ersetzen, beide ohne Kunstgriff:

```sql
-- (1) die Vorgabe existiert: PUBLIC hat USAGE auf public
SELECT EXISTS (
  SELECT 1 FROM aclexplode((SELECT nspacl FROM pg_namespace WHERE nspname='public')) a
   WHERE a.grantee = 0
) AS public_default_present;

-- (2) genau dieser Eintrag faellt beim Join auf pg_roles heraus
SELECT count(*) = 0 AS public_pseudo_role_hidden
  FROM aclexplode((SELECT nspacl FROM pg_namespace WHERE nspname='public')) a
  JOIN pg_roles r ON r.oid = a.grantee
 WHERE r.rolname = 'workforce_owner';
```

(1) ohne Join, (2) mit Join und an einen **benannten** Grantee gebunden. Fehlt das Schema, ist (1) falsch und der Test rot — auch das ein Zustand, den er heute nicht kennt. Und: Der Vergleich lautet „genau diese Rechtemenge", nie „mindestens" (Regel 48); wenn der Abnahmetest von `009` das an anderer Stelle bereits leistet, gehört hier ein Verweis darauf statt einer dritten Abschrift.

**Gate:** rot. Ohne die Trennung in zwei Abfragen ist die Zeile eine Zusicherung ohne Deckung und darf nicht als Abnahme gelten.

---

## G-095 — Test C ist kein Stempel; er hat eine benannte Lücke

**Zustand:** Test C kann rot werden, und zwar an vier unabhängigen Stellen. Er ist damit ein echter Test.

- `claim()` gibt etwas anderes als `CLAIMED` zurück → rot. Deckt den Normalfall des Anspruchs.
- `release_untouched()` gibt `False` zurück, obwohl nichts Dauerhaftes entstanden ist → rot. Das ist die Zusicherung aus `G-082`.
- Der Versuchszähler steht nach der Rückgabe nicht auf `0` → rot. Das ist der teure Teil von `G-082`: Ein Claim, der nichts getan hat, darf keinen Versuch kosten. Genau dieser Zustand — Zähler auf `1` — wäre die naheliegende Fehlimplementierung, und der Test bemerkt sie.
- Ein zweites `release_untouched()` gibt `True` zurück → rot. Damit ist die Rückgabe als einmalige, atomare Handlung gebunden und nicht als idempotenter Wunsch.

Der vierte Punkt ist der, der ihn über den Stempelverdacht hebt: Er prüft nicht nur, dass die Funktion tut, was sie soll, sondern dass sie es **nicht zweimal** tut.

**Was fehlt** (deshalb ein Befund, aber ein kleiner): Der Test führt `lease_seconds=60` und `max_attempts=3` als Argumente ein und misst beide nie.

1. **Lease.** Kein Zustand im Test lässt eine Lease ablaufen. Ein `claim()`, das `lease_seconds` ignoriert und den Claim für immer hält, besteht ihn — genau der Zustand aus `G-083`, in dem ein `/task` des CEO dauerhaft als „Dublette" gilt. Die Zusicherung „innerhalb der Frist bleibt er eine Dublette, danach verfällt er" braucht beide Hälften: ein zweiter `claim()` **vor** Ablauf muss abgelehnt werden, einer **danach** durchgehen.
2. **`max_attempts`.** Der Zähler wird auf `0` geprüft, die Decke nie. Ein Speicher, der nach `3` Versuchen weiter beansprucht, besteht ihn.
3. **Nebenbei:** `release_untouched` wird nur auf dem Pfad geprüft, auf dem tatsächlich nichts entstanden ist. Der interessantere Nachweis ist der Gegenfall — nach einer dauerhaften Wirkung darf die Rückgabe **nicht** gelingen (`G-013`). Fehlt der, ist die Regel „nur wer nichts produziert hat, darf freigeben" nicht abgesichert, sondern nur ihre erste Hälfte.

**Gegenprobe:** Drei Zustände, die heute grün durchgehen und rot werden müssten — (a) `lease_seconds` wird ignoriert, (b) `max_attempts` wird ignoriert, (c) `release_untouched` gelingt nach einer verbuchten Antwort.

**Kleinste sichere Korrektur:** Drei kurze Tests neben den bestehenden, mit steuerbarer Uhr statt echtem Warten (der Speicher braucht dafür eine injizierbare Zeitquelle — falls die fehlt, ist das die einzige Codeänderung dieses Befunds, und sie ist klein). Am bestehenden Test C wird nichts geändert.

**Gate:** gelb. Test C selbst ist freigabefähig; die Lücke wird als `G-095` geführt und im selben Commit geschlossen wie die Fassung, die `lease_seconds` und `max_attempts` einführt — ein Parameter, den kein Test misst, ist ein Feld ohne Deckung (`G-057`).

---

## Zusammenfassung und Gate

**Freigabe nicht erteilt.** Zwei der drei eingereichten Tests sind Stempel, und beide gehören zu Klassen, für die dieses Projekt bereits eine Regel hat — `G-094` sogar zu genau der, die der Nachcheck vom 2026-09-02 aufgeschrieben hat. Das ist der Punkt, an dem die Regelsammlung ihren Zweck verfehlt: Sie soll dafür sorgen, dass der Review **neue** Fehler findet.

Bedingungen für die Freigabe:

1. `G-093` — Negativvorlage plus Lauter-Fehlschlag-Fall für den Scanner; Nachweis, dass der Gegenproben-Wächter diesen Scanner erfasst.
2. `G-094` — zwei getrennte Abfragen, die zweite an einen benannten Grantee gebunden; keine Bedingung, die ihre eigene Zeilenmenge leert.
3. `G-095` — Lease- und Versuchsdecke gemessen, plus der Gegenfall zu `release_untouched`.

Zwei Regeln für `CLAUDE.md` (Abschnitt „Testkonventionen"), je ein Satz, im selben Commit wie die Korrektur:

- **Ein Scanner-Test ohne Negativvorlage misst die Vorlage, nicht den Scanner** (`G-093`).
- **Eine Bedingung, deren Join ihre eigene Zeilenmenge leert, ist kein Wächter, sondern eine leere Menge — zwei Tatsachen brauchen zwei Abfragen** (`G-094`; bestätigt und verschärft die Regel vom Nachcheck 2026-09-02, die damit ihre Befundnummer bekommt).

Nächste freie Nummer nach diesem Review: `G-096`.

*Nicht geprüft, weil nicht vorgelegt: der Rumpf von `boundary_scan`, die Signatur von `make_store`/`claim`/`release_untouched`, und ob `workforce/tests/` denselben Gegenproben-Wächter hat wie `nas-startup/workforce-agent`. Alle drei Aussagen oben, die davon abhängen, sind als Annahme gekennzeichnet und gehören vor dem Schließen der Befunde am Code nachgesehen.*
