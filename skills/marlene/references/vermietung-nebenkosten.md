# Vermietung und Nebenkostenabrechnung

Gilt für das vermietete Objekt in Rockhausen. Die Regeln des Mietvertrags (Abrechnungszeitraum, Umlageschlüssel, vereinbarte Kostenarten, Vorauszahlungen) werden einmal aus dem Vertrag gelesen und als Abrechnungsregeln hinterlegt; Marlene rechnet nach diesen Regeln und ändert sie nicht.

## Das Gesetz in vier Sätzen

- Über Betriebskostenvorauszahlungen ist **jährlich** abzurechnen, der Abrechnungszeitraum darf zwölf Monate nicht überschreiten (§ 556 Abs. 3 BGB).
- Die Abrechnung muss dem Mieter **bis zum Ablauf des zwölften Monats nach Ende des Abrechnungszeitraums** zugehen; danach ist eine Nachforderung ausgeschlossen, es sei denn, der Vermieter hat die Verspätung nicht zu vertreten.
- Der Mieter hat für Einwendungen **zwölf Monate ab Zugang** der Abrechnung.
- Umgelegt werden dürfen nur Kostenarten, die im Mietvertrag vereinbart sind und in § 2 BetrKV stehen.

## Die 17 Kostenarten nach § 2 BetrKV

1. laufende öffentliche Lasten, insbesondere Grundsteuer
2. Wasserversorgung
3. Entwässerung (Abwasser)
4. Heizung
5. Warmwasser
6. verbundene Heizungs- und Warmwasseranlagen
7. Aufzug
8. Straßenreinigung und Müllbeseitigung
9. Gebäudereinigung und Ungezieferbekämpfung
10. Gartenpflege
11. Beleuchtung
12. Schornsteinreinigung
13. Sach- und Haftpflichtversicherung
14. Hauswart
15. Gemeinschaftsantenne oder Breitbandnetz
16. Einrichtungen für die Wäschepflege
17. sonstige Betriebskosten (nur, wenn im Vertrag ausdrücklich benannt)

**Nicht umlagefähig:** Verwaltungskosten, Instandhaltung und Reparaturen, Kreditkosten. Sie gehören ins Journal als Ausgabe des Vermieters (steuerlich Werbungskosten), nicht in die Abrechnung.

## Das Journal

Je Jahr `VERMIETUNG_JJJJ.md` im Ordner des Objekts, eine Zeile je Buchung:

| Datum | Art | Kostenart (BetrKV-Nr. oder „nicht umlagefähig") | Betrag | umlagefähig | Zeitraum | Beleg (Datei) |
|---|---|---|---|---|---|---|

Einnahmen: Kaltmiete, Nebenkostenvorauszahlung, Nachzahlung aus Abrechnung. Ausgaben: jede Rechnung und jeder Bescheid, die das Objekt betreffen. Ein Beleg, dessen Zeitraum über den Jahreswechsel reicht, wird nach Tagen aufgeteilt und beide Anteile werden ausgewiesen.

## Die Abrechnung vorbereiten, Schritt für Schritt

0. Welches Jahr? Wird eine Abrechnung verlangt, deren Zeitraum noch läuft, ist die erste Rückfrage, ob das Vorjahr gemeint ist; die Frist des Vorjahres kann dann drängen. Ein laufendes Jahr wird nur als Vorabentwurf geführt.
1. Abrechnungsregeln laden: Zeitraum, Schlüssel (Wohnfläche, Personen, Verbrauch), vereinbarte Kostenarten, geleistete Vorauszahlungen.
2. Für jede vereinbarte Kostenart prüfen, ob für den vollen Zeitraum Belege vorliegen. Was fehlt, wird benannt und als Frist geführt (Beispiel: „Abwasserbescheid 2026 fehlt").
3. Umlage rechnen: Gesamtkosten je Kostenart, Anteil nach Schlüssel, Teilzeiträume nach Tagen, Summe, abzüglich Vorauszahlungen, Saldo. Rundung kaufmännisch auf Cent, einmal am Ende je Kostenart.
4. Plausibilität: jede Kostenart gegen das Vorjahr; Abweichungen über ein Fünftel werden im Entwurf genannt, nicht stillschweigend übernommen.
5. Entwurf erstellen: Anschreiben, Abrechnungstabelle, Belegliste. Kennzeichnung `ENTWURF, NICHT GESENDET`, Kennung, Fassungsnummer.
6. Vorlage an Tobias mit Kernaussage: vollständig oder was fehlt, Saldo, Frist nach § 556. Versand nur nach Freigabe genau dieser Fassung.
7. Nach Versand: Zugang belegen (Datum, Weg), Einwendungsfrist des Mieters als Frist führen, Abrechnung und Belege im Objektordner unter dem Jahr ablegen, Kopie in den Steuerordner.

## Was Marlene nicht tut

Sie entscheidet nicht, ob eine Kostenart umlagefähig ist, wenn der Vertrag schweigt; sie legt vor. Sie ändert keinen Schlüssel. Sie mahnt nicht ohne Freigabe. Sie bewertet keine Einwendung des Mieters, sie legt sie mit Frist vor.

## Quellen

- § 556 BGB, https://www.gesetze-im-internet.de/bgb/__556.html
- § 2 BetrKV, https://www.gesetze-im-internet.de/betrkv/__2.html
- Objego, Nebenkostenabrechnung Fristen für Vermieter, https://www.objego.de/blog/nebenkostenabrechnung-fristen/
- Wegora, Umlagefähige Betriebskosten nach § 2 BetrKV (nicht umlagefähige Kosten), https://nebenkosten.wegora.de/blog/umlagefaehige-betriebskosten
