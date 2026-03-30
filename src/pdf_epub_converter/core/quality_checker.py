"""
EPUB quality checking and validation.

Validates EPUB3 structure, metadata completeness, and content integrity,
providing detailed quality reports.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from zipfile import ZipFile
from xml.etree import ElementTree as ET


logger = logging.getLogger(__name__)


class QualityCheckError(Exception):
    """Base exception for quality checking errors."""
    pass


class QualityReport:
    """Represents EPUB quality check results."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.is_valid = True
    
    def add_error(self, message: str):
        """Add error to report."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add warning to report."""
        self.warnings.append(message)
    
    def add_info(self, message: str):
        """Add info message to report."""
        self.info.append(message)
    
    def summary(self) -> str:
        """Get summary string."""
        return (
            f"Valid: {self.is_valid} | "
            f"Errors: {len(self.errors)} | "
            f"Warnings: {len(self.warnings)} | "
            f"Info: {len(self.info)}"
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info,
            'summary': self.summary(),
        }
    
    def __str__(self) -> str:
        """String representation."""
        lines = [f"\n{'='*60}"]
        lines.append(f"EPUB Quality Report - {self.summary()}")
        lines.append(f"{'='*60}\n")
        
        if self.errors:
            lines.append("ERRORS:")
            for i, err in enumerate(self.errors, 1):
                lines.append(f"  {i}. {err}")
            lines.append("")
        
        if self.warnings:
            lines.append("WARNINGS:")
            for i, warn in enumerate(self.warnings, 1):
                lines.append(f"  {i}. {warn}")
            lines.append("")
        
        if self.info:
            lines.append("INFO:")
            for i, inf in enumerate(self.info, 1):
                lines.append(f"  {i}. {inf}")
            lines.append("")
        
        lines.append(f"{'='*60}\n")
        return "\n".join(lines)


