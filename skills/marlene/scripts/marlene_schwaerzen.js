// marlene_schwaerzen.js - Stellen in einem gescannten PDF unkenntlich machen, macOS-Bordmittel.
//
// Jede Seite wird gerastert, Vision erkennt den Text mit Position, jede Zeile, die auf ein
// Muster passt, wird im BILD schwarz uebermalt, und die Seite wird als Bild neu gespeichert.
// Damit ist die Stelle weg, nicht nur verdeckt: es gibt keine Textebene mehr, unter der sie
// weiterlebt. Der Preis: die Ausgabe ist ein reines Bild-PDF. Fuer eine Belegkopie an Dritte
// ist das richtig.
//
// Aufruf: osascript -l JavaScript marlene_schwaerzen.js <ein.pdf> <aus.pdf> <regex1> [regex2 ...]
// Ausgabe: je Seite die Zahl der geschwaerzten Zeilen; Exit 1, wenn kein Muster gefunden wurde.
// Nachpruefung gehoert dem Aufrufer: die Ausgabe mit marlene_lesen.js lesen und die Muster suchen.
ObjC.import('Quartz'); ObjC.import('Vision'); ObjC.import('AppKit');
function run(argv) {
  if (argv.length < 3) { return 'Aufruf: <ein.pdf> <aus.pdf> <regex> [...]'; }
  const eingabe = argv[0], ausgabe = argv[1];
  const muster = argv.slice(2).map(m => new RegExp(m, 'i'));
  const doc = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(eingabe));
  if (!doc || doc.pageCount === 0) { return 'Datei nicht lesbar: ' + eingabe; }
  const out = $.PDFDocument.alloc.init;
  const SKALA = 2.5; let gesamt = 0; const zeilen = [];
  for (let p = 0; p < doc.pageCount; p++) {
    const page = doc.pageAtIndex(p);
    const box = page.boundsForBox($.kPDFDisplayBoxMediaBox);
    const w = Math.round(box.size.width * SKALA), h = Math.round(box.size.height * SKALA);
    const img = page.thumbnailOfSizeForBox($.NSMakeSize(w, h), $.kPDFDisplayBoxMediaBox);
    const rep = $.NSBitmapImageRep.imageRepWithData(img.TIFFRepresentation);
    const tmp = $.NSTemporaryDirectory().js + 'marlene_schw_' + p + '.png';
    rep.representationUsingTypeProperties($.NSBitmapImageFileTypePNG, $({})).writeToFileAtomically(tmp, true);
    const req = $.VNRecognizeTextRequest.alloc.init;
    req.recognitionLevel = $.VNRequestTextRecognitionLevelAccurate;
    req.recognitionLanguages = $(['de-DE', 'en-US']);
    const handler = $.VNImageRequestHandler.alloc.initWithURLOptions($.NSURL.fileURLWithPath(tmp), $({}));
    handler.performRequestsError($([req]), null);
    const res = req.results; let n = 0;
    const neu = $.NSImage.alloc.initWithSize($.NSMakeSize(w, h));
    neu.lockFocus;
    img.drawInRectFromRectOperationFraction($.NSMakeRect(0, 0, w, h), $.NSMakeRect(0, 0, img.size.width, img.size.height), $.NSCompositingOperationCopy, 1.0);
    $.NSColor.blackColor.setFill;
    for (let i = 0; i < res.count; i++) {
      const o = res.objectAtIndex(i); const c = o.topCandidates(1);
      if (c.count === 0) continue;
      const s = ObjC.unwrap(c.objectAtIndex(0).string);
      if (!muster.some(m => m.test(s))) continue;
      const b = o.boundingBox; // normiert, Ursprung unten links
      const r = $.NSMakeRect(b.origin.x * w - 4, b.origin.y * h - 4, b.size.width * w + 8, b.size.height * h + 8);
      $.NSBezierPath.fillRect(r); n++;
    }
    neu.unlockFocus;
    const seite = $.PDFPage.alloc.initWithImage(neu);
    out.insertPageAtIndex(seite, out.pageCount);
    $.NSFileManager.defaultManager.removeItemAtPathError(tmp, null);
    zeilen.push('Seite ' + (p + 1) + ': ' + n + ' Zeile(n) geschwaerzt'); gesamt += n;
  }
  out.writeToFile(ausgabe);
  zeilen.push(gesamt > 0 ? 'geschrieben: ' + ausgabe : 'KEIN TREFFER, nichts geschwaerzt');
  return zeilen.join('\n');
}
