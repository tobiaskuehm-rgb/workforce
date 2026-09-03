# Owner-Probe zu `G-045`/Migration 009 — gelaufen am 2026-09-03

**Ergebnis:** `RESULT: PASS`, elf Zusicherungen.
**Ausgeführt:** 2026-09-03, Wegwerf-Container `g045probe` auf der NAS.
**Produktion:** unberührt. Migration `009` bleibt **nicht angewendet**.
**Freigabe:** CEO im Chat am 2026-09-02/03 (`CEO-CHAT-2026-09-02/PENDING-DEC`,
`G-006` — eine Chat-Freigabe ist echt, aber kein Eintrag im Entscheidungslog).

## Zuschnitt

Eigener PostgreSQL-17-Container mit `POSTGRES_USER=workforce_app`, also
derselben Bootstrap-Superuser-Lage wie produktiv (Regel 15 — daran ist die
erste `G-025`-Probe gescheitert und hat Grün für etwas Unmögliches gemeldet).
Angewendet werden dieselben sechs Migrationen wie produktiv (`001`–`003`,
`005`–`007`), danach `009`. `004` und `008` bleiben außen vor.

`postgres-init/` und `postgres-tests/` sind schreibgeschützt aus dem
deployten Stand gemountet. Aufgeräumt wird gezielt mit `docker rm -f`, nie mit
einem `prune` (`G-038`); nachgesehen: kein Container blieb zurück.

## Messwerte

```
=== G-045 Eigentuemertrennung, Wegwerf-Container ===

  Ausgangsstand                                          6 Migrationen angewendet
  SECURITY DEFINER beim Superuser, vorher                12
  009 angewendet                                         ja
  SECURITY DEFINER beim Superuser, nachher               0
  Relationen im Besitz von workforce_owner               0
  Kanal und Credential vorbereitet                       ok
  bus_send_message als workforce_api                     ok
  bus_events vorher/nachher                              68 -> 69
  Eventzuwachs                                           1
  Audit-Event mit Request-Id, Akteur, Typ und Operation  1
  public-USAGE ueber PUBLIC (Voreinstellung)             t
  direkte Schema-Grants ausserhalb workforce             0
  Trigger abschaltbar                                    NEIN - abgewiesen mit SQLSTATE 42501
  Abnahmetest 009                                        ok

RESULT: PASS
```

## Was damit belegt ist — und was nicht

**Belegt:**

1. **Migration `009` läuft durch**, auf einer Instanz mit der Rollenlage der
   Produktion. Damit ist auch belegt, dass `to_regprocedure()` alle zwölf
   Signaturen in der Schreibweise der Quelle auflöst — `timestamptz`
   eingeschlossen — und dass `oid[]::regprocedure[]` trägt. Beides stand bis
   heute als ungeprüfte Annahme da.
2. **Der Eigentumswechsel wirkt:** SECURITY-DEFINER-Funktionen beim Superuser
   `12 → 0`, und `workforce_owner` besitzt **keine** Relation.
3. **Die Allowlist reicht auf dem echten Pfad.** `bus_send_message` läuft als
   `workforce_api` durch und gibt die Nachrichten-Id zurück. Das ist der Punkt,
   den `SV-2026-09-03-02` verlangt hat: Der teuerste Ausgang einer
   Rechtemigration ist eine zu **enge** Allowlist, und der zeigt sich nur dort,
   wo die Funktion wirklich läuft.
4. **Der Audit-Trigger feuert unter dem neuen Eigentümer.** Genau ein Ereignis,
   gebunden an Request-Id, Akteur, `MESSAGE`, `INSERT` und `record_key` — nicht
   an einen Zählerstand. Damit trägt die PostgreSQL-Dokumentation, auf die sich
   `009` Abschnitt 3b beruft: `EXECUTE` auf eine Triggerfunktion wird beim
   **Anlegen** geprüft, nicht beim Auslösen. Das vorsichtshalber erteilte
   `GRANT EXECUTE` wäre wirklich überflüssig gewesen.
5. **Identity-Spalten brauchen kein Sequenzrecht.** `bus_events.event_id` ist
   `GENERATED ALWAYS AS IDENTITY`, und der `INSERT` ging durch, obwohl `009`
   **keine** Sequenzrechte erteilt. Das beantwortet die offene Frage aus `009`
   Abschnitt 3c — die PostgreSQL-Dokumentation zu `CREATE TABLE` sagt dazu
   nichts, deshalb stand sie als „nicht belegt, sondern gemessen" dort.
6. **`42501` ist die richtige SQLSTATE.** Das Abschalten des Audit-Triggers
   wird abgewiesen, und zwar mit genau der Kennung, an die der Negativtest
   gebunden ist. Ein beliebiger Prozessfehler hätte `unbestimmt` ergeben.
7. **Die `G-074`-Gegenprobe, beide Hälften.**
   `has_schema_privilege('workforce_owner','public','USAGE')` meldet `t` — die
   PUBLIC-Voreinstellung existiert wirklich, mein erster Abnahmetest wäre also
   auf jeder frischen Instanz falsch rot geworden. Und direkte Schema-Grants
   außerhalb von `workforce`: `0`.
8. **Der Abnahmetest `009` besteht**, mit Exitcode 0 **und** seinem
   Schlussmarker (`G-076`).

**Nicht belegt:**

- **Nichts über die Produktion.** `009` ist dort nicht angewendet, der Kanal
  steht auf `DISABLED`, `workforce_owner` existiert nicht. Diese Probe sagt,
  dass die Migration auf einer nachgebauten Instanz funktioniert — nicht, dass
  sie freigegeben ist.
- **Kein Rückbau.** Es gibt keine Migration `010` (`SV-2026-09-03-04`).
  Solange die fehlt, ist `009` nicht freigabereif, unabhängig von diesem
  Ergebnis.
- **Kein Review.** Gerd ist bis zum 2026-09-07 nicht verfügbar. Die sechs
  Befunde des Vertretungsreviews sind behoben, aber die Korrekturen selbst hat
  niemand außer mir gelesen.
- **Ein Lauf, kein Dauerbetrieb.** Die Probe zeigt einen Durchlauf mit einer
  Nachricht. Last, Nebenläufigkeit und die übrigen elf Funktionen sind nicht
  gemessen.

## Ein Fehlschlag auf dem Weg dorthin

Der erste Lauf endete mit `RESULT: FAIL — Eventzuwachs: '3' statt '1'`.

Die Ursache lag bei mir, nicht am System: Die Zählung von `bus_events` stand
**vor** dem Prepare, und der schreibt selbst zwei Auditzeilen — Kanal auf
`TESTING` und das angelegte Credential. Der Erwartungswert `1` stammte noch aus
der Zeit, als der einzige Schreibvorgang ein rohes `UPDATE` war.

Das ist keine Randnotiz, sondern der Beleg, dass das Urteil aus `G-070` tut,
was es soll: Es wurde **rot statt still**, nannte die Zusicherung beim Namen und
nannte Soll und Ist. Die gebundene Abfrage stand im selben Lauf schon auf `1` —
die grobe Zählung war die schwächere Messung und die falsch spezifizierte.
Behoben, indem der Zähler hinter den Prepare gezogen wurde: Gemessen wird der
Aufruf, nicht seine Voraussetzung.
