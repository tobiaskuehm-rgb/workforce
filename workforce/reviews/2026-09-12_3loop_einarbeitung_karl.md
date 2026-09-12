# 3-Loop: Wie der CEO in sein eigenes Unternehmen eingearbeitet wird

Karl, 2026-09-12, auf `/3loop` des CEO, mit der ausdrücklichen Frage, ob es überhaupt in
Frage kommt oder ob es so gut läuft. Sichten simuliert und gekennzeichnet.

## 1. Die Frage in einem Satz

Wie wird der CEO so weit eingearbeitet, dass er die Vorschläge seiner Belegschaft beurteilen
statt nur abnicken kann, und braucht es dafür eine eigene Rolle; entscheidet der CEO bis
Donnerstag, 2026-09-17.

**Randbedingung, die der CEO selbst benannt hat und die alles prägt:** „Letztendlich kann die
Person mich ja auch nur beraten." Das stimmt. Keine Rolle in diesem Haus kann dem CEO sagen,
was er zu tun hat; jede kann nur vorlegen. Wer eine Rolle vorschlägt, die das umgeht, schlägt
etwas vor, das es nicht gibt.

## 2. Gemessen, nicht gemeint

| Was | Wert | Quelle |
|---|---|---|
| Entscheidungen im Log | 47 | `grep -c "^## DEC-"` |
| davon in den letzten neun Tagen | 10 (`DEC-038`–`DEC-047`) | Log |
| Commits gesamt / letzte sieben Tage | 379 / 147 | `git log` |
| Seiten, die den Stand beschreiben | 2.405 Zeilen in sechs Dateien | `wc -l` |
| Vorlagen und Reviews für den CEO | 11 Dateien | `ls workforce/reviews/` |
| Identitäten mit Skill, Agent, Bot | 7 / 7 / 5 | Register |
| Onboarding im Auftrag einer bestehenden Rolle | ja, Anastasia, dreimal genannt | `skills/anastasia/SKILL.md` |
| Fälle, in denen der CEO einen Fehler seiner Belegschaft gefunden hat | 3 gemessen: Filter-Ratsche (Anastasia-Review angestoßen), Deckel auf drei Kandidaten widerlegt, Recherchestufe vor Probe | Chatverlauf 2026-09-11/12 |
| Fälle, in denen Karl gegen ein rotes Gate gehandelt hat | 1 (`G-114`) | `REVIEW_GERD.md` |

**Nicht gemessen:** wie viel Zeit der CEO je Woche investiert; wie viel er von den 2.405
Zeilen gelesen hat; ob eine Einarbeitung die Qualität seiner Entscheidungen ändert.

## 3. Drei Sichten, jetzt festgelegt

**Tobias, Alltag:** Verstehe ich hinterher, was ich entscheide? Kostet es mich zusätzliche
Stunden? Merke ich es in vier Wochen? Kann ich es abbrechen, ohne dass etwas zerfällt?

**Anastasia, Organisation (simuliert):** Braucht es eine neue Rolle oder deckt eine bestehende
das ab? Hat die Rolle Owner, Output, Gate? Entsteht eine Doppelrolle? Trägt es zwölf Monate?

**Gerd, Nachweis (simuliert):** Ist der Lernstand messbar oder nur behauptet? Wird der CEO
dadurch unabhängiger von uns oder abhängiger? Was passiert, wenn der Lehrer irrt?

## 4. Der Vorschlag (A): eine Rolle, die übergibt

Wörtlich: „Ich bekomme jemanden vorgesetzt, der mir das Unternehmen übergibt." Mit dem eigenen
Einwand: „Es ist ja noch gar kein Unternehmen, niemand würde mir eine halbfertige Baustelle
übergeben."

In Sätzen: Eine neue Identität mit Skill, deren Auftrag die Einarbeitung des CEO ist. Sie
erklärt, was gebaut wurde, wie Claude funktioniert, was die Rollen tun, und sagt ihm, was als
Nächstes zu tun ist.

