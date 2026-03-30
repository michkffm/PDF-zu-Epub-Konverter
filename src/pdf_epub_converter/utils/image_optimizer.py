"""
Image optimization utilities for EPUB conversion.

Handles image preprocessing, compression, format conversion,
and quality optimization for e-book distribution.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, List
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import hashlib


logger = logging.getLogger(__name__)


class ImageOptimizationError(Exception):
    """Base exception for image optimization errors."""
    pass


class ImageOptimizer:
    """
    Optimizes images for EPUB format.
    
    Features:
    - Automatic format selection (JPEG/PNG)
    - Size limiting
    - Quality preservation
    - Duplicate detection
    - Metadata stripping
    """
    
    # Configuration
    MAX_WIDTH = 2000
    MAX_HEIGHT = 2000
    JPEG_QUALITY = 85
    PNG_COMPRESSION = 6
    
    # File size limits
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
    
    # MIME types
    MIME_TYPES = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.webp': 'image/webp',
    }
    
    def __init__(
        self,
        max_width: int = MAX_WIDTH,
        max_height: int = MAX_HEIGHT,
        jpeg_quality: int = JPEG_QUALITY,
        aggressive: bool = False
    ):
        """
        Initialize image optimizer.
        
        Args:
            max_width: Maximum image width in pixels
            max_height: Maximum image height in pixels
            jpeg_quality: JPEG quality (1-100)
            aggressive: Enable aggressive compression
        """
        self.max_width = max_width
        self.max_height = max_height
        self.jpeg_quality = jpeg_quality
        self.aggressive = aggressive
        self.processed_hashes = set()
        
        logger.info(
            f"Initialized ImageOptimizer "
            f"(max: {max_width}x{max_height}, quality: {jpeg_quality})"
        )
    
    # ============ OPTIMIZATION ============
    
    def optimize(
        self,
        image_path: Path,
        output_path: Optional[Path] = None,
        force_format: Optional[str] = None
    ) -> Tuple[Path, str, int]:
        """
        Optimize image for EPUB.
        
        Args:
            image_path: Path to input image
            output_path: Output path (optional)
            force_format: Force specific format ('jpeg', 'png')
            
        Returns:
            Tuple of (output_path, mime_type, file_size_bytes)
        """
        try:
            image_path = Path(image_path)
            if not image_path.exists():
                raise ImageOptimizationError(f"Image not found: {image_path}")
            
            # Load image
            image = Image.open(str(image_path))
            original_format = image.format
            original_size = image_path.stat().st_size
            
            logger.debug(f"Processing image: {image_path.name} ({original_format})")
            
            # Preprocess
            image = self._preprocess(image)
            
            # Resize if needed
            image = self._resize(image)
            
            # Convert format
            target_format = force_format or self._select_format(image, original_format)
            image = self._convert_format(image, target_format)
            
            # Determine output path
            if output_path is None:
                suffix = '.jpg' if target_format == 'jpeg' else f'.{target_format.lower()}'
                output_path = image_path.with_suffix(suffix)
            else:
                # Ensure suffix matches format
                output_path = Path(output_path)
                if target_format == 'jpeg' and output_path.suffix.lower() != '.jpg':
                    output_path = output_path.with_suffix('.jpg')
                elif target_format == 'png' and output_path.suffix.lower() != '.png':
                    output_path = output_path.with_suffix('.png')
            
            output_path = Path(output_path)
            
            # Save with compression
            image = self._compress_and_save(image, output_path, target_format)
            
            output_size = output_path.stat().st_size
            compression_ratio = (1 - output_size / original_size) * 100
            
            # Determine MIME type from actual output file
            output_suffix = output_path.suffix.lower()
            if output_suffix == '.jpg' or output_suffix == '.jpeg':
                mime_type = 'image/jpeg'
            elif output_suffix == '.png':
                mime_type = 'image/png'
            elif output_suffix == '.gif':
                mime_type = 'image/gif'
            else:
                mime_type = self.MIME_TYPES.get(output_suffix, 'image/jpeg')
            
            logger.info(
                f"Optimized: {image_path.name} → {output_path.name} "
                f"({original_size}→{output_size} bytes, {compression_ratio:.1f}% reduction)"
            )
            
            return output_path, mime_type, output_size
        
        except Exception as e:
            raise ImageOptimizationError(f"Image optimization failed: {e}")
    
    def _preprocess(self, image: Image.Image) -> Image.Image:
        """Preprocess image (color mode conversion, etc)."""
        # Convert RGBA to RGB
        if image.mode == 'RGBA':
            bg = Image.new('RGB', image.size, (255, 255, 255))
            bg.paste(image, mask=image.split()[3])
            image = bg
        
        # Convert palette mode
        if image.mode == 'P':
            image = image.convert('RGB')
        
        # Ensure RGB or L for lossy formats
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        
        return image
    
    def _resize(self, image: Image.Image) -> Image.Image:
        """Resize image if exceeds limits."""
        if image.width > self.max_width or image.height > self.max_height:
            original_size = (image.width, image.height)
            image.thumbnail((self.max_width, self.max_height), Image.Resampling.LANCZOS)
            logger.debug(f"Resized from {original_size} to {image.size}")
        
        return image
    
    def _select_format(self, image: Image.Image, original_format: Optional[str]) -> str:
        """
        Select optimal format for image.
        
        Returns:
            Format name ('jpeg', 'png')
        """
        # Prioritize JPEG for photos/complex images, PNG for text/graphics
        if original_format and original_format.upper() == 'PNG':
            return 'png'
        
        # Heuristic: if image has many colors, use JPEG
        try:
            colors = image.getcolors(maxcolors=256)
            if colors and len(colors) < 256:
                return 'png'
        except:
            pass
        
        return 'jpeg'
    
    def _convert_format(self, image: Image.Image, target_format: str) -> Image.Image:
        """Convert image to target format."""
        if target_format.lower() == 'jpeg':
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
        elif target_format.lower() == 'png':
            if image.mode == 'L':
                pass  # Already grayscale
            elif image.mode != 'RGB':
                image = image.convert('RGB')
        
        return image
    
    def _compress_and_save(
        self,
        image: Image.Image,
        output_path: Path,
        target_format: str
    ) -> Image.Image:
        """Save image with optimized compression."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if target_format.lower() == 'jpeg':
            image.save(
                str(output_path),
                'JPEG',
                quality=self.jpeg_quality,
                optimize=True
            )
        else:  # PNG
            image.save(
                str(output_path),
                'PNG',
                compress_level=self.PNG_COMPRESSION,
                optimize=True
            )
        
        return image
    
    # ============ BATCH PROCESSING ============
    
    def optimize_batch(
        self,
        image_paths: List[Path],
        output_dir: Path,
        skip_duplicates: bool = True
    ) -> List[Tuple[Path, str, int]]:
        """
        Optimize multiple images.
        
        Args:
            image_paths: List of image paths
            output_dir: Output directory
            skip_duplicates: Skip duplicate images (by content hash)
            
        Returns:
            List of (output_path, mime_type, size) tuples
        """
        results = []
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for image_path in image_paths:
            try:
                image_path = Path(image_path)
                
                # Skip duplicates
                if skip_duplicates:
                    content_hash = self._compute_hash(image_path)
                    if content_hash in self.processed_hashes:
                        logger.debug(f"Skipping duplicate: {image_path.name}")
                        continue
                    self.processed_hashes.add(content_hash)
                
                # Optimize
                output_path, mime_type, size = self.optimize(
                    image_path,
                    output_path=output_dir / image_path.name
                )
                results.append((output_path, mime_type, size))
            
            except Exception as e:
                logger.warning(f"Failed to optimize {image_path}: {e}")
        
        logger.info(f"Batch optimization complete: {len(results)}/{len(image_paths)}")
        return results
    
    # ============ UTILITIES ============
    
    @staticmethod
    def _compute_hash(image_path: Path) -> str:
        """Compute SHA256 hash of image file."""
        sha256 = hashlib.sha256()
        with open(image_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    @staticmethod
    def get_image_info(image_path: Path) -> dict:
        """
        Get image information.
        
        Returns:
            Dictionary with image metadata
        """
        try:
            image_path = Path(image_path)
            image = Image.open(str(image_path))
            
            file_size = image_path.stat().st_size
            
            return {
                'filename': image_path.name,
                'format': image.format,
                'mode': image.mode,
                'width': image.width,
                'height': image.height,
                'size_bytes': file_size,
                'size_mb': file_size / (1024 * 1024),
                'dpi': image.info.get('dpi', (0, 0)),
            }
        except Exception as e:
            logger.error(f"Failed to get image info: {e}")
            return {}
