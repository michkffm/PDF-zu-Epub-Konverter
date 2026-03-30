"""
Unit tests for Phase 3: GUI components.

Tests for:
- Conversion worker threading
- Main window initialization
- Signal/slot connections
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import sys

from pdf_epub_converter.workers.conversion_worker import ConversionWorker, ConversionJob
from pdf_epub_converter.core.metadata import Metadata
from pdf_epub_converter.gui.main_window import MainWindow


# Ensure QApplication exists for tests
app = QApplication.instance() or QApplication(sys.argv)


class TestConversionWorker:
    """Tests for conversion worker threads."""
    
    def test_conversion_job_creation(self):
        """Test ConversionJob creation."""
        with TemporaryDirectory() as tmpdir:
            input_pdf = Path(tmpdir) / "input.pdf"
            output_epub = Path(tmpdir) / "output.epub"
            
            input_pdf.touch()  # Create dummy file
            
            metadata = Metadata(title="Test", author="Author")
            
            job = ConversionJob(
                input_pdf=input_pdf,
                output_epub=output_epub,
                metadata=metadata,
                use_ocr=False,
                optimize_images=True
            )
            
            assert job.input_pdf == input_pdf
            assert job.output_epub == output_epub
            assert job.metadata.title == "Test"
            assert job.use_ocr == False
            assert job.optimize_images == True
    
    def test_conversion_worker_initialization(self):
        """Test conversion worker init."""
        with TemporaryDirectory() as tmpdir:
            input_pdf = Path(tmpdir) / "input.pdf"
            output_epub = Path(tmpdir) / "output.epub"
            input_pdf.touch()
            
            job = ConversionJob(
                input_pdf=input_pdf,
                output_epub=output_epub,
                metadata=Metadata()
            )
            
            worker = ConversionWorker(job)
            
            assert worker.job == job
            assert worker.is_running == True
            
            # Check signals
            assert hasattr(worker, 'progress')
            assert hasattr(worker, 'finished')
            assert hasattr(worker, 'error')
            assert hasattr(worker, 'log')


class TestMainWindow:
    """Tests for main window GUI."""
    
    def test_main_window_creation(self):
        """Test main window initialization."""
        window = MainWindow()
        
        assert window.windowTitle() == "PDF to EPUB Converter 📚"
        assert window.width() == 1200
        assert window.height() == 800
        assert len(window.selected_pdfs) == 0
    
    def test_file_list_widget_exists(self):
        """Test file list widget."""
        window = MainWindow()
        
        assert hasattr(window, 'file_list_widget')
        assert window.file_list_widget is not None
        assert window.file_list_widget.count() == 0
    
    def test_metadata_widgets_exist(self):
        """Test metadata input widgets."""
        window = MainWindow()
        
        assert hasattr(window, 'title_input')
        assert hasattr(window, 'author_input')
        assert hasattr(window, 'language_combo')
        assert hasattr(window, 'description_input')
    
    def test_settings_widgets_exist(self):
        """Test settings widgets."""
        window = MainWindow()
        
        assert hasattr(window, 'ocr_combo')
        assert hasattr(window, 'optimize_combo')
        assert hasattr(window, 'validate_combo')
    
    def test_control_buttons_exist(self):
        """Test control buttons."""
        window = MainWindow()
        
        assert hasattr(window, 'start_btn')
        assert hasattr(window, 'stop_btn')
        assert window.start_btn is not None
        assert window.stop_btn is not None
    
    def test_progress_widgets_exist(self):
        """Test progress tracking widgets."""
        window = MainWindow()
        
        assert hasattr(window, 'progress_bar')
        assert hasattr(window, 'progress_label')
        assert hasattr(window, 'log_widget')
        
        assert window.progress_bar.value() == 0
    
    def test_add_file_to_list(self):
        """Test adding files to list."""
        window = MainWindow()
        
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.pdf"
            test_file.touch()
            
            window._add_file_to_list(test_file)
            
            assert window.file_list_widget.count() == 1
            item = window.file_list_widget.item(0)
            assert item.text() == "test.pdf"
    
    def test_clear_file_list(self):
        """Test clearing file list."""
        window = MainWindow()
        
        with TemporaryDirectory() as tmpdir:
            for i in range(3):
                test_file = Path(tmpdir) / f"test{i}.pdf"
                test_file.touch()
                window.selected_pdfs.append(test_file)
                window._add_file_to_list(test_file)
            
            assert window.file_list_widget.count() == 3
            
            window.clear_file_list()
            
            assert window.file_list_widget.count() == 0
            assert len(window.selected_pdfs) == 0
    
    def test_metadata_input_fields(self):
        """Test metadata input."""
        window = MainWindow()
        
        window.title_input.setText("Test Title")
        window.author_input.setText("Test Author")
        
        assert window.title_input.text() == "Test Title"
        assert window.author_input.text() == "Test Author"
    
    def test_language_selection(self):
        """Test language combo selection."""
        window = MainWindow()
        
        window.language_combo.setCurrentIndex(0)  # German
        assert "de" in window.language_combo.currentText()
        
        window.language_combo.setCurrentIndex(1)  # English
        assert "en" in window.language_combo.currentText()
    
    def test_ocr_settings(self):
        """Test OCR settings."""
        window = MainWindow()
        
        # Test OCR combo
        window.ocr_combo.setCurrentIndex(0)
        assert window.ocr_combo.currentText() == "Disabled"
        
        window.ocr_combo.setCurrentIndex(2)
        assert window.ocr_combo.currentText() == "Always Enabled"
        
        # Test OCR language
        window.ocr_lang_combo.setCurrentText("en")
        assert window.ocr_lang_combo.currentText() == "en"
    
    def test_status_bar_exists(self):
        """Test status bar."""
        window = MainWindow()
        
        status_bar = window.statusBar()
        assert status_bar is not None
        
        window.statusBar().showMessage("Test message")
        # Just verify it runs without error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
