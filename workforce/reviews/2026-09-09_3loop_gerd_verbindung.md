# 3-Loop: Die Verbindung zu Gerd in Codex und ChatGPT

Claude Code, 2026-09-09, für Tobias. Verfahren: `/3loop`. Die „Sicht von Gerd" unten ist
simuliert und so gekennzeichnet; Gerd kann sie im Review kippen.

**Randbedingungen, schon entschieden, hier nicht neu verhandelt:** Gerd ist derselbe Gerd in
Codex und Claude Code, eine Befundreihe, ein Maßstab (`skills/gerd/SKILL.md`, Register
2026-09-06). Die ChatGPT-Verläufe werden einmal exportiert und sind dann Archiv; die
ChatGPT-Assistentin ist keine Mitarbeiterin (CEO im Chat, 2026-09-08). „Was nicht in
`skills/gedaechtnis/` steht, weiß der Mitarbeiter nicht, egal wo er läuft" (Modell-Loop,
Auflage 1, umgesetzt). Vorschlag D unten widerspricht der ersten Randbedingung; das steht
dort im ersten Satz.

## 1. Die Frage in einem Satz

Wie wird Gerd, wenn er in Codex oder in ChatGPT gerufen wird, an denselben Gerd
angeschlossen, der in Claude Code läuft: ein Gedächtnis, eine Befundreihe, ein Maßstab; der
CEO entscheidet, sinnvoll bis zum Donnerstag 2026-09-10, weil der Export der Verläufe seitdem
offen ist.

## 2. Gemessen, nicht gemeint

| Was | Ergebnis | Befehl / Quelle |
|---|---|---|
| Gerds Gedächtnis | `skills/gedaechtnis/gerd.md`, 26 Zeilen, eine Entscheidung, eine Tatsache, zwei offene Vorgänge | `wc -l`, 2026-09-09 |
| Gerds Skill | `skills/gerd/SKILL.md`, 7,9 KB; `~/.claude/skills/gedaechtnis/gerd.md` löst in die Repo-Datei auf | `readlink -f` |
| Befundreihe Neubau | `REVIEW_GERD.md`, 211 Zeilen, letzte Nummer `G-113`; Prototyp 1743 Zeilen | `wc -l`, `tail` |
| Läufe „Gerd via Codex" mit dieser Kennzeichnung | **0** in beiden Review-Dateien | `grep -c "via Codex"` |
| Was Codex liest | `AGENTS.md`, 81 KB, Spiegel von `CLAUDE.md`; nennt `skills/gerd` und `gedaechtnis` **null** Mal | `grep -c` |
| Codex-Konfiguration auf dem Mac | `~/.codex/` vorhanden, kein `skills/`, kein eigenes `AGENTS.md`; `.chatgpt-projects/` vom 2026-08-31 | `ls -la ~/.codex` |
| Weg von ChatGPT ins Repo | keiner; ChatGPT hat weder Shell noch Git | Bauart, nicht gemessen |
| ChatGPT-Verläufe mit Gerd | nicht im Repo, Export offen seit 2026-09-07 | `gerd.md`, Zeile „Import" |
| Gerds LLM-Server aus Codex | seit `ab6241d` im Repo als `OllamaProvider` | `git log` |

**Nicht gemessen:** was in `.chatgpt-projects/` liegt (nicht geöffnet, privat); ob Codex in
diesem Ordner überhaupt gestartet wurde, seit `skills/` existiert; wie viele Gerd-Verläufe
ChatGPT hält.

## 3. Drei Sichten und ihre Fragen, jetzt festgelegt

**Tobias, der Alltag.** Wo tippt er „Gerd, prüf das", und bekommt er dort denselben Gerd?
Kostet ihn die Verbindung Handarbeit je Lauf? Geht es vom Handy? Was passiert, wenn er es
vergisst?

