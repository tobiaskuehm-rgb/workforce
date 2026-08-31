# Nachweis: ENG-008 Core-Roundtrip

**Datum:** 2026-08-31
**Quellreferenz:** `DEC-027/ENG-008`, Lauf-ID `20260831CORE4`, Suffix `20260831-CORE1`
**Beteiligte:** Karl (`SAO-001`), Gerd (`AI-ENG-001`), Anastasia (`PEO-001`)
**Ergebnis:** **`BUS LIFECYCLE PASS`** — 20 von 20 Schritten, Audit des Erfolgspfads 10 von 10
**Gate-Einstufung:** **`CORE ITERATE`** — siehe Korrektur unten
**Git-Commit des ausgeführten Stands:** siehe Abschnitt „Deployter Stand"

> **Korrektur, nachgetragen 2026-08-31 (Review-Befunde G-015 und G-018).**
> Dieser Nachweis war ursprünglich mit **`CORE PASS`** überschrieben. **Das war
> zu stark, und die Einstufung ist zurückgenommen.**
>
> Was der Lauf belegt: den **Bus-Lebenszyklus** — Task- und Handoff-Semantik,
> Berechtigungen, Reihenfolge, Idempotenz, Fehlerzustand des Busses. Das ist
> reale Evidenz und bleibt gültig.
>
> Was er **nicht** belegt: eine arbeitende Employee Runtime. `core_roundtrip.py`
> steuert drei `BusClient`-Instanzen mit fest verdrahteten Identitäten und
> Texten. Es verwendet weder `agent_worker.py` noch das Provider-Routing, noch
> `state_store.py`, Claim, Lease, Worker-Retry oder einen Worker-Fehlerzustand.
> `ENG-008` verlangt genau das, und `DEC-027` sagt ausdrücklich, dass der
> Roundtrip diesen Nachweis nicht ersetzt.
>
> Auch die Audit-Rekonstruktion ist enger als behauptet: `bus_events` enthält
> nur erfolgreiche Vorgänge. Abgewiesene Transaktionen hinterlassen dort keine
> Zeile, also rekonstruiert die Abfrage weder `DONE` ohne Evidenz noch die
> beiden Berechtigungs-Ablehnungen. „Audit 10/10" gilt für den Erfolgspfad.
>
> **Gate-Einstufung ist damit `CORE ITERATE`, nicht `CORE PASS`.** Der Text
> darunter bleibt unverändert, damit nachvollziehbar bleibt, was ursprünglich
> behauptet wurde.

Kein Modell beteiligt: `ENG-008` untersagt einen externen kostenpflichtigen Dienst, und das Gate prüft die Runtime, nicht Antwortqualität.

## Warum der bisherige Bus-Realtest nicht genügte

`DEC-027` ist ausdrücklich: frühere Bus-Abnahmen „dürfen als Evidenz wiederverwendet werden, ersetzen aber nicht den neuen Core-Roundtrip mit Gerd, Karl und Anastasia". Der Realtest vom selben Tag lief Karl ↔ Thorsten und deckt weder die Besetzung noch den Task-/Handoff-Lebenszyklus ab.

## Ausgangslage

| Prüfung | Ergebnis |
|---|---|
| Kanal | `DISABLED` |
| Aktive Credentials | `0` |
| Routen `TASK` Karl→Gerd, `HANDOFF` Gerd→Anastasia | vorhanden, `ACTIVE` |
| Lokale Tests | 89 Agenten-Tests grün |

Das Prepare-Skript prüft beide Routen vorab, damit ein Lauf nicht auf halber Strecke abbricht und einen offenen Task hinterlässt.

## Ablauf

```text
 1. channel_open                          TESTING
 2. karl_creates_task                     PENDING
 3. task_replay_is_idempotent
 4. gerd_sees_task
 5. karl_opens_task                       OPEN
 6. gerd_starts_work                      IN_PROGRESS
 7. gerd_reports_result                   MSG-BBD9E616…
 8. gerd_creates_handoff                  PENDING
 9. gerd_opens_handoff                    OPEN
10. anastasia_sees_handoff
11. anastasia_accepts_handoff             ACCEPTED
12. anastasia_reports_result              MSG-FE6A4C54…
13. gerd_moves_task_review                REVIEW
14. done_without_evidence_refused         BUS_TASK_COMPLETION_EVIDENCE_REQUIRED
15. karl_closes_task                      DONE
16. handoff_for_rejection_created
17. handoff_for_rejection_opened
18. anastasia_rejects_handoff             REJECTED
19. third_party_cannot_decide_handoff     BUS_HANDOFF_TRANSITION_DENIED
20. non_owner_cannot_transition_task      BUS_TASK_TRANSITION_DENIED
```

