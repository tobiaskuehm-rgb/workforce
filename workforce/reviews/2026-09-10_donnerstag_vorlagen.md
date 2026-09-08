# Donnerstagsvorlagen für den 2026-09-10

Karl, COO auf Probe. Gesammelt seit dem 2026-09-08, je Vorlage der Satz fürs Log; der CEO
antwortet mit „ja", „nein" oder einer Option. Alles andere hat der COO unter der Woche im Rahmen
von Budget und Invarianten entschieden und steht in der Montagsübersicht.

## P-2, Klasse Produktives: Deploy von Phase 3 auf die NAS

**Sachverhalt.** Seit `ca1bd20` liegen im Repo: Phase 3 (der Kern meldet sich, Montag und
Donnerstag an Karl), `G-105` (Startzeile mit Commit), `G-107` (Konfigurations-Hash),
`G-102`–`G-104`. Die NAS läuft weiter auf `ca1bd20`; der Zeitplan greift erst nach dem Deploy.
Gerds Nachcheck des Phase-3-Diffs: ⟨Ergebnis wird hier vor Donnerstag ergänzt⟩.

**Optionen.** (a) Deploy über `deploy_nas.sh` aus sauberem Baum, danach `verify` und Gerds
Review nach dem Lauf; Nutzen: erste Montagsnachricht am 2026-09-14, Risiko: ein Neustart des
Bots, Aufwand: eine Stunde. (b) Warten bis Gerd Phase 3 nachgeprüft hat, dann (a); Nutzen:
kein ungeprüfter Stand produktiv, Risiko: Montag ohne Nachricht, Aufwand: keiner. (c) Nicht
deployen, Phase 3 erst mit Phase 4 zusammen; Nutzen: ein Fenster statt zwei, Risiko: das
System meldet sich weitere Wochen nicht, Aufwand: keiner.

**Empfehlung:** (b), und (a) sobald Gerd freigibt.

**Satz fürs Log:** Klasse Produktives: Der CEO gibt den Deploy des Standes mit Phase 3 auf
die NAS frei, sobald Gerd den Diff nachgeprüft hat.

## R-2, Klasse Rechte: Ordnerrechte auf der NAS (`G-108`)

**Sachverhalt.** `/volume1/docker/workforce` und `secrets/` stehen auf `777`, `config.json`
und `deploy_nas.sh` auf `777`. Eine `640`-Secretdatei ist in einem `777`-Ordner ersetzbar,
ohne dass `verify` etwas merkt. Gerd, Review nach dem Deploy, mittel.

**Optionen.** (a) `chmod 750` auf die Ordner, `640` auf Konfiguration, `750` auf das Skript,
Eigentümer bleibt der SSH-Benutzer, Gruppe `10001`; danach `deploy_nas.sh` einmal messen,
weil `tar xzf` in einen `750`-Ordner mit derselben Kennung weiter funktioniert; Nutzen:
Secrets nicht mehr ersetzbar, Risiko: ein Deploy-Schritt scheitert an einem Recht, das der
Test nicht sah, Aufwand: zehn Minuten plus ein Messlauf. (b) Nur `secrets/` auf `750`; Nutzen:
kleinster Eingriff, Risiko: Konfiguration bleibt ersetzbar, Aufwand: eine Minute. (c) So
lassen und in `nas_status`-Art einen Wächter bauen, der `777` meldet; Nutzen: sichtbar,
Risiko: Finden ist nicht Verhindern (Regel 21), Aufwand: eine Stunde.

**Empfehlung:** (a), im selben Fenster wie P-2, weil beides ein NAS-Fenster braucht.

**Satz fürs Log:** Klasse Rechte: Der CEO gibt frei, die Ordner- und Dateirechte unter
`/volume1/docker/workforce` auf `750`/`640` zu setzen und den Deploy danach nachzumessen.

## S-2, Klasse Strategie: die C-Kandidaten

**Sachverhalt.** Der CEO sagt, die Kandidaten seien benannt; im Repo liegt keine Liste,
Thorsten kann nicht laufen. **Satz fürs Log:** Klasse Strategie: Der CEO nennt die drei bis
fünf Kandidaten für Baustein C schriftlich, im Chat oder als Datei, bis zum 2026-09-10.

## Zur Kenntnis, keine Entscheidung

- `G-107` ist über den Hash geschlossen; die Frage, die Konfiguration zu versionieren, ist
  damit vom Tisch, außer der CEO will es.
- Invarianten 4, 7, 13, 15 stehen datiert offen in `INVARIANTEN.md`, je mit dem Meilenstein,
  der sie bringt; Gerd hat die Kennzeichnung noch nicht abgenommen.
- COO-Probezeit, Maß bis 2026-10-02: drei Übersichten, keine Vorlage älter als sieben Tage,
  kein Deploy ohne Nachweis. Stand: eine Übersicht (dieses Dokument zählt nicht), null
  überfällige Vorlagen, ein Deploy mit Nachweis.

Nächster Schritt: Der CEO entscheidet P-2, R-2 und S-2 am 2026-09-10; Owner Tobias.
