# Nachweis: Contract-Test der Bus-Regeln und Aufräumen der Altlasten

**Datum:** 2026-08-31
**Quellreferenz:** `DEC-027/ENG-008`, Suffix `20260831-CONTRACT`
**Ergebnis:** Contract-Test **PASS** (107 von 107 Prüfungen), Aufräumen **PASS** (4 von 4 Datensätzen)

Zwei Vorgänge in einem Fenster. Kein Modell beteiligt.

---

## Nachtrag 2026-08-31, nach Prüfbefund `G-014`

**Die Zahl 107/107 trägt weniger, als sie klingt.** Der hier protokollierte Lauf hat gezählt, ob überhaupt ein `BusError` zurückkam — nicht, *welcher*. Ein `401`, ein `500` oder ein geschlossener Kanal hätte in dieser Fassung ebenfalls als korrekte Ablehnung gezählt. Und die 107 Prüfungen waren fast ausschließlich Ablehnungen: von den erlaubten Übergängen lief nur der Durchlauf selbst, vier von siebzehn.

Was hier steht, bleibt als Aufzeichnung des damaligen Laufs stehen. Es belegt eine große **einseitige** Ablehnungsmatrix, keine vollständige Übereinstimmung.

Die überarbeitete Fassung von `contract_test.py` prüft je Ablehnung Statuscode **und** Fehlerkennung, führt jedes erlaubte Übergangspaar mindestens einmal positiv aus (17/17 Task, 5/5 Handoff) und weist `DENY`, `ALLOW` und `WRONG_REASON` getrennt aus. Sie ist **noch nicht gegen den echten Bus gelaufen** — das braucht ein Fenster mit Freigabe. Bis dahin gilt für die Abschrift: gegen die Attrappe geprüft, gegen den Bus offen.

---

## Teil 1 — Contract-Test

### Warum

`workforce-agent/bus_rules.py` hält die Übergangsregeln des Busses als Abschrift aus `002_workforce_bus.sql`. Eine Abschrift kann veralten: Ändert sich die Migration, laufen die lokalen Tests weiter grün und liegen falsch. Nur der laufende Bus kann entscheiden, ob die Abschrift stimmt.

Der Anlass war konkret. Der Core-Roundtrip brauchte vier Anläufe, und jeder Fehlschlag lag an einer Stelle, an der die Testattrappe der Wirklichkeit widersprach — sie war nach meiner Annahme gebaut, hat mir die Annahme bestätigt, und der echte Bus hat abgelehnt.

### Zuschnitt

Eine naive Matrixprüfung bräuchte einen Datensatz je Zustand und ließe eine Spur abgebrochener Records zurück — die sich **nicht mehr aufräumen ließe**, weil der Bus `CANCELLED` nur aus `PENDING` erlaubt.

Der Test nutzt stattdessen aus, dass eine **Ablehnung nichts verändert**: ein Task und ein Handoff, durch ihre Zustände geführt, und an jedem Zustand jeder Übergang geprüft, den die Tabelle als abgelehnt vorhersagt. Die erlaubten Übergänge sind der Durchlauf selbst.

### Ergebnis

```json
{"checks_total": 107, "checks_failed": 0, "divergences": [], "result": "PASS"}
```

**107 Prüfungen bei zwei Datensätzen**, null Abweichungen. Die Abschrift in `bus_rules.py` stimmt mit dem Verhalten des laufenden Busses überein — einschließlich der drei Regeln, die jeweils einen Roundtrip-Anlauf gekostet hatten:

- `PENDING → OPEN` beim Task nur durch `SAO-001`, nicht durch den Owner
- `PENDING → OPEN` beim Handoff nur durch den Absender, nicht durch den Empfänger
- derselbe Status wird als Idempotenzkonflikt beantwortet, bevor Rechte geprüft werden

Endzustand der Prüfdatensätze: Task `DONE`, Handoff `ACCEPTED`.

---

