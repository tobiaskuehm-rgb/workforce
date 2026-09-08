# Zugänge: wo sie liegen und was sie dürfen

Gebaut am 08.09.2026 auf Entscheidung von Tobias. Die Begründung steht in `konzepte/2026-09-08_Sicherheitsmodell-Zugaenge.md`; hier steht, wie es benutzt wird.

## Wo die Zugangsdaten liegen

**Im macOS-Schlüsselbund. Nirgendwo sonst.** Nicht in einer Datei, nicht im Repo, nicht in der Ablage, nicht in einem Bericht, nicht in einer Nachricht.

Angelegt werden sie **von Tobias selbst**, nie von Marlene:

```
security add-generic-password -a "<benutzername>" -s "marlene-swe-erfurt" -w
```

Der Befehl fragt das Kennwort danach verdeckt ab; es steht damit nicht in der Befehlszeile und nicht im Verlauf der Shell. Marlene tippt es nie ein und bekommt es nie zu sehen: `marlene_tresor.py` reicht den Wert innerhalb des Programms weiter, druckt ihn nicht und schreibt ihn in kein Protokoll.

**Zwei Schlüsselbunde, nach Risiko getrennt:**

| Klasse | Schlüsselbund | Warum |
|---|---|---|
| C, Versorger und Alltag | Anmeldeschlüsselbund | offen, solange Tobias angemeldet ist; der Nachtlauf kommt daran |
| B, Gesundheit und Verträge | eigener Schlüsselbund `marlene`, gesperrt | wird je Lauf entsperrt; ohne Tobias läuft nichts |
| A, Geld und Identität | gar keiner | Lesezugang oder Vollmacht mit eigenen Zugangsdaten, kein geteiltes Passwort |

Ein Eintrag wird in der Schlüsselbundverwaltung einzeln gelöscht; das ist der Widerruf, und er wirkt sofort.

## Was ein Konto darf

`marlene_konten.json` ist das Register. Es enthält **keine Zugangsdaten**, nur den Namen des Schlüsselbund-Eintrags, die Klasse und die Liste erlaubter Abläufe. Fail closed: Ein Konto, das nicht darin steht, existiert für Marlene nicht, und eine Aktion, die nicht auf seiner Liste steht, findet nicht statt.

```
python3 marlene_tresor.py status                        was ist hinterlegt
python3 marlene_tresor.py pruefen <konto> <aktion>      greift die Schranke
```

## Die vier Schranken

Sie stehen in `marlene_schranken.py` als Funktionen, nicht als Vorsatz.

1. **IBAN-Allowlist.** Ein Zahlungsziel muss auf der Liste stehen. Die Liste speichert **nicht die IBAN**, sondern ihren SHA-256 mit einer Bezeichnung; damit lässt sich prüfen, ob eine Kontonummer bekannt ist, ohne dass irgendwo eine steht. Eintrag erzeugen: `python3 marlene_schranken.py fingerabdruck`.
2. **Aktions-Allowlist.** Je Konto benannte Abläufe, kein freies Klicken.
3. **Sperre für Unumkehrbares.** Kündigen, widerrufen, abschließen, löschen, zahlen, überweisen, Adresse, Bankverbindung, Stammdaten, Tarif, Vollmacht. Diese Sperre **schlägt die Kontoliste**: Auch wenn jemand `kuendigen` bei einem Konto einträgt, bleibt es gesperrt. Ein Test hält das fest.
4. **Empfängerbindung.** Jeder Empfänger kommt aus dem Vorgangsdatensatz, nie aus einem gelesenen Dokument.

## Der zweite Faktor

Bleibt bei Tobias, ohne Ausnahme. Ein zweiter Faktor, den zwei haben, ist keiner, und im Streitfall ist er der einzige Beleg dafür, dass er es nicht war. Ein Ablauf, der an einer Zwei-Faktor-Abfrage ankommt, hält dort an und meldet sich.

## Das Protokoll

Jeder Zugriff und jeder abgelehnte Versuch geht als Zeile nach `_Marlene/protokoll/zugriffe.jsonl`: Zeit, Konto, Aktion, Zweck, Ergebnis. Der Wert steht dort nie. Das Protokoll ist nicht für Marlene, sondern für Tobias: Damit ist hinterher unterscheidbar, was er war und was sie war.

## Die Probe

Erstes Konto ist **SWE Erfurt** (Wasser, Berggasse 1), Klasse C. Erlaubt sind anmelden, Postbox lesen, Dokument laden, Abschlag und Zählerstand ansehen, abmelden. Gesperrt ist alles andere, auch das Melden eines Zählerstands, weil das eine Erklärung gegenüber dem Versorger wäre.

Der erste Auftrag ist zugleich ein echter: Für die Betriebskostenabrechnung fehlt die Wasserrechnung für den Zeitraum August bis Dezember 2025.
