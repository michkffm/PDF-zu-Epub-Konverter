# PDF to EPUB Converter - User Guide 📚

Welcome to the PDF to EPUB Converter desktop application! This guide will walk you through using the application for converting PDF documents to EPUB3 format.

---

## 🚀 Getting Started

### Installation (One-Time Setup)

1. **Clone/Download the Project**
   ```bash
   cd "/Users/michaelkoch/Desktop/PDF zu Epub Konverter"
   ```

2. **Run First-Time Setup** (Option A - Automated)
   ```bash
   ./setup.sh
   ```
   This will automatically install:
   - Homebrew (if needed)
   - Python 3.11
   - Tesseract OCR engine
   - Poetry package manager
   - All Python dependencies

3. **Manual Setup** (Option B - Step by Step)
   ```bash
   # Install Homebrew dependencies
   brew install python@3.11 tesseract
   
   # Install Poetry (if not already installed)
   curl -sSL https://install.python-poetry.org | python3
   
   # Install Python dependencies
   cd "/Users/michaelkoch/Desktop/PDF zu Epub Konverter"
   poetry install --no-root
   ```

### Launching the Application

```bash
cd "/Users/michaelkoch/Desktop/PDF zu Epub Konverter"
./run_gui.sh
```

The GUI window will appear within a few seconds.

---

## 🎨 User Interface Overview

