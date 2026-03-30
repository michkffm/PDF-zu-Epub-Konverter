"""
Metadata management for EPUB documents.

Handles extraction, validation, and storage of document metadata
such as title, author, language, ISBN, and cover image.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


@dataclass
class Metadata:
    """
    Dataclass representing EPUB metadata.
    
    Attributes:
        title: Book title
        author: Author name(s)
        language: ISO 639-1 language code (e.g., 'de', 'en')
        identifier: Unique identifier (typically ISBN or UUID)
        description: Book description/synopsis
        publisher: Publisher name
        date_published: Publication date
        subject: Subject/category tags
        creator: Creator/editor information
        rights: Copyright information
        cover_image_path: Path to cover image file
    """
    
    title: str = "Untitled"
    author: str = ""
    language: str = "de"  # Default to German
    identifier: str = ""
    description: str = ""
    publisher: str = ""
    date_published: Optional[str] = None
    subject: list = field(default_factory=list)
    creator: str = ""
    rights: str = ""
    cover_image_path: Optional[Path] = None
    
    # Additional metadata
    source_pdf_path: Optional[Path] = None
    is_scanned: bool = False
    ocr_language: str = "deu"  # Tesseract language code
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        data = asdict(self)
        # Convert Path objects to strings
        if data.get('cover_image_path'):
            data['cover_image_path'] = str(data['cover_image_path'])
        if data.get('source_pdf_path'):
            data['source_pdf_path'] = str(data['source_pdf_path'])
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Metadata':
        """Create Metadata from dictionary."""
        # Convert string paths back to Path objects
        if data.get('cover_image_path'):
            data['cover_image_path'] = Path(data['cover_image_path'])
        if data.get('source_pdf_path'):
            data['source_pdf_path'] = Path(data['source_pdf_path'])
        return cls(**data)
    
    def validate(self) -> tuple[bool, list]:
        """
        Validate metadata completeness.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not self.title or self.title == "Untitled":
            errors.append("Title is required or set to default")
        
        if not self.author:
            errors.append("Author information is missing")
        
        if self.language not in self._VALID_LANGUAGES:
            errors.append(f"Language '{self.language}' is not valid")
        
        if self.cover_image_path and not Path(self.cover_image_path).exists():
            errors.append(f"Cover image not found: {self.cover_image_path}")
        
        return len(errors) == 0, errors
    
    def normalize(self) -> None:
        """Normalize metadata values."""
        # Strip whitespace
        self.title = self.title.strip() if self.title else "Untitled"
        self.author = self.author.strip() if self.author else ""
        self.description = self.description.strip() if self.description else ""
        
        # Ensure language is lowercase
        self.language = self.language.lower() if self.language else "de"
        
        # Ensure OCR language is lowercase
        self.ocr_language = self.ocr_language.lower() if self.ocr_language else "deu"
        
        logger.debug(f"Normalized metadata: {self.title} by {self.author}")
    
    # Valid ISO 639-1 language codes
    _VALID_LANGUAGES = {
        'de', 'en', 'fr', 'es', 'it', 'pt', 'nl', 'ru', 'ja', 'zh',
        'ko', 'ar', 'he', 'hi', 'pl', 'tr', 'th', 'ro', 'hu', 'cs',
        'sv', 'no', 'da', 'fi', 'el', 'uk', 'vi', 'id', 'fa', 'ur'
    }
