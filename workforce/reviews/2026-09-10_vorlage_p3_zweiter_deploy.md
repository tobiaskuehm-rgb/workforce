# Vorlage P-3, Klasse Produktives: zweiter Deploy vor Montag, 2026-09-14

Karl, COO auf Probe, 2026-09-10. Sofort und nicht Donnerstag, weil Produktives.

**Sachverhalt.** Der Deploy von heute Vormittag (`35e7ae3`) lief gegen ein rotes Gate: Gerd
hatte am 2026-09-09 `G-112` (Absturz zwischen Marke und Nachricht lässt einen Termin stumm
entfallen) und `G-113` (verpasster Termin könnte doppelt auditiert werden) eingetragen; ich
habe die Befunddatei vor dem Deploy nicht neu gelesen, und meine Vorlage P-2 nannte beide
nicht. Das ist `G-114`, mein Fehler, Regel 71. Kein Schaden: Der Lauf von heute ist
vollständig, die Donnerstagsnachricht ist zugestellt. Gerd hat nach dem Lauf zwei weitere
Punkte gestellt: `G-115` (Rechte von Hand gesetzt, in keiner Datei, `verify` sieht den Ordner
nicht) und `G-116` (der Deploy misst nicht, was er ausrollt). Alle vier sind seit heute
behoben, 67 Tests, jede Korrektur ohne Fix rot geprüft; Gerds Nachcheck läuft.

**Offen im ausgerollten Stand:** `G-112`, `G-113` (Code), `G-115`, `G-116` (Skript). Der
nächste Termin ist Montag 06:00 UTC; ohne zweiten Deploy läuft er mit der `G-112`-Lücke.

**Optionen.** (a) Zweiter Deploy nach Gerds Nachcheck, vor Montag; Nutzen: Montag läuft ohne
bekannte Lücke, das Skript setzt und misst Rechte und Prüfsummen erstmals selbst; Risiko: ein
Neustart, und der neue Rechte-Schritt könnte an einem ungemessenen DSM-Detail scheitern, dann
bricht das Skript vor `up` ab und der alte Container läuft weiter; Aufwand: eine Stunde.
(b) Montag mit der Lücke laufen lassen, Deploy am Donnerstag; Nutzen: kein Fenster am Freitag;
Risiko: ein Absturz zwischen zwei Anweisungen am Montagmorgen ließe die Wochenlage stumm
entfallen, Wahrscheinlichkeit gering, aber Invariante 5 verletzt; Aufwand: keiner.
(c) Zeitplan bis zum Deploy per `/stop` aus; Nutzen: keine Lücke im Betrieb; Risiko: auch der
Bot antwortet nicht; Aufwand: zwei Nachrichten.

**Empfehlung:** (a).

**Satz fürs Log:** Klasse Produktives: Der CEO gibt den zweiten Deploy des Neubaus vor dem
2026-09-14 frei; Gerd hat `6cda0c5` nachgeprüft und freigegeben; offen danach: `G-117` (ACL und
zweites Secret in der Rückmessung), `G-118` (Prüfsummen auch für `skills/`, Unerwartetes melden), beide ohne Deploy-Sperre.

Nächster Schritt: Der CEO entscheidet P-3; Owner Tobias.

## Nachtrag: Gerds Nachcheck liegt vor

`6cda0c5` ist freigegeben. Der Logsatz oben ist korrigiert: „offen danach: keine" war falsch, Gerd hat `G-117` und `G-118` gestellt, beide ohne Sperre. Ein Ja des CEO gilt damit für den Stand mit genau diesen zwei offenen Punkten.