**Anastasia, das Register.** Ist es eine Identität mit einer Spur, oder zwei mit demselben
Namen? Kann ein Probezeit-Review alle Läufe sehen? Wer trägt die Laufzeit-Kennzeichnung ein?

**Gerd, der Prüfer (simuliert).** Gibt es genau eine Befundreihe, und wer vergibt die
Nummer? Kann eine Kopie driften, ohne dass es auffällt? Ist ein Befund aus dem anderen Ort
nachweisbar, mit Commit und Diff? Was passiert bei Verlust des Gedächtnisses an einem Ort?

## 4. Der Vorschlag (A): „Connection zu Gerd Codex ChatGPT"

Wörtlich: eine Verbindung zu Gerd in Codex und in ChatGPT. In ganzen Sätzen: Gerd soll an
allen drei Orten derselbe sein; was er in Claude Code weiß und gefunden hat, weiß er auch in
Codex und ChatGPT, und umgekehrt. Annahmen, die A voraussetzt und nicht sagt: Es gibt eine
**lebende** Verbindung in beide Richtungen, alle drei Orte können denselben Zustand lesen
und schreiben, und ChatGPT ist ein gleichwertiger Ort. Die dritte Annahme ist nach der
Messung falsch: ChatGPT erreicht das Repo nicht.

| | A: lebende Verbindung an drei Orten |
|---|---|
| Ort | Repo plus ein Sync nach ChatGPT (Projekt-Dateien, von Hand oder Skript) und zurück |
| Ablauf | jeder Lauf schreibt ins Gedächtnis; Kopien nach ChatGPT werden nachgeführt; Befunde aus ChatGPT werden von Hand ins Repo übertragen |
| Kosten | null Geld |
| Aufwand | Tage für den Bau, dann Handarbeit je ChatGPT-Lauf |
| Risiko | zwei Kopien, die driften; Nummernkollision; die Verbindung schläft ein, sobald das Nachführen ausfällt |

## 5. Drei Gegenvorschläge

**B, das Gegenteil an der teuersten Stelle: kein ChatGPT-Gerd.** Die teuerste Stelle in A ist
der Weg nach ChatGPT, weil er ohne Repo nur von Hand geht. B streicht ihn: Export der Verläufe
einmal, Gedächtnis nachgetragen, dann ist ChatGPT Archiv. Codex wird angeschlossen, wo es
schon liest: `AGENTS.md` bekommt einen Abschnitt „Gerd" mit Pfad zu `skills/gerd/SKILL.md`
und `skills/gedaechtnis/gerd.md` und der Anweisung, beide vor jedem Review zu lesen.

| | B |
|---|---|
| Ort | Repo; Codex liest `AGENTS.md`, das auf Skill und Gedächtnis zeigt |
| Ablauf | Export einmal; danach schreiben beide Laufzeiten dieselben zwei Dateien, Nummer aus `REVIEW_GERD.md` |
| Kosten | null |
| Aufwand | ein Abschnitt in `AGENTS.md`, ein Wächter in `test_mirrors.py`, ein Export-Nachmittag |
| Risiko | Codex hält sich nicht an den Abschnitt; erst der erste „via Codex"-Lauf zeigt es |

**C, dasselbe Ziel mit dem, was da ist: ein ChatGPT-Projekt als Lesekopie.** Wie B für Codex.
ChatGPT bekommt zusätzlich ein Projekt „Gerd" mit drei hochgeladenen Dateien (`SKILL.md`,
`gerd.md`, der Kopf von `REVIEW_GERD.md` mit letzter Nummer), nachgeführt nach jedem Commit,
der sie ändert. Befunde von dort heißen „Gerd via ChatGPT", bekommen keine Nummer, und
werden in Claude Code oder Codex gegen den Diff nachgeprüft, bevor sie eine bekommen.