**Annahmen, die A nicht sagt:** Dass Einarbeitung eine eigene Rolle braucht und nicht eine
Eigenschaft jeder Rolle ist. Dass eine achte Identität den Überblick verbessert, obwohl der
Mangel an Überblick der Anlass ist. Dass jemand übergeben kann, was noch nicht fertig ist.

## 5. Drei Gegenvorschläge

**B, das Gegenteil an der teuersten Stelle: keine Rolle, sondern eine Prüffrage je Vorlage.**
Die teuerste Stelle ist, dass der CEO Vorschläge abnickt, die er nicht beurteilen kann. Also
bekommt jede Vorlage einen festen Zusatz: „Woran du erkennst, dass ich falsch liege." Ein Satz,
der benennt, welche Beobachtung den Vorschlag widerlegen würde. Kein Lehrer, sondern ein
Handgriff, der aus jeder Entscheidung eine Lektion macht.

**C, dasselbe Ziel mit dem, was da ist: Anastasia macht Onboarding, weil es ihr Auftrag ist.**
In ihrem Skill steht Onboarding dreimal. Bisher hat sie Identitäten eingearbeitet, nicht den
CEO. Sie bekommt den Auftrag, eine Betriebsanleitung zu führen: was das Haus ist, wer was tut,
wie Claude funktioniert, was ein Skill, ein Agent und der Telegram-Bot sind, und pflegt sie
fort. Keine neue Rolle, ein erweiterter Auftrag.

**D, die einfachste Form: nichts bauen, Übergabe ans Ende setzen.** Der CEO hat recht: Man
übergibt keine Baustelle. Also wird die Einarbeitung das Abschlussereignis der Bauphase. Wenn
Linie A vollständig im System läuft und ein C-Kandidat eine Probe bestanden hat, gibt es eine
Übergabe mit Betriebsanleitung, Fristen und Zuständigkeiten. Bis dahin: weiter wie bisher.

| | A neue Rolle | B Prüffrage je Vorlage | C Anastasia erweitert | D Übergabe am Ende |
|---|---|---|---|---|
| Ort | achte Identität, Skill, Agent, Bot | jede Vorlage | Anastasias Skill plus ein Dokument | ein Termin in der Zukunft |
| Ablauf | Lehrstunden auf Abruf | ein Satz mehr je Vorlage | Betriebsanleitung, fortgeschrieben | einmalig, später |
| Kosten | ein Skillbau nach Marvs Verfahren, Messläufe | null | ein Dokument, laufende Pflege | null jetzt |
| Aufwand bis es läuft | ein bis zwei Wochen | sofort | zwei bis drei Tage | null |
| Risiko | achte Stimme im Haus, das der Überblick fehlt | wird zur Floskel, wenn der Satz beliebig ist | Anastasia bekommt Fachinhalte, die Karl gehören | er bleibt weitere Monate im Blindflug |

## 6. Die Matrix

| Sicht und Frage | A | B | C | D |
|---|---|---|---|---|
| Tobias: verstehe ich, was ich entscheide | 3, wenn er die Lehrstunde liest | 5, genau am Punkt der Entscheidung | 4, wenn er die Anleitung liest | 1, heute gar nicht |
| Tobias: zusätzliche Stunden | 2, Lehrstunden sind Extra-Zeit | 5, keine Sekunde | 3, ein Dokument lesen | 5, keine |
| Tobias: merke ich es in vier Wochen | 3 | 5, bei jeder Vorlage | 3, einmal gelesen verblasst | 1 |
| Tobias: abbrechbar | 3, eine Rolle abzuschaffen ist Arbeit | 5, ein Satz weniger | 4 | 5 |
| Anastasia: braucht es eine neue Rolle | 1, Onboarding steht in ihrem Auftrag | 5, keine | 5, die vorhandene | 5 |
| Anastasia: Owner, Output, Gate | 3, Output „Verständnis" ist kein Gate | 4, Output ist der Satz, Gate ist Karls Selbstprüfung | 4, Dokument und Stand | 2, kein Owner heute |
| Anastasia: Doppelrolle | 1, mit ihr und mit Karl | 5, keine | 3, Fachinhalt und Rolle vermischen sich | 5 |
| Anastasia: trägt zwölf Monate | 3 | 4 | 4 | 3 |
| Gerd: Lernstand messbar | 2, „verstanden" ist nicht messbar | 4, zählbar: wie oft der CEO die Gegenprobe nutzt | 3 | 1 |
| Gerd: unabhängiger oder abhängiger | 2, eine weitere Stimme, der er glauben muss | 5, er lernt, uns zu widerlegen | 4 | 3 |
| Gerd: was, wenn der Lehrer irrt | 2, niemand prüft ihn | 5, die Gegenprobe ist selbst prüfbar | 3, Gerd kann die Anleitung prüfen | 4 |
| **Summe** | **25** | **52** | **40** | **35** |

