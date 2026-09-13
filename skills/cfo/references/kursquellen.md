# Kursquellen je Anlageklasse

Abgerufen und geprüft am 12.09.2026. Was nicht erreichbar war, steht als nicht erreichbar da.

## Teil 2 — Kursquellen ohne Konto und ohne Schlüssel

Jede Quelle unten wurde am 2026-09-12 mit `curl` **tatsächlich abgerufen**, ohne Registrierung und
ohne Schlüssel; die zurückgegebenen Werte sind als Beleg mit angegeben. Was nur beschrieben und
nicht abgerufen wurde, ist ausdrücklich markiert.

### 2.1 Krypto — CoinGecko Public API

**Abgerufen, HTTP 200:**

```
https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=eur&include_last_updated_at=true
→ {"bitcoin":{"eur":66581,"last_updated_at":1789249760},
   "ethereum":{"eur":2174.97,"last_updated_at":1789249760}}
```

- **Ohne Schlüssel erreichbar:** ja, verifiziert. Auch `/api/v3/ping` antwortet ohne Key mit 200.
- **Stichtag:** `include_last_updated_at=true` liefert einen Unix-Zeitstempel je Coin. Damit ist der
  Stichtag maschinenlesbar in der Antwort — das ist der Grund, diesen Parameter immer zu setzen.
- **Aktualität:** nahe Echtzeit (Zeitstempel lag beim Abruf wenige Minuten zurück).
- **Rate Limit:** Die Doku sagt für die Public API, das Limit sei IP-basiert und „shared across all
  users on the same IP"; **eine konkrete Zahl nennt die Doku für die schlüssellose Stufe nicht**.
  Für den kostenlosen Demo-Plan *mit* Key nennt die Doku 100 Aufrufe/Minute; Sekundärquellen nennen
  30/min und 10.000/Monat — **diese Zahlen sind nicht aus der Primärquelle belegt.**
- **Freie Stufe mit Schlüssel:** ja, der Demo-Plan ist kostenlos und bringt ein stabileres Limit.
  Für einen privaten Skill mit wenigen Abrufen pro Tag ist der schlüssellose Weg ausreichend.
- **Lizenz/Attribution:** Sekundärquellen sagen, die freie Stufe verlange öffentliche Attribution.
  Die CoinGecko-Attributionsseite war beim Abruf nur als JavaScript-Gerüst lesbar, die Preisseite
  antwortete mit HTTP 403 — **die Attributionspflicht ist damit nicht aus der Primärquelle belegt.**
  Praktische Folge: Quellenangabe „Quelle: CoinGecko" mitführen, das kostet nichts.

### 2.2 Aktien und ETFs über ISIN — Börse Frankfurt

**Abgerufen, direkt per ISIN:**

```
https://api.boerse-frankfurt.de/v1/data/quote_box/single?isin=DE0007164600&mic=XETR
→ {"isin":"DE0007164600","lastPrice":178.18,"open":175.68,
   "changeToPrevDayInPercent":-0.3100,"instrumentStatus":"Active",
   "timestamp":"2026-09-11T20:00:00Z", ...}

https://api.boerse-frankfurt.de/v1/data/quote_box/single?isin=IE00B4L5Y983&mic=XETR
→ {"isin":"IE00B4L5Y983","lastPrice":126.75,"open":125.91, ...}   (ETF, funktioniert gleich)
```

- **Das ist die beste Quelle für diese Anlageklasse**, weil sie die **ISIN direkt als Schlüssel
  nimmt** — keine Ticker-Übersetzung, kein Mapping-Schritt, keine Verwechslungsgefahr zwischen
  Handelsplätzen. `mic=XETR` benennt den Handelsplatz explizit.
- **Ohne Schlüssel und ohne Registrierung erreichbar:** ja, verifiziert (User-Agent gesetzt).
- **Stichtag:** `timestamp` im ISO-8601-Format mit Zeitzone, direkt in der Antwort. Vorbildlich für
  unseren Zweck.
