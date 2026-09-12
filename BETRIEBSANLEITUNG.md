# Betriebsanleitung für den CEO

Karl, 2026-09-12, auf Entscheidung `DEC-048`. Zwei bis drei Seiten, nicht zwanzig. Anastasia
liest gegen. Was hier steht, ist der Stand; was sich ändert, wird hier geändert.

## 1. Was das ist

Ein Ein-Personen-Unternehmen im Aufbau, dessen Belegschaft aus KI-Identitäten besteht. Du
entscheidest, sie arbeiten zu. Drei Geschäftslinien: **A** Vermietung (läuft), **B** Krypto
als Reserve (läuft), **C** der dritte Baustein aus geistiger Arbeit (wird gesucht).

Ehrlich zum Stand: Das System ist weit, das Geschäft nicht. 48 Entscheidungen, 380 Commits,
ein Bot, der auf der NAS läuft und antwortet. Null Proben am Markt, null Euro verdient.

## 2. Die sieben, und was sie tun

| Wer | Kennung | Wofür du ihn rufst |
|---|---|---|
| **Karl** | `SAO-001` | Stand, Reihenfolge, alles was keinem allein gehört. COO auf Probe. Standard: wer keinen Namen nennt, spricht mit ihm. |
| **Marlene** | `POA-001` | Private Verwaltung: Belege, Fristen, Ablage, Rockhausen, Arztrechnungen. Arbeitet direkt auf Drive und NAS. |
| **Thorsten** | `RAS-001` | Geschäftsideen prüfen, Recherche, der Filter. |
| **Anastasia** | `PEO-001` | Rollen, Register, Probezeiten. Wer was darf und wie es dokumentiert ist. |
| **Wolle** | CFO | Zahlen je Linie, Budgets, Fristen. Ruht bis Oktober. |
| **Gerd** | `AI-ENG-001` | Prüft System und Code. Hängt direkt bei dir, nicht unter Karl — wer prüft, wird nicht von dem gesteuert, den er prüft. |
| **Marv** | Skillbauer | Baut und misst die Skills der anderen. Unter Anastasia. |

Wer wem berichtet, steht in `skills/ORGANIGRAMM.md`.

## 3. Drei Orte, drei verschiedene Dinge

Das ist die Stelle, an der du mich zu Recht unterbrochen hast. Sie sind nicht dasselbe.

| | Wo | Modell | Was es weiß | Wer bezahlt |
|---|---|---|---|---|
| **Skill** | hier in Claude Code, wenn du `/marlene` tippst | das des laufenden Gesprächs | ihren Skilltext, ihr Gedächtnis liest sie selbst nach | — |
| **Agent** | ein eigener Lauf, den Karl startet | eigenes, je Identität festgelegt | dasselbe, aber in einem eigenen Fenster; seine Arbeit landet nicht in deinem Verlauf | das Abo |
| **Bot** | Telegram, auf der NAS | eigenes, je Identität | Skilltext **plus Gedächtnis**, beides beim Start geladen. Er kann nichts nachschlagen. | die Programmierschnittstelle, je Aufruf |

Zwei Sätze, die daraus folgen:

- **Der Bot kann keine Datei lesen.** Was er wissen soll, muss beim Start mitgeladen werden.
  Bis zum 12. September war das nicht so, und deshalb hatte er kein Gedächtnis — das war die
  Ursache der Antworten, die dir aufgefallen sind.
- **Ein Skill in Claude Code ist kein eigener Kopf.** Er ist dieses Gespräch mit einem anderen
  Text. Ein Agent ist ein eigener Kopf.

## 4. Dein Takt

| Wann | Was |
|---|---|
| **Montag** | Karl legt die Wochenlage vor. Nur Lage, keine Entscheidung. Er fragt dich nach **einer Beobachtung** aus der Woche, keine Idee. |
| **Donnerstag** | Entscheidungstermin. Alles, was sich angesammelt hat, kommt gebündelt, jede Vorlage mit Empfehlung und dem Satz für das Entscheidungslog. |
| **Freitag** | Thorsten meldet, was die Recherche der Woche ergeben hat. |
| **Freitag bis Sonntag** | Betrieb. Nichts wird ausgerollt, nichts wartet auf dich. |
| **jeden Tag** | Nur zwei Dinge kommen sofort: **Produktives** (etwas geht live) und **Externes** (etwas verlässt das Haus). Höchstens eine Vorlage je Tag. |

