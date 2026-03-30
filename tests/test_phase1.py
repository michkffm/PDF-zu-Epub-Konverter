"""
Unit tests for Phase 1: Core modules.

Tests for:
- PDF metadata extraction
- EPUB building basics
- Metadata validation
- Logging system
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from pdf_epub_converter.core.metadata import Metadata
from pdf_epub_converter.core.epub_builder import EPUBBuilder
from pdf_epub_converter.utils.logger import setup_logger


class TestMetadata:
    """Tests for Metadata class."""
    
    def test_metadata_creation(self):
        """Test basic metadata creation."""
        meta = Metadata(
            title="Test Book",
            author="Test Author",
            language="en"
        )
        assert meta.title == "Test Book"
        assert meta.author == "Test Author"
        assert meta.language == "en"
    
    def test_metadata_normalize(self):
        """Test metadata normalization."""
        meta = Metadata(
            title="  Test Book  ",
            author="  Test Author  ",
            language="EN"
        )
        meta.normalize()
        
        assert meta.title == "Test Book"
        assert meta.author == "Test Author"
        assert meta.language == "en"
    
    def test_metadata_validation_success(self):
        """Test successful metadata validation."""
        meta = Metadata(
            title="Test Book",
            author="Test Author",
            language="en"
        )
        is_valid, errors = meta.validate()
        assert is_valid
        assert len(errors) == 0
    
    def test_metadata_validation_missing_title(self):
        """Test validation with missing title."""
        meta = Metadata(
            title="Untitled",
            author="Test Author"
        )
        is_valid, errors = meta.validate()
        assert not is_valid
        assert any("Title" in error for error in errors)
    
    def test_metadata_to_dict(self):
        """Test conversion to dictionary."""
        meta = Metadata(
            title="Test Book",
            author="Test Author"
        )
        data = meta.to_dict()
        
        assert isinstance(data, dict)
        assert data['title'] == "Test Book"
        assert data['author'] == "Test Author"
    
    def test_metadata_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'title': "Test Book",
            'author': "Test Author",
            'language': "de"
        }
        meta = Metadata.from_dict(data)
        
        assert meta.title == "Test Book"
        assert meta.author == "Test Author"
        assert meta.language == "de"


class TestEPUBBuilder:
    """Tests for EPUBBuilder class."""
    
    def test_epub_builder_creation(self):
        """Test EPUB builder initialization."""
        meta = Metadata(title="Test Book", author="Test Author")
        builder = EPUBBuilder(meta)
        
        assert builder.metadata == meta
        assert len(builder.chapters) == 0
        assert len(builder.images) == 0
    
    def test_add_chapter_simple(self):
        """Test adding simple chapter."""
        meta = Metadata(title="Test Book", author="Test Author")
        builder = EPUBBuilder(meta)
        
        chapter = builder.add_chapter("Chapter 1", "This is test content", chapter_num=1)
        
        assert len(builder.chapters) == 1
        assert chapter.file_name == 'chap_001.xhtml'
    
    def test_add_chapter_with_html(self):
        """Test adding chapter with HTML content."""
        meta = Metadata(title="Test Book", author="Test Author")
        builder = EPUBBuilder(meta)
        
        html_content = "<p>This is <strong>bold</strong> text</p>"
        chapter = builder.add_chapter("Chapter 1", html_content)
        
        assert len(builder.chapters) == 1
    
    def test_epub_validation_success(self):
        """Test EPUB validation with valid content."""
        meta = Metadata(
            title="Test Book",
            author="Test Author"
        )
        builder = EPUBBuilder(meta)
        builder.add_chapter("Chapter 1", "Content")
        
        is_valid, errors = builder.validate()
        assert is_valid
        assert len(errors) == 0
    
    def test_epub_validation_no_chapters(self):
        """Test EPUB validation with no chapters."""
        meta = Metadata(title="Test Book", author="Test Author")
        builder = EPUBBuilder(meta)
        
        is_valid, errors = builder.validate()
        assert not is_valid
        assert any("chapters" in error.lower() for error in errors)
    
    def test_html_escape(self):
        """Test HTML escaping."""
        text = '<script>alert("xss")</script>'
        escaped = EPUBBuilder._escape_html(text)
        
        assert '<' not in escaped or '&lt;' in escaped
        assert '"' not in escaped or '&quot;' in escaped
    
    def test_format_content_plain_text(self):
        """Test formatting plain text content."""
        content = "Paragraph 1\n\nParagraph 2"
        formatted = EPUBBuilder._format_content(content)
        
        assert "<p>" in formatted
        assert "Paragraph 1" in formatted
        assert "Paragraph 2" in formatted
    
    def test_format_content_html(self):
        """Test formatting HTML content."""
        html = "<p>Already HTML</p>"
        formatted = EPUBBuilder._format_content(html)
        
        assert formatted == html


class TestLogger:
    """Tests for logging system."""
    
    def test_logger_creation(self):
        """Test logger creation."""
        logger = setup_logger("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"
    
    def test_logger_with_file(self):
        """Test logger with file output."""
        with TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = setup_logger("test_logger2", log_file=log_file)
            
            logger.info("Test message")
            assert log_file.exists()
            assert "Test message" in log_file.read_text()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
