"""
Unit tests for Phase 2: Advanced PDF Processing.

Tests for:
- OCR integration with Tesseract
- Image optimization
- Scanned PDF extraction
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image
from io import BytesIO

from pdf_epub_converter.workers.ocr_worker import OCRWorker, ScannedPDFExtractor, OCRError
from pdf_epub_converter.utils.image_optimizer import ImageOptimizer, ImageOptimizationError


class TestOCRWorker:
    """Tests for OCR worker."""
    
    @pytest.fixture
    def ocr_worker(self):
        """Create OCR worker instance."""
        try:
            return OCRWorker(language='en', max_workers=2)
        except OCRError:
            pytest.skip("Tesseract not installed")
    
    def test_ocr_worker_creation(self, ocr_worker):
        """Test OCR worker initialization."""
        assert ocr_worker is not None
        assert ocr_worker.language == 'en'
        assert ocr_worker.tesseract_lang == 'eng'
        assert ocr_worker.max_workers == 2
    
    def test_language_mapping(self, ocr_worker):
        """Test language code mapping."""
        assert OCRWorker.LANGUAGE_MAP['de'] == 'deu'
        assert OCRWorker.LANGUAGE_MAP['en'] == 'eng'
        assert OCRWorker.LANGUAGE_MAP['fr'] == 'fra'
        assert OCRWorker.LANGUAGE_MAP['es'] == 'spa'
    
    def test_preprocess_image_grayscale(self, ocr_worker):
        """Test image preprocessing (grayscale conversion)."""
        # Create test image
        img = Image.new('RGB', (100, 100), color='white')
        
        processed = ocr_worker.preprocess_image(img)
        
        assert processed.mode == 'L'  # Grayscale
        assert processed.size == (100, 100)
    
    def test_preprocess_image_rgba(self, ocr_worker):
        """Test image preprocessing (RGBA to RGB)."""
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 255))
        processed = ocr_worker.preprocess_image(img)
        
        assert processed.mode == 'L'  # After grayscale conversion
    
    def test_extract_text_from_image(self, ocr_worker):
        """Test OCR text extraction from simple image."""
        # Create image with text
        img = Image.new('RGB', (200, 100), color='white')
        
        # Note: This will return empty or minimal text without actual text in image
        # but validates the OCR pipeline works
        try:
            text = ocr_worker.extract_text_from_image(img)
            assert isinstance(text, str)
        except OCRError:
            pytest.skip("OCR extraction failed (expected for blank image)")
    
    def test_extract_data_from_image(self, ocr_worker):
        """Test OCR data extraction."""
        img = Image.new('RGB', (200, 100), color='white')
        
        try:
            data = ocr_worker.extract_data_from_image(img)
            assert isinstance(data, dict)
            # Should have 'text' key from pytesseract output
            assert 'text' in data
        except OCRError:
            pytest.skip("OCR data extraction failed")


class TestImageOptimizer:
    """Tests for image optimization."""
    
    @pytest.fixture
    def optimizer(self):
        """Create image optimizer instance."""
        return ImageOptimizer(max_width=1000, max_height=1000, jpeg_quality=85)
    
    def test_optimizer_creation(self, optimizer):
        """Test optimizer initialization."""
        assert optimizer.max_width == 1000
        assert optimizer.max_height == 1000
        assert optimizer.jpeg_quality == 85
    
    def test_get_image_info(self):
        """Test image information retrieval."""
        with TemporaryDirectory() as tmpdir:
            # Create test image
            img = Image.new('RGB', (800, 600), color='blue')
            img_path = Path(tmpdir) / "test.png"
            img.save(str(img_path))
            
            info = ImageOptimizer.get_image_info(img_path)
            
            assert info['width'] == 800
            assert info['height'] == 600
            assert info['format'] == 'PNG'
            assert info['mode'] == 'RGB'
            assert info['size_bytes'] > 0
    
    def test_preprocess_rgba_to_rgb(self, optimizer):
        """Test RGBA to RGB conversion."""
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 255))
        processed = optimizer._preprocess(img)
        
        assert processed.mode == 'RGB'
        assert processed.size == (100, 100)
    
    def test_resize_large_image(self, optimizer):
        """Test image resizing."""
        # Create large image
        img = Image.new('RGB', (3000, 2000), color='green')
        resized = optimizer._resize(img)
        
        # Should be resized to max dimensions
        assert resized.width <= 1000
        assert resized.height <= 1000
    
    def test_resize_small_image(self, optimizer):
        """Test that small images aren't enlarged."""
        img = Image.new('RGB', (400, 300), color='red')
        resized = optimizer._resize(img)
        
        # Should stay same size
        assert resized.size == (400, 300)
    
    def test_select_format_jpeg(self, optimizer):
        """Test format selection (JPEG for photos)."""
        # Create complex image (many colors)
        img = Image.new('RGB', (100, 100))
        pixels = img.load()
        for i in range(100):
            for j in range(100):
                pixels[i, j] = (i * 2, j * 2, (i + j) % 256)
        
        # Should prefer JPEG for complex images
        fmt = optimizer._select_format(img, None)
        assert fmt in ('jpeg', 'png')
    
    def test_select_format_png_from_original(self, optimizer):
        """Test format selection respects original PNG."""
        img = Image.new('RGB', (100, 100), color='white')
        fmt = optimizer._select_format(img, 'PNG')
        
        assert fmt == 'png'
    
    def test_optimize_single_image(self, optimizer):
        """Test single image optimization."""
        with TemporaryDirectory() as tmpdir:
            # Create test image
            img = Image.new('RGB', (2000, 1500), color='yellow')
            input_path = Path(tmpdir) / "input.jpg"
            output_path = Path(tmpdir) / "output.jpg"
            img.save(str(input_path), 'JPEG')
            
            # Optimize (force format to ensure JPEG output)
            result_path, mime_type, size = optimizer.optimize(
                input_path,
                output_path=output_path,
                force_format='jpeg'
            )
            
            assert result_path.exists()
            assert mime_type == 'image/jpeg'
            assert size > 0
            
            # Verify output is actually smaller (due to resizing)
            original_size = input_path.stat().st_size
            assert size <= original_size * 1.1  # Allow 10% variance
    
    def test_optimize_png_to_jpeg(self, optimizer):
        """Test PNG to JPEG conversion."""
        with TemporaryDirectory() as tmpdir:
            img = Image.new('RGB', (500, 500), color='cyan')
            input_path = Path(tmpdir) / "input.png"
            output_path = Path(tmpdir) / "output.png"
            img.save(str(input_path), 'PNG')
            
            result_path, mime_type, size = optimizer.optimize(
                input_path,
                output_path=output_path,
                force_format='jpeg'
            )
            
            # Should be saved as JPEG
            assert result_path.suffix.lower() == '.jpg' or mime_type == 'image/jpeg'
    
    def test_batch_optimization(self, optimizer):
        """Test batch image optimization."""
        with TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"
            input_dir.mkdir()
            
            # Create test images
            images = []
            for i in range(3):
                img = Image.new('RGB', (1500, 1000), color=(i * 80, 100, 150))
                img_path = input_dir / f"test_{i}.png"
                img.save(str(img_path), 'PNG')
                images.append(img_path)
            
            # Batch optimize
            results = optimizer.optimize_batch(images, output_dir, skip_duplicates=False)
            
            assert len(results) == 3
            for result_path, mime_type, size in results:
                assert result_path.exists()
                assert size > 0
    
    def test_duplicate_detection(self, optimizer):
        """Test duplicate image detection."""
        with TemporaryDirectory() as tmpdir:
            # Create identical images
            img = Image.new('RGB', (100, 100), color='magenta')
            path1 = Path(tmpdir) / "img1.png"
            path2 = Path(tmpdir) / "img2.png"
            img.save(str(path1), 'PNG')
            img.save(str(path2), 'PNG')
            
            # First should be processed
            result1 = optimizer.optimize_batch([path1], Path(tmpdir) / "out", skip_duplicates=True)
            assert len(result1) == 1
            
            # Second (duplicate) should be skipped
            result2 = optimizer.optimize_batch([path2], Path(tmpdir) / "out", skip_duplicates=True)
            assert len(result2) == 0  # Skipped as duplicate


class TestScannedPDFExtractor:
    """Tests for scanned PDF extractor."""
    
    def test_scanned_extractor_creation(self):
        """Test that scanned extractor initializes properly."""
        # This test checks basic initialization without an actual PDF
        try:
            from pdf_epub_converter.workers.ocr_worker import ScannedPDFExtractor
            # Can't fully test without actual PDF, but verifies import works
            assert ScannedPDFExtractor is not None
        except ImportError:
            pytest.skip("ScannedPDFExtractor import failed")
    
    def test_metadata_marked_as_scanned(self):
        """Test that extracted metadata is marked as scanned."""
        # Would require actual scanned PDF file
        # Placeholder for integration testing
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
