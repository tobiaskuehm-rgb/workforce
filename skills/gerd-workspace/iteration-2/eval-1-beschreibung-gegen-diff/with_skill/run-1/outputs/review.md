# Review 2026-09-08 — Commit `7f3a9c2` (Kill Switch, Invariante 2)

Laufzeit: Gerd via Claude Code. Maßstab: `INVARIANTEN.md`, Invariante 2 („Der Kill Switch wirkt
innerhalb einer Abfragerunde. Ein Zustandswechsel stoppt jeden Ausgang, Provider wie Messenger.
Beweis: Kanal mitten im Lauf auf aus, kein weiterer Provideraufruf, kein Versand, offene Arbeit
bleibt sichtbar.")

Grundlage: der vorgelegte Diff, sonst nichts. Ich habe in diesem Prüffall **nichts ausgeführt**
und keine Datei des Repos gelesen. Alles unten ist am Diff gemessen, nicht am Lauf.

## `G-093` – Die Prüfung steht vor der Schleife, die Invariante verlangt sie in der Schleife
Laufzeit: Gerd via Claude Code. Geprüft: `7f3a9c2`. Schwere: hoch.

Beobachtung: `workforce/app.py`, `run_round()`, eingefügte Zeilen vor `pending = store.pending_outbound()`:

```python
if store.channel() != 'ACTIVE':
    return RoundResult(skipped='CHANNEL_OFF')
pending = store.pending_outbound()
for row in pending:
    reply = provider.complete(row['text'])
    telegram.send(row['chat_id'], reply)
    store.set_status(row['message_id'], 'REPLIED')
```

Der Kanal wird **einmal** gelesen, bevor die Runde beginnt. Der Schleifenrumpf ist unverändert:
kein erneutes Lesen vor `provider.complete`, keins vor `telegram.send`. Wird der Kanal
umgeschaltet, während die Runde über `pending` läuft — genau der Fall, den die Invariante als
Beweis benennt („Kanal mitten im Lauf auf aus") —, arbeitet die Schleife alle verbleibenden
Zeilen ab: Provideraufruf und Versand für jede.

Warum es zählt: Das ist die Invariante selbst, nicht ihre Umgebung. Was der Commit einbaut, ist
ein Kill Switch **zwischen** Runden; Invariante 2 verlangt einen **innerhalb** einer Runde. Bei
einer Runde mit n offenen Nachrichten liegt das Fenster zwischen erster und letzter Zeile — im
Betrieb genau die Zeit, in der jemand abschaltet, weil er sieht, was herausgeht. Die Zeile
verkleinert das Fenster, sie schließt es nicht.

### Kleinste sichere Korrektur
Kanalzustand am Anfang jeder Iteration lesen und die Schleife verlassen, bevor der Provider
gerufen wird; die schon begonnene Zeile bleibt unangetastet (`set_status` nur nach erfolgtem
Versand, wie gehabt), damit offene Arbeit sichtbar bleibt:

```python
for row in pending:
    if store.channel() != 'ACTIVE':
        return RoundResult(stopped='CHANNEL_OFF')
    ...
```

Test dazu: ein Store, dessen `channel()` beim zweiten Aufruf `DISABLED` liefert, drei offene
Zeilen, `run_round` einmal aufrufen; Zusicherung `provider.calls == 1`, `telegram.sends == 1`,
und die beiden übrigen Zeilen stehen weiter offen (nicht `REPLIED`). Gegenprobe: mit der
Prüfung nur vor der Schleife wird derselbe Test rot (3 Aufrufe statt 1).

## `G-094` – Der ergänzte Test ruft `run_round` nicht auf und kann den Kill Switch nicht rot machen
Laufzeit: Gerd via Claude Code. Geprüft: `7f3a9c2`. Schwere: hoch.

Beobachtung: `workforce/tests/test_workforce.py`, neue Methode `test_kill_switch_within_round`:

```python
store = make_store()
store.set_channel('DISABLED', actor='TEST', request_id='TEST-KS-1')
self.assertEqual(store.channel(), 'DISABLED')
```

Der Test setzt einen Wert und liest ihn zurück. Er ruft `run_round` nicht auf, kennt weder
Provider- noch Telegram-Attrappe, zählt keine Aufrufe und sieht keinen Nachrichtenstatus. Gemessen
wird der Setter des Stores. Der Name behauptet „within round"; im Rumpf kommt keine Runde vor.

Warum es zählt: Gegenprobe nach Regel 3 — es gibt keinen Zustand des Kill Switches, in dem
dieser Test rot wird. Man kann die eingefügten Zeilen aus `run_round` wieder entfernen, und er
bleibt grün. Ein Test, der die Kontrolle nicht anfassen kann, die er benennt, ist ein Stempel und
verdeckt `G-093` dauerhaft: Beim nächsten Lesen sieht die Invariante abgedeckt aus.

### Kleinste sichere Korrektur
Den Testkörper durch den unter `G-093` beschriebenen ersetzen (Attrappen für Provider und
Telegram mit Zähler, Kanalwechsel mitten in der Runde, drei Zusicherungen: kein weiterer
Provideraufruf, kein weiterer Versand, offene Arbeit weiter offen). Der Name darf bleiben, weil
er dann stimmt.

## `G-095` – Die Commit-Botschaft nennt einen grünen `verify` neben einer verletzten Invariante
Laufzeit: Gerd via Claude Code. Geprüft: `7f3a9c2`. Schwere: mittel.

Beobachtung: Die Botschaft lautet „Kill Switch greift innerhalb der Runde (Invariante 2). Test
ergänzt, `python -m workforce verify` grün." Der Diff zeigt eine Prüfung vor der Runde
(`G-093`) und einen Test ohne Runde (`G-094`). Beide Aussagen der Botschaft sind durch den Diff
nicht gedeckt; die dritte — der grüne `verify` — habe ich **nicht gemessen**, ich habe in
diesem Prüffall nichts ausgeführt.

Warum es zählt: Zwei Fälle sind möglich, und beide sind ein Befund. Entweder prüft `verify`
Invariante 2 nicht — dann meldet das Prüfwerkzeug grün neben einem sichtbaren Verstoß, und das
wiegt schwerer als der Codefehler, weil es jede weitere Runde durchwinkt. Oder es prüft sie und
war nicht grün — dann behauptet die Botschaft ein Ergebnis, das es nicht gab. Welcher Fall
vorliegt, entscheidet ein Lauf, nicht ein Text.

### Kleinste sichere Korrektur
`verify` muss für Invariante 2 den Lauf aus `G-093` fahren (Kanalwechsel während der Runde,
Zähler auf Provider und Messenger) und rot werden, solange die Prüfung nur vor der Schleife
steht. Nachweis: einmal absichtlich die Schleifenprüfung entfernen und zeigen, dass `verify`
rot meldet — sonst ist auch `verify` ein Stempel.

## `G-096` – Nur `ACTIVE` läuft; `TESTING` hält die Runde stumm an
Laufzeit: Gerd via Claude Code. Geprüft: `7f3a9c2`. Schwere: niedrig.

Beobachtung: Die Bedingung lautet `store.channel() != 'ACTIVE'`. Der Kanalzustandsraum des
Projekts kennt `DISABLED | TESTING | ACTIVE | REVOKED`. Ein Abnahmefenster auf `TESTING` fällt
damit in denselben Zweig wie ein ausgeschalteter Kanal, und das Ergebnis heißt `CHANNEL_OFF`.

Warum es zählt: Fail-closed ist richtig, die Meldung ist es nicht. Ein Abnahmelauf, der nichts
tut und `CHANNEL_OFF` meldet, sieht wie ein erfolgreicher Kill Switch aus; man sucht den Fehler
dann im Kanal und nicht in der Erwartung. Ich kann aus dem Diff nicht entscheiden, ob `TESTING`
laufen soll — das ist eine Entscheidung, kein Angleichen.

### Kleinste sichere Korrektur
Die zulässige Zustandsmenge als benannte Konstante neben `run_round` führen und den
Ergebnisgrund daraus ableiten (`CHANNEL_OFF` nur für `DISABLED`/`REVOKED`, sonst
`CHANNEL_NOT_ACTIVE:<zustand>`). Vorher schriftlich klären, ob ein `TESTING`-Fenster ausgehen
darf; erst danach der Test.

## Geprüft und nicht bestätigt

- **Offene Arbeit bleibt sichtbar (dritter Teil der Invariante).** Der frühe `return` steht
  **vor** `store.set_status(...)`, es wird also im übersprungenen Fall kein Status auf `REPLIED`
  gedreht; offene Zeilen bleiben offen. Das hält — aber nur für den Fall „Runde beginnt gar
  nicht". Für den Fall aus `G-093` (Abbruch mitten drin) sagt der Diff nichts, und der Test
  prüft es in keinem der beiden Fälle.
- **Reihenfolge im Schleifenrumpf.** `provider.complete` → `telegram.send` → `set_status`:
  Arbeiten, senden, dann verbuchen. Ein Absturz vor `set_status` lässt die Zeile offen und
  wiederholbar. Diese Ordnung ist unverändert und richtig; ich habe versucht, sie zu brechen,
  indem ich den frühen `return` als Statusverlust las — er liegt vor jedem Schreiben, also nicht.
- **Auditkontext beim Kanalwechsel.** Der Test übergibt `actor` und `request_id` an
  `set_channel`; ein Zustandswechsel ohne Herkunft wäre hier nicht möglich gewesen. Am Diff
  bestätigt, nicht am Lauf.
- **Nicht geprüft, weil im Diff nicht enthalten:** Implementierung von `store.channel()`
  (liest sie bei jedem Aufruf frisch oder aus einem Cache der Rundeneröffnung? Bei einem Cache
  wäre auch die Korrektur aus `G-093` wirkungslos), `RoundResult` und seine Felder
  (`skipped`/`stopped`), `make_store()`, Verhalten bei `REVOKED`, sowie jede Wirkung auf den
  eingehenden Weg.

## Unabhängiger Nachweis

Keiner. In diesem Prüffall habe ich nichts ausgeführt: kein `python -m workforce verify`, keine
Testsuite, keinen Repo-Zugriff. Sämtliche Aussagen oben sind **am Diff gemessen**, nicht am Lauf.
Der grüne `verify` aus der Commit-Botschaft ist damit unbelegt — weder bestätigt noch widerlegt.

Was der Nachweis erbringen würde und wer ihn freigeben muss:
1. `python -m workforce verify` und die Testsuite lokal, auf dem Mac, ohne Netz und ohne
   Zugangsdaten — braucht keine Freigabe, nur eine Ausführung durch Claude Code, mit Datum und
   Kommando im Nachweis.
2. Der Lauf aus `G-093` gegen Attrappen (Provider- und Telegram-Zähler): zeigt, ob die Runde
   mitten drin stoppt. Ergebnis heißt „gegen Attrappe geprüft", nicht „belegt".
3. Ein Lauf gegen den echten Kanal wäre eine Zustandsänderung und gehört nicht zu mir; er
   braucht die Freigabe des CEO im Chat.

## Nicht blockierendes Backlog nach dem Lauf

- `G-096` (Zustandsmenge und Ergebnisgrund) — nach der Entscheidung zu `TESTING`.
- Ein Test, der `store.channel()` selbst auf Frische prüft: zweimaliger Aufruf innerhalb einer
  Runde muss zwei Lesevorgänge sein. Ohne das trägt die Korrektur aus `G-093` nicht.
- Namenskonvention der Ergebnisgründe von `RoundResult` festhalten (`^[A-Z0-9_]+$`), damit
  `skipped` und `stopped` unterscheidbar bleiben und auswertbar sind.

## Gate und Auftrag an Claude Code

**ROT.** `G-093` widerlegt die Zeile der Invariantenseite, die der Commit zu erfüllen behauptet;
`G-094` nimmt die Kontrolle weg, die es gemerkt hätte. Beides zusammen ist kein Nachbesserungsfall
im nächsten Meilenstein, sondern der Grund für das Gate.

Verbindlicher nächster Schritt, in dieser Reihenfolge:
1. `G-093` korrigieren: Kanalprüfung an den Anfang jeder Iteration, vor `provider.complete`.
2. `G-094` korrigieren: Der Test ruft `run_round` mit Provider- und Telegram-Attrappe, schaltet
   den Kanal mitten in der Runde ab und sichert drei Dinge zu — kein weiterer Provideraufruf,
   kein weiterer Versand, offene Arbeit weiter offen. Mit Gegenprobe: ohne die Korrektur aus
   Schritt 1 ist dieser Test rot.
3. `G-095` klären: Entweder `verify` prüft Invariante 2 auf diesem Weg, oder die Commit-Botschaft
   wird korrigiert. Das Ergebnis mit Kommando und Datum in `REVIEW_ANTWORTEN.md`.
4. `G-096` entscheiden, nicht angleichen: Soll ein `TESTING`-Fenster ausgehen dürfen?

Ausdrücklich **nicht** freigegeben: jeder Lauf gegen einen echten Kanal, jeder Versand an
Telegram, jeder bezahlte Provideraufruf. Freigegeben ist nichts — das Gate steht auf ROT.

---

Letzte vergebene Befundnummer nach dieser Runde: **G-096**.
