# Bedienungsanleitung

## Dateien und Metadaten

Über **File → Open PDF(s)** eine oder mehrere PDFs hinzufügen. Eine Datei in der Liste auswählen und Titel, Autor, Buchsprache und Beschreibung bearbeiten. Beim Wechsel werden diese Eingaben pro Datei gespeichert. Während der Konvertierung sind Dateiliste und Einstellungen gesperrt, damit laufende Aufträge konsistent bleiben.

## Einstellungen

- **OCR Disabled:** nur vorhandenen PDF-Text lesen.
- **Auto-detect:** Seiten ohne extrahierbaren Text mit OCR lesen; bereits vorhandenen Text erhalten.
- **Always Enabled:** alle Seiten mit OCR lesen.
- **OCR Language:** muss in Tesseract installiert sein; `de` entspricht `deu`.
- **Image Optimization:** deaktiviert, normal oder aggressive JPEG-Komprimierung.
- **EPUB Validation:** Strukturprüfung aktivieren oder ausdrücklich abschalten.

OCR kann Erkennungsfehler erzeugen. Eine Seite mit vorhandenem Text und zusätzlichen Textbildern wird im Auto-Modus nicht vollständig per OCR gelesen; dafür bei Bedarf Always Enabled wählen.

## Konvertieren und abbrechen

**Start Conversion** öffnet die Ordnerauswahl. Die Warteschlange wird nacheinander abgearbeitet. Gleiche Namen erhalten einen nummerierten Zusatz. Erfolg und Fehler erscheinen im Protokoll; Fehler stoppen die übrigen Dateien nicht.

**Stop** verwirft wartende Aufträge und bricht die aktuelle Verarbeitung an der nächsten sicheren Stelle ab. Ein laufender OCR-Aufruf kann bis zu 60 Sekunden benötigen; Rendering wird separat überwacht und spätestens nach 30 Sekunden beendet. Beim Schließen während der Verarbeitung wird zunächst abgebrochen. Danach erneut schließen.

## Ergebnis prüfen

EPUB im eigenen Reader öffnen. Textlayout und Kapitel können vom Original abweichen. Extrahierte Bilder stehen in einem separaten Illustrationskapitel, nicht an ihrer ursprünglichen Textposition. Der interne Prüfer kontrolliert Grundstruktur und XML, ersetzt aber keine vollständige EPUB-Konformitätsprüfung.

Grenzen, Installation, Logs, Tests und Hostingstatus: [README](README.md).
