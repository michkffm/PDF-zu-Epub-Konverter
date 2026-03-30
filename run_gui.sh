#!/bin/bash

###############################################################################
# PDF to EPUB Converter - GUI Launcher Script
###############################################################################
#
# Usage: ./run_gui.sh
#
# This script:
# 1. Checks if Poetry environment is set up
# 2. Installs dependencies if needed
# 3. Launches the desktop GUI application
#
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Welcome banner
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      PDF to EPUB Converter - Desktop Application 📚        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}❌ Poetry is not installed!${NC}"
    echo -e "${YELLOW}Install Poetry with: curl -sSL https://install.python-poetry.org | python3${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Poetry found${NC}: $(poetry --version)"
echo ""

# Step 2: Check if dependencies are installed
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ] && ! poetry env info > /dev/null 2>&1; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    poetry install --no-root
    echo -e "${GREEN}✓ Dependencies installed${NC}"
    echo ""
else
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
    echo ""
fi

# Step 3: Launch the GUI
echo -e "${YELLOW}🚀 Launching PDF to EPUB Converter GUI...${NC}"
echo -e "${BLUE}Window should appear in a moment...${NC}"
echo ""

# Export PYTHONPATH for module discovery
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

# Run the application
poetry run python src/main.py

# Exit with Poetry's exit code
exit $?