Damit sind alle vom Gate verlangten Bestandteile abgedeckt: der Positivpfad `Task → A → Ergebnis → Handoff → B → ACCEPTED → Bearbeitung → Ergebnis → DONE`, dazu `REJECTED`, fehlende Permission (zweimal, an unterschiedlichen Stellen), Fehlerzustand (`DONE` ohne Evidenz) und Idempotenz.

## Audit-Rekonstruktion

Der eigentliche Prüfpunkt, und der Teil, den ich zunächst falsch als nachrangig eingestuft hatte. `core_audit.sql` baut den Lauf **allein aus `workforce.bus_events`** wieder auf — ohne stdout, ohne Evidenzdatei, nach Containerrückbau. 13 Ereignisse:

| # | Akteur | Typ | Phase | Status |
|--:|---|---|---|---|
| 1 | `SAO-001` | TASK | `TASK-CREATE` | `PENDING` |
| 2 | `SAO-001` | TASK | `TASK-OPEN` | `OPEN` |
| 3 | `AI-ENG-001` | TASK | `TASK-INPROGRESS` | `IN_PROGRESS` |
| 4 | `AI-ENG-001` | MESSAGE | `GERD-RESULT` | `DELIVERED` |
| 5 | `AI-ENG-001` | HANDOFF | `HANDOFF-CREATE` | `PENDING` |
| 6 | `AI-ENG-001` | HANDOFF | `HANDOFF-OPEN` | `OPEN` |
| 7 | `PEO-001` | HANDOFF | `HANDOFF-ACCEPT` | `ACCEPTED` |
| 8 | `PEO-001` | MESSAGE | `PEO-RESULT` | `DELIVERED` |
| 9 | `AI-ENG-001` | TASK | `TASK-REVIEW` | `REVIEW` |
| 10 | `SAO-001` | TASK | `TASK-DONE` | `DONE` |
| 11–13 | | HANDOFF | Ablehnungspfad | `PENDING → OPEN → REJECTED` |

Zehn Prüfungen, alle erfüllt — darunter zwei Reihenfolgeprüfungen: Handoff nach Task, Abschluss nach Annahme. Möglich wird das dadurch, dass jeder Schreibvorgang eine Request-ID der Form `CORE-<lauf>-<phase>` trägt.

Endzustand: Task `DONE` mit Evidenz, ein Handoff `ACCEPTED`, einer `REJECTED`.

## Drei Korrekturen unterwegs

Der Lauf brauchte vier Anläufe. Jeder Fehlschlag lag an einer falschen Annahme **meinerseits** über die Bus-Regeln, nicht an einem Fehler im Bus — und die lokale Attrappe hatte alle drei mitgemacht, weil ich sie nach meiner Annahme gebaut hatte statt nach dem SQL.

**1. `PENDING → OPEN` beim Task gehört Karl, nicht dem Owner.** `bus_transition_task` erlaubt diesen Übergang ausschließlich `SAO-001`, und nur für die Owner `AI-ENG-001`, `RAS-001`, `PEO-001`. Der Owner kann seinen eigenen Task nicht aus `PENDING` holen — die Koordination bleibt bei Karl. Ich hatte Gerd das machen lassen.

**2. Auch ein Handoff wird erst vom Absender geöffnet.** `bus_transition_handoff`: Der Sender stellt `PENDING → OPEN`, erst dann darf der Empfänger `ACCEPTED`/`REJECTED` setzen. Der Absender schließt seine Übergabe ab, dann entscheidet die Gegenseite. Ich hatte Anastasia direkt annehmen lassen.

