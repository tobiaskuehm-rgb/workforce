# Postboxen: wie ein Dokument aus einem Konto herauskommt

## Der Satz, um den es geht

**Das Postbox-Problem löst man nicht, indem die Assistentin in die Postbox kommt, sondern indem das Dokument die Postbox verlässt.**

Jeder Versuch, Marlene in ein Portal zu bringen, endet bei einem Zugangsdatum, das handeln kann. Der Umweg über die Zustellung endet bei einer Datei im Eingang und ändert an den Rechten nichts.

## Der Fehler, den man dabei zuerst macht

Die naheliegende Idee ist, Marlenes Adresse bei den Anbietern zu hinterlegen. Das ist **kein Lesekanal, sondern ein Generalschlüssel**: Bei den meisten Anbietern setzt man das Passwort über die hinterlegte Adresse zurück. Wer sie liest, kann sich Zugang verschaffen, ganz ohne Passwort.

Daraus folgt die Trennung, die nicht verhandelbar ist:

- Die **Konto- und Wiederherstellungsadresse** bleibt bei Tobias. Immer.
- Marlenes Adresse wird nur dort eingetragen, wo der Anbieter eine **zusätzliche Benachrichtigungsadresse** getrennt führt, die für keine Wiederherstellung taugt.
- Wo der Anbieter das nicht trennt, bleibt die Adresse draußen und die Regel im Postfach von Tobias erledigt die Arbeit.

## Vier Wege, nach Güte

**1. Vollmacht mit eigenem Zugang.** Die sauberste Form: Der Bevollmächtigte bekommt **eigene Zugangsdaten**, kein geteiltes Passwort. Eigene Identität, eigene Rechte, einzeln widerrufbar, im Protokoll unterscheidbar. Bei der ING ist das belegt: Wer bevollmächtigt wird und noch kein Kunde ist, wird identifiziert und legt danach eigene Zugangsdaten an. Voraussetzung ist eine natürliche Person; ein Programm kann nicht bevollmächtigt werden. Zu prüfen ist je Anbieter, ob sich die Rechte auf Lesen begrenzen lassen.

**2. Der Anbieter liefert das Dokument selbst per Mail.** Wo sich einstellen lässt, dass Dokumente zusätzlich als Anhang kommen, ist die Sache erledigt: Die Mail-Regel fängt sie, Marlene hat das Original, niemand muss irgendwo hinein. Bei Versicherern und Versorgern häufig, bei Banken selten.

**3. Die Benachrichtigung wird zur Aufgabe.** Der Weg, der überall funktioniert. Die Bank schickt „neue Nachricht in der Post-Box" an Tobias, die Regel erkennt das, Marlene legt eine Aufgabe an und hält sie offen, bis das Dokument da ist. Tobias teilt es mit einem Tipp aus der App. Kein Zugangsdatum wandert, und die Aufgabe verschwindet nicht, wenn er es vergisst.

**4. Wo die App das Einreichen selbst kann, braucht es die Postbox gar nicht.** Die Debeka nimmt Belege in ihrer Leistungs-App per Foto, QR-Code oder PDF entgegen, und bei bestehender Beihilfeversicherung lässt sich der Beihilfeantrag mit denselben Rechnungen über die App mitschicken. Damit ist ein medizinischer Vorgang ohne Papier, ohne Unterschrift und ohne geteilten Zugang erledigt.

## Was Marlene dafür führt

Das Vertragsregister bekommt eine Spalte **Zustellweg** mit vier Werten:

| Wert | Bedeutung | Was Marlene tut |
|---|---|---|
| `Papier` | kommt mit der Post | Scanner, sonst nichts |
| `Mail mit Anhang` | Anbieter schickt das Dokument | Regel fängt es, fertig |
| `Postbox` | nur Benachrichtigung, Dokument bleibt im Portal | Aufgabe anlegen, offen halten, an Tobias erinnern |
| `App` | Einreichen und Empfangen läuft über eine App | Mappe vorbereiten, Tobias tippt |

Steht dort `Postbox`, ist das ein Verbesserungskandidat: Beim nächsten Kontakt mit dem Anbieter wird geprüft, ob sich `Mail mit Anhang` einstellen lässt. Das ist keine einmalige Umstellung, sondern eine, die mit jedem Anbieter einzeln besser wird.

## Was ausdrücklich nicht gemacht wird

Zugangsdaten in einem Tresor, auf den ein Programm zugreift; Browser-Automatisierung mit gespeicherter Sitzung; geteilte Zwei-Faktor-Codes. Alle drei verschaffen Zugang zur Postbox und geben dabei Handlungsmacht ab, die sich nicht auf Lesen begrenzen lässt.

## Quellen

- ING, Hilfe zur Post-Box (Benachrichtigung geht an die persönliche Adresse), https://www.ing.de/hilfe/persoenliches/postbox/
- ING, Vollmacht (Bevollmächtigte erhalten eigene Zugangsdaten), https://www.ing.de/hilfe/persoenliches/vollmacht/
- Debeka, Leistungs-App „Debeka Gesundheit" (Belege per Foto, QR oder PDF; Beihilfeantrag über die App), https://www.debeka.de/service/apps/leistungs-app.html
