# Schnellstart

Python 3.11+ und Poetry installieren, dann im Projektverzeichnis:

```bash
poetry install
poetry run python src/main.py
```

Für gescannte Dokumente zusätzlich Tesseract mit den gewünschten Sprachdaten installieren. Prüfen mit `tesseract --list-langs`: Deutsch benötigt `deu`, Englisch `eng`.

PDFs hinzufügen, je Datei Metadaten bearbeiten, Einstellungen prüfen und **Start Conversion** wählen. Der Ausgabeordner wird beim Start abgefragt. Vorhandene Bücher werden durch nummerierte Ausgaben geschützt.

Vollständige Installationshinweise, Systemvoraussetzungen, Sicherheitsgrenzen und Tests stehen im [README](README.md).