### Main Window Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  PDF to EPUB Converter 📚                              [_][□][×]  │
├─────────────────────────────────────────────────────────────────┤
│ File Edit Settings Help                                         │
├───────────────────┬─────────────────────────────────────────────┤
│                   │                                              │
│  📄 File List     │  📋 Metadata                                │
│  ────────────     │  ──────────────                             │
│  ○ input1.pdf     │  Title:        [________________]           │
│  ○ input2.pdf     │  Author:       [________________]           │
│  ○ input3.pdf     │  Language:     [Deutsch ▼    ]             │
│  ────────────     │  Description:  [____________   ]           │
│  [+ Add]           │                    [___________|]           │
│  [- Remove]        │  ⚙️ Settings                               │
│  [× Clear All]     │  OCR Mode:     [Auto-detect ▼ ]           │
│                   │  Optimize Img: [✓ Enabled    ]             │
│                   │  Validation:   [✓ Enabled    ]             │
│                   │                                              │
│                   │  📊 Progress                               │
│                   │  ████████████░░░░░ 65%                    │
│                   │  Converting: input2.pdf → output2.epub     │
│                   │                                              │
│                   │  📝 Conversion Log                          │
│                   │  ✓ [14:32] Image optimization applied     │
│                   │  ⓘ [14:33] OCR processing page 3...       │
│                   │  ✓ [14:35] Created EPUB successfully      │
│                   │                                              │
│                   │  [▶️ Start Conversion]  [⏹️ Stop]          │
└───────────────────┴─────────────────────────────────────────────┘
```

---

## 📖 Step-by-Step Workflow

### Step 1: Add PDF Files

1. Click the **[+ Add]** button in the File List panel
2. File dialog opens (may take a moment to appear)
3. Navigate to your PDF files
4. **Select one or more PDFs** using:
   - Click to select single file
   - Cmd+Click to select multiple files
   - Cmd+A to select all files in folder
5. Click **[Open]** to add them to the list

The selected PDFs will appear in the file list on the left side.

### Step 2: Configure Metadata (Optional)

Metadata helps create professional EPUB files:

- **Title** - Document title (appears in e-readers)
- **Author** - Creator name
- **Language** - Document language for text rendering
- **Description** - Long description or notes

**Tip:** Enter the same metadata for all files, or leave blank to auto-detect from PDF.

### Step 3: Configure Settings

#### OCR Mode
- **Disabled** - Skip OCR, use text extraction only
- **Auto-detect** - Use OCR only for scanned PDFs
- **Always Enabled** - Always run OCR (slower, for mixed PDFs)

#### Image Optimization
- **Enabled** (✓) - Compress and resize images (smaller EPUB files)
- **Disabled** - Keep original image quality

#### Publication Validation
- **Enabled** (✓) - Check EPUB structure and completeness
- **Disabled** - Skip validation

#### OCR Language
- Select target language for OCR (de/en/fr/es/it/pt/ru/ja/zh/ko)
- Must match document language for best results

### Step 4: Start Conversion

1. Click **[▶️ Start Conversion]** button (green)
2. **Do not close the application** during conversion
3. Watch the progress bar and log widget

**What happens in background:**
1. First PDF is read and content extracted
2. Images are optimized (if enabled)
3. EPUB structure is created
4. Document is validated
5. Output EPUB is saved to same folder as input PDF
6. Next PDF in list automatically starts

### Step 5: Monitor Progress

- **Progress Bar** - Shows overall conversion percentage (0-100%)
- **Status Label** - Real-time message about current operation
- **Log Widget** - Detailed conversion messages with three types:
  - ✓ (Green) = Successful operations
  - ⓘ (Blue) = Information messages
  - ⚠️ (Orange) = Warnings
  - ✗ (Red) = Errors

### Step 6: Check Results

After each file completes:
1. Success message appears
2. EPUB file is created in same directory as input PDF
3. Next file automatically starts (if more files remain)
4. To stop processing, click **[⏹️ Stop]** button

---

## 🎯 Common Workflows

### Workflow A: Convert Single Digital PDF
```
1. Click [+ Add] → Select single PDF → [Open]
2. (Optional) Enter Title and Author
3. OCR Mode: [Auto-detect] (already default)
4. Click [▶️ Start Conversion]
5. Wait for completion
6. EPUB file appears in same folder as PDF
```

### Workflow B: Batch Convert Multiple PDFs
```
1. Click [+ Add] → Select 5-10 PDFs → [Open]
2. (Optional) Enter metadata if needed
3. Click [▶️ Start Conversion]
4. Watch progress bar - files convert one after another
5. All EPUB files created automatically
```

### Workflow C: Convert Scanned PDFs with OCR
```
1. Click [+ Add] → Select scanned PDF → [Open]
2. OCR Mode: Select [Always Enabled] (or Auto-detect)
3. OCR Language: Select document language
4. Image Optimization: [✓ Enabled] (recommended)
5. Click [▶️ Start Conversion]
6. Takes longer due to OCR processing
7. EPUB file created with extracted text
```

### Workflow D: High-Quality EPUB
```
1. Click [+ Add] → Select PDF → [Open]
2. Image Optimization: [✓ Enabled] (compress images)
3. Validation: [✓ Enabled] (check EPUB quality)
4. Click [▶️ Start Conversion]
5. EPUB validated before saving
```

---

## ⚠️ Troubleshooting

### Problem: "Application won't launch"
**Solution 1:** Check if dependencies are installed
```bash
./setup.sh
```

**Solution 2:** Try manual launch
```bash
poetry run python src/main.py
```

Check error message in terminal.

### Problem: "No such file or directory" error
**Solution:** Make sure you're in correct directory
```bash
cd "/Users/michaelkoch/Desktop/PDF zu Epub Konverter"
./run_gui.sh
```

### Problem: "Tesseract not found" (OCR error)
**Solution:** Install Tesseract OCR
```bash
brew install tesseract
```

### Problem: "Slow conversion" or "application freezing"
**Note:** Conversions are normal:
- Digital PDF (no OCR): 5-30 seconds
- Scanned PDF (with OCR): 1-5 minutes (depends on page count)

This is normal - application should remain responsive during conversion.

### Problem: "EPUB is too large"
**Solution:** Enable Image Optimization
1. Check Image Optimization: **[✓ Enabled]**
2. Re-convert PDF
3. This compresses images and reduces file size by 30-50%

### Problem: "EPUB won't open in e-reader"
**Solution 1:** Enable Validation
1. Check Validation: **[✓ Enabled]**
2. Check log for warnings or errors
3. Re-convert PDF

**Solution 2:** Check log for OCR errors
1. Look at Log Widget for red error messages
2. If OCR error, try different OCR Language
3. Or disable OCR: OCR Mode: **[Disabled]**

### Problem: "Wrong text/missing text in EPUB"
**Solution 1 (Digital PDF):**
- PDF might be scanned
- Set OCR Mode: **[Always Enabled]**
- Re-convert

**Solution 2 (OCR):**
- Wrong language selected
- OCR Language: Select correct language
- Re-convert

### Problem: "Permission denied" when saving
**Solution:** Check folder permissions
```bash
# Make output folder writable
chmod 755 "/path/to/output/folder"
```

---

## 🔧 Advanced Tips

### Tip 1: Finding Output EPUB Files
- EPUB files are saved in **same directory as input PDF**
- Filename: `input_filename.epub`
- Example: `mybook.pdf` → `mybook.epub`

### Tip 2: Checking Conversion Quality
- Enable Validation: **[✓ Enabled]**
- Check Log Widget for warnings
- Test EPUB in multiple e-readers (Kindle, Apple Books, etc.)

### Tip 3: Batch Conversion
- Add 10-20 PDFs at once
- Start conversion
- Application processes them sequentially
- Go grab a coffee ☕ - it will work in background

### Tip 4: Memory Usage
- Conversion process normal memory: 50-100 MB per file
- Running multiple applications may slow things down
- Close other apps if experiencing slowness

### Tip 5: Log Files
ALL conversion activities are logged to:
```
~/.pdf_epub_converter/converter.log
```

View log file anytime:
```bash
tail -f ~/.pdf_epub_converter/converter.log
```

---

## 📊 Understanding the Log Messages

### Success Messages (✓ Green)
```
✓ Image optimization applied
✓ Created EPUB successfully
✓ EPUB validation passed
```

### Information Messages (ⓘ Blue)
```
ⓘ Processing PDF file
ⓘ Extracting text and images
ⓘ OCR processing page 3...
```

### Warning Messages (⚠️ Orange)
```
⚠️ PDF contains no text, using OCR
⚠️ Some images not optimized
```

### Error Messages (✗ Red)
```
✗ Failed to read PDF file
✗ OCR engine not found
✗ EPUB validation failed
```

---

## 🎨 Menu Options

### File Menu
- **Open PDF Files...** - Same as [+ Add] button
- **Quit** - Close application

### Edit Menu
- **Clear File List** - Remove all PDFs from list
- **Settings...** - Open advanced settings dialog

### Settings Menu
- **Preferences** - Application settings
- **OCR Languages** - Download/manage OCR languages
- **About** - Application information

### Help Menu
- **User Guide** - This document
- **Report Issue** - Open GitHub issue tracker
- **Website** - Visit project website

---

## 💾 File Locations

### Application Logs
```
~/.pdf_epub_converter/converter.log
```

### Configuration Files
```
~/.pdf_epub_converter/config.json
~/.pdf_epub_converter/ocr_languages/
```

### Python Virtual Environment
```
.venv/
```

---

## 🔐 Privacy & Security

✅ **No cloud uploads** - Everything runs locally
✅ **No tracking** - No usage data collected
✅ **No ads** - Completely ad-free
✅ **Open source** - Code is open for review

---

## 📞 Getting Help

### Check Documentation
- README.md - Project overview
- PHASE1_STATUS.md - Technical details (Phase 1)
- PHASE2_STATUS.md - Technical details (Phase 2)
- PHASE3_STATUS.md - Technical details (Phase 3)

### View Logs
```bash
# Real-time log view
tail -f ~/.pdf_epub_converter/converter.log

