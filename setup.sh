#!/bin/bash

###############################################################################
# PDF to EPUB Converter - First-Time Setup Script
###############################################################################
#
# Usage: ./setup.sh
#
# This script:
# 1. Installs Homebrew if needed
# 2. Installs system dependencies (Python, Tesseract)
# 3. Installs Poetry
# 4. Sets up Python environment
# 5. Installs Python dependencies
#
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Welcome
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   PDF to EPUB Converter - Setup & Configuration 📚         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Check Homebrew
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo -e "${GREEN}✓ Homebrew installed${NC}"
else
    echo -e "${GREEN}✓ Homebrew already installed${NC}"
fi
echo ""

# Step 2: Install system dependencies
echo -e "${YELLOW}📦 Installing system dependencies...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "  Installing Python..."
    brew install python@3.11
    echo -e "${GREEN}  ✓ Python installed${NC}"
else
    echo -e "${GREEN}  ✓ Python found${NC}: $(python3 --version)"
fi

# Check Tesseract for OCR
if ! command -v tesseract &> /dev/null; then
    echo -e "  Installing Tesseract for OCR..."
    brew install tesseract
    echo -e "${GREEN}  ✓ Tesseract installed${NC}"
else
    echo -e "${GREEN}  ✓ Tesseract already installed${NC}"
fi

# Check ffmpeg (for image conversion if needed)
if ! command -v ffmpeg &> /dev/null; then
    echo -e "  Installing ffmpeg for image processing..."
    brew install ffmpeg
    echo -e "${GREEN}  ✓ ffmpeg installed${NC}"
else
    echo -e "${GREEN}  ✓ ffmpeg found${NC}"
fi

echo ""

# Step 3: Install Poetry
if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Poetry...${NC}"
    curl -sSL https://install.python-poetry.org | python3
    export PATH="$HOME/.local/bin:$PATH"
    echo -e "${GREEN}✓ Poetry installed${NC}"
    echo -e "${BLUE}ℹ️  Add ~/.local/bin to your PATH for permanent access${NC}"
else
    echo -e "${GREEN}✓ Poetry already installed${NC}: $(poetry --version)"
fi
echo ""

# Step 4: Setup project directory
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

echo -e "${YELLOW}📂 Configuring project in: $PROJECT_DIR${NC}"
echo ""

# Step 5: Install Python dependencies
echo -e "${YELLOW}📦 Installing Python dependencies with Poetry...${NC}"
poetry install --no-root

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                   ✅ Setup Complete! 🎉                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Display next steps
echo -e "${GREEN}📋 Quick Start:${NC}"
echo ""
echo -e "  ${YELLOW}1. Launch GUI:${NC}"
echo "     ./run_gui.sh"
echo ""
echo -e "  ${YELLOW}2. Run tests:${NC}"
echo "     poetry run pytest tests/"
echo ""
echo -e "  ${YELLOW}3. View logs:${NC}"
echo "     tail -f ~/.pdf_epub_converter/converter.log"
echo ""

# Verify setup
echo -e "${GREEN}📌 Verification:${NC}"
echo ""
echo -n "  Python: "
python3 --version

echo -n "  Poetry: "
poetry --version

echo -n "  Tesseract: "
tesseract --version 2>&1 | head -1

echo ""
echo -e "${GREEN}✓ All systems ready!${NC}"
echo ""
