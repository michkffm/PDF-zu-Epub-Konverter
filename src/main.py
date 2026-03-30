"""
Main entry point for PDF to EPUB Converter GUI application.

Launch the PyQt6 desktop application.
"""

import sys
import logging
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from pdf_epub_converter.utils.logger import setup_logger
from pdf_epub_converter.gui.main_window import MainWindow


def main():
    """Launch the GUI application."""
    
    # Setup logging
    log_dir = Path.home() / ".pdf_epub_converter"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "converter.log"
    
    logger = setup_logger(
        name="pdf_epub_converter",
        log_level=logging.DEBUG,
        log_file=log_file,
        use_color=True
    )
    
    logger.info("="*60)
    logger.info("PDF to EPUB Converter - Starting GUI")
    logger.info("="*60)
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("PDF to EPUB Converter")
    app.setApplicationVersion("0.1.0")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    logger.info("GUI window opened")
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
