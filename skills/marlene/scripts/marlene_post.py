#!/usr/bin/env python3
"""Marlenes Post: abholen, pruefen, zustellen; senden nur nach Freigabe.

Standardbibliothek, Python 3.9. Das Kennwort kommt aus dem Schluesselbund ueber
marlene_tresor.geheimnis(); es wird nie gedruckt und nie protokolliert.

    marlene_post.py abholen [--ohne-ki] [--ollama URL]
        IMAP: neue Nachrichten aus INBOX holen, durch die Poststelle pruefen,
        als .eml in den Eingang legen (normal) oder in den Eingang mit Vermerk
        (verdacht) oder in die Quarantaene (ablehnen). Verarbeitete UIDs werden
        gemerkt; nichts wird im Postfach geloescht.
    marlene_post.py senden <entwurf.eml> <vorgang.json>
        SMTP: nur wenn ausgang_pruefen() freigibt (Empfaenger im Vorgang,
        Freigabe-Kennung, keine fremde IBAN). Kopie nach Gesendet.
    marlene_post.py test <an>
        Eine Testmail an genau diese Adresse; Freigabe-Kennung TEST.
"""
import datetime, email, email.policy, email.utils, imaplib, json, os, smtplib, sys
from email.message import EmailMessage

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import marlene_tresor as T
import marlene_poststelle as P
import marlene_schranken as S

KONTO = "marlene-postfach"
BASIS = os.path.expanduser("~/Library/CloudStorage/GoogleDrive-Tobias.kuehm@icloud.com/Meine Ablage/01_Ablage_Eingang")
EINGANG = BASIS
QUARANTAENE = os.path.expanduser("~/Documents/_Aussortiert")
ZUSTAND = os.path.join(BASIS, "_Marlene", "post_zustand.json")
PROTOKOLL = os.path.join(BASIS, "_Marlene", "protokoll", "post.jsonl")


def konto():
    return T.register()[KONTO]


def zugang(aktion, zweck):
    wert, grund = T.geheimnis(KONTO, aktion, zweck)
    if wert is None:
        raise SystemExit("ABBRUCH: " + grund)
    return wert


def protokoll(**z):
    z["zeit"] = datetime.datetime.now().isoformat(timespec="seconds")
    os.makedirs(os.path.dirname(PROTOKOLL), exist_ok=True)
    with open(PROTOKOLL, "a", encoding="utf-8") as f:
        f.write(json.dumps(z, ensure_ascii=False) + "\n")


def zustand_laden():
    try:
        return json.load(open(ZUSTAND, encoding="utf-8"))
    except Exception:
        return {"uids": []}


def zustand_sichern(z):
    os.makedirs(os.path.dirname(ZUSTAND), exist_ok=True)
    json.dump(z, open(ZUSTAND, "w", encoding="utf-8"))


def dateiname(msg, stufe):
    k = P.E.kopf(msg)
    try:
        d = email.utils.parsedate_to_datetime(k["datum"]).strftime("%Y-%m-%d")
    except Exception:
        d = datetime.date.today().isoformat()
    name, adr = email.utils.parseaddr(k["von"])
    absender = P.E.sauber(name or adr.split("@")[0], "Absender")[:30]
    betreff = P.E.sauber(k["betreff"], "ohne-Betreff")[:40]
    prefix = "" if stufe == "normal" else "VERDACHT_"
    return "%s%s_%s_%s.eml" % (prefix, d, absender, betreff)


def eindeutig(pfad):
    basis, ext = os.path.splitext(pfad); n = 2
    while os.path.exists(pfad):
        pfad = "%s-%d%s" % (basis, n, ext); n += 1
    return pfad


