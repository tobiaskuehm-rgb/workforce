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

Er blockiert nie. Ein Fehler im Hook darf keinen Commit verhindern, deshalb endet er
ausnahmslos mit `exit 0`.

## Was gezählt wird

Ein Commit betrifft eine Identität, wenn er **ihren Skillordner berührt** oder wenn sein
**Betreff mit ihrem Rufnamen beginnt**. Beides zusammen, weil Arbeit *an* einer Identität und
Arbeit *durch* eine Identität verschiedene Spuren hinterlassen. Doppelt gezählt wird nicht.

Schwellen stehen in `stand.json`: fünf in der Probezeit, zehn im Regelbetrieb, je Identität
überschreibbar. Wer auf `ruht` steht, wird nicht gezählt; das ist derzeit Wolle bis Oktober.

## Die Grenze dieses Maßes, ausdrücklich

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