**3. Zwei Erwartungen im Test waren selbst falsch.** Der Idempotenz-Test wiederholte die Task-Anlage, *nachdem* der Task auf `DONE` stand — der Bus vergleicht den gespeicherten Datensatz gegen die Wiederholung, also ist das eine veraltete Anfrage und keine Dublette; `409` war die richtige Antwort. Und der Negativfall „Dritter entscheidet Handoff" verlangte `ACCEPTED` auf einen bereits akzeptierten Handoff, worauf der Bus mit Idempotenzkonflikt antwortet, **bevor** er Rechte prüft. Ein Negativfall muss die Prüfung erreichen, die er zu testen behauptet.

Alle drei Regeln sind jetzt in der Testattrappe nachgebildet, damit die lokale Suite dieselben Fehler künftig fängt.

## Rückbau

```text
 PASS | DISABLED | AI-ENG-001 | REVOKED | 0
 PASS | DISABLED | PEO-001    | REVOKED | 0
 PASS | DISABLED | SAO-001    | REVOKED | 0
```

Alle drei Token-Dateien gelöscht, Compose-Projekte und Testnetz entfernt, Kanal `DISABLED`, 0 aktive Credentials. Task-, Handoff-, Nachrichten- und Auditdatensätze bleiben append-only erhalten — sie sind der Nachweis.

## Deployter Stand

Der Lauf verwendete den Repository-Stand nach Commit `3686c76` plus die drei oben beschriebenen Korrekturen an `core_roundtrip.py`. Die Korrekturen sind im Anschluss committet; der exakte Hash steht in der Commit-Historie zu diesem Nachweis.

## Nicht abgedeckt

- ~~**Persistenz über Neustart** für den Core-Roundtrip~~ — **nachgetragen am selben Tag, siehe unten.**
- **Leftover aus Fehlversuchen:** Die Läufe `20260831CORE1` bis `CORE3` haben Tasks und Handoffs in Zwischenzuständen hinterlassen (`PENDING`, `IN_PROGRESS`, `ACCEPTED`). Sie sind Testartefakte, keine offene Arbeit, aber sie stehen in der Datenbank.
- **Kein Modellbetrieb.** Das war weder Ziel noch erlaubt.

## Nachtrag: Persistenz über Neustart

Beim Abschluss oben war der Runner zustandslos und startete bei einem Abbruch von vorn — womit er am ersten bereits erledigten Schritt in einen Idempotenzkonflikt gelaufen wäre. Das ist nachgeholt.

Der Runner braucht weiterhin keinen eigenen Zustand: Jede ID leitet sich aus der Lauf-ID ab, ein zweiter Prozess adressiert also dieselben Datensätze. Was fehlte, war die **Erkennung** — jeder Schritt nahm an, er müsse etwas tun. Jetzt prüfen `ensure_task_status()` und `ensure_handoff_status()` zuerst den Ist-Zustand und melden bereits Erreichtes als `resumed`. Dasselbe gilt für das Anlegen von Task und Handoffs.

Der Ablehnungspfad brauchte eine eigene Behandlung: `REJECTED` liegt außerhalb der Reihenfolge `PENDING → OPEN → ACCEPTED`, und ein abgelehnter Handoff lässt sich nicht wieder öffnen.

**Nachweis:** `test_resumes_after_a_crash_at_every_write` lässt den Prozess an **jeder der elf Schreibpositionen** sterben und verlangt, dass der Folgelauf sauber zu Ende kommt und der Task auf `DONE` steht. Dazu Prüfungen gegen Dubletten und darauf, dass wiederaufgesetzte Schritte im Transcript als solche markiert sind — sonst sähe ein Wiederholungslauf in der Evidenz wie frische Arbeit aus.

Auch hier hat die Testattrappe einen eigenen Fehler offengelegt: Sie vergab bei jedem `send_message` eine neue ID und verbarg damit genau die Duplizierung, die ein wiederaufgesetzter Lauf nicht verursachen darf. Der echte Bus leitet die `message_id` aus Token und Idempotenzschlüssel ab; das ist jetzt nachgebildet.

Damit ist der Nachweis **lokal** vollständig. Ein Wiederaufsetzen gegen die echte NAS ist noch nicht gelaufen — dafür bräuchte es erneut das Firewall-Fenster.