def abholen(ohne_ki=False, ollama=None):
    k = konto(); host, port = k["imap"].split(":")
    pw = zugang("imap_lesen", "Post abholen")
    z = zustand_laden(); bekannt = set(z["uids"])
    m = imaplib.IMAP4_SSL(host, int(port))
    try:
        m.login(k["benutzer"], pw)
    except imaplib.IMAP4.error as e:
        protokoll(aktion="imap_login", ergebnis="fehlgeschlagen: " + str(e)[:120])
        raise SystemExit("IMAP-Anmeldung fehlgeschlagen. Ist POP3/IMAP bei GMX freigeschaltet und das App-Passwort im Schluesselbund?")
    finally:
        del pw
    m.select("INBOX", readonly=False)
    typ, daten = m.uid("search", None, "ALL")
    uids = [u.decode() for u in daten[0].split()] if daten and daten[0] else []
    neu = [u for u in uids if u not in bekannt]
    ergebnis = {"normal": 0, "verdacht": 0, "ablehnen": 0}
    for uid in neu:
        typ, teile = m.uid("fetch", uid, "(RFC822)")
        roh = teile[0][1]
        msg = email.message_from_bytes(roh, policy=email.policy.default)
        rs, mark = P.feste_regeln(msg)
        if ohne_ki:
            ks, gr = "normal", ["KI-Schicht ausgelassen (--ohne-ki)"]
        else:
            ks, gr = P.ki_einstufen(msg, ollama)
        stufe = P.entscheiden(rs, ks)
        if stufe == "ablehnen":
            ziel_dir = os.path.join(QUARANTAENE, datetime.date.today().isoformat(), "Post")
        else:
            ziel_dir = EINGANG
        os.makedirs(ziel_dir, exist_ok=True)
        ziel = eindeutig(os.path.join(ziel_dir, dateiname(msg, stufe)))
        with open(ziel, "wb") as f:
            f.write(roh)
        import hashlib
        sha = hashlib.sha256(roh).hexdigest()[:12]
        protokoll(aktion="abholen", uid=uid, stufe=stufe, regeln=mark, ki=gr, ziel=ziel, sha=sha)
        ergebnis[stufe] += 1
        bekannt.add(uid)
    z["uids"] = sorted(bekannt, key=int)
    zustand_sichern(z)
    m.logout()
    return {"neu": len(neu), **ergebnis}


def _senden(msg, freigabe):
    k = konto(); host, port = k["smtp"].split(":")
    pw = zugang("smtp_senden", "Senden, Freigabe " + str(freigabe))
    try:
        with smtplib.SMTP(host, int(port), timeout=60) as s:
            s.starttls(); s.login(k["benutzer"], pw); s.send_message(msg)
        # Kopie nach Gesendet
        try:
            ih, ip = k["imap"].split(":")
            im = imaplib.IMAP4_SSL(ih, int(ip)); im.login(k["benutzer"], pw)
            im.append("Gesendet", "\\Seen", imaplib.Time2Internaldate(datetime.datetime.now().timestamp()), msg.as_bytes())
            im.logout()
        except Exception as e:
            protokoll(aktion="gesendet_ablegen", ergebnis="fehlgeschlagen: " + type(e).__name__)
    finally:
        del pw


def senden(entwurf, vorgang_pfad):
    msg = P.E.laden(entwurf)
    vorgang = json.load(open(vorgang_pfad, encoding="utf-8"))
    allow = {k: v for k, v in S.laden(os.path.join(HIER, "marlene_ibans.json")).items() if not k.startswith("_")}
    ok, gruende = P.ausgang_pruefen(msg, vorgang, T.register(), allow)
    if not ok:
        protokoll(aktion="senden", ergebnis="gestoppt", gruende=gruende, entwurf=entwurf)
        raise SystemExit("GESTOPPT: " + "; ".join(gruende))
    _senden(msg, vorgang.get("freigabe"))
    protokoll(aktion="senden", ergebnis="gesendet", an=str(msg["To"]), betreff=str(msg["Subject"]), freigabe=vorgang.get("freigabe"))
    return "gesendet an " + str(msg["To"])


def test(an):
    msg = EmailMessage()
    msg["From"] = "Marlene <tobias.kuehm@gmx.de>"
    msg["To"] = an
    msg["Subject"] = "[Marlene] Poststelle, erste Testmail"
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg.set_content("Hallo Tobias,\n\ndas ist die erste Mail aus meinem Postfach. Wenn sie ankommt, funktioniert der Versand; "
                    "antworte einfach darauf, dann pruefe ich damit die Abholung.\n\nMarlene\n\n"
                    "(Freigabe TEST, Empfaenger aus dem Vorgang, gesendet von marlene_post.py)")
    vorgang = {"empfaenger": [an], "freigabe": "TEST"}
    ok, gruende = P.ausgang_pruefen(msg, vorgang, T.register(), {})
    if not ok:
        raise SystemExit("GESTOPPT: " + "; ".join(gruende))
    _senden(msg, "TEST")
    protokoll(aktion="senden", ergebnis="gesendet", an=an, betreff=str(msg["Subject"]), freigabe="TEST")
    return "Testmail gesendet an " + an


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip()); return 2
    b = argv[1]
    if b == "abholen":
        url = argv[argv.index("--ollama") + 1] if "--ollama" in argv else None
        print(json.dumps(abholen("--ohne-ki" in argv, url), ensure_ascii=False)); return 0
    if b == "senden" and len(argv) >= 4:
        print(senden(argv[2], argv[3])); return 0
    if b == "test" and len(argv) >= 3:
        print(test(argv[2])); return 0
    print(__doc__.strip()); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
