"""
Main application window for PDF to EPUB Converter.

Provides the primary UI for the desktop application with
multi-file support, metadata editing, and progress tracking.
"""

import logging
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QFileDialog, QMessageBox, QLabel, QPushButton,
    QStatusBar, QProgressBar, QTabWidget, QListWidget, QListWidgetItem,
    QStatusBar, QComboBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSlot, QUrl
from PyQt6.QtGui import QIcon, QAction, QColor, QFont

from pdf_epub_converter.core.metadata import Metadata
from pdf_epub_converter.workers.conversion_worker import ConversionWorker, ConversionJob


logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window.
    
    Features:
    - File list management
    - Metadata display/editing
    - Conversion progress tracking
    - Settings panel
    """
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        self.setWindowTitle("PDF to EPUB Converter 📚")
        self.setGeometry(100, 100, 1200, 800)
        
        # State
        self.selected_pdfs: List[Path] = []
        self.conversion_jobs: List[ConversionJob] = []
        self.current_worker: Optional[ConversionWorker] = None
        self.metadata_overrides = {}  # Per-file metadata overrides
        
        # Setup UI
        self._setup_menu_bar()
        self._setup_central_widget()
        self._setup_status_bar()
        self._setup_styles()
        
        logger.info("Main window initialized")
    
    def _setup_menu_bar(self):
        """Setup application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open PDF(s)...", self)
        open_action.triggered.connect(self.open_pdfs)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("&Quit", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        clear_action = QAction("&Clear List", self)
        clear_action.triggered.connect(self.clear_file_list)
        edit_menu.addAction(clear_action)
        
        # Settings menu
        settings_menu = menubar.addMenu("&Settings")
        
        ocr_action = QAction("Enable &OCR for Scanned PDFs", self)
        ocr_action.setCheckable(True)
        ocr_action.setChecked(False)
        ocr_action.triggered.connect(self.toggle_ocr)
        settings_menu.addAction(ocr_action)
        self.ocr_action = ocr_action
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def _setup_central_widget(self):
        """Setup central widget with main layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel: File list
        left_layout = QVBoxLayout()
        
        left_label = QLabel("PDF Files:")
        left_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        left_layout.addWidget(left_label)
        
        self.file_list_widget = QListWidget()
        self.file_list_widget.itemSelectionChanged.connect(self.on_file_selected)
        left_layout.addWidget(self.file_list_widget)
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_selected_file)
        left_layout.addWidget(remove_btn)
        
        left_panel = QWidget()
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(300)
        
        # Right panel: Metadata + Progress
        right_layout = QVBoxLayout()
        
        # Tabs for metadata and settings
        self.tabs = QTabWidget()
        
        # Metadata tab
        metadata_view = self._create_metadata_widget()
        self.tabs.addTab(metadata_view, "📝 Metadata")
        
        # Settings tab
        settings_view = self._create_settings_widget()
        self.tabs.addTab(settings_view, "⚙️ Settings")
        
        right_layout.addWidget(self.tabs)
        
        # Progress section
        progress_label = QLabel("Conversion Progress:")
        progress_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        right_layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        right_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Ready")
        right_layout.addWidget(self.progress_label)
        
        # Log output
        log_label = QLabel("Conversion Log:")
        log_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        right_layout.addWidget(log_label)
        
        self.log_widget = QListWidget()
        self.log_widget.setMaximumHeight(150)
        right_layout.addWidget(self.log_widget)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ Start Conversion")
        self.start_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.start_btn.clicked.connect(self.start_conversion)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        button_layout.addWidget(self.start_btn)
        
        stop_btn = QPushButton("⏹️ Stop")
        stop_btn.clicked.connect(self.stop_conversion)
        button_layout.addWidget(stop_btn)
        self.stop_btn = stop_btn
        
        right_layout.addLayout(button_layout)
        
        right_panel = QWidget()
        right_panel.setLayout(right_layout)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)
        
        central_widget.setLayout(main_layout)
    
    def _create_metadata_widget(self) -> QWidget:
        """Create metadata editor widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        layout.addWidget(QLabel("Title:"))
        self.title_input = self._create_text_input()
        layout.addWidget(self.title_input)
        
        # Author
        layout.addWidget(QLabel("Author:"))
        self.author_input = self._create_text_input()
        layout.addWidget(self.author_input)
        
        # Language
        layout.addWidget(QLabel("Language:"))
        self.language_combo = QComboBox()
        self.language_combo.addItems([
            "de (Deutsch)",
            "en (English)",
            "fr (Français)",
            "es (Español)",
            "it (Italiano)",
            "pt (Português)",
            "ru (Русский)",
        ])
        layout.addWidget(self.language_combo)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_input = self._create_text_input(height=80)
        layout.addWidget(self.description_input)
        
        layout.addStretch()
        return widget
    
    def _create_settings_widget(self) -> QWidget:
        """Create settings widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # OCR setting
        layout.addWidget(QLabel("OCR Processing:"))
        self.ocr_combo = QComboBox()
        self.ocr_combo.addItems(["Disabled", "Auto-detect", "Always Enabled"])
        layout.addWidget(self.ocr_combo)
        
        # Image optimization
        layout.addWidget(QLabel("Image Optimization:"))
        self.optimize_combo = QComboBox()
        self.optimize_combo.addItems(["Disabled", "Enabled", "Aggressive"])
        self.optimize_combo.setCurrentIndex(1)
        layout.addWidget(self.optimize_combo)
        
        # OCR Language
        layout.addWidget(QLabel("OCR Language:"))
        self.ocr_lang_combo = QComboBox()
        self.ocr_lang_combo.addItems(["de", "en", "fr", "es", "it", "pt"])
        self.ocr_lang_combo.setCurrentText("de")
        layout.addWidget(self.ocr_lang_combo)
        
        # Validation
        layout.addWidget(QLabel("EPUB Validation:"))
        self.validate_combo = QComboBox()
        self.validate_combo.addItems(["Enabled", "Disabled"])
        layout.addWidget(self.validate_combo)
        
        layout.addStretch()
        return widget
    
    @staticmethod
    def _create_text_input(height: int = 30):
        """Helper to create text input field."""
        from PyQt6.QtWidgets import QLineEdit, QPlainTextEdit
        if height == 30:
            return QLineEdit()
        else:
            widget = QPlainTextEdit()
            widget.setMaximumHeight(height)
            return widget
    
    def _setup_status_bar(self):
        """Setup status bar."""
        self.statusBar().showMessage("Ready")
    
    def _setup_styles(self):
        """Setup application styles."""
        # Optional: Add custom stylesheet
        pass
    
    # ============ FILE MANAGEMENT ============
    
    def open_pdfs(self):
        """Open PDF file dialog."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select PDF files to convert",
            str(Path.home() / "Documents"),
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if files:
            for file_path in files:
                pdf_path = Path(file_path)
                if pdf_path not in self.selected_pdfs:
                    self.selected_pdfs.append(pdf_path)
                    self._add_file_to_list(pdf_path)
            
            logger.info(f"Added {len(files)} PDFs")
            self.statusBar().showMessage(f"Added {len(files)} file(s)")
    
    def _add_file_to_list(self, file_path: Path):
        """Add file to list widget."""
        item = QListWidgetItem(file_path.name)
        item.setData(Qt.ItemDataRole.UserRole, str(file_path))
        self.file_list_widget.addItem(item)
    
    def remove_selected_file(self):
        """Remove selected file from list."""
        item = self.file_list_widget.currentItem()
        if item:
            file_path = Path(item.data(Qt.ItemDataRole.UserRole))
            if file_path in self.selected_pdfs:
                self.selected_pdfs.remove(file_path)
            
            self.file_list_widget.takeItem(self.file_list_widget.row(item))
            logger.info(f"Removed: {file_path.name}")
    
    def clear_file_list(self):
        """Clear all files from list."""
        self.selected_pdfs.clear()
        self.file_list_widget.clear()
        logger.info("Cleared file list")
    
    def on_file_selected(self):
        """Handle file selection in list."""
        item = self.file_list_widget.currentItem()
        if item:
            file_path = Path(item.data(Qt.ItemDataRole.UserRole))
            logger.debug(f"Selected: {file_path.name}")
    
    # ============ CONVERSION CONTROL ============
    
    def start_conversion(self):
        """Start PDF to EPUB conversion."""
        if not self.selected_pdfs:
            QMessageBox.warning(self, "No Files", "Please select PDF files to convert")
            return
        
        # Create output directory
        output_dir = Path.home() / "EPUBs"
        output_dir.mkdir(exist_ok=True)
        
        # Start conversion for first file
        pdf_path = self.selected_pdfs[0]
        epub_path = output_dir / pdf_path.with_suffix('.epub').name
        
        # Gather metadata
        metadata = Metadata(
            title=self.title_input.text() or pdf_path.stem,
            author=self.author_input.text() or "Unknown",
            language=self.language_combo.currentText().split(" ")[0],
            description=self.description_input.toPlainText() if hasattr(self.description_input, 'toPlainText') else ""
        )
        
        # Create job
        job = ConversionJob(
            input_pdf=pdf_path,
            output_epub=epub_path,
            metadata=metadata,
            use_ocr=(self.ocr_combo.currentIndex() == 2),
            ocr_language=self.ocr_lang_combo.currentText(),
            optimize_images=(self.optimize_combo.currentIndex() > 0),
            validate=(self.validate_combo.currentIndex() == 0)
        )
        
        # Start worker
        self.current_worker = ConversionWorker(job)
        self.current_worker.progress.connect(self.on_conversion_progress)
        self.current_worker.finished.connect(self.on_conversion_finished)
        self.current_worker.error.connect(self.on_conversion_error)
        self.current_worker.log.connect(self.on_log_message)
        self.current_worker.start()
        
        self.start_btn.setEnabled(False)
        self.statusBar().showMessage(f"Converting: {pdf_path.name}...")
        logger.info(f"Started conversion: {pdf_path.name}")
    
    def stop_conversion(self):
        """Stop current conversion."""
        if self.current_worker:
            self.current_worker.stop()
            self.progress_label.setText("Stopped")
            self.statusBar().showMessage("Conversion stopped")
            logger.info("Conversion stopped by user")
    
    @pyqtSlot(int, int, str)
    def on_conversion_progress(self, current: int, total: int, message: str):
        """Handle progress update."""
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"{message} ({current}/{total}%)")
    
    @pyqtSlot(str, bool, str)
    def on_conversion_finished(self, output_path: str, success: bool, message: str):
        """Handle conversion finished."""
        self.start_btn.setEnabled(True)
        
        if success:
            self.progress_bar.setValue(100)
            self.statusBar().showMessage(f"✅ {message}")
            QMessageBox.information(
                self,
                "Conversion Complete",
                f"EPUB saved to:\n{output_path}"
            )
            
            # Remove from list
            if self.selected_pdfs:
                self.selected_pdfs.pop(0)
                self.file_list_widget.takeItem(0)
        else:
            self.statusBar().showMessage(f"❌ Error: {message}")
    
    @pyqtSlot(str)
    def on_conversion_error(self, error_message: str):
        """Handle conversion error."""
        self.start_btn.setEnabled(True)
        self.statusBar().showMessage(f"❌ Error: {error_message}")
        QMessageBox.critical(self, "Conversion Error", error_message)
    
    @pyqtSlot(str, int)
    def on_log_message(self, message: str, level: int):
        """Handle log message."""
        item = QListWidgetItem(message)
        
        # Color code by level
        if level >= logging.ERROR:
            item.setForeground(QColor("red"))
        elif level >= logging.WARNING:
            item.setForeground(QColor("orange"))
        else:
            item.setForeground(QColor("green"))
        
        self.log_widget.addItem(item)
        self.log_widget.scrollToBottom()
    
    # ============ SETTINGS ============
    
    def toggle_ocr(self):
        """Toggle OCR setting."""
        self.ocr_combo.setEnabled(self.ocr_action.isChecked())
    
    # ============ HELP ============
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.information(
            self,
            "About PDF to EPUB Converter",
            "PDF to EPUB Converter v0.1.0\n\n"
            "Convert PDF documents to EPUB e-books with ease.\n"
            "Supports both digital and scanned PDFs with OCR.\n\n"
            "© 2026"
        )
