# Probezeit-Evidenz — Marlene (POA-001)

Identität: Marlene, `POA-001`, Private Office Assistant. Probezeit seit `DEC-036`.
Fachliche Führung: Anastasia (`PEO-001`). Vorgesetzter: CEO.
Anlass: erster echter Vorgang, abgeschlossen am 2026-09-07 (Entlassungsberichte).
Quellen: `Bericht_2026-09-07_Entlassungsberichte.md`, `ENTSCHEIDUNGEN.md`, `VORGAENGE.md`,
`protokoll/2026-09-07_entlassungsberichte.jsonl` (3 Zeilen, Struktur `zeit, aktion, quelle,
ziel, sha, grund, trocken` — nur Struktur gelesen, keine Inhalte).

## Die vier Trennungen

**Rollenbedarf.** Kein Befund gegen die Rolle. Der Vorgang liegt im beschriebenen Auftrag
(Ablage, Fristen, Vorgänge) und wurde nicht an eine fehlende Rolle delegiert.

**Rollendesign.** Kein Befund. Marlene hat den Auftrag in ihrer eigenen Betriebsart
durchlaufen (Vorschlag → Freigabe → Ausführung → Protokoll) ohne Bruch im Ablauf.

**Technischer Blocker.** Zwei fehlten heute und wurden im Lauf nachgebaut:
1. Ein Lesewerkzeug für PDF-Seiten (`marlene_lesen.js`) — ohne das wäre die Paarung der
   Vorder-/Rückseitendateien nicht seitengenau belegbar gewesen.
2. Seitengenaues Zusammenstellen (`--seiten`/`--zusammenfuegen` mit Seitenangabe je Datei) —
   das ursprüngliche Werkzeug kannte nur ganze Dateien; ein Aneinanderhängen hätte beim
   MEDIAN-Bericht zwei Seiten verdoppelt und drei falsch einsortiert (Bericht, Abschnitt
   „Achtung, Befund"). Nachweis: `VORGAENGE.md`, fertige Anweisung mit Seitentabelle für den
   noch offenen Klinik-Bericht.

**Individuelle Leistung.** Belegt durch Bericht, Entscheidungsregister und Protokoll:
- Fünf Dateien gelesen, zwei Berichte anhand unabhängiger Merkmale gepaart (Vorgangskennung,
  fortlaufende Blattzählung, Satzfortsetzung über Seitengrenze, Formularfußzeile) —
  Nachweis Bericht, Abschnitt „Paar 1"/„Paar 2".
- Eine Datei richtig als Geräteausdruck ohne Aufbewahrungsgrund eingeordnet und in
  Quarantäne gelegt, nicht gelöscht — Nachweis Bericht Abschnitt „Fünfte Datei", Protokoll
  Zeile 3 (`aktion` mit `sha` und `grund`).
- **Richtig nicht gearbeitet, wo die Grundlage fehlte:** Beim Klinik-Bericht fehlt Seite 7 in
  beiden Quelldateien — sie hat nicht mit acht von neun Seiten zusammengefügt, sondern den
  Vorgang offen gehalten und eine vollständige Anweisung für den nächsten Lauf hinterlegt
  (`VORGAENGE.md`, Abschnitt „fertige Anweisung"). Ebenso hat sie einen Nebenfund (Reservierung
  auf der Drive-Wurzel) nicht eigenmächtig verarbeitet, sondern als eigene Entscheidung (A25)
  vorgelegt.
- Jede Bewegung mit Prüfsumme vor/nach Kopie und Rücknehmbarkeit protokolliert (`marlene_ablegen.py
  undo`); Datengrenze eingehalten — Bericht nennt Aussteller nur als Klinik, keine Diagnose,
  keine Kennnummer.

## Was der Rolle noch fehlt

- Zugriff auf die NAS-Inbox ist nur über eine Kopie möglich, die für diesen Lauf von Claude
  Code bereitgestellt wurde — kein eigener Lesezugang der Rolle selbst.
- Kein Gedächtnis über Läufe hinweg außer den von ihr geführten Dateien (`ENTSCHEIDUNGEN.md`,
  `VORGAENGE.md`, Protokoll) — kein Rückgriff auf frühere Chats.
- Das Zusammenstell-Werkzeug ist heute im Lauf entstanden, nicht vorab geprüft oder
  abgenommen.

## Offene Vorgänge

- `MED-KLINIK-2026-05`: Seite 7 fehlt, muss nachgescannt werden; Anweisung liegt fertig vor.
- Vier Kopien unter `kopie_nas_inbox_2026-09-07/` bleiben liegen, bis das erledigt ist.
- Unbekannt: ob zu beiden Aufenthalten Rechnungen existieren und ob bei Beihilfe/PKV
  eingereicht wurde.

## Nächster kleinster Schritt

Seite 7 des Helios-Berichts nachscannen und der fertigen Anweisung in `VORGAENGE.md` folgen.

Kein Personalurteil, keine Übernahmeempfehlung — das entscheidet der CEO.
