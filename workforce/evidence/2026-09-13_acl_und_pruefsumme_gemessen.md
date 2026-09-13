# Nachweis: ACL-Wächter und Prüfsummen-Fehlerpfad, an der NAS gemessen, 2026-09-13

Anlass: Der Code-Review vom 2026-09-12 fand drei Wächter, die bei einem Fehlschlag grün
melden. Nach der Korrektur waren zwei Fragen offen, die nur die NAS beantwortet.

## 1. `synoacltool` liegt nicht im Pfad

```
command -v synoacltool  ->  FEHLT
ls -l /usr/syno/bin/synoacltool  ->  -rwxr-xr-x root root 33394
```

Derselbe Fall wie `docker` und `/usr/local/bin/docker`: In einer nicht-interaktiven
SSH-Sitzung fehlt der Pfad. Mein erster Entwurf hätte **jeden** Deploy mit
„synoacltool fehlt" abgebrochen.

## 2. Das Muster fand echte ACL-Einträge nicht

`/volume1/docker` trägt acht Einträge (`drwxrwxrwx+`, `[0] user:Drucker:deny:…`). Die Zeilen
beginnen mit einem **Tabulator**:

```
Muster ^ *\[[0-9]          ->  ACL:0   (falsch)
Muster ^[[:space:]]*\[[0-9] ->  ACL:8   (richtig)
```

Der Wächter war also nach der Korrektur immer noch blind. Gefunden nur, weil gegen einen Pfad
gemessen wurde, an dem er anschlagen **muss** — die eigene Attrappe hätte das nie gezeigt.

## 3. Stand nach beiden Korrekturen, gegen die echte NAS

```
/volume1/docker/workforce, /secrets, /config.json  ->  ACL:0 ACL:0 ACL:0
Gegenprobe /volume1/docker                          ->  ACL:8
```

## 4. Fehlerpfad der Prüfsumme (`G-119`)

Im Wegwerf-Container auf der NAS, Busybox:

```
abweichende Zeile   -> exit 1
gleiche Zeile       -> exit 0
fehlende Datei      -> exit 1
```

`G-119` ist damit gemessen, nicht abgeleitet.

**Nicht gemessen:** ein vollständiger Deploy mit den neuen Prüfungen; der steht am 2026-09-14 an.
