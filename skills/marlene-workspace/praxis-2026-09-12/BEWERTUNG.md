# Marlenes Skill, gemessen an ihrem praktischen Tun

**Marv, 2026-09-12.** Nicht gegen Prüffälle, sondern gegen sechs Tage echter Arbeit: 6. bis 12. September 2026. Grundlage sind ihre eigenen Spuren im Drive (`01_Ablage_Eingang/_Marlene`), nicht ihre Berichte über sich selbst allein.

## Was gemessen wurde

| Was | Gemessen | Herkunft |
|---|---|---|
| Berichte | 6 (Praxistest, Eingang, iCloud-Wurzel, drei Morgenberichte) | `_Berichte/` |
| Register | 9 Dateien: Entscheidungen, Fristen, Vorgänge, Rechnungen, Verträge, Stammblatt, Steuerübergabe, Vermietung, Todo | `_Marlene/` |
| Entscheidungen des CEO | 67 Zeilen, von A1 bis A76 durchnummeriert | `ENTSCHEIDUNGEN.md` |
| Fristen | 26 Zeilen, jede mit Paragraph oder Vertragsquelle, Vorfrist, Status, Nachweisspalte | `FRISTEN.md` |
| Protokolle | 56 Dateien, davon 12 Bewegungsprotokolle, ein Postprotokoll (63 Zeilen), ein Zugriffsprotokoll (67 Zeilen) | `protokoll/` |
| Post | 38 Abholungen, 23 Sendungen, 1 gestoppte Sendung | `protokoll/post.jsonl` |
| Zugänge | 4 Konten: Postfach, Bank-Anmeldung, Bank-FinTS, Versicherungsportal; 66 freigegebene Zugriffe, 1 abgelehnter | `protokoll/zugriffe.jsonl` |
| Ausgang | 23 Schreiben mit Kennung, Fassung und Vorgangsdatei | `ausgang/` |
| Konzepte | 11, darunter vier 3-Loops | `konzepte/` |
| Aussortiert | 6 Tagesordner, nichts gelöscht | `~/Documents/_Aussortiert/` |
| Klärfälle offen | 9 Dateien, die ältesten seit dem 07.09. | `_Klären/` |

Nicht gemessen: ob die abgelegten Dateien inhaltlich am richtigen Ort liegen (das prüft nur der Nutzer), und ob die Bankumsätze mit den Rechnungen zusammenpassen (der Lesezugang besteht erst seit dem 10.09.).

## Was der Skill verlangt und die Praxis eingelöst hat

**Die Rücknehmbarkeit hat einen echten Absturz überstanden.** Am 07.09. brach die Sitzung zweimal ab, mitten in einem Lauf über 380 Dateien. Der Bericht sagt es im zweiten Satz, und er belegt es: Ein Vergleich von Plan gegen Protokoll ergab keine halbe Bewegung, jede Bewegung trägt ihre Prüfsumme, `marlene_ablegen.py undo` bleibt möglich. Regel 4 des Skills ist damit nicht behauptet, sondern gehalten.

**Frist zuerst, auch rückwirkend.** Die Fristenliste führt 26 Zeilen. Sie enthält auch das, was schmerzt: eine Widerspruchsfrist, die 2025 abgelaufen ist und erst 2026 erfasst wurde, mit dem Vermerk „abgelaufen ohne Widerspruch (nachträglich erfasst)". Eine Assistentin, die nur Erfolge führt, hätte diese Zeile nicht.

**Eine Korrektur gegen sich selbst.** Am 07.09. korrigierte sie die Abrechnungsfrist für die Nebenkosten von Dezember 2026 auf Juli 2027, weil der Abrechnungszeitraum anders läuft als zuerst gelesen. Die alte Zeile blieb stehen, mit dem Vermerk „ersetzt".

**Die Freigabe je Fassung greift maschinell.** Jede der 23 Sendungen trägt in ihrer Vorgangsdatei eine Freigabekennung. Am 11.09. um 11:23 Uhr stoppte die Poststelle einen Versand mit dem Grund „keine Freigabe-Kennung im Vorgang"; eine Minute später ging dasselbe Schreiben mit Freigabe hinaus. Regel 9 ist keine Absichtserklärung mehr, sondern eine Sperre.

**Die Zugriffskontrolle hat einmal nein gesagt.** Von 67 Zugriffen wurde einer abgelehnt: „Aktion steht nicht auf der Liste dieses Kontos". Eine Kontrolle, die nie rot wird, wäre ein Stempel; diese ist rot geworden.

**Rückfragen sind gebündelt und entscheidbar.** 76 nummerierte Fragen, im Bericht jeweils mit Vorschlag und fett gesetzten Antwortmöglichkeiten. Der Morgenbericht vom 11.09. nennt fünf und sagt bei jeder, was sie bewegt und was sie braucht.

**Die Grenze zur Fachentscheidung hält.** Im Bericht vom 07.09. steht der Satz, dass der Einwand der Mieter keine Frage an sie ist: Ob die Wartung mangelhaft war und ob die Position gekürzt wird, entscheidet Tobias. Sie führt nur, was verlangt wird und bis wann.

## Was die Praxis tut, das im Skill nicht steht

Der Skill beschreibt eine Assistentin, die Dateien liest, benennt, ablegt und berichtet. Die Praxis ist in sechs Tagen über diesen Text hinausgewachsen, in acht Feldern:

