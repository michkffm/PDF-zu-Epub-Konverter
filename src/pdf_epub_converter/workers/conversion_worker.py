"""
Background conversion worker for PyQt6 GUI.

Handles PDF to EPUB conversion in separate thread,
keeping UI responsive with progress updates.
"""

import logging
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass

from PyQt6.QtCore import QThread, pyqtSignal

from pdf_epub_converter.core.pdf_extractor import DigitalPDFExtractor
from pdf_epub_converter.workers.ocr_worker import ScannedPDFExtractor, OCRError
from pdf_epub_converter.core.epub_builder import EPUBBuilder, EPUBBuildError
from pdf_epub_converter.core.metadata import Metadata
from pdf_epub_converter.utils.image_optimizer import ImageOptimizer, ImageOptimizationError
from pdf_epub_converter.core.quality_checker import EPUBValidator


logger = logging.getLogger(__name__)


@dataclass
class ConversionJob:
    """Represents a single PDF to EPUB conversion job."""
    
    input_pdf: Path
    output_epub: Path
    metadata: Metadata
    use_ocr: bool = False
    ocr_language: str = 'de'
    optimize_images: bool = True
    validate: bool = True


class ConversionWorker(QThread):
    """
    QThread worker for PDF to EPUB conversion.
    
    Signals:
    - progress: (current: int, total: int, message: str)
    - finished: (output_path: str, success: bool, message: str)
    - error: (error_message: str)
    """
    
    # PyQt6 signals
    progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal(str, bool, str)  # output_path, success, message
    error = pyqtSignal(str)  # error_message
    log = pyqtSignal(str, int)  # message, level (logging level)
    
    def __init__(self, job: ConversionJob):
        """
        Initialize conversion worker.
        
        Args:
            job: ConversionJob object with conversion parameters
        """
        super().__init__()
        self.job = job
        self.is_running = True
    
    def run(self):
        """Execute conversion in background thread."""
        try:
            logger.info(f"Starting conversion: {self.job.input_pdf.name} → {self.job.output_epub.name}")
            
            # Step 1: Extract from PDF
            self._log_and_emit("Extracting PDF content...", logging.INFO)
            extracted_content = self._extract_pdf()
            if not extracted_content:
                return
            
            text, images, metadata_extracted = extracted_content
            
            # Merge metadata
            final_metadata = self.job.metadata
            if self.job.metadata.title == "Untitled" and metadata_extracted.title != "Untitled":
                final_metadata.title = metadata_extracted.title
            if not self.job.metadata.author and metadata_extracted.author:
                final_metadata.author = metadata_extracted.author
            
            # Step 2: Optimize images (optional)
            if self.job.optimize_images:
                self._log_and_emit("Optimizing images...", logging.INFO)
                images = self._optimize_images(images)
            
            # Step 3: Build EPUB
            self._log_and_emit("Building EPUB...", logging.INFO)
            self.progress.emit(70, 100, "Creating EPUB structure...")
            
            epub_path = self._build_epub(text, images, final_metadata)
            if not epub_path:
                return
            
            # Step 4: Validate (optional)
            if self.job.validate:
                self._log_and_emit("Validating EPUB...", logging.INFO)
                self.progress.emit(95, 100, "Validating EPUB...")
                self._validate_epub(epub_path)
            
            # Success
            self.progress.emit(100, 100, "Conversion complete!")
            self._log_and_emit(f"✅ EPUB created: {epub_path}", logging.INFO)
            self.finished.emit(str(epub_path), True, "Conversion successful")
        
        except Exception as e:
            logger.error(f"Conversion failed: {e}", exc_info=True)
            self._log_and_emit(f"❌ Error: {e}", logging.ERROR)
            self.error.emit(str(e))
            self.finished.emit("", False, str(e))
    
    def _extract_pdf(self) -> Optional[tuple]:
        """
        Extract content from PDF.
        
        Returns:
            Tuple of (text, images, metadata) or None if failed
        """
        extractor = None
        try:
            self.progress.emit(10, 100, "Opening PDF...")
            
            if self.job.use_ocr:
                logger.info(f"Using OCR for: {self.job.input_pdf.name}")
                extractor = ScannedPDFExtractor(
                    self.job.input_pdf,
                    language=self.job.ocr_language
                )
                
                self.progress.emit(30, 100, "Running OCR (this may take a while)...")
                text = extractor.extract_text_ocr(
                    progress_callback=self._ocr_progress_callback
                )
                metadata = extractor.extract_metadata()
                images = extractor.extract_images()
            else:
                extractor = DigitalPDFExtractor(self.job.input_pdf)
                
                self.progress.emit(20, 100, "Extracting text...")
                text = extractor.extract_text()
                
                self.progress.emit(40, 100, "Extracting images...")
                images = extractor.extract_images()
                
                metadata = extractor.extract_metadata()
            
            logger.info(f"Extracted: {len(text)} chars, {len(images)} images")
            self._log_and_emit(
                f"Extracted {len(text)} characters and {len(images)} images",
                logging.INFO
            )
            return text, images, metadata
        
        except OCRError as e:
            self._log_and_emit(f"OCR Error: {e}", logging.ERROR)
            raise
        except Exception as e:
            self._log_and_emit(f"PDF extraction failed: {e}", logging.ERROR)
            raise
        finally:
            if extractor is not None:
                try:
                    extractor.close()
                except Exception:
                    logger.debug("Failed to close PDF extractor", exc_info=True)
    
    def _ocr_progress_callback(self, current: int, total: int):
        """Callback for OCR progress updates."""
        pct = int(30 + (current / total) * 30)  # 30-60% range for OCR
        self.progress.emit(pct, 100, f"OCR: page {current}/{total}")
    
    def _optimize_images(self, image_paths) -> list:
        """
        Optimize extracted images.
        
        Args:
            image_paths: List of image Path objects
            
        Returns:
            List of optimized image paths
        """
        try:
            normalized_paths = self._normalize_image_paths(image_paths)
            if not normalized_paths:
                return []
            
            optimizer = ImageOptimizer()
            output_dir = self.job.output_epub.parent / "images_optimized"
            
            optimized = optimizer.optimize_batch(
                normalized_paths,
                output_dir,
                skip_duplicates=True
            )
            
            logger.info(f"Optimized {len(optimized)} images")
            
            # Return optimized paths
            return [result[0] for result in optimized]
        
        except ImageOptimizationError as e:
            logger.warning(f"Image optimization failed: {e}, continuing without")
            return self._normalize_image_paths(image_paths)

    @staticmethod
    def _normalize_image_paths(image_items) -> list[Path]:
        """Normalize image input to a clean list of Path objects."""
        normalized_paths: list[Path] = []
        
        for item in image_items or []:
            candidate = item[0] if isinstance(item, (tuple, list)) and item else item
            if candidate is None:
                continue
            
            try:
                normalized_paths.append(Path(candidate))
            except TypeError:
                logger.warning(f"Skipping unsupported image item: {item!r}")
        
        return normalized_paths
    
    def _build_epub(self, text: str, images: list, metadata: Metadata) -> Optional[Path]:
        """
        Build EPUB document.
        
        Returns:
            Path to generated EPUB or None if failed
        """
        try:
            builder = EPUBBuilder(metadata)
            
            # Split text into chapters (simple split by double newlines)
            chapters = text.split('\n\n---\n\n')  # Allow manual chapter breaks
            if len(chapters) == 1:
                # Fallback: split into chapters by length
                chapter_size = 50000  # ~10 pages per chapter
                chapters = [
                    text[i:i + chapter_size]
                    for i in range(0, len(text), chapter_size)
                ]
            
            # Add chapters
            for i, chapter_text in enumerate(chapters):
                if chapter_text.strip():
                    builder.add_chapter(
                        f"Chapter {i + 1}",
                        chapter_text,
                        chapter_num=i
                    )
            
            # Add images
            normalized_images = self._normalize_image_paths(images)
            for i, img_path in enumerate(normalized_images):
                try:
                    builder.add_image(f"img_{i}", img_path)
                except Exception as e:
                    logger.warning(f"Failed to add image {img_path}: {e}")
            
            # Generate EPUB
            self.job.output_epub.parent.mkdir(parents=True, exist_ok=True)
            epub_path = builder.generate(self.job.output_epub)
            
            logger.info(f"EPUB generated: {epub_path}")
            return epub_path
        
        except EPUBBuildError as e:
            self._log_and_emit(f"EPUB build error: {e}", logging.ERROR)
            raise
    
    def _validate_epub(self, epub_path: Path):
        """
        Validate generated EPUB.
        
        Args:
            epub_path: Path to EPUB file
        """
        try:
            validator = EPUBValidator(epub_path)
            report = validator.validate()
            
            if not report.is_valid:
                for error in report.errors:
                    self._log_and_emit(f"EPUB Error: {error}", logging.WARNING)
            
            for warning in report.warnings:
                self._log_and_emit(f"EPUB Warning: {warning}", logging.WARNING)
            
            logger.info(f"EPUB validation: {report.summary()}")
        
        except Exception as e:
            logger.warning(f"EPUB validation failed: {e}")
    
    def _log_and_emit(self, message: str, level: int):
        """Log message and emit signal."""
        logger.log(level, message)
        self.log.emit(message, level)
    
    def stop(self):
        """Stop the worker gracefully."""
        self.is_running = False
        self.quit()
        self.wait()