- **Aktualität:** Schlusskurs des letzten Handelstags bzw. laufender Kurs während der Handelszeit.
- **WKN:** Der geprüfte Endpunkt nimmt die ISIN. Ob er auch WKN akzeptiert — **nicht geprüft**.
  Da jede WKN eine ISIN hat, ist die ISIN der robustere Schlüssel; eine WKN-zu-ISIN-Auflösung
  müsste aus den eigenen Depotunterlagen kommen, nicht aus einer zusätzlichen Abfrage.
- **Lizenz:** Dies ist eine **interne API der Website**, keine dokumentierte öffentliche
  Schnittstelle. Die Nutzungsbedingungen von boerse-frankfurt.de wurden **nicht abgerufen** (die
  URL antwortete mit einer Weiterleitung, HTTP 308) — die Lizenzlage ist damit **nicht belegt**.
  Für die private Einzelabfrage des eigenen Depots unproblematisch; sparsam abfragen, nicht
  weiterverteilen. Eine nicht dokumentierte API kann sich jederzeit ändern — der Skill braucht
  einen sauberen Fehlerpfad, kein Raten.

### 2.3 Aktien und ETFs — Yahoo Finance als Zweitquelle

**Abgerufen, HTTP 200:**

```
https://query1.finance.yahoo.com/v8/finance/chart/SAP.DE?interval=1d&range=1d
→ "currency":"EUR","symbol":"SAP.DE","fullExchangeName":"XETRA",
  "regularMarketPrice":177.26,"regularMarketTime":1789140910,"timezone":"CEST"
```

- **Ohne Schlüssel erreichbar:** ja, verifiziert (User-Agent nötig).
- **Stichtag:** `regularMarketTime` als Unix-Zeitstempel, plus Zeitzone.
- **Nachteil gegenüber 2.2:** arbeitet mit **Tickersymbolen**, nicht mit ISIN. Das erzwingt eine
  Übersetzung, die falsch sein kann — und das ist bei Vermögenszahlen die teure Sorte Fehler.
  Deshalb: Zweitquelle zur Plausibilisierung, nicht Erstquelle.
- **Lizenz — hier liegt eine echte Einschränkung:** Die Yahoo Developer API Terms erlauben nach den
  abgerufenen Beschreibungen nur **persönliche, nicht-kommerzielle** Nutzung; Einkünfte aus der
  Nutzung der APIs sind ohne ausdrückliche Erlaubnis untersagt. `query1.finance.yahoo.com` ist
  zudem eine **inoffizielle, nicht von Yahoo unterstützte** Schnittstelle. Die konkrete Klausel
  wurde aus Suchergebnisbeschreibungen entnommen, **die Terms-Seite selbst wurde nicht abgerufen**
  — insoweit **nicht primärbelegt**, aber die Richtung ist eindeutig genug, um sie zu beachten.
  Für die private Vermögensübersicht des Eigentümers passt das; sobald daraus ein Angebot würde,
  passt es nicht mehr.

### 2.4 Edelmetalle — LBMA Benchmark-Preise

**Abgerufen, HTTP 200, mit tagesaktuellen Werten:**

```
https://prices.lbma.org.uk/json/gold_pm.json
→ letzter Eintrag: {"d":"2026-09-11","v":[4386.25, 3241.88, 3777]}
                                          USD      GBP      EUR      (je Feinunze)

https://prices.lbma.org.uk/json/silver.json
→ letzter Eintrag: {"d":"2026-09-11","v":[63.84, 47.27, 55.07]}
                                        USD    GBP    EUR        (je Feinunze)
```

- **Ohne Schlüssel und ohne Registrierung erreichbar:** ja, verifiziert. Die Datei enthält die
  **vollständige Historie** — Gold zurück bis 1968-04-01 — als ein JSON-Array. Für einen
  Tagesabruf reicht das letzte Element.
