# 🚀 QUICK START GUIDE

Get the PDF to EPUB Converter up and running in 5 minutes!

---

## ⚡ TL;DR (Super Quick)

```bash
cd "/Users/michaelkoch/Desktop/PDF zu Epub Konverter"
./setup.sh      # First time: ~2-3 minutes (installs everything)
./run_gui.sh    # Launches the app
```

---

## 📋 Prerequisites Check

Before starting, verify:
- ✅ macOS (Monterey or newer recommended)
- ✅ Internet connection (for first-time setup)
- ✅ ~2GB free disk space

---

## 🎯 5-Minute Setup

### Step 1: Navigate to Project (10 seconds)
```bash
cd "/Users/michaelkoch/Desktop/PDF zu Epub Konverter"
ls -la  # Should show setup.sh, run_gui.sh, src/, tests/, etc.
```

### Step 2: Run Setup (2-3 minutes)
```bash
./setup.sh
```

**What this does:**
- Installs Homebrew (if needed)
- Installs Python 3.11
- Installs Tesseract OCR
- Installs Poetry
- Installs all Python dependencies

**If setup fails:** Run the sections manually:
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11 tesseract

# Install Poetry
curl -sSL https://install.python-poetry.org | python3
export PATH="$HOME/.local/bin:$PATH"

# Setup project
poetry install --no-root
```

### Step 3: Launch GUI (30 seconds)
```bash
./run_gui.sh
```

**Expected output:**
```
╔════════════════════════════════════════════════════════════╗
║      PDF to EPUB Converter - Desktop Application 📚        ║
╚════════════════════════════════════════════════════════════╝

✓ Poetry found: Poetry (version 1.8.2)
✓ Dependencies already installed
🚀 Launching PDF to EPUB Converter GUI...
Window should appear in a moment...
```

### Step 4: GUI Appears (Should be instant)
- Window opens to 1200×800 px
- "PDF to EPUB Converter 📚" in title bar
- Ready to use!

### Step 5: Convert First PDF (1 minute)
1. Click **[+ Add]** button → Select any PDF file
2. (Optional) Enter Title and Author
3. Click **[▶️ Start Conversion]** (green button)
4. Watch progress bar → EPUB created when done!

---

## 🎯 First-Time Conversions

### Try These Examples

**Example A: Simple Digital PDF (Fastest)**
1. Add your favorite ebook PDF (2-50 pages)
2. OCR Mode: **Disabled** (already default)
3. Click Start → 5-30 seconds → Done!

**Example B: Batch Convert Multiple**
1. Add 3-5 PDF files at once
2. Leave settings default
3. Click Start → Will process sequentially
4. Check folder for multiple EPUBs

**Example C: Scanned PDF (With OCR)**
1. Add a PDF of scanned book/document
2. OCR Mode: **Always Enabled**
3. OCR Language: Select correct language
4. Click Start → Wait 1-5 minutes
5. Result: Text is extracted via OCR!

---

## ✅ Verify Installation

### Option 1: Quick Test
```bash
cd "/Users/michaelkoch/Desktop/PDF zu Epub Konverter"
poetry run pytest tests/ -v
```

Expected result: **49/49 tests PASSED ✅**

### Option 2: Launch GUI
```bash
./run_gui.sh
```

Expected result: Window appears with no errors

---

## 🔍 Troubleshooting Quick Fixes

### Problem: "Permission denied" when running setup.sh
```bash
chmod +x setup.sh
./setup.sh
```

### Problem: "Poetry not found" after setup
```bash
export PATH="$HOME/.local/bin:$PATH"
./run_gui.sh
```

### Problem: "Tesseract not found"
```bash
brew install tesseract
```

### Problem: "Python not found"
```bash
brew install python@3.11
```

### Problem: "Dependencies already installed but errors occur"
```bash
poetry install --no-root --force-reinstall
```

---

## 📂 Important File Locations

After setup, these locations will exist:

```
Logs:
  ~/.pdf_epub_converter/converter.log

Configuration:
  ~/.pdf_epub_converter/config.json

Python Virtual Environment:
  ./.venv/

Project Code:
  ./src/pdf_epub_converter/
