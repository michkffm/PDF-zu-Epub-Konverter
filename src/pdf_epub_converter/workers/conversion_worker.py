"""
Background conversion worker for PyQt6 GUI.

Handles PDF to EPUB conversion in separate thread,
keeping UI responsive with progress updates.
"""

import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from tempfile import TemporaryDirectory
import shutil

from PyQt6.QtCore import QThread, pyqtSignal

from pdf_epub_converter.core.pdf_extractor import DigitalPDFExtractor
from pdf_epub_converter.workers.ocr_worker import ScannedPDFExtractor, OCRError
from pdf_epub_converter.core.epub_builder import EPUBBuilder, EPUBBuildError
from pdf_epub_converter.core.metadata import Metadata
from pdf_epub_converter.utils.image_optimizer import (
    ImageOptimizer,
    ImageOptimizationError,
)
from pdf_epub_converter.core.quality_checker import EPUBValidator

logger = logging.getLogger(__name__)


@dataclass
class ConversionJob:
    """Represents a single PDF to EPUB conversion job."""

    input_pdf: Path
    output_epub: Path
    metadata: Metadata
    use_ocr: bool = False
    auto_ocr: bool = False
    aggressive_images: bool = False
    ocr_language: str = "de"
    optimize_images: bool = True
    validate: bool = True


class ConversionWorker(QThread):
    """
    QThread worker for PDF to EPUB conversion.

    Signals:
    - progress: (current: int, total: int, message: str)
    - result: (output_path: str, success: bool, message: str)
    - error: (error_message: str)
    """

    # PyQt6 signals
    progress = pyqtSignal(int, int, str)  # current, total, message
    result = pyqtSignal(str, bool, str)  # output_path, success, message
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

    def _check_cancel(self):
        if not self.is_running or self.isInterruptionRequested():
            raise InterruptedError("Conversion cancelled")

    def run(self):
        """Build and validate privately before publishing without overwriting."""
        created_output = False
        try:
            self._check_cancel()
            if self.job.output_epub.exists():
                raise FileExistsError(
                    "Output already exists. Choose another filename or directory."
                )
            with TemporaryDirectory(prefix="pdf-epub-job-") as temporary:
                self._work_dir = Path(temporary)
                text, images, extracted = self._extract_pdf()
                self._check_cancel()
                metadata = self.job.metadata
                if metadata.title == "Untitled":
                    metadata.title = extracted.title
                if not metadata.author:
                    metadata.author = extracted.author
                if self.job.optimize_images:
                    images = self._optimize_images(images)
                self._check_cancel()
                epub_path = self._build_epub(text, images, metadata)
                if self.job.validate:
                    self._validate_epub(epub_path)
                self._check_cancel()
                self.job.output_epub.parent.mkdir(parents=True, exist_ok=True)
                with self.job.output_epub.open("xb") as output:
                    created_output = True
                    with epub_path.open("rb") as source:
                        shutil.copyfileobj(source, output)
                self._check_cancel()
            self.progress.emit(100, 100, "Conversion complete!")
            self.result.emit(str(self.job.output_epub), True, "Conversion successful")
        except Exception as exc:
            if created_output:
                self.job.output_epub.unlink(missing_ok=True)
            message = str(exc)
            if not self.is_running or self.isInterruptionRequested():
                message = "Conversion cancelled"
            self._log_and_emit(message, logging.WARNING)
            self.result.emit("", False, message)

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
                    language=self.job.ocr_language,
                    check_cancel=self._check_cancel,
                )

                self.progress.emit(30, 100, "Running OCR (this may take a while)...")
                text = extractor.extract_text_ocr(
                    progress_callback=self._ocr_progress_callback
                )
                metadata = extractor.extract_metadata()
                images = extractor.extract_images(self._work_dir / "extracted")
            else:
                extractor = DigitalPDFExtractor(
                    self.job.input_pdf, check_cancel=self._check_cancel
                )

                self.progress.emit(20, 100, "Extracting text...")
                texts = []
                for index in range(extractor.page_count):
                    self._check_cancel()
                    page_text = extractor.extract_text(index)
                    if self.job.auto_ocr and not page_text.strip():
                        # OCR only image-only pages, retaining digital text on mixed PDFs.
                        if not hasattr(self, "_ocr_worker"):
                            from pdf_epub_converter.workers.ocr_worker import OCRWorker

                            self._ocr_worker = OCRWorker(language=self.job.ocr_language)
                        images_for_ocr = self._ocr_worker.pdf_to_images(
                            self.job.input_pdf,
                            first_page=index,
                            last_page=index,
                            check_cancel=self._check_cancel,
                        )
                        try:
                            page_text = self._ocr_worker.extract_text_from_image(
                                images_for_ocr[0][1]
                            )
                        finally:
                            images_for_ocr[0][1].close()
                    texts.append(page_text)
                    self.progress.emit(
                        20 + int(40 * (index + 1) / extractor.page_count),
                        100,
                        f"Reading page {index + 1}/{extractor.page_count}",
                    )
                text = "\n\n".join(texts)

                self.progress.emit(40, 100, "Extracting images...")
                images = extractor.extract_images(self._work_dir / "extracted")

                metadata = extractor.extract_metadata()

            logger.info(f"Extracted: {len(text)} chars, {len(images)} images")
            self._log_and_emit(
                f"Extracted {len(text)} characters and {len(images)} images",
                logging.INFO,
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

            optimizer = ImageOptimizer(
                jpeg_quality=65 if self.job.aggressive_images else 85
            )
            output_dir = self._work_dir / "optimized"

            optimized = optimizer.optimize_batch(
                normalized_paths, output_dir, skip_duplicates=True
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

    def _build_epub(
        self, text: str, images: list, metadata: Metadata
    ) -> Optional[Path]:
        """
        Build EPUB document.

        Returns:
            Path to generated EPUB or None if failed
        """
        try:
            builder = EPUBBuilder(metadata)

            # Split text into chapters (simple split by double newlines)
            chapters = text.split("\n\n---\n\n")  # Allow manual chapter breaks
            if len(chapters) == 1:
                # Fallback: split into chapters by length
                chapter_size = 50000  # ~10 pages per chapter
                chapters = [
                    text[i : i + chapter_size]
                    for i in range(0, len(text), chapter_size)
                ]

            # Add chapters
            for i, chapter_text in enumerate(chapters):
                if chapter_text.strip():
                    self._check_cancel()
                    builder.add_chapter(f"Chapter {i + 1}", chapter_text, chapter_num=i)

            # Add images
            normalized_images = self._normalize_image_paths(images)
            if normalized_images:
                builder.add_chapter(
                    "Illustrations",
                    "",
                    images={
                        f"img_{i}": path for i, path in enumerate(normalized_images)
                    },
                )
            epub_path = builder.generate(self._work_dir / "book.epub")

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
        report = EPUBValidator(epub_path).validate()
        for warning in report.warnings:
            self._log_and_emit(f"EPUB Warning: {warning}", logging.WARNING)
        if not report.is_valid:
            raise EPUBBuildError("EPUB validation failed: " + "; ".join(report.errors))

    def _log_and_emit(self, message: str, level: int):
        """Log message and emit signal."""
        logger.log(level, message)
        self.log.emit(message, level)

    def stop(self):
        """Stop the worker gracefully."""
        self.is_running = False
        self.requestInterruption()
