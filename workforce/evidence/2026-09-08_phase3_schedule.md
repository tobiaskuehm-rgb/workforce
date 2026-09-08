# Nachweis: Phase 3, der Kern meldet sich

**Auftrag:** Masterplan Phase 3, seit dem 3-Loop vom 2026-09-08 nächster Meilenstein vor
Phase 4 (CEO-Entscheidung „kannste alles so umsetzen"). „Zeitplan im Kern … Jede geplante
Nachricht ist ein normaler Ausgang mit Audit, Budget und Kill Switch."

**Umsetzung:** `Config.schedule` — Liste von `ScheduleItem(id, weekday, hour, identity,
prompt)`, validiert beim Start (typfest, `weekday` 1–7, `hour` 0–23, Identität muss existieren,
Route `CEO → identity` muss bereits erlaubt sein — ein Termin erzeugt keine neue Route,
Invariante 3). `App.check_schedule()` legt an fälligen Tagen einen Eingang an
(`derived_id("SCHED", id, tag)`, `update_id=None`, Absender `CEO`, Empfänger die konfigurierte
Identität, Text der `prompt`) und übergibt ihn an denselben Pfad wie eine echte Nachricht:
Datengrenze, Budget, Modellaufruf, Antwort an den Chat. Ein zweiter Aufruf am selben Tag legt
nichts an (`store.message(id)` existiert schon); Wiederaufnahme bei erschöpftem Budget läuft
über den vorhandenen `resume()`-Mechanismus aus `G-097`/`G-100`, ohne eigenen Code.

**Konfiguriert:** Montag 06:00 UTC „Wochenlage", Donnerstag 06:00 UTC „Entscheidungstermin",
beide an Karl (`config.nas.json`) beziehungsweise die Vorgabeidentität
(`config.example.json`). Der Prompt spiegelt Karls Takt aus `skills/ORGANIGRAMM.md`.

**Getestet:** 13 neue Tests (`ScheduleConfigTest`, `ScheduleTest`), Gegenprobe: alle 13 rot
gegen den Stand vor dieser Änderung. 60 Tests insgesamt grün. Zwei nebenbei gefundene und
behobene Lücken in der Wiederaufnahme (`resume()`, `process()`), die vor `G-109` nur mit
echten Telegram-`update_id`s geprüft waren und mit `update_id=None` abgestürzt wären.

**Nicht gemessen:** ein echter Lauf auf der NAS über eine volle Woche; ob die UTC-Uhrzeit
06:00 (8:00 CEST / 7:00 CET) für den CEO praktikabel ist — nachzusehen nach der ersten Woche.
**Deploy steht noch aus**, das ist eine Donnerstagsvorlage.