```

---

## 🎮 Basic GUI Usage

### Main Buttons
| Button | Action | When to Click |
|--------|--------|---------------|
| **[+ Add]** | Add PDF files | Start conversion |
| **[- Remove]** | Remove selected PDF | If wrong file added |
| **[× Clear All]** | Remove all files | Start over |
| **[▶️ Start]** | Begin conversion | After adding files |
| **[⏹️ Stop]** | Stop conversion | If something wrong |

### Important Fields
| Field | Purpose | Default |
|-------|---------|---------|
| **Title** | EPUB document title | From PDF |
| **Author** | EPUB creator name | From PDF |
| **Language** | Document language | German |
| **OCR Mode** | Text extraction method | Auto-detect |
| **Optimize Images** | Compress images | Enabled |

---

## 📊 Perfect Results Checklist

After first conversion, verify:
- ✅ EPUB file created in same folder as original PDF
- ✅ EPUB filename: `original_name.epub`
- ✅ EPUB file size reasonable (typically 30-60% of PDF size)
- ✅ Can open EPUB in iBooks, Kindle, or other e-reader
- ✅ Text is readable and formatted nicely
- ✅ Images are included (if original PDF had them)

---

## 💡 Tips for Best Results

### Tip 1: Digital vs Scanned PDFs
- **Digital PDF (has text):** Use Auto-detect or Disabled
- **Scanned PDF (no text):** Use Always Enabled for OCR

### Tip 2: File Sizes
- Enable **Image Optimization** to reduce EPUB size by 30-50%
- Good for e-readers with storage limitations

### Tip 3: Batch Processing
- Add up to 20+ PDFs at once
- Click Start once
- Application processes them sequentially
- Ideal for converting your entire book library

### Tip 4: Metadata
- Leave fields empty to auto-detect from PDF
- Or enter specific values for all files
- Metadata appears in e-reader apps

### Tip 5: Language
- Select correct language for OCR
- Better accuracy with matching language
- German (de) is default

---

## 🚀 Next Steps After First Conversion

### A. Test with Your Own PDFs
1. Collect 5-10 PDFs you want to convert
2. Add them all at once
3. Start batch conversion
4. Transfer EPUBs to your e-reader

### B. Explore Advanced Settings
1. Try different OCR modes
2. Test with/without image optimization
3. Experiment with different languages

### C. Read Full Documentation
- `USER_GUIDE.md` - Complete usage manual
- `README.md` - Project overview
- `FINAL_PROJECT_SUMMARY.md` - Technical details

### D. Run Tests
```bash
poetry run pytest tests/ -v  # See all 49 tests
```

---

## 📞 Need Help?

### Check These First
1. **Setup Issues:** Run `./setup.sh` again
2. **Launch Issues:** Try manual `poetry run python src/main.py`
3. **Conversion Issues:** Check logs with `tail -f ~/.pdf_epub_converter/converter.log`
4. **Test Issues:** Run `poetry run pytest tests/ -v` to verify installation

### Common Issues Rapid Solutions

**"Application won't start"**
```bash
./setup.sh
./run_gui.sh
```

**"Tesseract error"**
```bash
brew install tesseract
# Or specify Tesseract path in settings
```

**"EPUB is 100MB"**
- Enable Image Optimization in Settings
- Re-convert

**"Text is gibberish"**
- Wrong OCR language selected
- Change Language dropdown
- Re-convert

---

## ⏱️ Typical Conversion Times

| PDF Type | Size | Time |
|----------|------|------|
| Digital PDF, 100 pages | 5 MB | 10 seconds |
| Digital PDF, 500 pages | 25 MB | 30 seconds |
| Scanned PDF, 100 pages | 50 MB | 2-3 minutes |
| Scanned PDF, 500 pages | 250 MB | 10 minutes |

Note: Times depend on your Mac's CPU. Faster on newer M1/M2 Macs.

---

## ✨ Advanced Users

### Run from Terminal
```bash
cd "/Users/michaelkoch/Desktop/PDF zu Epub Konverter"
PYTHONPATH=src poetry run python src/main.py
```

### Run Tests with Coverage
```bash
poetry run pytest tests/ --cov=src/pdf_epub_converter
```

### View Detailed Logs
```bash
# Real-time log (Ctrl+C to stop)
tail -f ~/.pdf_epub_converter/converter.log

# Last 100 lines
tail -100 ~/.pdf_epub_converter/converter.log

# Search in logs
grep "error\|Error\|ERROR" ~/.pdf_epub_converter/converter.log
```

### Check Installed Packages
```bash
poetry show
```

---

## 🎓 Learning Resources

### Inside the Project
- **PHASE1_STATUS.md** - Core features explained
- **PHASE2_STATUS.md** - OCR & optimization explained
- **PHASE3_STATUS.md** - GUI implementation explained
- **FINAL_PROJECT_SUMMARY.md** - Architecture & design
- **src/pdf_epub_converter/*** - Well-commented code

### External Resources
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [EPUB3 Standard](https://www.w3.org/TR/epub-overview-33/)
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)

---

## 🎉 You're Ready!

Everything is set up and ready to go. Start converting:

```bash
./run_gui.sh
```

**Enjoy converting PDFs to EPUB! 📚**

---

**Last Updated:** Phase 3 Complete  
**Status:** ✅ Production Ready  
**Support:** See USER_GUIDE.md for detailed help
