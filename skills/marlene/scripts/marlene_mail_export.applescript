-- marlene_mail_export.applescript
--
-- Wird von einer Mail-Regel aufgerufen: "Regeln ausfuehren" -> "AppleScript ausfuehren".
-- Schreibt jede durchgelassene Nachricht als .eml in Marlenes Eingang. Mehr nicht:
-- kein Loeschen, kein Verschieben im Postfach, kein Senden, kein Zugriff auf andere Ordner.
--
-- Warum .eml und nicht PDF: die .eml traegt die Anhaenge mit. Bei einer Belegmail ist
-- die Rechnung der Anhang, nicht der Text. marlene_eml.py packt sie danach aus.
--
-- Das Ziel ist hier fest eingetragen und nicht aus der Umgebung gelesen: eine Mail-Regel
-- laeuft ohne Terminal, und ein Ziel, das jemand von aussen setzen kann, waere ein Weg
-- nach draussen (dieselbe Regel wie beim Deploy-Helfer, Befund G-090).

property zielOrdner : "/Users/Tobi/Library/CloudStorage/GoogleDrive-Tobias.kuehm@icloud.com/Meine Ablage/01_Ablage_Eingang/"

on sauber(t)
	set ergebnis to ""
	set erlaubt to "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"
	repeat with i from 1 to (count of characters of t)
		set c to character i of t
		if c is in erlaubt then
			set ergebnis to ergebnis & c
		else if c is in {" ", "_", ".", ",", "/", ":"} then
			if ergebnis does not end with "-" and ergebnis is not "" then set ergebnis to ergebnis & "-"
		else if c is "ä" or c is "Ä" then
			set ergebnis to ergebnis & "ae"
		else if c is "ö" or c is "Ö" then
			set ergebnis to ergebnis & "oe"
		else if c is "ü" or c is "Ü" then
			set ergebnis to ergebnis & "ue"
		else if c is "ß" then
			set ergebnis to ergebnis & "ss"
		end if
	end repeat
	if ergebnis ends with "-" then set ergebnis to text 1 thru -2 of ergebnis
	if (count of characters of ergebnis) > 40 then set ergebnis to text 1 thru 40 of ergebnis
	return ergebnis
end sauber

on zweistellig(n)
	if n < 10 then return "0" & n
	return n as string
end zweistellig

using terms from application "Mail"
	on perform mail action with messages nachrichten for rule meineRegel
		tell application "Mail"
			repeat with m in nachrichten
				try
					set d to date received of m
					set datumsteil to (year of d as string) & "-" & my zweistellig(month of d as integer) & "-" & my zweistellig(day of d)
					set absender to my sauber(extract name from sender of m)
					if absender is "" then set absender to my sauber(extract address from sender of m)
					set betreff to my sauber(subject of m)
					if betreff is "" then set betreff to "ohne-Betreff"
					set basis to datumsteil & "_" & absender & "_" & betreff
					set pfad to zielOrdner & basis & ".eml"
					-- nie ueberschreiben: eine zweite Mail gleichen Namens bekommt einen Zusatz
					set n to 2
					repeat while my existiert(pfad)
						set pfad to zielOrdner & basis & "-" & (n as string) & ".eml"
						set n to n + 1
						if n > 50 then exit repeat
					end repeat
					set quelle to source of m
					set f to open for access (POSIX file pfad) with write permission
					set eof f to 0
					write quelle to f as «class utf8»
					close access f
				on error fehler
					try
						close access f
					end try
					do shell script "echo " & quoted form of ("marlene_mail_export: " & fehler) & " >> /tmp/marlene_mail_export.log"
				end try
			end repeat
		end tell
	end perform mail action with messages
end using terms from

on existiert(p)
	try
		do shell script "test -e " & quoted form of p
		return true
	on error
		return false
	end try
end existiert
