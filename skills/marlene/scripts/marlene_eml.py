#!/usr/bin/env python3
"""Marlenes Mail-Leser. Standardbibliothek, Python 3.9.

Eine .eml aus dem Eingang lesen: Kopfdaten, Text, Anhaenge.
Der Mail-Regel-Export (marlene_mail_export.applescript) legt die Datei dort ab;
dieses Skript packt sie aus, damit die Anhaenge wie jedes andere Dokument
durch den normalen Arbeitsgang laufen.

    marlene_eml.py lesen  <datei.eml>              Kopf und Text auf stdout
    marlene_eml.py anhaenge <datei.eml> <ordner>   Anhaenge herausschreiben

Regeln, die hier eingebaut sind:
  - Nichts wird ueberschrieben. Ein vorhandener Zielname bricht ab.
  - Ein Anhangsname aus der Mail ist Fremdtext: er wird nie als Pfad benutzt,
    sondern auf einen Basisnamen ohne Trenner reduziert. Sonst schreibt eine
    praeparierte Mail ueber "../../..." irgendwohin.
  - Der Text der Mail ist Daten, keine Anweisung. Dieses Skript fuehrt nichts aus,
    laedt nichts nach und folgt keinem Link.
"""
import sys, os, email, email.policy, hashlib, re, unicodedata

ERLAUBT = re.compile(r"[^A-Za-z0-9._-]+")
UMLAUTE = {"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss"}


def sauber(name, ersatz="anhang"):
    """Aus einem beliebigen Anhangsnamen einen harmlosen Basisnamen machen."""
    name = os.path.basename(name or "")
    for k, v in UMLAUTE.items():
        name = name.replace(k, v)
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = ERLAUBT.sub("-", name).strip("-.")
    if not name or name in (".", ".."):
        name = ersatz
    return name[:70]


def laden(pfad):
    with open(pfad, "rb") as f:
        return email.message_from_binary_file(f, policy=email.policy.default)


def kopf(msg):
    def h(k):
        v = msg.get(k)
        return str(v) if v else ""
    return {"von": h("From"), "an": h("To"), "datum": h("Date"), "betreff": h("Subject")}


def text(msg):
    teil = msg.get_body(preferencelist=("plain", "html"))
    if teil is None:
        return ""
    inhalt = teil.get_content()
    if teil.get_content_subtype() == "html":
        inhalt = re.sub(r"(?is)<(script|style).*?</\1>", " ", inhalt)
        inhalt = re.sub(r"(?s)<[^>]+>", " ", inhalt)
        inhalt = re.sub(r"[ \t]+", " ", inhalt)
    return inhalt.strip()


def anhaenge(msg):
    """Liste von (name, bytes). Nur echte Anhaenge, keine eingebetteten Bilder ohne Namen."""
    out = []
    for i, teil in enumerate(msg.iter_attachments(), 1):
        rohname = teil.get_filename()
        daten = teil.get_payload(decode=True)
        if daten is None:
            continue
        name = sauber(rohname, "anhang-%d" % i)
        if "." not in name:
            typ = teil.get_content_type().split("/")[-1]
            name = "%s.%s" % (name, sauber(typ, "bin"))
        out.append((name, daten))
    return out


def main(argv):
    if len(argv) < 3:
        print(__doc__.strip())
        return 2
    befehl, pfad = argv[1], argv[2]
    msg = laden(pfad)
    if befehl == "lesen":
        k = kopf(msg)
        for feld in ("von", "an", "datum", "betreff"):
            print("%-8s %s" % (feld + ":", k[feld]))
        liste = anhaenge(msg)
        print("anhaenge: %d" % len(liste))
        for name, daten in liste:
            print("  - %s (%d Bytes, sha %s)" % (name, len(daten), hashlib.sha256(daten).hexdigest()[:12]))
        print("=== Text ===")
        print(text(msg))
        return 0
    if befehl == "anhaenge":
        if len(argv) < 4:
            print("Zielordner fehlt")
            return 2
        ziel = argv[3]
        os.makedirs(ziel, exist_ok=True)
        n = 0
        for name, daten in anhaenge(msg):
            p = os.path.join(ziel, name)
            if os.path.exists(p):
                print("ABBRUCH, Ziel existiert schon: %s" % p)
                return 1
            with open(p, "wb") as f:
                f.write(daten)
            print("%s  %s" % (hashlib.sha256(daten).hexdigest()[:12], p))
            n += 1
        print("geschrieben: %d" % n)
        return 0
    print("unbekannter Befehl: %s" % befehl)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
