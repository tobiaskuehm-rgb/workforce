"""Selbsttest fuer marlene_lesen.js: Text-PDF -> Scan ohne Textebene -> zurueckgelesen.

Standardbibliothek plus macOS-Bordmittel (cupsfilter, osascript). Laeuft in einem Wegwerfordner.
"""
import pathlib, subprocess, sys, tempfile

HIER = pathlib.Path(__file__).resolve().parent
JS = HIER / "marlene_lesen.js"
SATZ = "Rechnung Nummer 4711 vom 12.03.2026 ueber 412,30 Euro, zahlbar bis 26.03.2026."


def lesen(pfad: str) -> str:
    return subprocess.run(["osascript", "-l", "JavaScript", str(JS), pfad], capture_output=True, text=True, check=True).stdout


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        txt = pathlib.Path(tmp) / "t.txt"; txt.write_text(SATZ + "\n", encoding="utf-8")
        text_pdf = pathlib.Path(tmp) / "text.pdf"; scan_pdf = pathlib.Path(tmp) / "scan.pdf"
        with open(text_pdf, "wb") as out:
            subprocess.run(["cupsfilter", str(txt)], stdout=out, stderr=subprocess.DEVNULL, check=True)
        a = lesen(str(text_pdf))
        subprocess.run(["osascript", "-l", "JavaScript", str(JS), "--rasterisieren", str(text_pdf), str(scan_pdf)],
                       capture_output=True, text=True, check=True)
        b = lesen(str(scan_pdf))
    befunde = [
        ("Textebene erkannt", "(textebene)" in a and "4711" in a),
        ("Scan als ocr erkannt", "(ocr)" in b),
        ("Nummer aus dem Scan gelesen", "4711" in b),
        ("Betrag aus dem Scan gelesen", "412,30" in b or "412.30" in b),
        ("Frist aus dem Scan gelesen", "26.03.2026" in b),
    ]
    for name, ok in befunde:
        print(("PASS " if ok else "FAIL ") + name)
    ok = all(x for _, x in befunde)
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