class EPUBValidator:
    """
    Validates EPUB3 documents.
    
    Checks:
    - ZIP structure validity
    - EPUB3 container format
    - Content Document validation
    - Metadata completeness
    - File integrity
    """
    
    # EPUB namespaces
    OPF_NS = 'http://www.idpf.org/2007/opf'
    OPS_NS = 'http://www.idpf.org/2007/ops'
    DCNS = 'http://purl.org/dc/elements/1.1/'
    
    def __init__(self, epub_path: Path):
        """
        Initialize validator.
        
        Args:
            epub_path: Path to EPUB file
        """
        self.epub_path = Path(epub_path)
        if not self.epub_path.exists():
            raise QualityCheckError(f"EPUB file not found: {epub_path}")
        
        logger.info(f"Validating EPUB: {self.epub_path.name}")
    
    def validate(self) -> QualityReport:
        """
        Perform complete EPUB validation.
        
        Returns:
            QualityReport object
        """
        report = QualityReport()
        
        try:
            # Check ZIP structure
            self._check_zip_structure(report)
            
            # Check container metadata
            self._check_container_metadata(report)
            
            # Check package document
            self._check_package_document(report)
            
            # Check content documents
            self._check_content_documents(report)
            
            # Check file integrity
            self._check_file_integrity(report)
            
            logger.info(f"Validation complete: {report.summary()}")
        
        except Exception as e:
            report.add_error(f"Validation failed: {e}")
            logger.error(f"Validation error: {e}")
        
        return report
    
    def _check_zip_structure(self, report: QualityReport):
        """Check ZIP container structure."""
        try:
            with ZipFile(str(self.epub_path), 'r') as epub_zip:
                file_list = epub_zip.namelist()
                
                # Essential files
                if 'mimetype' not in file_list:
                    report.add_error("Missing 'mimetype' file")
                else:
                    mime_content = epub_zip.read('mimetype').decode('utf-8').strip()
                    if mime_content != 'application/epub+zip':
                        report.add_error(f"Invalid mimetype: {mime_content}")
                    else:
                        report.add_info("mimetype is correct")
                
                if 'META-INF/container.xml' not in file_list:
                    report.add_error("Missing 'META-INF/container.xml'")
                
                if not any(f.endswith('.opf') for f in file_list):
                    report.add_error("No OPF (package) document found")
                
                report.add_info(f"EPUB contains {len(file_list)} files")
        
        except Exception as e:
            report.add_error(f"ZIP structure check failed: {e}")
    
    def _check_container_metadata(self, report: QualityReport):
        """Check container.xml metadata."""
        try:
            with ZipFile(str(self.epub_path), 'r') as epub_zip:
                try:
                    container_xml = epub_zip.read('META-INF/container.xml')
                    root = ET.fromstring(container_xml)
                    
                    # Find rootfile reference
                    rootfile = root.find('.//{*}rootfile')
                    if rootfile is not None:
                        opf_path = rootfile.get('full-path', '')
                        report.add_info(f"Package document: {opf_path}")
                    else:
                        report.add_warning("No rootfile reference in container.xml")
                
                except ET.ParseError as e:
                    report.add_error(f"container.xml parse error: {e}")
        
        except Exception as e:
            report.add_warning(f"Container metadata check skipped: {e}")
    
    def _check_package_document(self, report: QualityReport):
        """Check OPF package document."""
        try:
            with ZipFile(str(self.epub_path), 'r') as epub_zip:
                # Find OPF file
                opf_file = None
                for name in epub_zip.namelist():
                    if name.endswith('.opf'):
                        opf_file = name
                        break
                
                if not opf_file:
                    report.add_error("No OPF file found")
                    return
                
                try:
                    opf_content = epub_zip.read(opf_file)
                    root = ET.fromstring(opf_content)
                    
                    # Check metadata
                    metadata = root.find('.//{%s}metadata' % self.OPF_NS)
                    if metadata is None:
                        report.add_error("No metadata in OPF")
                        return
                    
                    # Check required metadata
                    title = metadata.find('{%s}title' % self.DCNS)
                    if title is None or not title.text:
                        report.add_warning("Missing or empty dc:title")
                    else:
                        report.add_info(f"Title: {title.text}")
                    
                    creator = metadata.find('{%s}creator' % self.DCNS)
                    if creator is None or not creator.text:
                        report.add_warning("Missing or empty dc:creator")
                    else:
                        report.add_info(f"Creator: {creator.text}")
                    
                    lang = metadata.find('{%s}language' % self.DCNS)
                    if lang is None or not lang.text:
                        report.add_warning("Missing or empty dc:language")
                    else:
                        report.add_info(f"Language: {lang.text}")
                    
                    # Check manifest
                    manifest = root.find('.//{%s}manifest' % self.OPF_NS)
                    if manifest is None:
                        report.add_error("No manifest in OPF")
                    else:
                        items = list(manifest)
                        report.add_info(f"Manifest contains {len(items)} items")
                    
                    # Check spine
                    spine = root.find('.//{%s}spine' % self.OPF_NS)
                    if spine is None:
                        report.add_error("No spine in OPF")
                    else:
                        itemrefs = list(spine)
                        report.add_info(f"Spine contains {len(itemrefs)} itemrefs")
                
                except ET.ParseError as e:
                    report.add_error(f"OPF parse error: {e}")
        
        except Exception as e:
            report.add_warning(f"Package document check skipped: {e}")
    
    def _check_content_documents(self, report: QualityReport):
        """Check XHTML content documents."""
        try:
            with ZipFile(str(self.epub_path), 'r') as epub_zip:
                xhtml_files = [f for f in epub_zip.namelist() if f.endswith(('.xhtml', '.html'))]
                
                if not xhtml_files:
                    report.add_warning("No XHTML/HTML content documents found")
                    return
                
                report.add_info(f"Found {len(xhtml_files)} content documents")
                
                # Check first few files for validity
                for xhtml_file in xhtml_files[:5]:  # Check first 5
                    try:
                        content = epub_zip.read(xhtml_file)
                        ET.fromstring(content)
                    except ET.ParseError as e:
                        report.add_warning(f"XHTML parse error in {xhtml_file}: {e}")
        
        except Exception as e:
            report.add_warning(f"Content document check skipped: {e}")
    
    def _check_file_integrity(self, report: QualityReport):
        """Check file sizes and integrity."""
        try:
            epub_size = self.epub_path.stat().st_size
            
            if epub_size == 0:
                report.add_error("EPUB file is empty")
            elif epub_size > 100 * 1024 * 1024:  # 100 MB
                report.add_warning(f"EPUB file is very large: {epub_size / (1024*1024):.1f} MB")
            else:
                report.add_info(f"EPUB file size: {epub_size / (1024*1024):.1f} MB")
        
        except Exception as e:
            report.add_warning(f"File integrity check skipped: {e}")
