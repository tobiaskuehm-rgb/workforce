// marlene_lesen.js - Text aus PDF oder Bild, nur mit macOS-Bordmitteln.
//
// PDFKit liefert die Textebene; hat eine Seite keine (Scan), rendert PDFKit die Seite und
// Vision erkennt den Text - lokal auf diesem Mac, nichts verlaesst das Haus, keine Installation.
// Aufruf:  osascript -l JavaScript marlene_lesen.js <datei.pdf|bild>
//          osascript -l JavaScript marlene_lesen.js --rasterisieren <ein.pdf> <aus.pdf>  (Scan ohne Textebene, fuer Tests)
//          osascript -l JavaScript marlene_lesen.js --zusammenfuegen <aus.pdf> <ein1.pdf> <ein2.pdf> ...  (Vorder- und Rueckseite zu einer Datei)
// Ausgabe: je Seite ein Block "=== Seite N (textebene|ocr) ===" gefolgt vom Text.
// Selbsttest: marlene_lesen_selbsttest.py (Text-PDF -> Scan ohne Textebene -> zurueckgelesen).
ObjC.import('Quartz'); ObjC.import('Vision'); ObjC.import('AppKit');
function ocrURL(url) {
  const req = $.VNRecognizeTextRequest.alloc.init;
  req.recognitionLevel = $.VNRequestTextRecognitionLevelAccurate;
  req.recognitionLanguages = $(['de-DE', 'en-US']);
  req.usesLanguageCorrection = true;
  const handler = $.VNImageRequestHandler.alloc.initWithURLOptions(url, $({}));
  handler.performRequestsError($([req]), null);
  const res = req.results; const lines = [];
  for (let i = 0; i < res.count; i++) { const c = res.objectAtIndex(i).topCandidates(1); if (c.count > 0) lines.push(ObjC.unwrap(c.objectAtIndex(0).string)); }
  return lines.join('\n');
}
function pngFromPage(page, tmpPath) {
  const box = page.boundsForBox($.kPDFDisplayBoxMediaBox);
  const img = page.thumbnailOfSizeForBox($.NSMakeSize(box.size.width * 2.5, box.size.height * 2.5), $.kPDFDisplayBoxMediaBox);
  const rep = $.NSBitmapImageRep.imageRepWithData(img.TIFFRepresentation);
  const png = rep.representationUsingTypeProperties($.NSBitmapImageFileTypePNG, $({}));
  png.writeToFileAtomically(tmpPath, true);
  return $.NSURL.fileURLWithPath(tmpPath);
}
function lesen(path) {
  const out = [];
  if (path.toLowerCase().endsWith('.pdf')) {
    const doc = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(path));
    for (let p = 0; p < doc.pageCount; p++) {
      const page = doc.pageAtIndex(p);
      let text = ObjC.unwrap(page.string) || ''; let quelle = 'textebene';
      if (text.replace(/\s/g, '').length < 40) {
        const tmp = $.NSTemporaryDirectory().js + 'marlene_seite_' + p + '.png';
        text = ocrURL(pngFromPage(page, tmp)); quelle = 'ocr';
        $.NSFileManager.defaultManager.removeItemAtPathError(tmp, null);
      }
      out.push('=== Seite ' + (p + 1) + ' (' + quelle + ') ===\n' + text);
    }
  } else {
    out.push('=== Bild (ocr) ===\n' + ocrURL($.NSURL.fileURLWithPath(path)));
  }
  return out.join('\n');
}
function rasterisieren(ein, aus) {
  const doc = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(ein));
  const neu = $.PDFDocument.alloc.init;
  for (let p = 0; p < doc.pageCount; p++) {
    const tmp = $.NSTemporaryDirectory().js + 'marlene_raster_' + p + '.png';
    pngFromPage(doc.pageAtIndex(p), tmp);
    neu.insertPageAtIndex($.PDFPage.alloc.initWithImage($.NSImage.alloc.initWithContentsOfFile(tmp)), p);
    $.NSFileManager.defaultManager.removeItemAtPathError(tmp, null);
  }
  neu.writeToFile(aus); return 'rasterisiert: ' + doc.pageCount + ' Seite(n)';
}
function zusammenfuegen(argv) {
  // argv: <aus.pdf> <ein1.pdf> <ein2.pdf> ... - Seiten in Aufrufreihenfolge, Quellen bleiben unberuehrt.
  const neu = $.PDFDocument.alloc.init; let n = 0;
  for (let i = 1; i < argv.length; i++) {
    const doc = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(argv[i]));
    for (let p = 0; p < doc.pageCount; p++) neu.insertPageAtIndex(doc.pageAtIndex(p), n++);
  }
  neu.writeToFile(argv[0]); return 'zusammengefuegt: ' + n + ' Seite(n) nach ' + argv[0];
}
function run(argv) {
  if (argv[0] === '--zusammenfuegen') return zusammenfuegen(argv.slice(1));
  if (argv.length === 0) return 'Aufruf: marlene_lesen.js <datei> | --rasterisieren <ein.pdf> <aus.pdf>';
  return argv[0] === '--rasterisieren' ? rasterisieren(argv[1], argv[2]) : lesen(argv[0]);
}