- **Stichtag:** Feld `d` als ISO-Datum je Eintrag. Sauber.
- **Weitere Dateien:** `gold_am.json` (Vormittagsfixing) analog — **beschrieben, nicht abgerufen**.
- **Feststellungszeiten** (LBMA-Seite „About LBMA Daily Auction Prices", abgerufen): Gold zweimal
  täglich 10:30 und 15:00 Londoner Zeit; Silber einmal täglich 12:00; Platin/Palladium 09:45 und
  14:00. Veröffentlichung frei **mit Verzögerung bis Mitternacht Londoner Zeit** — Echtzeit
  erfordert eine IBA-Lizenz.
- **Währung:** Notiert wird primär in **US-Dollar**. Die LBMA-Seite sagt ausdrücklich, dass die
  Angaben in Sterling und Euro „indicative and for settlement only" sind. **Das ist für uns
  wichtig:** Der Euro-Wert aus der Datei ist ein indikativer Umrechnungswert, kein Benchmark.
  Wer einen nachvollziehbaren Euro-Wert will, rechnet besser selbst: USD-Preis aus LBMA mal
  EZB-Referenzkurs (2.6) — beide mit eigenem, benanntem Stichtag.
- **Einheit:** Feinunze. Umrechnung auf Gramm: 1 Feinunze = 31,1034768 g — **diese Konstante wurde
  nicht aus einer Quelle abgerufen**, sie ist als Definition allgemein bekannt; wenn sie im Skill
  steht, gehört eine Quellenangabe dazu oder der Vermerk, dass sie ungeprüft übernommen ist.
- **Lizenz — echte Einschränkung:** Nach den abgerufenen Suchergebnisbeschreibungen der
  LBMA/IBA-Seiten benötigt jede Partei, die den LBMA Gold Price bzw. Silver Price „for valuation
  and pricing activities and in transactions and financial products" verwendet, eine **Nutzungslizenz
  von IBA**; jede kommerzielle Nutzung — Bepreisung, Bewertung, Abrechnung, Verweise in Verträgen
  oder Finanzinstrumenten — verlangt eine gültige IBA-Lizenz. Frei veröffentlicht wird der jeweils
  letzte Tagespreis auf der LBMA-Seite.
  **Das ist zu beachten:** Eine private Vermögensübersicht ist nach dem Wortlaut eine
  „valuation activity". Ob die private Eigenbewertung ohne Weitergabe darunterfällt, ist
  **nicht belegt** und im Zweifel eine Frage an IBA oder einen Anwalt. Eine Alternative steht in
  2.5 — die sollte im Skill als Standardweg dienen, LBMA als Referenz für den amtlichen Fixingpreis.

### 2.5 Edelmetalle — Alternative ohne Lizenzfrage

**Abgerufen, HTTP 200:**

```
https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=1d&range=1d
→ "currency":"USD","symbol":"GC=F","fullExchangeName":"COMEX",
  "instrumentType":"FUTURE","regularMarketTime":1789160399
```

- Das ist der **COMEX-Gold-Future**, nicht der LBMA-Kassapreis — ein anderer Preis, kein Ersatz im
  engen Sinn. Als laufende Größenordnung brauchbar, für eine Bestandsbewertung weniger passend.
- Es gelten dieselben Yahoo-Lizenzeinschränkungen wie in 2.3.
- **Nicht funktioniert hat:** `XAUEUR=X` bei Yahoo (`No data found, symbol may be delisted`) und
  sämtliche Stooq-CSV-Endpunkte (`https://stooq.com/q/l/?s=...&e=csv` antwortete durchgehend mit
  **HTTP 404**, für Aktien wie für `xaueur`/`xageur`). **Stooq ist damit als Quelle ausgeschieden** —
  es steht hier nur, damit niemand es ein zweites Mal probiert.

**Empfehlung für den Skillbau** (technisch, nicht rechtlich): LBMA als benannter Stichtagspreis in
USD, Umrechnung über den EZB-Referenzkurs, und die Lizenzfrage als offener Punkt im Skill vermerkt.

### 2.6 Referenzzinsen und Wechselkurse — EZB Data Portal API

**Abgerufen, HTTP 200, jeweils mit Datumsspalte:**

```
€STR (Euro short-term rate):
https://data-api.ecb.europa.eu/service/data/EST/B.EU000A2X2A25.WT?lastNObservations=3&format=csvdata
→ 2026-09-08: 2,188   2026-09-09: 2,189   2026-09-10: 2,190   (Prozent)

EUR/USD Referenzkurs:
https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?lastNObservations=2&format=csvdata
→ 2026-09-10: 1,1616   2026-09-11: 1,1592
```

- **Ohne Schlüssel und ohne Registrierung erreichbar:** ja, verifiziert.
- **Stichtag:** Spalte `TIME_PERIOD` je Beobachtung. Die CSV-Antwort führt zusätzlich Titel,
  Einheit und `DECIMALS` mit — der Datensatz beschreibt sich selbst, was ihn für ein Skript
  besonders angenehm macht.
- **Parameter, die den Abruf klein halten:** `lastNObservations=N` und `format=csvdata`.
  Auch `format=jsondata` existiert — **beschrieben, nicht abgerufen.**
- **Aktualität:** Der EUR/USD-Referenzkurs wird laut Datensatzbeschreibung um 14:15 MEZ
  festgestellt („ECB reference exchange rate, US dollar/Euro, 2.15 pm (C.E.T.)") — das steht
  wörtlich in der abgerufenen CSV-Antwort.
- **Lizenz — hier ist die Lage am klarsten:** Der EZB-Disclaimer (abgerufen) erlaubt die
  kostenlose Weiterverwendung von Inhalten, sofern die Information „accurately" erscheint und
  „the ECB must be cited as the source"; veränderte Daten sind als verändert zu kennzeichnen.
  Also: **Quellenangabe „Europäische Zentralbank" mitführen, abgeleitete Werte als abgeleitet
  kennzeichnen** — beides ohnehin gute Praxis für dieses Projekt.
- **Euribor:** Nicht abgerufen. Euribor wird vom EMMI administriert, nicht von der EZB; ob eine
  freie Abrufmöglichkeit besteht, ist **nicht belegt**. €STR ist der von der EZB selbst berechnete
  Tagesgeldsatz und für Rücklagen die naheliegende Referenz.

### 2.7 Umlaufrendite / Bundesanleihen — Deutsche Bundesbank

**Abgerufen, HTTP 200:**

```
https://api.statistiken.bundesbank.de/rest/data/BBSIS/D.I.ZST.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A?format=csv&lastNObservations=2
→ 2026-09-10;3,51   2026-09-11;3,56   (Prozent, Semikolon-getrennt, Dezimalkomma)
```

- Tagesaktuelle Rendite börsennotierter Bundeswertpapiere mit 10 Jahren Restlaufzeit — brauchbar
  als Referenz für Kredit- und Rücklagenentscheidungen.
- **Ohne Schlüssel erreichbar:** ja, verifiziert.
- **Achtung beim Parsen:** **Dezimalkomma und Semikolon** als Trenner — nicht die
  angelsächsische Form. Ein Skript, das das übersieht, liest 3,56 als 356 oder scheitert.
- **Nicht funktioniert haben** die geratenen Schlüssel `BBK01/WT3030`, `BBK01/WZ3400` und eine
  geratene Umlaufrendite-Kennung (jeweils HTTP 404 mit klarer Fehlermeldung). **Ein Reihenschlüssel
  wird im Portal nachgeschlagen, nicht erfunden** — dieselbe Regel wie überall sonst in diesem
  Projekt.
- **Lizenz:** Nutzungsbedingungen der Bundesbank **nicht abgerufen**, damit **nicht belegt**.

### 2.8 Wechselkurse — Frankfurter (bequeme Alternative zu 2.6)

**Abgerufen, HTTP 200:**

```
https://api.frankfurter.dev/v1/latest?base=EUR&symbols=USD,CHF
→ {"amount":1.0,"base":"EUR","date":"2026-09-11","rates":{"CHF":0.9451,"USD":1.1592}}
```

- **Ohne Schlüssel:** ja, verifiziert; die Projektseite sagt ausdrücklich „requires no API key".
- **Stichtag:** Feld `date`.
- **Der USD-Wert stimmt mit dem EZB-Referenzkurs aus 2.6 für denselben Tag exakt überein (1,1592)** —
  ein netter Beleg dafür, dass die Kette sauber ist.
- **Herkunft:** laut Projektseite Zentralbanken und offizielle Quellen, darunter die EZB.
- **Lizenz:** als Open Source beschrieben; die **genaue Lizenz nennt die Seite nicht**, sie verweist
  auf die Bedingungen der jeweiligen Datenprovider. Damit **nicht belegt**.
- **Einordnung:** bequemer als 2.6, aber eine Zwischenschicht mehr. Wo die Zahl zählt, direkt zur
  EZB gehen — deren Lizenzlage ist zudem als einzige klar belegt.

### 2.9 Übersicht

| Anlageklasse | Quelle | Schlüssel nötig | Stichtag in der Antwort | Lizenzlage | abgerufen |
|---|---|---|---|---|---|
| Krypto | CoinGecko `simple/price` | nein | `last_updated_at` (Unix) | Attribution wahrscheinlich, nicht primärbelegt | ✅ |
| Aktien/ETF per ISIN | Börse Frankfurt `quote_box/single` | nein | `timestamp` (ISO) | nicht belegt, interne API | ✅ |
| Aktien/ETF per Ticker | Yahoo `v8/finance/chart` | nein | `regularMarketTime` | nur privat/nicht-kommerziell, inoffiziell | ✅ |
| Gold/Silber Fixing | LBMA `gold_pm.json`, `silver.json` | nein | Feld `d` (ISO) | **IBA-Lizenz für Bewertung**, offen | ✅ |
| Gold laufend | Yahoo `GC=F` (Future, kein Kassapreis) | nein | `regularMarketTime` | wie Yahoo oben | ✅ |
| €STR, Wechselkurse | EZB Data Portal API | nein | `TIME_PERIOD` | frei mit Quellenangabe, **klar belegt** | ✅ |
| Bundesanleiherendite | Bundesbank `api.statistiken` | nein | Datumsspalte | nicht belegt | ✅ |
| Wechselkurse bequem | Frankfurter `v1/latest` | nein | `date` | nicht belegt | ✅ |
| — ausgeschieden — | Stooq CSV | — | — | — | ❌ HTTP 404 |
| — ausgeschieden — | Yahoo `XAUEUR=X` | — | — | — | ❌ kein Datensatz |

**Zwei Konventionen, die daraus für den Skill folgen:**

1. **Jeder gespeicherte Kurs trägt seinen Stichtag aus der Antwort, nicht die Abrufzeit.** Alle
   sieben tragfähigen Quellen liefern ihn mit; ihn wegzuwerfen und stattdessen `now()` zu
   schreiben, wäre derselbe Fehler wie eine erfundene Versionsnummer.
2. **Jeder gespeicherte Kurs trägt die Quelle namentlich.** Das ist bei EZB und CoinGecko
   Lizenzbedingung und überall sonst die Voraussetzung dafür, eine Zahl später nachprüfen zu
   können.

### 2.10 Was offen bleibt

- **LBMA/IBA-Lizenz für die private Bestandsbewertung** — nicht geklärt, siehe 2.4. Der einzige
  Punkt in Teil 2, an dem eine Rückfrage nötig sein könnte.
- **Nutzungsbedingungen von boerse-frankfurt.de und Bundesbank** — nicht abgerufen.
- **CoinGecko-Attributionspflicht** — nur sekundär belegt (Primärseiten lieferten 403 bzw. nur ein
  JS-Gerüst).
- **WKN-Abfrage bei Börse Frankfurt** — nicht geprüft.
- **Euribor frei abrufbar** — nicht belegt.

---

## Quellen

Alle am 2026-09-12 abgerufen, soweit nicht anders vermerkt.

**Gesetzestexte**

1. § 1 KWG (Abs. 1a Satz 2 Nr. 1, 1a, 3) — https://www.gesetze-im-internet.de/kredwg/__1.html
2. § 32 KWG (Erlaubnispflicht) — https://www.gesetze-im-internet.de/kredwg/__32.html
3. § 2 WpIG (Begriffsbestimmungen) — https://www.gesetze-im-internet.de/wpig/__2.html
4. § 2 StBerG (Hilfeleistung in Steuersachen) — https://www.gesetze-im-internet.de/stberg/__2.html
5. § 5 StBerG (Verbot der unbefugten Hilfeleistung) — https://www.gesetze-im-internet.de/stberg/__5.html
6. § 6 StBerG (Ausnahmen) — https://www.gesetze-im-internet.de/stberg/__6.html

**Aufsichtsquellen**

7. BaFin, Merkblatt „Hinweise zum Tatbestand der Anlageberatung", Stand 10.02.2025 —
   https://www.bafin.de/SharedDocs/Veroeffentlichungen/DE/Merkblatt/mb_250210_anlageberatung.html
8. BaFin, Merkblatt Anlagevermittlung, Stand 13.07.2017 —
   https://www.bafin.de/SharedDocs/Veroeffentlichungen/DE/Merkblatt/mb_091204_tatbestand_anlagevermittlung.html

**Kursquellen (Endpunkte, tatsächlich aufgerufen)**

9.  CoinGecko — https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=eur&include_last_updated_at=true
10. CoinGecko Rate-Limit-Doku — https://docs.coingecko.com/docs/common-errors-rate-limit
11. Börse Frankfurt — https://api.boerse-frankfurt.de/v1/data/quote_box/single?isin=DE0007164600&mic=XETR
12. Yahoo Finance Chart — https://query1.finance.yahoo.com/v8/finance/chart/SAP.DE?interval=1d&range=1d
13. LBMA Gold PM — https://prices.lbma.org.uk/json/gold_pm.json
14. LBMA Silber — https://prices.lbma.org.uk/json/silver.json
15. LBMA, „About LBMA Daily Auction Prices" — https://www.lbma.org.uk/prices-and-data/about-lbma-daily-auction-prices
16. EZB Data Portal, €STR — https://data-api.ecb.europa.eu/service/data/EST/B.EU000A2X2A25.WT?lastNObservations=3&format=csvdata
17. EZB Data Portal, EUR/USD — https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?lastNObservations=2&format=csvdata
18. EZB Disclaimer/Copyright — https://www.ecb.europa.eu/services/disclaimer/html/index.en.html
19. Deutsche Bundesbank, Zeitreihen-API — https://api.statistiken.bundesbank.de/rest/data/BBSIS/D.I.ZST.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A?format=csv&lastNObservations=2
20. Frankfurter — https://api.frankfurter.dev/v1/latest?base=EUR&symbols=USD,CHF
21. Frankfurter Projektseite — https://frankfurter.dev/

**Nur über Suchergebnisbeschreibungen erfasst, nicht primär abgerufen**

22. Yahoo Developer API Terms of Use — https://legal.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.html
23. LBMA Precious Metal Prices / IBA-Lizenzierung — https://www.lbma.org.uk/prices-and-data/lbma-precious-metal-prices
24. CoinGecko Public-Plan-Rate-Limit (Support) — https://support.coingecko.com/hc/en-us/articles/4538771776153-What-is-the-rate-limit-for-CoinGecko-API-public-plan

**Fehlgeschlagene Abrufe (dokumentiert, damit sie nicht wiederholt werden)**

25. Stooq CSV — https://stooq.com/q/l/?s=sap.de&f=sd2t2ohlcv&h&e=csv — HTTP 404, auch für `xaueur`, `xageur`
26. CoinGecko Pricing-Seite — https://www.coingecko.com/en/api/pricing — HTTP 403
27. EZB Data-Examples-Seite — https://data.ecb.europa.eu/help/data-examples — HTTP 503
28. LBMA Preisseite (HTML) — https://www.lbma.org.uk/prices-and-data/precious-metal-prices — leere Antwort / 403
