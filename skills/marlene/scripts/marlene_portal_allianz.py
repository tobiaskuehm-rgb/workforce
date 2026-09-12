#!/usr/bin/env python3
"""Allianz "Meine Allianz": erster Verbindungstest, Login-Ablauf zweistufig
(E-Mail, dann Kennwort). Das Kennwort verlaesst dieses Programm nie -
es wird nur in Playwright's Formularfeld getippt, nie gedruckt oder
protokolliert.

Zweiter Faktor moeglich (SMS-Code laut Allianz-Seite): wenn danach gefragt
wird, bricht dieses Programm ab und meldet es, statt zu raten.

    marlene_portal_allianz.py test [--sichtbar]
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import marlene_tresor as T
import marlene_schranken as S
from playwright.sync_api import sync_playwright

KONTO = "marlene-allianz-pkv"
START = "https://www.allianz.de/meine-allianz/"

def main():
    reg = T.register()
    ok, grund = S.aktion_erlaubt(KONTO, "anmelden", reg)
    if not ok:
        print("ABBRUCH:", grund); return 1
    benutzer = reg[KONTO]["benutzer"] if "benutzer" in reg[KONTO] else None
    if not benutzer:
        wert, fehler = T.geheimnis(KONTO, "anmelden", "Benutzername fehlt im Register")
        print("ABBRUCH: kein Benutzername im Register hinterlegt"); return 1
    kennwort, fehler = T.geheimnis(KONTO, "anmelden", "Verbindungstest Allianz")
    if kennwort is None:
        print("ABBRUCH:", fehler); return 1

    sichtbar = "--sichtbar" in sys.argv
    ergebnis = "unbekannt"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=not sichtbar)
            seite = browser.new_page()
            seite.goto(START, timeout=30000)
            seite.wait_for_load_state("domcontentloaded", timeout=15000); seite.wait_for_timeout(2000)

            # Schritt 1: E-Mail
            feld = seite.get_by_label("E-Mail-Adresse")
            if feld.count() == 0:
                feld = seite.locator('input[type="email"], input[name*="mail" i]').first
            feld.fill(benutzer)
            seite.get_by_role("button", name="Weiter").click()
            seite.wait_for_timeout(1500)

            # Schritt 2: Kennwort
            pw_feld = seite.locator('input[type="password"]').first
            pw_feld.wait_for(timeout=10000)
            pw_feld.fill(kennwort)
            weiter = seite.get_by_role("button", name="Weiter")
            if weiter.count() == 0:
                weiter = seite.get_by_role("button", name="Anmelden")
            weiter.first.click()
            seite.wait_for_timeout(3000)

            text = seite.locator("body").inner_text()[:400]
            titel = seite.title()
            url = seite.url
            if any(w in text.lower() for w in ("sms", "code", "zwei-faktor", "2-faktor", "tan")):
                ergebnis = "ZWEITER FAKTOR NOETIG, abgebrochen"
            elif "meine-allianz" in url and "anmelden" not in url.lower() and "login" not in url.lower():
                ergebnis = "ANGEMELDET, Titel: %s, URL: %s" % (titel, url)
            else:
                ergebnis = "UNKLAR, Titel: %s, URL: %s, Text: %s" % (titel, url, text[:200])
            browser.close()
    finally:
        del kennwort

    print(ergebnis)
    return 0

if __name__ == "__main__":
    sys.exit(main())
