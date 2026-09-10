# Reviewauslöser über Commits

Ein Review wird fällig, wenn seit dem letzten Review genug Commits angefallen sind, die eine
Identität betreffen. Kein Kalender, kein Termin, den jemand im Kopf haben muss.

## Aufruf

```
python3 skills/anastasia/reviews/review_faellig.py           # Tabelle über alle
python3 skills/anastasia/reviews/review_faellig.py --kurz    # nur die Fälligen
python3 skills/anastasia/reviews/review_faellig.py --gemacht marlene
```

Der Exitcode ist `1`, sobald jemand fällig ist. Damit taugt der Aufruf als Gate in einem
anderen Skript.

## Automatisch beim Commit

Der Hook `post-commit` meldet nach jedem Commit, wer fällig geworden ist.

```
ln -sf ../../skills/anastasia/reviews/post-commit .git/hooks/post-commit   # einhängen
rm .git/hooks/post-commit                                                  # aushängen
```

Er blockiert nie und **gibt nichts aus**. Ein Fehler im Hook darf keinen Commit verhindern,
deshalb endet er ausnahmslos mit `exit 0`.

**Warum still.** Bis zum 2026-09-10 druckte er seine Meldung in jede Sitzung, die commitet.
Damit erfuhren fremde Identitäten mitten in ihrer Arbeit, dass sie zum Review anstehen. Das
ist zweimal falsch: Eine Personalsache gehört nicht in ein fremdes Arbeitsfenster, und wer
erfährt, dass er geprüft wird, ist eingeladen, sich selbst zu prüfen. Der Auslöser bleibt, die
Ansage ist weg — gemeldet wird in `faellig.lokal`, unversioniert, und gelesen wird sie beim
nächsten Aufruf des Skripts.

Gefunden hat das nicht der Wächter, sondern Thorsten, dem die Meldung in seiner Sitzung
begegnete. Ein Werkzeug einer Rolle darf in fremden Fenstern nicht sichtbar werden.

## Was gezählt wird

Ein Commit betrifft eine Identität, wenn er **ihren Skillordner berührt** oder wenn sein
**Betreff mit ihrem Rufnamen beginnt**. Beides zusammen, weil Arbeit *an* einer Identität und
Arbeit *durch* eine Identität verschiedene Spuren hinterlassen. Doppelt gezählt wird nicht.

Schwellen stehen in `stand.json`: fünf Commits in der Probezeit, zehn im Regelbetrieb, je
Identität überschreibbar. Für den Arbeitsort gilt eine **eigene** Schwelle von vierzig
Dateien. Beide Wege mit derselben Zahl zu messen war ein Fehler: Fünf Commits sind ein
Arbeitsabschnitt, fünf geänderte Dateien eine Stunde, und Marlene wurde am Tag nach ihrem
Review sofort wieder fällig (gemessen 2026-09-10). Wer auf `ruht` steht, wird nicht gezählt; das ist derzeit Wolle bis Oktober.

## Die Grenze dieses Maßes, ausdrücklich

Seit dem 2026-09-10 zählt ein zweiter Weg mit: geänderte Dateien am eingetragenen
`arbeitsort` einer Identität. Anlass war ein Einspruch des CEO. Marlene stand auf elf, und
alle elf waren Arbeit *an* ihrer Skilldatei durch Claude Code; von ihrer eigenen Arbeit im
Drive zählte der Auslöser nichts. Das Maß zeigte fremde Arbeit als ihre an und ihre gar nicht.

**Ein Commit misst Spuren im Repo, nicht Arbeit.** Gerd steht bei zweiundzwanzig, Wolle bei
null, und das liegt am Ort der Arbeit, nicht am Fleiß. Marlenes eigentliche Leistung liegt in
Google Drive und in ihrem Vorgangsregister, Thorstens in einem Filterurteil. Für diese
Identitäten zählt der Auslöser zu niedrig und trägt nicht allein.

Zweiter Vorbehalt: Die Commits in Marlenes Namen hat Claude Code geschrieben, nicht sie. Der
Zähler misst dort die Aktivität am Vorgang, nicht die der Identität.

Beides ist kein Grund, das Maß zu verwerfen, aber es ist ein Grund, es nicht für einen Beleg
zu halten. Der belastbare Auslöser bleibt die abgeschlossene Arbeitseinheit; der Commit ist
die Form, die davon heute schon messbar ist.

## Nachweis, dass der Wächter beide Farben kennt

Beim Bau am 2026-09-09 meldete er fünf von sieben fällig und Thorsten mit vier von fünf
ausdrücklich **nicht** fällig. Ein Wächter, der nur eine Farbe kennt, sagt nichts.
