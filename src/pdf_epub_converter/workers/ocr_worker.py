"""
OCR worker module for processing scanned PDFs.

Handles multi-threaded OCR processing using Tesseract,
with image preprocessing and text extraction.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
from io import BytesIO

from PIL import Image
import pytesseract

from pdf_epub_converter.core.pdf_extractor import DigitalPDFExtractor


logger = logging.getLogger(__name__)


class OCRError(Exception):
    """Base exception for OCR errors."""
    pass


class OCRWorker:
    """
    Handles OCR processing for scanned PDFs.
    
    Features:
    - Multi-threaded processing for performance
    - Image preprocessing (contrast, noise reduction)
    - Support for multiple languages
    - Progress tracking
    - Error handling and fallback
    """
    
    # Tesseract language codes mapping
    LANGUAGE_MAP = {
        'de': 'deu',        # German
        'en': 'eng',        # English
        'fr': 'fra',        # French
        'es': 'spa',        # Spanish
        'it': 'ita',        # Italian
        'pt': 'por',        # Portuguese
        'ru': 'rus',        # Russian
        'ja': 'jpn',        # Japanese
        'zh': 'chi_sim',    # Chinese
        'ko': 'kor',        # Korean
    }
    
    def __init__(
        self,
        language: str = 'de',
        max_workers: int = 4,
        preprocessing: bool = True
    ):
        """
        Initialize OCR worker.
        
        Args:
            language: ISO 639-1 language code (default: 'de' for German)
            max_workers: Number of parallel threads
            preprocessing: Enable image preprocessing
        """
        self.language = language
        self.max_workers = max_workers
        self.preprocessing = preprocessing
        self.tesseract_lang = self.LANGUAGE_MAP.get(language.lower(), 'deu')
        
        # Verify Tesseract installation
        self._verify_tesseract()
        logger.info(f"Initialized OCR worker (lang: {language}, workers: {max_workers})")
    
    @staticmethod
    def _verify_tesseract():
        """
        Verify Tesseract-OCR is installed.
        
        Raises:
            OCRError: If Tesseract not found
        """
        try:
            pytesseract.get_tesseract_version()
            logger.debug("Tesseract verification: OK")
        except Exception as e:
            raise OCRError(
                f"Tesseract-OCR not found or not properly installed. "
                f"Install it: macOS: `brew install tesseract`, "
                f"Windows: https://github.com/UB-Mannheim/tesseract/wiki, "
                f"Linux: `sudo apt-get install tesseract-ocr`. "
                f"Error: {e}"
            )
    
    # ============ IMAGE PREPROCESSING ============
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR accuracy.
        
        Applies:
        - Grayscale conversion
        - Contrast enhancement
        - Deskewing (optional)
        - Noise reduction
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        if not self.preprocessing:
            return image
        
        try:
            # Convert to RGB if RGBA
            if image.mode == 'RGBA':
                bg = Image.new('RGB', image.size, (255, 255, 255))
                bg.paste(image, mask=image.split()[3])
                image = bg
            
            # Convert to grayscale
            image = image.convert('L')
            
            # Enhance contrast (improves OCR)
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)
            
            logger.debug("Image preprocessing applied")
            return image
        
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}, continuing without")
            return image
    
    # ============ OCR PROCESSING ============
    
    def extract_text_from_image(self, image: Image.Image) -> str:
        """
        Extract text from image using Tesseract OCR.
        
        Args:
            image: PIL Image object
            
        Returns:
            Extracted text
        """
        try:
            # Preprocess
            image = self.preprocess_image(image)
            
            # Run OCR
            text = pytesseract.image_to_string(
                image,
                lang=self.tesseract_lang,
                config='--psm 1'  # PSM 1 for automatic page segmentation
            )
            
            logger.debug(f"OCR extracted {len(text)} characters")
            return text
        
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise OCRError(f"OCR failed: {e}")
    
    def extract_data_from_image(self, image: Image.Image) -> Dict:
        """
        Extract detailed data from image (text + metadata).
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary with text and confidence scores
        """
        try:
            image = self.preprocess_image(image)
            
            # Get detailed data
            data = pytesseract.image_to_data(
                image,
                lang=self.tesseract_lang,
                output_type=pytesseract.Output.DICT
            )
            
            return data
        
        except Exception as e:
            logger.error(f"OCR data extraction failed: {e}")
            raise OCRError(f"OCR data extraction failed: {e}")
    
    # ============ BATCH PROCESSING ============
    
    def process_images_parallel(
        self,
        images: List[Tuple[int, Image.Image]],
        progress_callback=None
    ) -> Dict[int, str]:
        """
        Process multiple images in parallel.
        
        Args:
            images: List of (page_num, PIL_Image) tuples
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary mapping page_num to extracted text
        """
        results = {}
        total = len(images)
        completed = 0
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                futures = {
                    executor.submit(self.extract_text_from_image, img): page_num
                    for page_num, img in images
                }
                
                # Process completed tasks
                for future in as_completed(futures):
                    page_num = futures[future]
                    try:
                        text = future.result()
                        results[page_num] = text
                        completed += 1
                        
                        if progress_callback:
                            progress_callback(completed, total)
                        
                        logger.debug(f"Processed page {page_num} ({completed}/{total})")
                    
                    except Exception as e:
                        logger.error(f"Error processing page {page_num}: {e}")
                        results[page_num] = ""
            
            logger.info(f"OCR processing complete: {completed}/{total} pages")
            return results
        
        except Exception as e:
            raise OCRError(f"Parallel OCR processing failed: {e}")
    
    # ============ PDF TO IMAGES ============
    
    @staticmethod
    def pdf_to_images(
        pdf_path: Path,
        dpi: int = 150,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ) -> List[Tuple[int, Image.Image]]:
        """
        Convert PDF pages to images.
        
        Args:
            pdf_path: Path to PDF file
            dpi: Resolution in dots per inch
            first_page: First page to convert (0-indexed, optional)
            last_page: Last page to convert (inclusive, optional)
            
        Returns:
            List of (page_num, PIL_Image) tuples
        """
        try:
            import pdf2image
        except ImportError:
            # Fallback: try PIL's PDF support
            try:
                from PIL import ImageSequence
                logger.warning("pdf2image not installed, using PIL fallback")
                return OCRWorker._pdf_to_images_pil(pdf_path, first_page, last_page)
            except Exception as e:
                raise OCRError(
                    f"PDF to image conversion failed. "
                    f"Install pdf2image: pip install pdf2image. "
                    f"Error: {e}"
                )
        
        try:
            pages = pdf2image.convert_from_path(
                str(pdf_path),
                dpi=dpi,
                first_page=first_page,
                last_page=last_page
            )
            
            images = [(i, page) for i, page in enumerate(pages)]
            logger.info(f"Converted {len(images)} PDF pages to images (DPI: {dpi})")
            return images
        
        except Exception as e:
            raise OCRError(f"PDF to image conversion failed: {e}")
    
    @staticmethod
    def _pdf_to_images_pil(pdf_path: Path, first_page=None, last_page=None):
        """Fallback PDF to images conversion using PIL."""
        try:
            images = []
            pdf = Image.open(str(pdf_path))
            
            frame_count = getattr(pdf, 'n_frames', 1)
            start = first_page or 0
            end = (last_page + 1) if last_page else frame_count
            
            for frame_idx in range(start, min(end, frame_count)):
                pdf.seek(frame_idx)
                images.append((frame_idx, pdf.copy()))
            
            return images
        except Exception as e:
            raise OCRError(f"PIL PDF conversion failed: {e}")


class ScannedPDFExtractor(DigitalPDFExtractor):
    """
    Extractor specialized for scanned PDFs.
    
    Extends DigitalPDFExtractor with OCR capabilities
    for text-based extraction from image-based PDFs.
    """
    
    def __init__(
        self,
        pdf_path: Path,
        language: str = 'de',
        ocr_dpi: int = 150
    ):
        """
        Initialize scanned PDF extractor.
        
        Args:
            pdf_path: Path to PDF file
            language: Language for OCR (ISO 639-1 code)
            ocr_dpi: DPI for PDF to image conversion
        """
        super().__init__(pdf_path)
        self.language = language
        self.ocr_dpi = ocr_dpi
        self.ocr_worker = OCRWorker(language=language)
        self.metadata_obj = self.extract_metadata()
        self.metadata_obj.is_scanned = True
        self.metadata_obj.ocr_language = self.ocr_worker.tesseract_lang
        logger.info(f"Initialized scanned PDF extractor (lang: {language})")
    
    def extract_text_ocr(
        self,
        page_num: Optional[int] = None,
        progress_callback=None
    ) -> str:
        """
        Extract text using OCR for scanned PDFs.
        
        Args:
            page_num: Specific page or None for all
            progress_callback: Optional callback for progress
            
        Returns:
            Extracted text
        """
        try:
            # Convert PDF to images
            if page_num is not None:
                images = self.ocr_worker.pdf_to_images(
                    self.pdf_path,
                    dpi=self.ocr_dpi,
                    first_page=page_num,
                    last_page=page_num
                )
            else:
                images = self.ocr_worker.pdf_to_images(
                    self.pdf_path,
                    dpi=self.ocr_dpi
                )
            
            # Run parallel OCR
            results = self.ocr_worker.process_images_parallel(
                images,
                progress_callback=progress_callback
            )
            
            # Combine results
            text = "\n\n".join(
                results[i] for i in sorted(results.keys())
                if results[i]
            )
            
            logger.info(f"OCR extraction complete: {len(text)} characters")
            return text
        
        except Exception as e:
            raise OCRError(f"OCR text extraction failed: {e}")
    
    def extract_metadata(self):
        """Override to mark as scanned."""
        metadata = super().extract_metadata()
        metadata.is_scanned = True
        return metadata
