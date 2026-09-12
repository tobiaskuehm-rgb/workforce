#!/usr/bin/env python3
"""Kontoumsaetze der letzten N Tage lesen, nur letzte vier Ziffern der IBAN.
    marlene_bank_umsaetze.py <tage>
"""
import sys, os, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import marlene_tresor as T
import marlene_schranken as S
from fints.client import FinTS3PinTanClient

BLZ = "50010517"
ENDPUNKT = "https://fints.ing.de/fints/"

def main():
    tage = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    reg = T.register()
    ok, grund = S.aktion_erlaubt("marlene-ing-login", "umsaetze_ansehen", reg)
    if not ok:
        print("ABBRUCH:", grund); return 1
    benutzer = reg["marlene-ing-login"]["benutzer"]
    kennwort, fehler = T.geheimnis("marlene-ing-login", "umsaetze_ansehen", "Umsatzabfrage")
    if kennwort is None:
        print("ABBRUCH:", fehler); return 1
    produkt_id, _ = T.geheimnis("marlene-ing-fints", "produkt_id_lesen", "Umsatzabfrage")
    try:
        client = FinTS3PinTanClient(BLZ, benutzer, kennwort, ENDPUNKT, product_id=produkt_id)
    finally:
        del kennwort, produkt_id
    ab = datetime.date.today() - datetime.timedelta(days=tage)
    with client:
        if client.init_tan_response:
            print("ZWEITER FAKTOR NOETIG"); return 2
        konten = client.get_sepa_accounts()
        for k in konten:
            try:
                ums = client.get_transactions(k, start_date=ab, end_date=datetime.date.today())
            except Exception as e:
                continue
            if not ums: continue
            print("=== Konto ...%s ===" % k.iban[-4:])
            for u in ums:
                d = u.data
                betrag = d.get("amount")
                zweck = (d.get("purpose") or "")[:70]
                empf = (d.get("applicant_name") or "")[:30]
                datum = d.get("date")
                print("%s  %8s  %-30s  %s" % (datum, betrag, empf, zweck))
    return 0

if __name__ == "__main__":
    sys.exit(main())
