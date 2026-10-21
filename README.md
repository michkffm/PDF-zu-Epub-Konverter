# PDF to EPUB Converter

A Python desktop application for turning digital and scanned PDFs into EPUB e-books. Select files, edit their metadata and run conversions from a PyQt6 interface.

**Python · PyQt6 · pdfplumber · Tesseract OCR · ebooklib · Pillow**

<p align="center"><img src="assets/branding/logo.png" alt="PDF to EPUB Converter logo" width="280"></p>

![Desktop interface with file list, metadata editor and conversion controls](docs/screenshot.png)

## Implemented features

- Text and image extraction from digital PDFs, with a fallback extractor.
- Optional OCR for scanned PDFs using Tesseract.
- A file queue, editable title/author/language/description and output-folder selection.
- Background conversion with progress messages and a conversion log.
- Image optimization and EPUB generation.
- Structural EPUB validation in the conversion worker.

This is a development project. Complex layouts, tables and reading order still need manual review in the resulting e-book. The built-in validator is not a replacement for external EPUB conformance testing. A command-line interface and an integrated EPUB reader are not provided by the current application entry point.

## Quick start

The project declares Python 3.9 or newer. The checks below were run with an existing Python 3.14 environment on macOS; other platforms were not verified in this review. Install [Poetry](https://python-poetry.org/docs/#installation) and, for scanned documents, [Tesseract](https://tesseract-ocr.github.io/tessdoc/Installation.html) including the required language data.

```bash
git clone https://github.com/michkffm/PDF-zu-Epub-Konverter.git
cd PDF-zu-Epub-Konverter
poetry install --no-root
poetry run python src/main.py
```

Tesseract is optional for digital text-based PDFs. To inspect the OCR languages available on your system:

```bash
tesseract --list-langs
```

## Using the application

1. Add PDFs through the File menu and select an output folder.
2. Review the metadata and conversion settings.
3. Enable OCR only when needed and select an installed OCR language.
4. Start conversion and follow the progress and log messages.
5. Open the generated EPUB in an e-book reader to check the result.

The application processes documents locally. The normal launcher stores its diagnostic log under `~/.pdf_epub_converter/converter.log`; use non-confidential sample files when reporting issues and review logs before sharing them.

## Architecture

| Location | Responsibility |
| --- | --- |
| `src/main.py` | Desktop application entry point |
| `src/pdf_epub_converter/gui/` | PyQt6 window, metadata and settings |
| `src/pdf_epub_converter/core/` | PDF extraction, metadata, EPUB creation and validation |
| `src/pdf_epub_converter/workers/` | Background conversion and OCR |
| `src/pdf_epub_converter/utils/` | Image optimization and logging |
| `tests/` | Core, OCR and GUI tests |

The GUI delegates conversion work to a worker thread, allowing the interface to display progress while documents are processed.

## Tests and verification

Install the development extras and run the existing tests:

```bash
poetry install --no-root --extras dev
poetry run pytest tests -q
```

For GUI tests in an environment without a display:

```bash
QT_QPA_PLATFORM=offscreen poetry run pytest tests -q
```

On 21 October 2026, **49 tests passed** using the existing Python environment and `QT_QPA_PLATFORM=offscreen`. The desktop window was also opened for the screenshot. These checks do not establish conversion quality for arbitrary real-world PDFs or compatibility with every operating system.

## Documentation status and license

This README reflects the current source tree. Older phase reports and roadmap documents remain historical development notes and may differ from the implementation.

The previous project description identifies the license as MIT; a separate `LICENSE` file is not currently included in this repository.

Copyright © Michael Koch 2026.

[GitHub profile](https://github.com/michkffm) · [Interactive portfolio](https://michael-koch-portfolio.onrender.com/)