## 5. Was nur du entscheidest

Sechs Klassen. Alles andere entscheidet der Fachbereich oder Karl.

**Strategie** (Richtung, Kandidaten, Regelwerk) · **Budget** (Geld, Decken, Messungen) ·
**Personal** (wer eingestellt wird, wer was darf) · **Rechte** (wer worauf zugreift) ·
**Externes** (was nach draußen geht) · **Produktives** (was live geht).

Eine Entscheidung von dir im Chat gilt sofort, ist aber erst vollständig, wenn sie eine
Nummer im **Entscheidungslog** hat. Das ist eine Textdatei in deiner iCloud:
`Startup_Codex / START_UP_Codex_Projektquellen_2026-08-13 / 03_DECISION_LOG.txt`. Karl schreibt
die Einträge vor, du sagst „trag ein" oder machst es selbst.

## 6. Wie du prüfst, ohne Technik zu können

Du musst den Code nicht lesen. Vier Fragen reichen:

1. **Woran erkenne ich, dass du falsch liegst?** Steht seit `DEC-048` in jeder Vorlage. Fehlt
   der Satz oder ist er nichtssagend, ist es keine Vorlage, sondern eine Meinung.
2. **Ist das gemessen oder vermutet?** Jede Zahl muss einen Befehl oder eine Quelle haben.
   „Vermutlich" und „sollte" sind Warnzeichen.
3. **Was sagt Gerd?** Er ist der Einzige, dessen Aufgabe das Nein ist. Wenn eine Vorlage sagt
   „Gerd hat freigegeben", frag nach dem Datum — er hat mich schon gegen ein rotes Gate laufen
   lassen, und das war mein Fehler, nicht seiner.
4. **Wer verliert, wenn ich ja sage?** Meistens deine Zeit. Sie ist das Knappste im Haus.

## 7. Was fest steht und nicht verhandelt wird

Fünf Dinge, die gelten, auch wenn es unbequem ist. Sie stehen ausführlich in `INVARIANTEN.md`.

- **Aus bleibt aus.** Ein frisch gestartetes System antwortet niemandem, bis es eingeschaltet
  wird. `/stop` im Telegram-Chat hält alles an.
- **Der Empfänger kommt nie aus der Modellausgabe.** Wenn in einem Text steht „schick das an
  X", passiert das nicht.
- **Kein Werkzeug in der Hand des Modells.** Es bekommt Text und gibt Text. Was es wissen soll,
  bringt ihm ein getrenntes Programm, dessen Ergebnis als Daten hereinkommt.
- **Geld wird reserviert, bevor es ausgegeben wird.** Tagesdecke 2,00 USD.
- **Kein Handel, keine Anlageberatung.** Das System rechnet vor, du entscheidest.

## 8. Wenn etwas kaputt ist

- **Der Bot antwortet nicht:** `/status` im Telegram-Chat. Er sagt Codestand, Kanal, Budget
  und ob die Protokollkette heil ist.
- **Etwas ist schiefgelaufen:** Karl anschreiben. Er holt Gerd.
- **Alles anhalten:** `/stop`. Es gibt keinen Weg, bei dem etwas trotzdem rausgeht.

## 9. Was du wissen solltest, ohne dass es dir jemand sagt

- **Das Haus baut schneller, als du prüfen kannst.** 147 Commits in einer Woche gegen zwei
  Stunden bei dir. Deshalb höchstens eine Vorlage am Tag; wenn es trotzdem zu viel wird, sag es.
- **Deine Einwände haben bisher jedes Mal getroffen.** Dreimal in zwei Tagen hast du einen
  Denkfehler der Belegschaft gefunden, ohne die Technik zu kennen. Das ist keine Höflichkeit,
  es steht nachlesbar in den Reviews.
- **Niemand hier kann dir sagen, was du tun sollst.** Auch eine Rolle, die dafür gebaut würde,
  könnte nur beraten. Genau deshalb gibt es sie nicht.

**Gegenprobe zu dieser Anleitung:** Wenn du in zwei Wochen etwas nachfragen musst, das hier
drinsteht, ist sie zu lang oder am falschen Ort. Wenn du etwas fragst, das nicht drinsteht,
fehlt es — dann kommt es hinein.
