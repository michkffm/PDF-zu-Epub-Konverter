# PDF to EPUB Converter 📚

A professional, feature-rich desktop application for converting PDF documents to EPUB3 e-book format.

## Features 🚀

- **Digital PDF Support**: Extract text, images, and metadata from text-based PDFs
- **Scanned PDF Support**: OCR integration with Tesseract for scanned documents
- **Batch Conversion**: Convert multiple PDFs in one operation
- **Metadata Editing**: Edit title, author, language, cover image, and more
- **EPUB Preview**: View converted EPUBs directly in the application
- **Quality Reports**: Automatic validation and quality checks after conversion
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Tech Stack 🛠️

- **Language**: Python 3.9+
- **GUI Framework**: PyQt6
- **PDF Processing**: pdfplumber (digital), PyPDF2 (fallback)
- **OCR**: pytesseract + Tesseract-OCR
- **EPUB Creation**: ebooklib
- **Image Processing**: Pillow

## Installation 💾

### Prerequisites

1. **Python 3.9+**
2. **Tesseract-OCR** (for scanned PDF support)
   - **macOS**: `brew install tesseract`
   - **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - **Linux**: `sudo apt-get install tesseract-ocr`

### Setup

```bash
# Clone or download the repository
cd "PDF zu Epub Konverter"

# Install dependencies with Poetry
poetry install --no-root

# Activate virtual environment
poetry shell
```

## Usage 🎯

### Run the Application

```bash
poetry run python src/main.py
```

### Command-Line Interface (Coming in Phase 3)

```bash
pdf-epub-converter convert input.pdf -o output.epub
```

## Project Structure 📁

```
src/
├── main.py                          # Application entry point
├── gui/                             # PyQt6 GUI components
│   ├── main_window.py               # Main application window
│   └── widgets/                     # UI widgets
├── core/                            # Core conversion logic
│   ├── pdf_extractor.py             # PDF text/image extraction
│   ├── epub_builder.py              # EPUB document creation
│   ├── metadata.py                  # Metadata management
│   └── quality_checker.py           # EPUB validation
├── workers/                         # Background thread workers
│   └── conversion_worker.py         # Async conversion
└── utils/                           # Utilities
    ├── logger.py                    # Logging configuration
    ├── config.py                    # App configuration
    └── validators.py                # Input validation

tests/                              # Unit and integration tests
docs/                               # Documentation
```

## Development 🔧

### Phase 1: Foundation ✅ (In Progress)
- [x] Project setup with Poetry
- [x] Logging system
- [x] Metadata manager
- [x] Digital PDF extractor
- [x] EPUB builder
- [x] Basic unit tests

### Phase 2: Advanced PDF (In Progress)
- [ ] OCR integration (Tesseract)
- [ ] Image extraction and optimization
- [ ] Layout analysis
- [ ] Scanned PDF support

### Phase 3: GUI & User Interaction
- [ ] PyQt6 main window
- [ ] Drag-and-drop upload
- [ ] Batch conversion
- [ ] Metadata editor dialog
- [ ] Progress tracking

### Phase 4: Preview & Quality
- [ ] EPUB validator
- [ ] HTML preview widget
- [ ] Quality report generation

### Phase 5: Integration & Polish
- [ ] Config system
- [ ] End-to-end workflows
- [ ] Full error handling
- [ ] Documentation
- [ ] Packaging/Distribution

## Testing 🧪

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_phase1.py -v

# Run with coverage
poetry run pytest --cov=src tests/
```

## Troubleshooting 🐛

### Tesseract Not Found
If you get "Tesseract not found" errors:
- macOS: `brew install tesseract`
- Check installation: `tesseract --version`

### PDF Extraction Issues
- Try with a different PDF file to isolate the issue
- Check PDF corruption: Open in Adobe Reader
- For scanned PDFs, check if Tesseract is installed

## Contributing 🤝

Contributions are welcome! Feel free to submit issues or pull requests.

## License 📄

MIT License - see LICENSE file for details

## Roadmap 🗺️

- [ ] v0.2: Scanned PDF + OCR support
- [ ] v0.3: Full GUI implementation
- [ ] v0.4: Quality checks & preview
- [ ] v1.0: Production release with all features

## Contact 📧

maintainer: michkffm (michael.koch@vodafone.de)

---

**Status**: Phase 1 Foundation - Core modules implemented, testing in progress
