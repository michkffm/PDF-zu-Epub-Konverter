<div align="center">

<img src="assets/branding/logo.png" alt="PDF zu EPUB Konverter" width="200">

# PDF → EPUB Konverter

### Dein Dokument. Dein Lesefluss.

PDFs lokal in flexible E-Books verwandeln – mit Texterkennung, Metadaten-Editor und einer übersichtlichen Desktop-Oberfläche.

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![PyQt6 Desktop](https://img.shields.io/badge/Oberfl%C3%A4che-PyQt6-174C40)](#funktionen)
[![Lokale Verarbeitung](https://img.shields.io/badge/Verarbeitung-lokal-174C40)](#sicherheit-und-lokale-daten)

**[Projektseite ansehen ↗](https://michkffm.github.io/PDF-zu-Epub-Konverter/)** · [Schnellstart](#installation) · [Bedienungsanleitung](USER_GUIDE.md) · [Fehler melden](https://github.com/michkffm/PDF-zu-Epub-Konverter/issues)

</div>

---

> **Desktop-Anwendung:** Deine PDFs werden auf deinem Rechner verarbeitet. Die Projektseite erklärt das Programm; sie bietet keinen Online-Upload oder Browser-Konverter.

## Einblick

![Desktop-Anwendung mit Dateiliste, Metadaten-Editor und Konvertierungsfortschritt](docs/screenshot.png)

*Der Screenshot zeigt einen früheren Oberflächenstand. Warteschlange und Ordnerauswahl wurden inzwischen überarbeitet.*

## Funktionen

| Funktion | Was du damit machen kannst |
| --- | --- |
| **PDF → EPUB** | Textbasierte PDFs in E-Books mit anpassbarem Textfluss umwandeln. |
| **Texterkennung / OCR** | Gescannte Seiten mit Tesseract lesen: automatisch für textlose Seiten oder ausdrücklich für alle Seiten. |
| **Warteschlange** | Mehrere Dateien nacheinander verarbeiten und bei Bedarf abbrechen. |
| **Metadaten-Editor** | Titel, Autor, Sprache und Beschreibung pro Datei festlegen. |
| **Bilder** | Illustrationen extrahieren, optional komprimieren und in einem eigenen Kapitel anzeigen. |
| **Geschützte Ausgabe** | Ausgabeordner wählen und bestehende EPUBs durch nummerierte Dateinamen erhalten. |
| **Strukturprüfung** | Grundstruktur und XML des erzeugten EPUBs vor der Ausgabe prüfen. |

PDFs haben feste Seitenlayouts. Das Ergebnis ist ein neu fließendes E-Book, keine originalgetreue Kopie. Tabellen, Spalten, Formeln und die genaue Position von Bildern können abweichen. Kapitel werden nach Textlänge aufgeteilt; eine semantische Kapitelerkennung ist nicht implementiert. Der integrierte Strukturprüfer ersetzt keine vollständige EPUBCheck-Prüfung.

## Installation

Du brauchst **Python 3.11 oder neuer**, [Poetry](https://python-poetry.org/docs/#installation) und Git für den folgenden Schnellstart. Tesseract ist nur für gescannte Dokumente erforderlich.

### In vier Befehlen starten

```bash
git clone https://github.com/michkffm/PDF-zu-Epub-Konverter.git
cd PDF-zu-Epub-Konverter
poetry install
poetry run python src/main.py
```

Unter macOS/Linux sind alternativ `./setup.sh` und `./run_gui.sh` nutzbar. Das Setup installiert die Python-Pakete aus der Lockdatei; es installiert keine Systemsoftware und führt keine heruntergeladenen Installationsskripte aus.

### OCR einrichten

Für reine Text-PDFs ist Tesseract nicht erforderlich. Für Scans installiere [Tesseract samt Sprachdaten](https://tesseract-ocr.github.io/tessdoc/Installation.html). Die Anwendung benötigt kein separates Poppler oder pdf2image: Die Rasterisierung nutzt den bereits von pdfplumber mitgelieferten Renderer.

```bash
# macOS mit vorhandenem Homebrew, einschließlich deutscher Sprachdaten:
brew install tesseract tesseract-lang

# Debian/Ubuntu:
sudo apt install tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng

# Verfügbare Sprachen prüfen:
tesseract --list-langs
```

Unter Windows Tesseract nach der verlinkten Anleitung installieren und sein Verzeichnis zum `PATH` hinzufügen. `de` in der Oberfläche benötigt `deu`, `en` benötigt `eng`. Fehlende Sprachdaten werden mit einer konkreten Fehlermeldung angezeigt.

## Bedienung

1. Über **File → Open PDF(s)** Dateien hinzufügen.
2. Je Datei die Metadaten prüfen; beim Wechsel bleiben Eingaben erhalten.
3. In **Settings** OCR, OCR-Sprache, Bildoptimierung und Validierung einstellen.
4. **Start Conversion** wählen und den Ausgabeordner festlegen.
5. Fortschritt im Fenster verfolgen und das fertige Buch im eigenen EPUB-Reader prüfen.

**Stop** leert die verbleibende Warteschlange und fordert den laufenden Auftrag zum Abbruch auf. Die Oberfläche bleibt bedienbar. Ein bereits laufender Tesseract-Aufruf endet spätestens nach seinem 60-Sekunden-Limit; Rendering läuft separat mit 30-Sekunden-Limit und kann vorher beendet werden. Beim Schließen während einer Konvertierung wird zunächst abgebrochen; danach das Fenster erneut schließen.

Ein fehlgeschlagener Auftrag wird protokolliert; die nächste Datei wird trotzdem versucht. Erfolgreiche Dateien verschwinden aus der Liste, fehlgeschlagene bleiben zur erneuten Bearbeitung stehen.

## Plattformen

| Plattform | Aktueller Prüfstand |
| --- | --- |
| **macOS** | Automatisierte GUI-Tests und echte Text-/Scan-Konvertierungen mit Python 3.14 erfolgreich geprüft. |
| **Windows** | Durch Python und PyQt grundsätzlich möglich; Installation und Laufzeit noch nicht praktisch abgenommen. |
| **Linux** | Durch Python und PyQt grundsätzlich möglich; Installation und Laufzeit noch nicht praktisch abgenommen. |
| **Browser / Smartphone** | Keine entsprechende Konverter-Anwendung enthalten. |

## Sicherheit und lokale Daten

- PDF-/OCR-Text wird als Klartext in XHTML eingebettet. Tags aus PDFs werden nicht als aktive Buchinhalte übernommen.
- Maximal 100 MiB pro PDF, 500 Seiten, 16 Megapixel pro gerenderter Seite, 500 extrahierte Bilder und 200 MiB extrahierte Bilddateien pro Auftrag.
- OCR verarbeitet Seiten einzeln und nutzt Zeitlimits. Rasterisierung läuft in einem separaten, zeitlich begrenzten Prozess. Diese Grenzen sind keine vollständige Betriebssystem-Sandbox.
- Temporäre Bilder und Zwischenbücher werden in privaten temporären Verzeichnissen verarbeitet und nach Erfolg, Fehler oder Abbruch aufgeräumt. Bei einem erzwungenen Prozess-/Systemabsturz kann das Betriebssystem temporäre Reste zurücklassen.
- Bestehende EPUBs werden weder von der Oberfläche noch vom direkten Schreibpfad überschrieben.
- Die Anwendung lädt keine PDFs hoch. Lokale Diagnosemeldungen können Dateinamen und Metadaten enthalten: `~/.pdf_epub_converter/converter.log`. Vor dem Teilen prüfen.

## Entwicklung und Prüfungen

Der Stack besteht aus **Python, PyQt6, pdfplumber, pytesseract, Pillow, ebooklib und lxml**. Die Python-Abhängigkeiten werden mit Poetry und `poetry.lock` verwaltet.

### Prüfungen ausführen

```bash
poetry install --extras dev
poetry run pytest tests -q
poetry run flake8 src --select=F401,F811,F821
poetry check --lock
poetry build
```

Ohne Bildschirm für GUI-Tests: `QT_QPA_PLATFORM=offscreen poetry run pytest tests -q`.

### Zuletzt verifiziert · 23. Oktober 2026

| Prüfung | Ergebnis |
| --- | --- |
| Tests unter macOS / Python 3.14 | **73 bestanden**, einschließlich englischer OCR-Integration |
| Gezielte Import- und Namensprüfung (`F401`, `F811`, `F821`) | Keine Befunde |
| Poetry-Konfiguration und Lockdatei | Erfolgreich geprüft |
| Paketbau | Wheel und Quellpaket erfolgreich erzeugt |
| Paketabgleich mit `pip-audit` | Keine bekannten Schwachstellen in der geprüften, synchronisierten Umgebung |

Diese Ergebnisse dokumentieren den genannten Prüfstand; sie sind kein automatisch aktualisierter CI-Status und keine Garantie für beliebige PDFs oder alle Betriebssysteme.

Die Regressionstests prüfen unter anderem tatsächliche Text-/Scan-Konvertierung, eingebundene Bilder, harmlose Ausgabe von HTML-Zeichen, Schutz vorhandener Bücher, Validierungsfehler, Abbruch, Renderlimits und mehrteilige Warteschlangen. OCR-Integrationstests werden bei fehlendem Tesseract/englischen Sprachdaten übersprungen; für vollständige Prüfung `eng` installieren.

## Projektstruktur

| Pfad | Aufgabe |
| --- | --- |
| `src/main.py` | Desktop-Startpunkt |
| `src/pdf_epub_converter/gui/` | Oberfläche und Warteschlange |
| `src/pdf_epub_converter/core/` | Extraktion, begrenztes Rendering, Metadaten, EPUB und Strukturprüfung |
| `src/pdf_epub_converter/workers/` | Hintergrundkonvertierung und OCR |
| `src/pdf_epub_converter/utils/` | Bildoptimierung und Logging |
| `tests/` | Modul- und Regressionstests |

## Projektseite und Dokumentation

Die **[Projektseite auf GitHub Pages](https://michkffm.github.io/PDF-zu-Epub-Konverter/)** ist veröffentlicht. Sie stellt Funktionen, Installation und Plattformen vor und verlinkt den Quellcode. Die Website liegt unter `docs/` und wird aus `main` veröffentlicht.

| Anlaufstelle | Inhalt |
| --- | --- |
| [Projektseite](https://michkffm.github.io/PDF-zu-Epub-Konverter/) | Überblick und Einstieg |
| [Kurzanleitung](QUICK_START.md) | Installation und erster Start |
| [Bedienungsanleitung](USER_GUIDE.md) | Einstellungen, Ablauf und Ergebnisprüfung |
| [GitHub Issues](https://github.com/michkffm/PDF-zu-Epub-Konverter/issues) | Fehler und Verbesserungsvorschläge |

Eine Browserversion des Konverters ist nicht enthalten. Dafür wären eine Weboberfläche und ein abgesicherter Python-Dienst erforderlich.

Die Phasenberichte und `FINAL_PROJECT_SUMMARY.md` bleiben historische Entwicklungsnotizen; für den aktuellen Funktionsumfang gilt dieses README.

## Lizenzstatus

Im früheren Projekttext wurde MIT genannt. Eine separate `LICENSE`-Datei liegt derzeit nicht vor; deshalb wird hier keine abgeschlossene Lizenzierung behauptet.

---

<div align="center">

Ein Projekt von **[Michael Koch](https://github.com/michkffm)** · Mit Python entwickelt, für den eigenen Lesefluss gemacht.

</div>