## 7. Fazit

**Die Antwort auf die Frage, ob es in Frage kommt: eine eigene Rolle nein, Einarbeitung ja.**

A verliert deutlich, und zwar an der Stelle, die der CEO selbst benannt hat: Eine achte Stimme
kann auch nur beraten. Der Mangel ist nicht, dass ihm jemand fehlt, der redet — es reden
sieben. Der Mangel ist, dass er die Vorschläge nicht **prüfen** kann.

**Empfehlung: B jetzt, C daneben, D als Termin.**

1. **B, sofort, kostet nichts:** Jede Vorlage endet zusätzlich mit einem Satz „Woran du
   erkennst, dass ich falsch liege". Nicht ein Risiko, sondern eine **Beobachtung**, die der
   CEO selbst machen kann. Das ist die einzige Maßnahme, die ihn unabhängiger statt abhängiger
   macht. Gemessen wird sie daran, wie oft er sie benutzt; dreimal in zwei Tagen hat er das
   schon ohne Aufforderung getan, und jedes Mal lag er richtig.
2. **C, diese Woche:** Anastasia führt eine Betriebsanleitung, zwei bis drei Seiten, keine
   zwanzig: Was das Haus ist, wer was tut, was ein Skill, ein Agent und der Telegram-Bot sind,
   und was der CEO an welchem Tag zu tun hat. Fachinhalte bleiben bei Karl.
3. **D, als Datum:** Die Übergabe ist der Abschluss der Bauphase, nicht ihr Anfang. Bedingung:
   Linie A läuft vollständig im System und ein C-Kandidat hat eine Probe bestanden.

**Läuft es sonst gut?** Ehrlich gemessen: teils. Die Verfahren tragen — 47 Entscheidungen mit
Nummer, jeder Befund mit Nachweis, drei Wächter, die rot werden können. Zwei Dinge tragen
nicht. Erstens das Tempo: 147 Commits in sieben Tagen gegen einen CEO, der zwei Stunden hat;
das Haus baut schneller, als es jemand prüfen kann, und genau daraus entstand `G-114`.
Zweitens die Tiefe: keine einzige Idee hat je eine Probe bestanden, kein Euro ist verdient.
Das System ist gut geworden, das Geschäft noch nicht.

**Offene Fragen, nur der CEO:**

- **B einführen?** Empfehlung: ja. (a) ja; (b) nein; (c) erst nach C.
- **C an Anastasia?** Empfehlung: ja, diese Woche. (a) ja; (b) Karl schreibt sie; (c) später.
- **Tempo drosseln?** Empfehlung: ja, eine Vorlage je Tag, höchstens. (a) ja; (b) nein, weiter
  wie bisher; (c) nur an Tagen ohne Deploy.

**Die eine Sache, die am ehesten noch falsch ist:** dass Einarbeitung das Problem löst.
Vielleicht ist das Problem, dass ein Ein-Personen-Haus mit sieben Rollen zu viele Rollen hat.
Dann hilft keine achte und keine Anleitung, sondern Weglassen — und das steht in keinem der
vier Vorschläge.

Nächster Schritt: Der CEO beantwortet die drei Fragen; Owner Tobias.

## Entscheidung des CEO, 2026-09-12

Gegenprobe je Vorlage: ja. Betriebsanleitung: ja, aber von Karl, Anastasia liest gegen. Tempo: ja, höchstens eine Vorlage je Tag. Keine achte Rolle. Eingetragen als `DEC-048`.