## Teil 2 — Altlasten aus den Fehlversuchen

### Ausgangslage

Die Roundtrip-Anläufe `CORE1` und `CORE2` hatten je einen Task auf `IN_PROGRESS` und einen Handoff auf `PENDING` hinterlassen. Datensätze, die wie offene Arbeit aussehen, aber keine sind.

### Warum nicht per SQL

Der naheliegende Weg wäre ein `UPDATE` direkt gegen die Datenbank gewesen. Abgelehnt, und der Grund gehört festgehalten: Der Bus erlaubt `CANCELLED` **nur aus `PENDING`**, damit abgebrochene Arbeit nicht stillschweigend verschwinden kann. Diese Sperre ist der Sinn der Sache, kein Hindernis — sie mit SQL zu umgehen hätte genau die Kontrollen untergraben, die dieses Projekt den ganzen Tag nachgewiesen hat.

### Durchführung

Über die Regeln des Busses selbst:

| Datensatz | Von | Nach | Weg |
|---|---|---|---|
| `HO-CORE-20260831CORE1` | `PENDING` | `CANCELLED` | Absender bricht ab |
| `HO-CORE-20260831CORE2` | `PENDING` | `CANCELLED` | Absender bricht ab |
| `ENG-CORE-20260831CORE1` | `IN_PROGRESS` | `DONE` | Owner → `REVIEW`, Ersteller → `DONE` |
| `ENG-CORE-20260831CORE2` | `IN_PROGRESS` | `DONE` | Owner → `REVIEW`, Ersteller → `DONE` |

Handoffs zuerst: Ein offener Handoff an einem bereits geschlossenen Task sähe seltsamer aus als der Ausgangszustand.

Die Abschluss-Evidenz sagt, was diese Datensätze waren:

> „Abgebrochener Testlauf des Core-Roundtrips vom 2026-08-31. Keine fachliche Arbeit, kein fachliches Ergebnis. Geschlossen, damit der Datensatz nicht als offene Arbeit erscheint."

Ein Aufräumen, das einen abgebrochenen Test als erledigte Arbeit ausgäbe, wäre schlimmer als die Unordnung gewesen.

### Endzustand

```text
 ENG-CONTRACT-20260831CONTRACT1 | DONE
 ENG-CORE-20260831CORE1         | DONE
 ENG-CORE-20260831CORE2         | DONE
 ENG-CORE-20260831CORE3         | DONE
 ENG-CORE-20260831CORE4         | DONE
```

Kein Task des Projekts steht mehr offen.

---

## Ein Fehler unterwegs

Der erste Prepare-Versuch scheiterte an `sed: /run/startup.env: Permission denied` — eine Kollision zweier eigener Korrekturen desselben Tages.

Befund F3 hatte `startup.env` auf `600` für `TOBKUM` gesetzt. Befund G-010 hatte die Einmalcontainer von `env_file` auf einen Mount umgestellt, damit `WORKFORCE_API_KEY` nicht mehr in `docker inspect` steht. Damit wechselte aber, **wer die Datei liest**: vorher der Docker-Daemon als echter Root, danach der Container als Root ohne `CAP_DAC_OVERRIDE` — der an einer `600`-Datei fremden Eigentümers scheitert.

Behoben durch `root:users` mit `660`: Der Container liest sie als Eigentümer, `TOBKUM` über die Gruppe, Dritte gar nicht. Unterm Strich enger als vorher, weil die Datei jetzt Root gehört.

Das ist dieselbe Klasse wie die `cap_drop`-Kette vom Nachmittag: Eine Härtung verschiebt, wer worauf zugreift, und das fällt erst beim nächsten Lauf auf.

## Rückbau

Drei Credentials `REVOKED`, Kanal `DISABLED`, 0 aktive Zugänge, Token-Dateien gelöscht, alle Compose-Projekte und das Testnetz entfernt. Temporäre Firewall-Regel im Anschluss zurückgenommen.
