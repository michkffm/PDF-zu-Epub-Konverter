"""
PDF extraction module for digital (text-based) PDFs.

Handles text extraction, image extraction, metadata extraction,
and structure analysis from PDF documents.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any
import io

import pdfplumber
from PIL import Image
import pytesseract

from .metadata import Metadata


logger = logging.getLogger(__name__)


class PDFExtractionError(Exception):
    """Base exception for PDF extraction errors."""
    pass


class DigitalPDFExtractor:
    """
    Extracts content from digital (text-based) PDF files.
    
    Uses pdfplumber for structure-aware extraction of:
    - Text with layout information
    - Images and graphics
    - Metadata
    - Document structure
    """
    
    def __init__(self, pdf_path: Path):
        """
        Initialize extractor with PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Raises:
            PDFExtractionError: If PDF cannot be opened
        """
        self.pdf_path = Path(pdf_path)
        
        if not self.pdf_path.exists():
            raise PDFExtractionError(f"PDF file not found: {pdf_path}")
        
        try:
            self.pdf = pdfplumber.open(str(self.pdf_path))
            self.page_count = len(self.pdf.pages)
            logger.info(f"Opened PDF: {self.pdf_path.name} ({self.page_count} pages)")
        except Exception as e:
            raise PDFExtractionError(f"Failed to open PDF: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close PDF."""
        self.close()
    
    def close(self):
        """Close PDF file."""
        if hasattr(self, 'pdf'):
            self.pdf.close()
            logger.debug(f"Closed PDF: {self.pdf_path.name}")
    
    # ============ METADATA EXTRACTION ============
    
    def extract_metadata(self) -> Metadata:
        """
        Extract metadata from PDF.
        
        Returns:
            Metadata object with extracted information
        """
        pdf_metadata = self.pdf.metadata or {}
        
        metadata = Metadata(
            title=pdf_metadata.get('Title', 'Untitled'),
            author=pdf_metadata.get('Author', ''),
            language=self._detect_language(pdf_metadata.get('Language', 'de')),
            identifier=pdf_metadata.get('Subject', ''),
            description=pdf_metadata.get('Subject', ''),
            creator=pdf_metadata.get('Creator', ''),
            rights=pdf_metadata.get('Producer', ''),
            source_pdf_path=self.pdf_path,
            is_scanned=False,
        )
        
        metadata.normalize()
        logger.info(f"Extracted metadata: {metadata.title} by {metadata.author}")
        return metadata
    
    @staticmethod
    def _detect_language(lang_str: str) -> str:
        """
        Detect language from PDF metadata.
        
        Args:
            lang_str: Language string from PDF
            
        Returns:
            ISO 639-1 language code
        """
        # Common language mappings
        lang_map = {
            'german': 'de', 'deutsch': 'de', 'de': 'de',
            'english': 'en', 'englisch': 'en', 'en': 'en',
            'french': 'fr', 'französisch': 'fr', 'fr': 'fr',
            'spanish': 'es', 'spanisch': 'es', 'es': 'es',
        }
        
        detected = lang_map.get(lang_str.lower().strip(), 'de')
        logger.debug(f"Detected language: {detected} from '{lang_str}'")
        return detected
    
    # ============ TEXT EXTRACTION ============
    
    def extract_text(self, page_num: Optional[int] = None) -> str:
        """
        Extract text from PDF page(s).
        
        Args:
            page_num: Specific page number (0-indexed), or None for all pages
            
        Returns:
            Extracted text string
        """
        try:
            if page_num is not None:
                if page_num < 0 or page_num >= self.page_count:
                    raise PDFExtractionError(f"Invalid page number: {page_num}")
                text = self.pdf.pages[page_num].extract_text() or ""
                logger.debug(f"Extracted text from page {page_num}")
            else:
                text = "\n\n".join(
                    page.extract_text() or "" for page in self.pdf.pages
                )
                logger.info(f"Extracted text from all {self.page_count} pages")
            
            return text
        except Exception as e:
            raise PDFExtractionError(f"Text extraction failed: {e}")
    
    def extract_text_with_layout(self, page_num: Optional[int] = None) -> List[Dict]:
        """
        Extract text with layout information (positions, sizes).
        
        Args:
            page_num: Specific page number or None for all pages
            
        Returns:
            List of dictionaries with text and position info
        """
        try:
            pages_data = []
            page_indices = [page_num] if page_num is not None else range(self.page_count)
            
            for idx in page_indices:
                page = self.pdf.pages[idx]
                chars = page.chars or []
                
                page_text_items = []
                for char in chars:
                    page_text_items.append({
                        'text': char['text'],
                        'x': char['x0'],
                        'y': char['top'],
                        'size': char['size'],
                        'font': char.get('fontname', 'Unknown'),
                    })
                
                pages_data.append({
                    'page': idx,
                    'width': page.width,
                    'height': page.height,
                    'items': page_text_items,
                })
            
            logger.info(f"Extracted layout information for {len(pages_data)} page(s)")
            return pages_data
        except Exception as e:
            raise PDFExtractionError(f"Layout extraction failed: {e}")
    
    # ============ IMAGE EXTRACTION ============
    
    def extract_images(self, output_dir: Optional[Path] = None) -> List[Tuple[Path, str]]:
        """
        Extract images from PDF.
        
        Args:
            output_dir: Directory to save images, defaults to temp directory
            
        Returns:
            List of tuples (image_path, image_format)
        """
        if output_dir is None:
            output_dir = Path(self.pdf_path.parent) / f"{self.pdf_path.stem}_images"
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        images = []
        try:
            for page_idx, page in enumerate(self.pdf.pages):
                for img_idx, image in enumerate(page.images):
                    try:
                        img_stream = io.BytesIO(image['stream'].get_rawdata())
                        pil_image = Image.open(img_stream)
                        
                        # Optimize image
                        pil_image = self._optimize_image(pil_image)
                        
                        # Save image
                        img_filename = f"page_{page_idx:03d}_img_{img_idx:02d}.jpg"
                        img_path = output_dir / img_filename
                        pil_image.save(str(img_path), 'JPEG', quality=85, optimize=True)
                        
                        images.append((img_path, 'JPEG'))
                        logger.debug(f"Extracted image: {img_filename}")
                    except Exception as e:
                        logger.warning(f"Failed to extract image on page {page_idx}: {e}")
            
            logger.info(f"Extracted {len(images)} images from PDF")
            return images
        except Exception as e:
            raise PDFExtractionError(f"Image extraction failed: {e}")
    
    @staticmethod
    def _optimize_image(image: Image.Image, max_width: int = 2000, max_height: int = 2000) -> Image.Image:
        """
        Optimize image for EPUB (resize, compress format).
        
        Args:
            image: PIL Image object
            max_width: Maximum image width
            max_height: Maximum image height
            
        Returns:
            Optimized PIL Image object
        """
        # Resize if too large
        if image.width > max_width or image.height > max_height:
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            logger.debug(f"Resized image to {image.width}x{image.height}")
        
        # Convert RGBA to RGB if needed
        if image.mode in ('RGBA', 'LA'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3] if image.mode == 'RGBA' else image.split()[1])
            image = rgb_image
        
        return image
    
    # ============ STRUCTURE DETECTION ============
    
    def detect_structure(self) -> Dict[str, Any]:
        """
        Detect document structure (chapters, sections).
        
        Returns:
            Dictionary with structure information
        """
        try:
            structure = {
                'page_count': self.page_count,
                'chapters': [],
                'has_toc': False,
            }
            
            # Analyze font sizes to detect hierarchy
            font_sizes = self._analyze_font_sizes()
            structure['font_sizes'] = font_sizes
            
            logger.info(f"Detected structure with {len(font_sizes)} unique font sizes")
            return structure
        except Exception as e:
            logger.warning(f"Structure detection failed: {e}")
            return {'page_count': self.page_count, 'chapters': []}
    
    def _analyze_font_sizes(self) -> Dict[float, int]:
        """
        Analyze font sizes in document.
        
        Returns:
            Dictionary mapping font size to occurrence count
        """
        font_sizes = {}
        
        for page in self.pdf.pages:
            chars = page.chars or []
            for char in chars:
                size = round(char['size'], 1)
                font_sizes[size] = font_sizes.get(size, 0) + 1
        
        # Sort by descending occurrence
        return dict(sorted(font_sizes.items(), key=lambda x: x[1], reverse=True))
    
    # ============ VALIDATION ============
    
    def is_scanned(self) -> bool:
        """
        Check if PDF is likely scanned (image-based).
        
        Returns:
            True if PDF appears to be scanned
        """
        try:
            # Get first page
            if self.page_count == 0:
                return False
            
            first_page = self.pdf.pages[0]
            text = (first_page.extract_text() or "").strip()
            
            # If very little text, likely scanned
            if len(text) < 50:
                logger.info("PDF appears to be scanned (minimal text)")
                return True
            
            return False
        except Exception as e:
            logger.warning(f"Could not determine if PDF is scanned: {e}")
            return False
