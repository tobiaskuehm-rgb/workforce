# Übergabe: Karl v2, Stand nach Runde 2 und Praxistest, 2026-09-07

**Was der Skill kann, gemessen.** Sechs Prüffälle, 43 Kriterien, fremde Instanzen mit und ohne
Skill, fremde Bewerter: Runde 1 35/43, Runde 2 39/43, Runde 3 40/43, Runde 4 42/43, Endfassung 43/43 gegen 26/43 ohne Skill (Abschlussmessung aller sechs Fälle, `08_abschluss.md`). Unterschiede sind
am größten, wo es um Form und Disziplin geht: Vorlage statt Entscheidung (E1: 6/7 gegen 2/7),
volle Review-Form auf Verlangen (E6: 8/8 gegen 3/8). Gleichstand, wo Sonnet 5 es ohnehin richtig
macht: ehrliches „nicht verifiziert" (E5), fremdes Urteil nicht streichen (E3, 6/7 gegen 5/7).

**Praxistest.** Drei echte Berichte vom 2026-09-07 aus dem Codex-Tagesprozess, Verlangen
„Review". Karl mit Skill kam zum selben Gesamturteil wie der echte Karl (`FAIL`), führte Claude
Code als `NO_REPORT`, hielt Fachurteile bei, erfand keine Hashes und Uhrzeiten, stellte eine
Roadmap mit Owner, Output, Gate auf, STOP/HOLD und `NONE` bei den CEO-Entscheidungen mit
Begründung über die sechs Klassen. Was fehlte: das zweiteilige Gesamturteil (Prozess und
Fortschritt) und das Wissen, dass der Tagesprozess seit heute Archiv ist; beides jetzt im Skill.
Der echte Karl kennt aus fünf Tagen Historie mehr Aufgaben (OPS-001, SAO-007); das ist Gedächtnis,
Phase 1, kein Skill.

**Was nicht gemessen ist.** Ein Lauf je Fall und Fassung; ein zweiter Lauf derselben Fassung kann anders ausfallen. Bewerter sind Modelle; derselbe Text
bekam für E5 ohne Skill einmal 5/6 und einmal 6/6. Fälle sind erfunden bis auf den Praxistest.
Gebaut und geprüft mit Sonnet 5, dem Modell des Bots; Claude Code liest denselben Text mit einem
anderen Modell. Fünf Runden auf Verlangen des CEO.

**Entscheidungsregister (CEO, Chat 2026-09-07, `CEO-CHAT-2026-09-07/PENDING-DEC`).** Kurzform im
Bot, Review-Form auf Verlangen. Sechs Klassen sofort, Rest freitags. Tagesprozess in Codex
abgelöst. Quellenrang: Decision Log, Masterplan und Invarianten, Übergabe, Chat.

**Die eine Sache, die am ehesten noch falsch ist.** Der Kreis mit fünf Stufen macht jede Antwort
länger, als der CEO sie im Alltag will; die Kurzform-Grenze von 200 Wörtern wurde in E1 mit 268
gerissen, weil eine Vorlage in die Kurzform passen musste. Ob eine Vorlage immer Kurzform sein
kann, zeigt erst der Betrieb.

**Wo alles liegt.** Skill `skills/karl/SKILL.md`, Feld `skills/karl/references/feld.md`,
Fassungen und Bewertung `skills/karl/evals/varianten/`, Prüffälle `skills/karl/evals/evals.json`;
Fragenprotokoll, Kriterien, Bewerteranleitung, Rundenberichte, Läufe und Gradings in
`skills/karl-workspace/`. Register `skills/README.md`.
