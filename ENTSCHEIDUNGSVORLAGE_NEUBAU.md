# Entscheidungsvorlage: PostgreSQL-System weiterführen oder SQLite-Neubau

**Status:** Vorlage für eine ausdrückliche CEO-Entscheidung, offenes Gate. Im maßgeblichen
Decision Log ist `DEC-037` der jüngste Eintrag; `PEO-007` und `HO-027` sind offen. Diese Datei
erzeugt keine Nummer (`G-006`). **Bis zur Entscheidung: kein NAS-Lauf, kein Neubau, keine
Änderung am Prototyp, kein weiterer Prüfzyklus.**
**Erstellt:** 2026-09-03 von Claude Code auf Verlangen von Gerd. Messbasis: Stand `781cc84`.

## Die Frage

Wird das bestehende System — PostgreSQL 17, FastAPI-Bus, drei Laufzeitpakete, Compose auf
der NAS — weitergeführt und in Phase 5 gebracht? Oder wird es als Orakel eingefroren und durch
einen Neubau ersetzt — ein Python-Prozess, eine SQLite-Datei, ein Container, nach
`INVARIANTEN.md`?

## Ausgangslage, gemessen am Stand `781cc84`

| | |
|---|---|
| Versionierte Dateien | 246 |
| Produktcode / Testcode Python | 8.900 / 13.800 Zeilen, 829 Testfunktionen |
| SQL | 10.500 Zeilen, 10 Migrationen |
| Dokumentation | 14.300 Zeilen, 49 Markdown-Dateien, 56 Regeln |
| Compose-Dateien / Shell-Skripte | 33 / 25 |
| Befunde | 91 `G-`, 8 `SV-`, 9 `GP-` |
| Echte Modellantworten | 0 |
| Was je ein Mensch benutzt hat | die Chat-Schleife, einmal, mit Echo |

## Option A — Weiterführen

**Nutzen.** Läuft auf der NAS, Kanal `DISABLED`. Zwanzig Prüfrunden bestanden, das technische
Vorgate ist beendet, der isolierte 009/010-Lauf ist von Gerd freigegeben. Der Bus ist ein
HTTP-Dienst, den Menschen und fremde Agenten ansprechen können. Nichts wird neu geschrieben.

**Risiken.** Drei Viertel der Masse sind nicht das Produkt; jede Änderung berührt sechs bis
acht Dateien. Die Prüfschleife hat in vier Tagen 108 Befunde und null Modellantworten
erzeugt. Drei Zustandsspeicher bleiben, damit bleibt die Klasse der Claim- und
Dublettenbefunde möglich. Der Eigentümerwechsel `009` ist noch nicht produktiv.

**Wiederverwendung.** Alles.

**Zeit und Kosten.** Bis zur ersten Modellantwort: 009/010-Lauf ein Abend, Phase-5-Fenster
mit Echo ein Abend, danach Modell-`DEC` und ein Lauf — bei zügigen Freigaben eine Woche.
`HO-027` danach ein bis zwei Tage Bau plus Prüfrunden. Laufend: die Prüfschleife, bisher etwa
eine Runde pro Tag. Abos und Modellkosten wie unten.

**Datenmigration.** Keine.

**Rückfallweg.** Der jetzige Stand; Rückfallmarken und Sicherungen existieren.

## Option B — Neubau

**Nutzen.** Ein Zustand statt drei; die Befundklassen „verteilter Zustand", „Konfiguration
an fünf Orten" und „Superuser als Eigentümer" sind bauartbedingt unmöglich. Geschätzt ein
Zehntel der Masse: 5.000 bis 6.000 Zeilen, ein Container, eine Compose-Datei, drei Dokumente.
Läuft auf dem Mac wie auf der NAS. Erste Modellantwort Ende der ersten Woche. Lokales Modell
über Ollama für Vorsortierung und Tests, Datengrenze `FULL` nur dort.

**Risiken.** Ein zweites System, bevor das erste je mit Modell lief. Neuer Code hat neue
Fehler. Der Bus ist kein HTTP-Dienst mehr für fremde Clients. SQLite hat einen Schreiber; das
passt zu einem Prozess und zu nichts anderem. **Der größte:** Die Masse kam mehr aus dem
Prozess als aus der Technik. Ohne Review nach dem Lauf statt vor dem Lauf erzeugt der Neubau
dieselbe Masse noch einmal.

**Wiederverwendung.** Rund 40 Prozent des Produktcodes — Datengrenze, Budget, Allowlist,
Provider, Connector-Kern —, ein Drittel der Tests, alle Befunde als Spezifikation, das
Bedrohungsmodell, das Betriebswissen zur NAS.

**Zeit und Kosten.** Drei Meilensteine, zwei bis drei Wochen bis zur Parität mit dem, was
heute benutzt wird; Private Office danach als vierter Meilenstein. Abos unverändert,
Modellkosten identisch zu A.

**Datenmigration.** Registry, Routen und Policies werden als eine Konfigurationsdatei
exportiert. Das Audit wird **nicht** migriert: Der PostgreSQL-Dump wird als versiegeltes
Archiv mit Prüfsumme abgelegt, die neue Hash-Kette beginnt mit einem Verweis darauf.
Nutzerinhalte gibt es keine — das System hat nie produktiv geantwortet.

**Rückfallweg.** Der Prototyp bleibt eingefroren und deployt. Der Neubau bekommt im Bau einen
eigenen Telegram-Bot, weil ein Bot-Token nur einen Abfrager verträgt. Umschalten heißt: der
CEO schreibt dem neuen Bot. Rückfall heißt: dem alten. Beide Systeme stehen nebeneinander,
solange kein Kanal offen ist, den beide bedienen.

## Was beide Optionen teilen

Modellkosten hängen an der Nutzung, nicht an der Bauform: mit Opus 5 unter vier Cent je
Antwort, bei zwanzig Antworten am Tag rund zwanzig Dollar im Monat. Telegram bleibt in
beiden ein dünner Adapter. `INVARIANTEN.md` gilt für beide — in A als Maßstab für Phase 5,
in B als Maßstab für jeden Meilenstein.

## Empfehlung

**B, unter einer Bedingung:** Der Review wechselt auf „nach dem Lauf gegen die Seite".
Ohne diese Bedingung ist **A** die günstigere Wahl, weil sie näher am ersten echten Lauf ist
und der Neubau die Schleife nur verlagern würde.

## Was der CEO entscheidet

Ein Satz je Punkt, im Decision Log, mit Nummer:

1. **Bauform:** A weiterführen **oder** B Neubau nach `INVARIANTEN.md`.
2. **Isolierter 009/010-Wegwerflauf:** durchführen (A) **oder** entfallen (B).
3. **`HO-027`:** weiterbauen im Prototyp (A) **oder** pausieren bis Meilenstein 4 (B).
4. **Reviewmodus:** nach dem Lauf gegen die Seite — gilt für A wie B.