| | C |
|---|---|
| Ort | Repo plus ChatGPT-Projekt mit drei Dateien, nur lesend |
| Ablauf | wie B; dazu Nachführen der drei Dateien nach Änderung; ChatGPT-Befunde als Vorbefunde ohne Nummer |
| Kosten | null |
| Aufwand | B plus fünf Minuten je Nachführung; ein Skript `gerd_chatgpt_bundle.sh`, das die drei Dateien in einen Ordner legt |
| Risiko | die Lesekopie veraltet still; ChatGPT-Gerd prüft ohne Diff und ohne Tests, sein Befund ist eine Vermutung mit Gerds Namen |

**D, die einfachste Form, die noch alles erfüllt: Gerd nur in Claude Code.** Widerspricht der
Randbedingung „derselbe Gerd in Codex und Claude Code". Export der Verläufe, dann Archiv;
Codex und ChatGPT sind Werkzeuge ohne Gerd-Identität. Wer dort prüft, prüft als niemand, und
das Ergebnis wird als Hinweis nach Claude Code getragen.

| | D |
|---|---|
| Ort | Repo, ein Ort |
| Ablauf | nichts nachführen; ein Export |
| Kosten | null |
| Aufwand | ein Export-Nachmittag, ein Satz im Register |
| Risiko | wenn Claude Code ausfällt, gibt es keinen Gerd; die Codex-Zeile im Register wird falsch |

## 6. Die Matrix

Note 1 bis 5, je Note ein Grund. Summe unten als Sortierhilfe.

| Frage | A | B | C | D |
|---|---|---|---|---|
| **Tobias:** Wo tippe ich, und ist es derselbe Gerd? | 3: überall, aber in ChatGPT ein Gerd ohne Diff | 4: Claude Code und Codex, beide lesen dasselbe | 4: wie B, plus ChatGPT als Vorprüfer | 2: nur ein Ort |
| **Tobias:** Handarbeit je Lauf? | 2: jeder ChatGPT-Lauf braucht Nachführen und Rückübertragen | 5: keine | 3: Nachführen nach jedem Commit an drei Dateien | 5: keine |
| **Tobias:** Geht es vom Handy? | 4: ChatGPT-App ja, mit veralteter Kopie | 2: nur, wo Codex oder Claude Code laufen | 4: ChatGPT-App mit Lesekopie | 1: nein |
| **Tobias:** Was, wenn ich das Nachführen vergesse? | 1: Drift, unbemerkt, beide Richtungen | 5: nichts zu vergessen | 3: Kopie veraltet, aber ohne Nummer richtet sie keinen Schaden an | 5: nichts zu vergessen |
| **Anastasia:** Eine Identität, eine Spur? | 2: drei Orte, zwei davon ohne Commit | 5: eine Spur im Repo, Laufzeit im Befund | 4: eine Spur; ChatGPT-Vorbefunde landen erst mit Nachprüfung darin | 4: eine Spur, aber das Register sagt „Codex" und meint es nicht mehr |
| **Anastasia:** Sieht ein Probezeit-Review alle Läufe? | 2: nur, was zurückübertragen wurde | 5: alles ist im Repo | 4: alles Nummerierte; Vorbefunde nur, wenn übertragen | 5: alles |
| **Anastasia:** Wer trägt die Laufzeit ein? | 3: der Mensch beim Rückübertragen | 5: der Skill verlangt es, `AGENTS.md` auch | 4: wie B, ChatGPT-Läufe von Hand | 5: entfällt |
| **Gerd (sim.):** Eine Reihe, eine Nummernvergabe? | 1: ChatGPT kann `REVIEW_GERD.md` nicht schreiben, Nummern entstehen daneben | 5: Nummer aus der Datei, Kopfzeile reserviert | 5: ChatGPT vergibt keine Nummer | 5: eine Reihe |
| **Gerd (sim.):** Kann eine Kopie driften, ohne aufzufallen? | 1: ja, in beide Richtungen | 4: Codex liest die Repo-Datei selbst; `test_mirrors.py` hält `AGENTS.md` | 2: die drei Dateien im Projekt driften still; kein Wächter sieht ChatGPT | 5: keine Kopie |
| **Gerd (sim.):** Befund mit Commit und Diff nachweisbar? | 2: aus ChatGPT nie, aus Codex ja | 5: beide Laufzeiten haben Git | 3: Codex ja; ChatGPT-Vorbefund erst nach Nachprüfung | 5: ja |
| **Gerd (sim.):** Verlust des Gedächtnisses an einem Ort? | 2: welche Kopie gilt, ist nicht festgelegt | 5: eine Datei im Repo, auf der NAS gepusht | 4: Repo gilt; die ChatGPT-Kopie ist Wegwerf | 5: eine Datei |
| **Summe** | **23** | **50** | **40** | **47** |

