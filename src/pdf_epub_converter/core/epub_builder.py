"""
EPUB builder module for creating EPUB3 documents.

Handles chapter management, metadata integration, image embedding,
and final EPUB package creation.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from ebooklib import epub
from lxml import etree

from .metadata import Metadata


logger = logging.getLogger(__name__)


class EPUBBuildError(Exception):
    """Base exception for EPUB building errors."""
    pass


class EPUBBuilder:
    """
    Builds EPUB3 documents from extracted PDF content.
    
    Manages:
    - Chapter/section creation
    - Metadata integration
    - Image embedding
    - Navigation generation
    - Final EPUB packaging
    """
    
    # EPUB3 namespace for XHTML
    XHTML_NS = "http://www.w3.org/1999/xhtml"
    OPF_NS = "http://www.idpf.org/2007/opf"
    
    def __init__(self, metadata: Metadata):
        """
        Initialize EPUB builder.
        
        Args:
            metadata: Metadata object with book information
        """
        self.metadata = metadata
        self.book = epub.EpubBook()
        self.chapters = []
        self.images = {}
        self.spine_items = []
        
        # Configure EPUB metadata
        self._setup_metadata()
        logger.info(f"Initialized EPUB builder for: {metadata.title}")
    
    def _setup_metadata(self):
        """Configure EPUB metadata from Metadata object."""
        self.book.set_identifier(self.metadata.identifier or str(uuid.uuid4()))
        self.book.set_title(self.metadata.title)
        self.book.set_language(self.metadata.language)
        
        if self.metadata.author:
            self.book.add_author(self.metadata.author)
        
        if self.metadata.description:
            self.book.add_metadata('DC', 'description', self.metadata.description)
        
        if self.metadata.publisher:
            self.book.add_metadata('DC', 'publisher', self.metadata.publisher)
        
        if self.metadata.rights:
            self.book.add_metadata('DC', 'rights', self.metadata.rights)
        
        logger.debug("Configured EPUB metadata")
    
    # ============ CHAPTER MANAGEMENT ============
    
    def add_chapter(
        self, 
        title: str, 
        content: str, 
        images: Optional[Dict[str, Path]] = None,
        chapter_num: Optional[int] = None
    ) -> epub.EpubHtml:
        """
        Add a chapter to the EPUB.
        
        Args:
            title: Chapter title
            content: Chapter content (HTML or plain text)
            images: Dictionary mapping image_id to image_path
            chapter_num: Optional chapter number for naming
            
        Returns:
            EpubHtml chapter object
        """
        try:
            chapter_id = chapter_num if chapter_num is not None else len(self.chapters)
            
            # Create chapter
            chapter = epub.EpubHtml()
            chapter.id = f'chap_{chapter_id:03d}'
            chapter.file_name = f'chap_{chapter_id:03d}.xhtml'
            chapter.language = self.metadata.language
            
            # Add title
            if title:
                html_content = f"""<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="{self.XHTML_NS}" lang="{self.metadata.language}">
<head>
    <title>{self._escape_html(title)}</title>
    <meta charset="utf-8"/>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <h1>{self._escape_html(title)}</h1>
    {self._format_content(content)}
</body>
</html>"""
            else:
                html_content = f"""<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="{self.XHTML_NS}" lang="{self.metadata.language}">
<head>
    <meta charset="utf-8"/>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    {self._format_content(content)}
