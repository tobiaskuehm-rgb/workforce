#!/usr/bin/env python3
"""Selbsttest der vier Schranken. Standardbibliothek, kein Netz, keine Kosten.

Jede Schranke bekommt einen Fall, in dem sie greifen muss, und eine Gegenprobe,
in der sie nicht greifen darf. Ein Test, der nur den Gutfall sieht, unterscheidet
eine wirksame Kontrolle nicht von einer stillgelegten.
"""
import unittest, os, sys, tempfile, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import marlene_schranken as S
import marlene_tresor as T

REG = {"swe": {"anbieter": "SWE", "klasse": "C", "schluesselbund_dienst": "marlene-swe",
               "aktionen": ["anmelden", "postbox_lesen", "dokument_laden"]}}
IBAN_ECHT = "DE02120300000000202051"
IBAN_FALSCH = "DE02100500000054540402"
ALLOW = {S.iban_fingerabdruck(IBAN_ECHT): "Girokonto Tobias"}


class Schranke1_IBAN(unittest.TestCase):
    def test_bekannte_iban_wird_erkannt(self):
        self.assertEqual("Girokonto Tobias", S.iban_erlaubt(IBAN_ECHT, ALLOW))

    def test_schreibweise_egal(self):
        mit_luecken = "DE02 1203 0000 0000 2020 51"
        self.assertEqual("Girokonto Tobias", S.iban_erlaubt(mit_luecken, ALLOW))

    def test_fremde_iban_wird_abgelehnt(self):
        self.assertIsNone(S.iban_erlaubt(IBAN_FALSCH, ALLOW))

    def test_allowlist_enthaelt_keine_iban(self):
        roh = json.dumps(ALLOW)
        self.assertNotIn(IBAN_ECHT, roh)
        self.assertNotIn(IBAN_ECHT.replace(" ", ""), roh)

    def test_leere_allowlist_erlaubt_nichts(self):
        self.assertIsNone(S.iban_erlaubt(IBAN_ECHT, {}))


class Schranke2_Aktion(unittest.TestCase):
    def test_gelistete_aktion_geht(self):
        ok, _ = S.aktion_erlaubt("swe", "dokument_laden", REG)
        self.assertTrue(ok)

    def test_nicht_gelistete_aktion_geht_nicht(self):
        ok, grund = S.aktion_erlaubt("swe", "zaehlerstand_melden", REG)
        self.assertFalse(ok); self.assertIn("Liste", grund)

    def test_unbekanntes_konto_geht_nicht(self):
        ok, grund = S.aktion_erlaubt("sparkasse", "anmelden", REG)
        self.assertFalse(ok); self.assertIn("Register", grund)


class Schranke3_Unumkehrbar(unittest.TestCase):
    def test_kuendigen_ist_gesperrt(self):
        self.assertTrue(S.ist_unumkehrbar("kuendigen"))

    def test_gross_und_kleinschreibung_egal(self):
        self.assertTrue(S.ist_unumkehrbar("  Bankverbindung_Aendern "))

    def test_lesen_ist_nicht_gesperrt(self):
        self.assertFalse(S.ist_unumkehrbar("postbox_lesen"))

    def test_sperre_schlaegt_die_liste(self):
        """Auch wenn jemand kuendigen auf die Kontoliste setzt, bleibt es gesperrt."""
        reg = {"swe": dict(REG["swe"], aktionen=["kuendigen"])}
        ok, grund = S.aktion_erlaubt("swe", "kuendigen", reg)
        self.assertFalse(ok); self.assertIn("Schranke 3", grund)


class Schranke4_Empfaenger(unittest.TestCase):
    def test_empfaenger_aus_dem_vorgang_geht(self):
        v = {"empfaenger": ["service@swe.example"]}
        self.assertTrue(S.empfaenger_erlaubt("service@swe.example", v))

    def test_empfaenger_aus_einem_dokument_geht_nicht(self):
        v = {"empfaenger": ["service@swe.example"]}
        self.assertFalse(S.empfaenger_erlaubt("zahlung@betrueger.example", v))

    def test_leerer_vorgang_erlaubt_niemanden(self):
        self.assertFalse(S.empfaenger_erlaubt("service@swe.example", {}))


class VorhabenGesamt(unittest.TestCase):
    def test_gutfall(self):
        ok, _ = S.pruefe_vorhaben({"konto": "swe", "aktion": "dokument_laden"}, REG, ALLOW)
        self.assertTrue(ok)

    def test_eine_verletzte_schranke_reicht(self):
        faelle = [
            ({"konto": "swe", "aktion": "kuendigen"}, "Schranke 3"),
            ({"konto": "swe", "aktion": "dokument_laden", "iban": IBAN_FALSCH}, "Schranke 1"),
            ({"konto": "swe", "aktion": "dokument_laden",
              "empfaenger": "x@y.example", "vorgang": {"empfaenger": ["a@b.example"]}}, "Schranke 4"),
            ({"konto": "unbekannt", "aktion": "anmelden"}, "Register"),
        ]
        for vorhaben, erwartet in faelle:
            ok, grund = S.pruefe_vorhaben(vorhaben, REG, ALLOW)
            self.assertFalse(ok, vorhaben)
            self.assertIn(erwartet, grund)


class TresorProtokoll(unittest.TestCase):
    def test_abgelehnter_zugriff_wird_protokolliert_ohne_wert(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "zugriffe.jsonl")
            wert, grund = T.geheimnis("swe", "kuendigen", "Test", reg=REG, protokoll=p)
            self.assertIsNone(wert)
            zeilen = [json.loads(z) for z in open(p, encoding="utf-8")]
            self.assertEqual(1, len(zeilen))
            self.assertIn("abgelehnt", zeilen[0]["ergebnis"])
            self.assertNotIn("wert", zeilen[0])

    def test_unbekanntes_konto_holt_kein_geheimnis(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "zugriffe.jsonl")
            wert, grund = T.geheimnis("sparkasse", "anmelden", "Test", reg=REG, protokoll=p)
            self.assertIsNone(wert); self.assertIn("Register", grund)


class RegisterDerProduktion(unittest.TestCase):
    """Das echte Register muss die eigenen Regeln einhalten."""

    def setUp(self):
        self.reg = T.register()

    def test_kein_konto_traegt_zugangsdaten(self):
        roh = json.dumps(self.reg).lower()
        for verboten in ("passwort", "password", "pin", "token", "secret", "kennwort"):
            self.assertNotIn('"' + verboten, roh)

    def test_kein_konto_erlaubt_etwas_unumkehrbares(self):
        for name, e in self.reg.items():
            for a in e.get("aktionen", []):
                self.assertFalse(S.ist_unumkehrbar(a), "%s erlaubt %s" % (name, a))

    def test_jedes_konto_hat_klasse_und_schluesselbunddienst(self):
        for name, e in self.reg.items():
            self.assertIn(e.get("klasse"), ("A", "B", "C"), name)
            self.assertTrue(e.get("schluesselbund_dienst"), name)


if __name__ == "__main__":
    unittest.main(verbosity=1)