# See last 50 lines
tail -50 ~/.pdf_epub_converter/converter.log
```

### Run Tests
```bash
# Run all tests
poetry run pytest tests/ -v

# Run specific test
poetry run pytest tests/test_phase1.py -v
```

### Contact
- GitHub Issues: [Project Repository]
- Email: [Your Email]

---

## 📈 Performance Tips

### For Faster Conversion
- Disable Image Optimization if not needed
- Set OCR Mode to [Disabled] for digital PDFs
- Disable Validation if not needed

### For Smaller EPUB Files
- Enable Image Optimization: **[✓ Enabled]**
- This reduces file size by up to 50%

### For Better Quality
- Enable Validation: **[✓ Enabled]**
- Use [Auto-detect] for OCR Mode
- Select correct OCR Language

---

## ✅ Next Steps

1. **Download/Clone Project**
   ```bash
   git clone [repository-url]
   cd "PDF zu Epub Konverter"
   ```

2. **Run Setup** (first time only)
   ```bash
   ./setup.sh
   ```

3. **Launch Application**
   ```bash
   ./run_gui.sh
   ```

4. **Convert Your First PDF**
   - Click [+ Add]
   - Select PDF file
   - Click [▶️ Start Conversion]
   - Wait for completion

5. **Check Result**
   - EPUB file created in same folder as PDF
   - Try opening in e-reader app

---

## 🎉 You're Ready!

Start converting your PDFs to EPUB now. Enjoy! 📚

---

**Version:** 1.0  
**Last Updated:** Phase 3 Complete  
**Status:** Production Ready ✅