## 7. Fazit

**Empfehlung: B**, mit zwei Auflagen aus C und einer aus D.

1. **Aus C: ChatGPT darf Gerd lesen, nie schreiben.** Wenn Tobias unterwegs mit Gerd
   sprechen will, bekommt das ChatGPT-Projekt die drei Dateien als Lesekopie, erzeugt von
   einem Skript im Repo, und jeder Befund von dort ist ein Vorbefund ohne Nummer, der in
   Claude Code oder Codex gegen den Diff geht. Das steht als Satz in `SKILL.md`: „Gerd via
   ChatGPT vergibt keine Nummer."
2. **Aus C: das Nachführen ist ein Befehl, kein Vorsatz.** `skills/gerd/chatgpt_bundle.sh`
   legt die drei Dateien mit Commit-Hash im Kopf in einen Ordner; die Kopie sagt selbst,
   wie alt sie ist.
3. **Aus D: der Export zuerst.** Bevor Codex angeschlossen wird, kommen die ChatGPT-Verläufe
   ins Gedächtnis, sonst weiß Codex-Gerd weniger als ChatGPT-Gerd und die Verbindung beginnt
   mit einem Rückstand.

**Der Test, der die Entscheidung hält:** `test_mirrors.py` bekommt eine Prüfung, dass
`AGENTS.md` den Abschnitt „Gerd" mit beiden Pfaden enthält und dass beide Pfade existieren;
Gegenprobe: Pfad umbenannt, Test rot. Und der erste Codex-Lauf danach trägt „Gerd via Codex"
und die nächste freie Nummer, sonst hat der Abschnitt nicht gewirkt.

**Offene Fragen, nur der CEO:**

- **Soll ChatGPT Gerd überhaupt noch sehen?** Empfehlung: ja, als Lesekopie (Auflage 1), weil
  es der einzige Ort vom Handy ist. Optionen: (a) Lesekopie; (b) gar nicht, ChatGPT ist nur
  Archiv; (c) erst, wenn der Export durch ist.
- **Wann kommt der Export?** Empfehlung: vor dem Codex-Anschluss, ein Nachmittag. Optionen:
  (a) diese Woche; (b) Karl bekommt den Auftrag, Tobias liefert nur die Datei; (c) gar nicht,
  dann gilt das Gedächtnis ab heute als vollständig, und was ChatGPT weiß, ist verloren.
- **Prüft Codex-Gerd denselben Neubau oder nur den Prototyp?** Empfehlung: denselben; der
  Prototyp ist eingefroren. Optionen: (a) Neubau; (b) Codex bleibt beim Prototyp und damit
  ohne Aufgabe.

**Was am ehesten noch falsch ist:** die Annahme, dass Codex einen Abschnitt in `AGENTS.md`
befolgt, den es zwischen 81 KB anderer Regeln findet. Gemessen ist das nicht; null
„via Codex"-Läufe heißt, dass der Weg noch nie gegangen wurde. Wenn der erste Lauf die
Kennzeichnung nicht trägt, ist die Antwort nicht mehr Text, sondern ein eigenes, kurzes
`AGENTS.md`-Präfix für Gerd ganz oben.
