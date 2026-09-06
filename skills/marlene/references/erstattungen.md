# Erstattungen: Arztrechnung, Beihilfe, PKV

Tobias ist Beamter in Thüringen. Krankheitskosten werden zu einem Teil von der Beihilfe des Landes und zum Rest von der privaten Krankenversicherung erstattet. Eine Arztrechnung ist deshalb ein Vorgang mit zwei Stellen und drei Fristen.

## Die Regeln

- **Beihilfe Thüringen:** Antrag innerhalb **eines Jahres** nach Rechnungsdatum oder Entstehen der Aufwendung; maßgeblich ist der **Eingang bei der Festsetzungsstelle**, nicht das Absendedatum (§ 50 ThürBhV). Bemessungssatz laut Ratgeber: 50 Prozent für aktive Beamte mit bis zu einem Kind, 70 Prozent ab zwei Kindern, 80 Prozent für Kinder. **Der für diesen Haushalt geltende Satz wird aus dem letzten Beihilfebescheid gelesen und hinterlegt, nicht aus dieser Tabelle.**
- **PKV:** Einreichung innerhalb von **drei Jahren**, gerechnet ab Ende des Jahres der Rechnungsausstellung (§§ 195, 199 BGB). Erstattung meist innerhalb weniger Wochen.
- **Zahlung an den Arzt:** nach dem Zahlungsziel der Rechnung, unabhängig davon, ob Erstattungen schon da sind.

## Der Vorgang

Je Rechnung eine Zeile im Register Erstattungen:

| Feld | Inhalt |
|---|---|
| Kennung | `MED-JJJJ-NNNN` |
| Rechnung | Datum, Aussteller (ohne Fachrichtung, wenn sie eine Diagnose verrät), Betrag, Zahlungsziel, bezahlt am |
| Beihilfe | eingereicht am, Eingang bestätigt am, erwartet (Betrag × Satz), erhalten am, erhalten Betrag |
| PKV | eingereicht am, erwartet (Rest), erhalten am, erhalten Betrag |
| Rest | Rechnung minus Beihilfe minus PKV, **gerechnet, nie geschätzt** |
| nächste Kontrolle | Datum |
| Status | offen, wartet auf Beihilfe, wartet auf PKV, wartet auf Tobias, erledigt |

## Ablauf

1. Rechnung eingegangen: Vorgang anlegen, Zahlungsziel als Frist, Beihilfe-Jahresfrist als Frist (Rechnungsdatum plus ein Jahr, Wiedervorlage zwei Monate vorher), Ablage im Personenordner unter Krankenkasse.
2. Einreichung vorbereiten: Beleg und gegebenenfalls Rezept als Anlagen benennen; Einreichen ist eine externe Aktion und wird vorgelegt, solange kein Zugang zu einem Portal freigegeben ist.
3. Nach Einreichung: Kontrolle nach vier Wochen. Kein Eingang: Vorlage „Nachfrage entwerfen?".
4. Erstattung eingegangen: Betrag gegen erwartet prüfen. Gleich: weiter zur nächsten Stelle oder erledigt. Abweichend: Status `wartet auf Tobias`, Vorlage mit Differenz und dem Text der Erstattungsmitteilung, **ohne** Bewertung, ob die Kürzung berechtigt ist.
5. Erledigt, wenn beide Stellen gezahlt haben und der Rest bei Tobias verbucht ist. Kopie von Rechnung und Erstattungsmitteilungen in den Steuerordner (außergewöhnliche Belastung: nur der Eigenanteil zählt).

## Was Marlene nie tut

Sie sagt nicht, ob eine Behandlung beihilfefähig ist. Sie schreibt keine Diagnose in Register, Namen oder Bericht. Sie schließt keinen Vorgang, weil eine Erstattung „wahrscheinlich" ist.

## Quellen

- Belegkompass, Beihilfe Thüringen (Antragsfrist § 50 ThürBhV, Bemessungssätze), https://belegkompass.de/ratgeber/beihilfe/thueringen/
- Thüringer Landesfinanzdirektion, Merkblatt Beihilfe, https://tlf.thueringen.de/fileadmin/tlf/beihilfe/Berufsanfaenger_02_2023.pdf
- Verivox, Rechnung einreichen bei der PKV, https://www.verivox.de/private-krankenversicherung/ratgeber/rechnung-einreichen-bei-der-pkv-fristen-und-ablauf-1000782/
- PKV-Serviceportal, Arztrechnungen: Welche Fristen gibt es in der PKV, https://www.privat-patienten.de/beim-arzt/arztrechnungen-welche-fristen-gibt-es-in-der-pkv/
