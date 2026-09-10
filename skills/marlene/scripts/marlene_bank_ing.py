#!/usr/bin/env python3
"""Erster Verbindungstest zur ING per FinTS, nur lesend.

Nutzt die Schranken: die Aktion muss auf marlene-ing-login erlaubt sein
(marlene_konten.json), das Kennwort kommt aus dem Schluesselbund und wird
nie gedruckt oder protokolliert. Kein Zahlen, kein Ueberweisen - das
verbietet schon die Aktionsliste des Kontos.

    marlene_bank_ing.py test        Verbindung aufbauen, Konten auflisten
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import marlene_tresor as T
import marlene_schranken as S

BLZ = "50010517"
ENDPUNKT = "https://fints.ing.de/fints/"

def main():
    reg = T.register()
    ok, grund = S.aktion_erlaubt("marlene-ing-login", "anmelden", reg)
    if not ok:
        print("ABBRUCH:", grund); return 1
    benutzer = reg["marlene-ing-login"]["benutzer"]
    kennwort, fehler = T.geheimnis("marlene-ing-login", "anmelden", "Verbindungstest")
    if kennwort is None:
        print("ABBRUCH:", fehler); return 1
    produkt_id, fehler2 = T.geheimnis("marlene-ing-fints", "produkt_id_lesen", "Verbindungstest, Produkt-ID")
    if produkt_id is None:
        print("ABBRUCH (Produkt-ID):", fehler2); return 1

    from fints.client import FinTS3PinTanClient, NeedTANResponse
    try:
        client = FinTS3PinTanClient(BLZ, benutzer, kennwort, ENDPUNKT,
                                     product_id=produkt_id)
    finally:
        del kennwort, produkt_id

    with client:
        if client.init_tan_response:
            print("Zwei-Faktor noetig (pushTAN in der ING App), Antwort:", client.init_tan_response.challenge)
            return 2
        konten = client.get_sepa_accounts()
        for k in konten:
            print("Konto: IBAN endet auf ...%s" % k.iban[-4:])
    return 0

if __name__ == "__main__":
    sys.exit(main())