| Feld | Was tatsächlich läuft | Was der Skill dazu sagt |
|---|---|---|
| **Posteingang** | Eigenes Postfach, 38 Abholungen, Mails als `.eml` im Eingang, Anhänge getrennt | nichts; Mail kommt im Arbeitsgang nicht vor |
| **Postausgang** | 23 Sendungen an Mieter, Versicherung, Lieferanten, mit Kennung und Fassung | nur das Verbot „senden ohne Freigabe" |
| **Bankzugang** | Lesender Zugang, acht Konten, Umsätze einsehbar, Überweisungen durch TAN-Pflicht ausgeschlossen | „ein Konto anfassen: nie" — pauschal, ohne Lesen und Schreiben zu trennen |
| **Portale** | Zwei Versicherungszugänge im Schlüsselbund, mit Aktionsliste je Konto | nichts |
| **Zugriffsprotokoll** | Jeder Zugriff mit Konto, Aktion, Zweck, Ergebnis | nichts; der Skill kennt nur das Bewegungsprotokoll |
| **Automatik** | Nächtlicher Lauf um 4 Uhr über sieben Quellen, Morgenbericht um 6 Uhr | „ein Bericht je Arbeitsgang" — kein Begriff für einen Lauf ohne Auftrag |
| **Verdachtsfälle** | Vier Mails mit dem Präfix `VERDACHT_` im Eingang | nichts; der Entscheidungsbaum kennt Werbung, aber keinen Betrugsversuch per Mail |
| **Zweite Person** | Marlen ist seit dem 11.09. gleichrangig befugt, im Konfliktfall gilt Tobias | der Skill kennt genau einen Auftraggeber |

Das ist kein Vorwurf an Marlene. Es ist der Abstand zwischen einem Text vom 6. September und einer Arbeit vom 12. September. Aber jede dieser acht Zeilen ist eine Stelle, an der sie heute ohne Regel arbeitet.

**Der teuerste Punkt ist der Bankzugang.** Der Skill verbietet „ein Konto anfassen" ohne Unterscheidung. Am 8. September habe ich genau diesen Vorschlag eines externen Reviewers zurückgewiesen, mit der Begründung, es gebe keinen Bankzugang und das sei Absicht. Zwei Tage später gab es ihn. Die Praxis hat den Reviewer bestätigt und mich widerlegt.

## Wo die Praxis hinter dem Skill zurückbleibt

**Der Dokumentationsrückstand.** Am 10.09. um 14:08 und 14:11 gingen drei Schreiben hinaus. Am Morgen des 11.09. führten Vorgänge, Fristen und Ausgangsordner sie weiterhin als offen. Marlene hat das selbst als Kernaussage ihres Morgenberichts gemeldet, und das ist die richtige Reaktion; die Regel dazu fehlt trotzdem. Der Skill sagt „Erledigt ist nur, was belegt ist". Die Umkehrung fehlt: Was belegt ist, gehört noch in derselben Sitzung ins Register. Zwischen Poststelle und Register liegt ein Riss, den nur ein Mensch bemerkt hat.

**Die Klärfälle altern.** Neun Dateien liegen in `_Klären`, die ältesten seit dem 07.09., fünf Tage ohne Bewegung. Der Skill sagt, Unklares komme dorthin mit Vorschlag; er sagt nicht, wie lange es dort liegen darf und was passiert, wenn die Antwort ausbleibt.

**Eine Sendung ohne Freigabekennung in der Vorgangsdatei.** 22 von 23 Ausgängen tragen sie, einer nicht. Er ging am 11.09. hinaus, und die Registerlage legt nahe, dass die Freigabe mündlich vorlag. Das ist kein Verstoß gegen die Regel, aber eine Lücke im Nachweis.

## Was im Skill steht und nie gebraucht wurde

Die Zeile „ein Schaden ist passiert" im Entscheidungsbaum samt Verweis auf den Versicherungsfall kam in sechs Tagen nicht vor. Das ist kein Fehler; eine Regel für den seltenen Fall ist richtig, solange sie kurz ist. Anders der Satz „Monatlich der Bankabgleich: jede Abbuchung hat einen Beleg": Er stand seit dem 3. September im Text und war bis zum 10. September unausführbar, weil es keinen Zugang gab. Vier Fristenzeilen tragen bis heute den Vermerk „Bankeinzug angekündigt, nicht geprüft".

## Urteil

Der Skill trägt, wo er etwas sagt. Von zehn Regeln sind acht in der Praxis belegbar eingelöst, zwei nur teilweise: „Erledigt ist nur, was belegt ist" (Rückstand) und „die Ablage muss ohne dich lesbar bleiben" (neun alternde Klärfälle, deren Vorschlag nur im Bericht steht).

Sein Problem ist nicht, was drinsteht, sondern was fehlt. Die Assistentin vom 6. September legte Dateien ab. Die vom 12. September empfängt und versendet Post, bedient vier Zugänge, läuft nachts allein und hat eine zweite Auftraggeberin. Sie hat sich in sechs Tagen ihre eigenen Verfahren gegeben — Poststelle, Freigabekennungen, Zugriffsprotokoll, Verdachtspräfix — und keines davon steht in ihrem Vertrag.

Das ist der Zustand, vor dem Marv seit Lehre 16 warnt, nur in der anderen Richtung: Nicht der Skill war zu streng für die Praxis, sondern die Praxis ist ihm davongelaufen. Ein Skill, den die Arbeit überholt, ist am nächsten Tag eine Beschreibung von gestern.

## Die eine Sache, die am ehesten noch falsch ist

Ich habe die Spuren gelesen, nicht die Ablage. Ob die 57 abgelegten Dateien am richtigen Ort liegen und ob die Nebenkostenabrechnung rechnerisch stimmt, sagt keines ihrer Protokolle; das sieht nur, wer die Dokumente selbst prüft. Mein Urteil misst Verfahren, nicht Inhalt.
