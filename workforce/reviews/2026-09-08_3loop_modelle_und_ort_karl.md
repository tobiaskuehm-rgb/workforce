# 3-Loop: Welches Modell, an welchem Ort, mit welchem Gedächtnis

Karl, COO auf Probe, 2026-09-08, auf Verlangen des CEO („mach dir grundlegend Gedanken über
Modell-Switching und wo ich den Mitarbeiter abhole, als 3-Loop"). Verfahren `3loop`.

## 1. Die Frage in einem Satz

Wie bekommt jeder Mitarbeiter je Aufgabe das passende Modell, groß zum Problemlösen, klein
zum Sichten und Ablegen, und an welchem Ort holt der CEO ihn ab, ohne dass Gedächtnis und
Name über ChatGPT, Claude Code, Cowork, Codex und Telegram verstreut sind; entscheidet der
CEO am Donnerstag, 2026-09-10.

**Randbedingungen, schon entschieden:** Modellpolitik erst Cloud, dann lokal; kein neuer
Rechner jetzt, Mac mini M1 bleibt (2026-09-03). Der Agent bleibt werkzeuglos, die Datengrenze
bleibt eine Funktion (Invarianten 8, 10). Ein lokales Modell darf mehr sehen als ein fremdes,
und das steht in der Konstante (Invariante 8). Ollama ist nur an Loopback und
`host.docker.internal` erlaubt (`G-092`); der Netzweg NAS → Mac mini ist nicht festgelegt.
Tagesdecke 2,0 USD. Zwei Abos, Bot per API.

## 2. Gemessen, nicht gemeint

| Was | Wert | Quelle |
|---|---|---|
| Modelle je Agent in Claude Code | Gerd, Marv Opus; Karl, Marlene, Thorsten, Anastasia, CFO Sonnet | `.claude/agents/*.md`, seit `fade82f` |
| Modelle im Bot | Karl, Thorsten Opus; Marlene, Anastasia, CFO Sonnet | `config.nas.json` |
| Allowlist des Kerns | `echo-v1`, `claude-haiku-4-5`, `claude-sonnet-5`, `claude-opus-5` | `workforce/models.py` |
| Provider im Kern | Echo, Ollama, Claude, eine Schnittstelle | `workforce/providers.py` |
| Modellwahl je Aufgabe | keine; ein Modell je Identität, fest | `config.py`, `Identity.model` |
| Gedächtnisdateien | 5 von 7: Anastasia, CFO, Gerd, Karl, Thorsten; **Marlene und Marv fehlen** | `skills/gedaechtnis/` |
| Ollama auf diesem Mac | nicht erreichbar | `curl 127.0.0.1:11434` |
| Gerds LLM-Server aus Codex | im Repo keine Spur | `grep -rli` über `.md .py .yaml .txt` |
| Kosten je Antwort, gemessen | 0,0017 USD, Sonnet, ein Datenpunkt | `HANDOVER.md` |
| Kostendeckel je Aufruf | vorhanden, je Modell | `models.py`, `max_usd_per_call` |
| ChatGPT-Verläufe mit den Mitarbeitern | nicht im Repo, Export seit 2026-09-07 offen | Gedächtnisse, Zeile „Import" |

**Nicht gemessen:** was die ChatGPT-Assistentin „jenseits von Gut und Böse" antwortet und
ob es am Modell oder am fehlenden Gedächtnis liegt; wie viel des Abos Karl als Agent heute
verbraucht; die Qualität eines Open-Source-Modells auf dem Mac mini M1 für Sichtungsarbeit.

## 3. Der Vorschlag des CEO (A): das passende Modell von selbst, ein Ort für alle

Wörtlich: Karl „läuft auf Fable 5.1, weil ich einen sicheren COO brauche, der Mann über
alles". Die Assistentin „auf Opus 5, in Ordnung, aber bei manchen Aufgaben reicht ein
niedrigeres, Open Source, keine Ahnung". „Für Problemlösung das größte Modell, für Ablage und
Sichtung das niedrigste oder was dafür geeignet ist." Und: „Ich weiß immer noch nicht, wo ich
den Mitarbeiter abhole"; überall stehen die Namen, „zusammengedachte Erinnerungen holen mich
ab"; Telegram kostet Token; vielleicht eine Brücke von ChatGPT zu Claude.

In Sätzen: Jeder Mitarbeiter erkennt die Schwere einer Aufgabe und nimmt das Modell dazu. Es
gibt einen Ort, an dem der CEO jeden Mitarbeiter abholt, und dort ist das Gedächtnis
vollständig. Die Oberflächen sind verbunden, notfalls über eine Brücke zwischen Anbietern.

**Annahmen, die A macht und nicht sagt:** Die Schwere einer Aufgabe lässt sich vor der
Antwort erkennen, und zwar billiger als die Antwort. Die schlechten Antworten kommen vom
Modell, nicht vom fehlenden Gedächtnis. ChatGPT ist ein Ort, an dem ein Mitarbeiter stehen
kann. Eine Brücke zwischen Anbietern existiert oder lässt sich bauen.

## 4. Drei Gegenvorschläge

**B, das Gegenteil an der teuersten Stelle: ein Ort, der Bot.** Die teuerste Stelle ist
„überall". Also: Mitarbeiter gibt es nur im Bot auf der NAS; ChatGPT, Cowork und der Codex-
Chat sind keine Orte für Mitarbeiter, dort stehen keine Namen mehr. Claude Code bleibt
Werkstatt für Gerd und Marv. Modellwahl: je Identität zwei Modelle in der Konfiguration,
Sichten als Standard, Denken auf Ansage.

**C, dasselbe Ziel mit dem, was da ist: die Datei ist der Mitarbeiter.** Ein Mitarbeiter ist
sein Skill plus sein Gedächtnis im Repo, sonst nichts. Jede Oberfläche, die diese zwei
Dateien liest, ist ein gültiger Ort: Claude Code über den Verweis, der Bot über
`/etc/workforce/skills`, Cowork, wenn es das Repo sieht. Was die Dateien nicht lesen kann
(ChatGPT), ist kein Ort; die Verläufe dort werden einmal exportiert und sind dann Archiv.
Modellwahl wie B, explizit statt erkannt.

**D, die einfachste Form: nichts schalten, zwei Listen.** Keine Modellwahl je Aufgabe. Zwei
feste Zuordnungen, wie sie heute schon stehen: groß für Urteil (Karl im Bot, Gerd, Marv),
Sonnet für alles andere. Ollama erst, wenn der Mac mini als Ziel steht und Gerd den Netzweg
abgenommen hat. Ein Ort für Arbeit (Claude Code), einer für unterwegs (Bot). ChatGPT bleibt
privat.

| | A von selbst | B nur Bot | C die Datei | D zwei Listen |
|---|---|---|---|---|
| Ort | überall, verbunden | Bot | jede Oberfläche, die das Repo liest | Claude Code und Bot |
| Modellwahl | erkannt je Aufgabe | zwei je Identität, auf Ansage | zwei je Identität, auf Ansage | eine je Identität, fest |
| Gedächtnis | überall synchron, Brücke nötig | im Bot, Repo | im Repo, eine Wahrheit | im Repo |
| Kosten | Erkennung kostet einen Aufruf je Nachricht; Brücke unbekannt | Bot per API, Abo entlastet | wie B, Abo für Werkstatt | wie heute |
| Aufwand | Wochen, Brücke ungewiss | Tage: Konfiguration, ein Schaltwort | Tage: wie B plus Marlenes und Marvs Gedächtnis | null |
| Risiko | Erkennung irrt, Brücke nie fertig | unterwegs gut, am Schreibtisch umständlich | Cowork-Zugriff aufs Repo ungeprüft | Sichtungsarbeit weiter auf Sonnet-Preis |

## 5. Drei Sichten, vorher benannt

**Tobias, Alltag:** Weiß ich beim Aufmachen, wo der Mitarbeiter ist? Erinnert er sich?
Kostet mich das Schalten Handgriffe? Wird die Antwort besser?

**Gerd, Prüfer:** Kommt der Empfänger und das Modell aus dem Datensatz oder aus einer
Erkennung? Steht in der Auditzeile, welches Modell geantwortet hat? Bleibt die Datengrenze
eine Konstante je Modell? Was verlässt das Haus?

**Wolle, Zahlen (ruht bis Oktober, hier als Sicht):** Was kostet eine Sichtungsantwort?
Was kostet die Erkennung? Was kostet der Mac mini im Betrieb gegen die API? Ist es
gedeckelt?

## 6. Die Matrix

| Sicht und Frage | A | B | C | D |
|---|---|---|---|---|
| Tobias: weiß, wo | 3, überall heißt nirgends | 5, ein Ort | 4, jede Oberfläche, die liest | 4, zwei Orte, klar |
| Tobias: erinnert sich | 2, Brücke nötig | 4, Bot liest Repo | 5, Datei ist die Wahrheit | 4 |
| Tobias: Handgriffe | 5, keine | 4, ein Wort | 4, ein Wort | 5, keine |
| Tobias: Antwort besser | 3, wenn Erkennung trifft | 4 | 4 | 3, Sichtung teuer, Denken ok |
| Gerd: aus dem Datensatz | 1, Erkennung ist Modellausgabe | 5, Konfiguration | 5 | 5 |
| Gerd: Modell im Audit | 3, vorhanden, aber Erkennung nicht | 5 | 5 | 5 |
| Gerd: Grenze je Modell | 2, wechselnde Modelle, eine Grenze | 4 | 4 | 5 |
| Gerd: verlässt das Haus | 2, Brücke ist ein zweiter Weg | 4 | 4 | 4 |
| Wolle: Sichtung billig | 4, Haiku oder lokal | 4 | 4 | 2 |
| Wolle: Erkennung | 1, ein Aufruf mehr je Nachricht | 5, keine | 5 | 5 |
| Wolle: Mac mini gegen API | 3, offen | 3 | 3 | 4, kein Strom |
| Wolle: gedeckelt | 4 | 5 | 5 | 5 |
| **Summe** | **33** | **52** | **52** | **51** |

Die Erkennung ist der Punkt, an dem A verliert: Sie ist eine Modellausgabe, die entscheidet,
welches Modell antwortet, genau das, was Invariante 3 für den Empfänger verbietet, und sie
kostet einen Aufruf je Nachricht, bevor die Arbeit beginnt.

## 7. Fazit

**Empfehlung: C, die Datei ist der Mitarbeiter, mit Auflagen aus B und D.**

1. **Aus C: Gedächtnis für alle sieben, jetzt.** Marlene und Marv bekommen ihre Datei; der
   Wächter `test_identitaeten.py` verlangt für jede Registeridentität ein Gedächtnis. Die
   ChatGPT-Verläufe werden einmal exportiert, in die Dateien übertragen und sind dann
   Archiv. Ab dann gilt: Was nicht in `skills/gedaechtnis/` steht, weiß der Mitarbeiter
   nicht, egal wo er läuft. Das ist die Antwort auf „zusammengedachte Erinnerungen".
2. **Aus B: zwei Modelle je Identität, explizit.** Die Konfiguration bekommt je Identität
   `model` für Sichten und `model_deep` für Denken; Standard ist Sichten. Ein Schaltwort am
   Anfang der Nachricht (Vorschlag: `!` oder `denk:`) wählt Denken; das Wort kommt aus dem
   Datensatz, nicht aus einer Erkennung. Jede Antwort trägt schon heute das Modell im Audit.
   Für Marlene heißt das: Sichten auf Haiku oder Sonnet, Denken auf Opus; für Karl: Sonnet
   und Opus. In Claude Code bleibt der Agentenkopf, wie er ist; für schwere Aufgaben ruft
   der CEO Karl als Skill im laufenden Fenster, das ist heute Fable, und das ist richtig
   so: der Überblick sitzt beim teuersten Modell, das nur der CEO aufruft.
3. **Aus D: Ollama erst mit Ziel und Netzweg.** Kein Open-Source-Modell, bevor der Mac mini
   als Ziel gemessen ist und Gerd den Weg NAS → Mac mini abgenommen hat (`G-092`). Bis dahin
   ist Haiku die billige Stufe. Der Mac mini M1 ist für Sichtungsarbeit vermutlich
   ausreichend, das ist eine Annahme.
4. **Keine Brücke zwischen Anbietern.** Es gibt keine belegte Brücke von ChatGPT nach
   Claude, und sie wäre ein zweiter Weg nach draußen (Invariante 8). ChatGPT bleibt privat,
   ohne Mitarbeiternamen. Cowork ist nur dann ein Ort, wenn es das Repo lesen kann; das ist
   zu prüfen, bevor dort ein Name steht.
5. **Der Workforce Bus lebt.** Der Neubau ist der Bus in kleiner Form: ein Kern, eine
   Datengrenze, Adapter außen. Ein neuer Ort ist ein Adapter, der dieselben zwei Dateien
   liest, keine Brücke zwischen Anbietern.

**Jetzt oder warten?** Auflage 1 jetzt, ein Tag, ohne Deploy. Auflage 2 als Meilenstein
nach dem Phase-3-Deploy, mit Gerds Review, weil sie den Kern anfasst. Auflage 3 warten.

**Der Test, der die Entscheidung hält:** `test_identitaeten.py` verlangt je Registeridentität
eine Gedächtnisdatei; `test_workforce.py` verlangt, dass beide Modelle einer Identität in der
Allowlist stehen und dass das Schaltwort das Modell im Audit ändert, das Modell in der
Antwort aber nie aus der Modellausgabe kommt.

**Offene Fragen, nur der CEO:**

- **Welches Schaltwort für Denken?** Empfehlung: `!` am Anfang, weil kürzer als ein Wort am
  Telefon. Optionen: (a) `!`; (b) `denk:`; (c) je Identität ein eigenes.
- **Ist die ChatGPT-Assistentin eine Mitarbeiterin?** Empfehlung: nein, sie hat kein
  Gedächtnis im Repo und kann keins lesen; ihr Verlauf wird exportiert und geht an Marlene.
  Optionen: (a) Export, dann Archiv; (b) weiterführen als privates Werkzeug ohne Namen;
  (c) als Mitarbeiterin ins Register, dann muss sie das Repo lesen können, was ChatGPT nicht kann.
- **Gerds LLM-Server aus Codex:** im Repo nicht vorhanden. Empfehlung: Gerd legt ihn ins
  Repo oder erklärt ihn für Archiv; bis dahin zählt er nicht.

**Die eine Sache, die am ehesten noch falsch ist:** dass die schlechten Antworten am Modell
liegen. Wahrscheinlicher liegen sie am fehlenden Gedächtnis und am fehlenden Skill dort, wo
die Assistentin gerade läuft; Opus ohne Gedächtnis antwortet „jenseits von Gut und Böse",
Sonnet mit Gedächtnis nicht. Auflage 1 prüft das, bevor Auflage 2 Geld kostet.

Kontrolle: Am Donnerstag sehe ich nach, ob die drei Fragen beantwortet sind und ob der Export vorliegt.

Nächster Schritt: Der CEO beantwortet die drei Fragen am 2026-09-10 und liefert den ChatGPT-Export; Owner Tobias.

## Nachtrag 2026-09-08: Antworten des CEO

„!", „Export", „Gerd legt ihn ins Repo". Damit: Schaltwort `!`; die ChatGPT-Assistentin wird exportiert und ist dann Archiv, der Verlauf geht an Marlene; Gerd bringt den LLM-Server ins Repo, bis dahin zählt er nicht. Auflage 1 umgesetzt: Gedächtnis für Marlene und Marv, Verweis in beiden Skills, Wächter in `test_identitaeten.py`. Der Export selbst steht noch aus.