</body>
</html>"""
            
            chapter.content = html_content.encode('utf-8')
            self.book.add_item(chapter)
            
            # Add images
            if images:
                for img_id, img_path in images.items():
                    self.add_image(img_id, img_path)
            
            self.chapters.append(chapter)
            self.spine_items.append(chapter)
            logger.debug(f"Added chapter: {title} (chapter_{chapter_id:03d}.xhtml)")
            return chapter
        
        except Exception as e:
            raise EPUBBuildError(f"Failed to add chapter '{title}': {e}")
    
    @staticmethod
    def _format_content(content: str) -> str:
        """
        Format content for EPUB chapter.
        
        Converts plain text to HTML if needed.
        
        Args:
            content: Content string
            
        Returns:
            Formatted HTML content
        """
        if not content:
            return ""
        
        # If content looks like HTML already, use as-is
        if '<' in content and '>' in content:
            return content
        
        # Convert plain text to HTML paragraphs
        paragraphs = content.split('\n\n')
        html_paragraphs = [f"<p>{p.replace(chr(10), '<br/>')}</p>" for p in paragraphs if p.strip()]
        return '\n'.join(html_paragraphs)
    
    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    # ============ IMAGE MANAGEMENT ============
    
    def add_image(self, image_id: str, image_path: Path) -> epub.EpubImage:
        """
        Add image to EPUB.
        
        Args:
            image_id: Unique image identifier
            image_path: Path to image file
            
        Returns:
            EpubImage object
        """
        try:
            image_path = Path(image_path)
            
            if not image_path.exists():
                raise EPUBBuildError(f"Image file not found: {image_path}")
            
            # Read image
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Determine media type
            suffix = image_path.suffix.lower()
            media_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.svg': 'image/svg+xml',
            }
            media_type = media_type_map.get(suffix, 'image/jpeg')
            
            # Create EPUB image (ebooklib 0.20 uses attributes, no set_filename())
            epub_image = epub.EpubImage()
            epub_image.id = image_id
            epub_image.file_name = f'images/{image_id}{suffix}'
            epub_image.media_type = media_type
            epub_image.set_content(image_data)
            
            self.images[image_id] = epub_image
            logger.debug(f"Added image: {image_id} ({media_type})")
            return epub_image
        
        except Exception as e:
            raise EPUBBuildError(f"Failed to add image '{image_id}': {e}")
    
    # ============ COVER MANAGEMENT ============
    
    def set_cover(self, cover_image_path: Path) -> None:
        """
        Set EPUB cover image.
        
        Args:
            cover_image_path: Path to cover image file
        """
        try:
            cover_image_path = Path(cover_image_path)
            
            if not cover_image_path.exists():
                logger.warning(f"Cover image not found: {cover_image_path}")
                return
            
            with open(cover_image_path, 'rb') as f:
                cover_data = f.read()
            
            self.book.set_cover('image_cover', cover_data)
            logger.info("Set EPUB cover image")
        
        except Exception as e:
            logger.warning(f"Failed to set cover: {e}")
    
    # ============ EPUB GENERATION ============
    
    def generate(self, output_path: Path) -> Path:
        """
        Generate final EPUB file.
        
        Args:
            output_path: Path where to save EPUB file
            
        Returns:
            Path to generated EPUB file
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Ensure .epub extension
            if output_path.suffix.lower() != '.epub':
                output_path = output_path.with_suffix('.epub')
            
            # Add chapters to spine
            self.book.spine = ['nav'] + self.spine_items
            
            # Add images to book
            for image in self.images.values():
                self.book.add_item(image)
            
            # Create table of contents
            toc = self._create_toc()
            self.book.toc = toc
            
            # Add navigation
            self.book.add_item(epub.EpubNcx())
            self.book.add_item(epub.EpubNav())
            
            # Add CSS stylesheet
            self._add_default_css()
            
            # Write EPUB file
            epub.write_epub(str(output_path), self.book, {})
            
            logger.info(f"Generated EPUB: {output_path}")
            logger.info(f"EPUB size: {output_path.stat().st_size / 1024:.1f} KB")
            
            return output_path
        
        except Exception as e:
            raise EPUBBuildError(f"Failed to generate EPUB: {e}")
    
    def _create_toc(self) -> tuple:
        """
        Create table of contents from chapters.
        
        Returns:
            Tuple of chapter objects for TOC
        """
        return tuple(self.chapters)
    
    def _add_default_css(self) -> None:
        """Add default CSS stylesheet to EPUB."""
        css_content = """
body {
    font-family: Georgia, serif;
    line-height: 1.6;
    margin: 1em;
    text-align: justify;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    font-weight: bold;
}

h1 {
    font-size: 2em;
    border-bottom: 2px solid #333;
    padding-bottom: 0.3em;
}

h2 {
    font-size: 1.5em;
    margin-top: 1.2em;
}

h3 {
    font-size: 1.2em;
}

p {
    margin: 0.5em 0;
}

img {
    max-width: 100%;
    height: auto;
    margin: 1em 0;
    display: block;
}

a {
    color: #0066cc;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

blockquote {
    margin-left: 1.5em;
    border-left: 3px solid #ccc;
    padding-left: 1em;
    font-style: italic;
}

code {
    background-color: #f4f4f4;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
}

th, td {
    border: 1px solid #ddd;
    padding: 0.5em;
    text-align: left;
}

th {
    background-color: #f2f2f2;
    font-weight: bold;
}

hr {
    margin: 1.5em 0;
    border: none;
    border-top: 1px solid #ccc;
}
"""
        
        style = epub.EpubItem()
        style.id = 'style'
        style.file_name = 'style.css'
        style.media_type = 'text/css'
        style.set_content(css_content.encode('utf-8'))
        self.book.add_item(style)
        
        logger.debug("Added default CSS stylesheet")
    
    # ============ VALIDATION ============
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate EPUB structure.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not self.metadata.title or self.metadata.title == "Untitled":
            errors.append("EPUB title is not set")
        
        if len(self.chapters) == 0:
            errors.append("EPUB contains no chapters")
        
        if not self.metadata.author:
            errors.append("EPUB author is not set")
        
        return len(errors) == 0, errors
