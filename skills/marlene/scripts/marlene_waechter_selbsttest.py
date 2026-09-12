#!/usr/bin/env python3
"""Selbsttest der drei Waechter. Standardbibliothek, Python 3.9, Wegwerfordner.

Jeder Waechter bekommt zwei Proben: eine saubere Lage, in der er gruen sein muss,
und eine Lage mit genau einem eingebauten Verstoss, in der er genau einen Fund
melden muss. Ein Waechter, der nie rot wird, ist keiner (CLAUDE.md, Regel 47);
ein Waechter, der immer rot ist, wird abgeschaltet statt gelesen.

Die Verstoesse sind die echten Faelle vom 10. und 11.09.2026:
  1 Drei Schreiben gingen hinaus, die Register fuehrten sie am naechsten Morgen offen.
  2 Neun Klaerfaelle lagen, die aeltesten seit fuenf Tagen.
  3 Einer von 23 Ausgaengen hatte keine Freigabekennung.

  python3 marlene_waechter_selbsttest.py
"""
import datetime
import json
import os
import pathlib
import shutil
import tempfile
import time
import unittest

import marlene_waechter as w


def lage(wurzel, gesendet_verbucht=True, freigabe=True, klaerfall_alter_tage=0):
    """Baut eine vollstaendige, saubere Lage und schaltet auf Wunsch einen Mangel ein."""
    eingang = wurzel / "01_Ablage_Eingang"
    marlene = eingang / "_Marlene"
    (marlene / "protokoll").mkdir(parents=True)
    (marlene / "ausgang").mkdir(parents=True)
    (eingang / "_Klären").mkdir(parents=True)

    post = [
        {"aktion": "abholen", "zeit": "2026-09-10T09:00:00"},
        {"aktion": "senden", "ergebnis": "gesendet", "zeit": "2026-09-10T14:08:54",
         "an": "mieter@example.invalid", "betreff": "Belegeinsicht", "freigabe": "F07"},
        {"aktion": "senden", "ergebnis": "gestoppt", "zeit": "2026-09-11T11:23:13",
         "entwurf": str(marlene / "ausgang" / "E09.eml"),
         "gruende": ["keine Freigabe-Kennung im Vorgang"]},
    ]
    with (marlene / "protokoll" / "post.jsonl").open("w", encoding="utf-8") as f:
        for e in post:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    vorgang = {"kennung": "E01", "empfaenger": ["mieter@example.invalid"], "freigabe": "F07"}
    if gesendet_verbucht:
        vorgang["gesendet_am"] = "2026-09-10T14:08:54"
    if not freigabe:
        vorgang.pop("freigabe")
    (marlene / "ausgang" / "E01.vorgang.json").write_text(
        json.dumps(vorgang, ensure_ascii=False), encoding="utf-8")

    (marlene / "VORGAENGE.md").write_text(
        "# Vorgaenge\n\n| Kennung | Stand |\n|---|---|\n"
        "| NK-BERGGASSE1 | E01 gesendet 2026-09-10 |\n", encoding="utf-8")

    fall = eingang / "_Klären" / "Rechnung-unklar.pdf"
    fall.write_bytes(b"%PDF-1.4 Probe")
    if klaerfall_alter_tage:
        alt = time.time() - klaerfall_alter_tage * 86400
        os.utime(fall, (alt, alt))  # mtime zurueckdrehen; ctime bleibt jung
    return eingang


class WaechterTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="waechterprobe-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # --- Waechter 1: Poststelle gegen Register -------------------------------

    def test_1_gruen_wenn_versand_verbucht_ist(self):
        eingang = lage(self.tmp)
        funde, _ = w.waechter_1(eingang)
        self.assertEqual([], funde)

    def test_1_rot_wenn_versand_nicht_verbucht_ist(self):
        """Eine von zwei Vorgangsdateien fuehrt den Vermerk, die andere nicht."""
        eingang = lage(self.tmp)
        ausgang = eingang / "_Marlene" / "ausgang"
        (ausgang / "E02.vorgang.json").write_text(json.dumps(
            {"kennung": "E02", "freigabe": "F08"}), encoding="utf-8")
        with (eingang / "_Marlene" / "protokoll" / "post.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"aktion": "senden", "ergebnis": "gesendet",
                                "zeit": "2026-09-11T09:00:00", "freigabe": "F08"}) + "\n")
        funde, _ = w.waechter_1(eingang)
        self.assertEqual(1, len(funde), funde)
        self.assertIn("E02", funde[0])
        self.assertIn("keinen Versand", funde[0])

    def test_1_fehlendes_verfahren_wird_einmal_gemeldet_nicht_je_sendung(self):
        """Fuehrt keine Vorgangsdatei einen Vermerk, ist das ein Befund, nicht dreiundzwanzig."""
        eingang = lage(self.tmp, gesendet_verbucht=False)
        ausgang = eingang / "_Marlene" / "ausgang"
        (ausgang / "E02.vorgang.json").write_text(json.dumps(
            {"kennung": "E02", "freigabe": "F08"}), encoding="utf-8")
        with (eingang / "_Marlene" / "protokoll" / "post.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"aktion": "senden", "ergebnis": "gesendet",
                                "zeit": "2026-09-11T09:00:00", "freigabe": "F08"}) + "\n")
        funde, _ = w.waechter_1(eingang)
        self.assertEqual(1, len(funde), funde)
        self.assertIn("gesendet_am", funde[0])

    def test_1_versand_ohne_freigabe_im_protokoll_ist_ein_fund(self):
        eingang = lage(self.tmp)
        with (eingang / "_Marlene" / "protokoll" / "post.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"aktion": "senden", "ergebnis": "gesendet",
                                "zeit": "2026-09-11T10:00:00"}) + "\n")
        funde, _ = w.waechter_1(eingang)
        self.assertEqual(1, len(funde), funde)
        self.assertIn("ohne Freigabekennung", funde[0])

    def test_1_versand_ohne_passende_vorgangsdatei_ist_ein_fund(self):
        eingang = lage(self.tmp)
        with (eingang / "_Marlene" / "protokoll" / "post.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"aktion": "senden", "ergebnis": "gesendet",
                                "zeit": "2026-09-11T10:00:00", "freigabe": "F99"}) + "\n")
        funde, _ = w.waechter_1(eingang)
        self.assertEqual(1, len(funde), funde)
        self.assertIn("F99", funde[0])

    def test_1_rot_wenn_die_kennung_im_register_fehlt(self):
        eingang = lage(self.tmp)
        (eingang / "_Marlene" / "VORGAENGE.md").write_text("# Vorgaenge\n", encoding="utf-8")
        funde, _ = w.waechter_1(eingang)
        self.assertEqual(1, len(funde), funde)
        self.assertIn("VORGAENGE.md", funde[0])

    def test_1_die_gestoppte_sendung_zaehlt_nicht_als_versand(self):
        eingang = lage(self.tmp)
        funde, _ = w.waechter_1(eingang)
        self.assertEqual([], funde)

    def test_1_meldet_fehlendes_protokoll_statt_gruen(self):
        eingang = lage(self.tmp)
        (eingang / "_Marlene" / "protokoll" / "post.jsonl").unlink()
        funde, _ = w.waechter_1(eingang)
        self.assertEqual(1, len(funde))
        self.assertIn("Postprotokoll fehlt", funde[0])

    def test_1_zaehlt_kaputte_protokollzeilen(self):
        eingang = lage(self.tmp)
        with (eingang / "_Marlene" / "protokoll" / "post.jsonl").open("a", encoding="utf-8") as f:
            f.write("{kein json\n")
        _, kaputt = w.waechter_1(eingang)
        self.assertEqual(1, kaputt)

    # --- Waechter 2: Liegezeit ----------------------------------------------

    def test_2_gruen_beim_frischen_faLl(self):
        eingang = lage(self.tmp)
        funde, _ = w.waechter_2(eingang, 7)
        self.assertEqual([], funde)

    def test_2_rot_wenn_ein_fall_zu_lange_liegt(self):
        """ctime laesst sich nicht setzen; die Regel wird deshalb direkt gespeist."""
        jetzt = datetime.datetime(2026, 9, 12, 6, 0)
        funde = w.fund_wenn_aelter("Rechnung-unklar.pdf",
                                   jetzt - datetime.timedelta(days=9), 7, jetzt)
        self.assertEqual(1, len(funde), funde)
        self.assertIn("9 Tagen", funde[0])

    def test_2_genau_an_der_grenze_bleibt_gruen(self):
        jetzt = datetime.datetime(2026, 9, 12, 6, 0)
        self.assertEqual([], w.fund_wenn_aelter("x.pdf",
                                                jetzt - datetime.timedelta(days=7), 7, jetzt))
        self.assertEqual(1, len(w.fund_wenn_aelter("x.pdf",
                                                   jetzt - datetime.timedelta(days=8), 7, jetzt)))

    def test_2_altes_dokumentdatum_ist_kein_alter_faLl(self):
        """Eine Rechnung von 2024 liegt nicht seit 2024 zur Klaerung."""
        eingang = lage(self.tmp, klaerfall_alter_tage=900)
        funde, _ = w.waechter_2(eingang, 7)
        self.assertEqual([], funde, "mtime darf nicht als Liegezeit gelten")

    def test_2_ordner_werden_uebergangen(self):
        eingang = lage(self.tmp)
        (eingang / "_Klären" / "Unterordner").mkdir()
        funde, _ = w.waechter_2(eingang, 7)
        self.assertEqual([], funde)

    # --- Waechter 3: Freigabekennung ----------------------------------------

    def test_3_gruen_mit_freigabe(self):
        eingang = lage(self.tmp)
        funde, _ = w.waechter_3(eingang)
        self.assertEqual([], funde)

    def test_3_rot_ohne_freigabe(self):
        eingang = lage(self.tmp, freigabe=False)
        funde, _ = w.waechter_3(eingang)
        self.assertEqual(1, len(funde), funde)
        self.assertIn("E01", funde[0])

    def test_3_json_null_gilt_als_fehlende_freigabe(self):
        """Der echte Fall E13: freigabe stand auf null, und str(None) ist nicht leer."""
        eingang = lage(self.tmp)
        datei = eingang / "_Marlene" / "ausgang" / "E01.vorgang.json"
        daten = json.loads(datei.read_text(encoding="utf-8"))
        daten["freigabe"] = None
        datei.write_text(json.dumps(daten), encoding="utf-8")
        funde, _ = w.waechter_3(eingang)
        self.assertEqual(1, len(funde), funde)
        self.assertIn("E01", funde[0])

    def test_3_leere_freigabe_gilt_als_fehlend(self):
        eingang = lage(self.tmp)
        datei = eingang / "_Marlene" / "ausgang" / "E01.vorgang.json"
        daten = json.loads(datei.read_text(encoding="utf-8"))
        daten["freigabe"] = "  "
        datei.write_text(json.dumps(daten), encoding="utf-8")
        funde, _ = w.waechter_3(eingang)
        self.assertEqual(1, len(funde))

    def test_3_unlesbare_vorgangsdatei_ist_ein_fund(self):
        eingang = lage(self.tmp)
        (eingang / "_Marlene" / "ausgang" / "E01.vorgang.json").write_text("{kaputt",
                                                                          encoding="utf-8")
        funde, _ = w.waechter_3(eingang)
        self.assertEqual(1, len(funde))
        self.assertIn("nicht lesbar", funde[0])

    # --- Selbstmeldung gegen den stillen Ausfall -----------------------------

    def test_4_erster_lauf_wird_als_solcher_gemeldet(self):
        eingang = lage(self.tmp)
        text, rot = w.bericht(eingang, 7)
        self.assertIn("erster Lauf", text)
        self.assertFalse(rot)

    def test_4_alter_lauf_macht_den_waechter_selbst_rot(self):
        eingang = lage(self.tmp)
        protokoll = eingang / "_Marlene" / "protokoll" / "waechter.jsonl"
        alt = datetime.datetime.now() - datetime.timedelta(hours=w.LAUF_FRIST_STUNDEN + 5)
        protokoll.write_text(json.dumps({"zeit": alt.isoformat(timespec="seconds"),
                                         "ergebnis": "gruen"}) + "\n", encoding="utf-8")
        text, rot = w.bericht(eingang, 7)
        self.assertTrue(rot, text)
        self.assertIn("Waechter selbst", text)

    def test_4_frischer_lauf_bleibt_gruen(self):
        eingang = lage(self.tmp)
        w.bericht(eingang, 7)
        text, rot = w.bericht(eingang, 7)
        self.assertFalse(rot, text)
        self.assertIn("letzter Lauf", text)

    def test_4_der_lauf_wird_vermerkt(self):
        eingang = lage(self.tmp)
        w.bericht(eingang, 7)
        eintraege, _ = w.zeilen(eingang / "_Marlene" / "protokoll" / "waechter.jsonl")
        self.assertEqual(1, len(eintraege))
        self.assertIn(eintraege[0]["ergebnis"], ("gruen", "rot"))

    def test_4_probe_schreibt_keine_laufzeile(self):
        eingang = lage(self.tmp)
        w.bericht(eingang, 7, schreiben=False)
        self.assertFalse((eingang / "_Marlene" / "protokoll" / "waechter.jsonl").exists())

    # --- Gesamturteil --------------------------------------------------------

    def test_5_ein_einzelner_mangel_faerbt_den_bericht_rot(self):
        eingang = lage(self.tmp, freigabe=False)
        text, rot = w.bericht(eingang, 7, schreiben=False)
        self.assertTrue(rot)
        self.assertIn("ROT", text)

    def test_5_saubere_lage_bleibt_ohne_rot(self):
        eingang = lage(self.tmp)
        text, rot = w.bericht(eingang, 7, schreiben=False)
        self.assertFalse(rot)
        self.assertNotIn("ROT", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
