"""
Main application window for PDF to EPUB Converter.

Provides the primary UI for the desktop application with
multi-file support, metadata editing, and progress tracking.
"""

import logging
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QMessageBox,
    QLabel,
    QPushButton,
    QProgressBar,
    QTabWidget,
    QListWidget,
    QListWidgetItem,
    QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QAction, QColor, QFont

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
        self._metadata_path = None
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
        self.language_combo.addItems(
            [
                "de (Deutsch)",
                "en (English)",
                "fr (Français)",
                "es (Español)",
                "it (Italiano)",
                "pt (Português)",
                "ru (Русский)",
            ]
        )
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
        if self.current_worker is not None:
            return
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select PDF files to convert",
            str(Path.home() / "Documents"),
            "PDF Files (*.pdf);;All Files (*)",
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
        if self.current_worker is not None:
            return
        item = self.file_list_widget.currentItem()
        if item:
            file_path = Path(item.data(Qt.ItemDataRole.UserRole))
            if file_path in self.selected_pdfs:
                self.selected_pdfs.remove(file_path)

            self.file_list_widget.takeItem(self.file_list_widget.row(item))
            logger.info(f"Removed: {file_path.name}")

    def clear_file_list(self):
        """Clear all files from list."""
        if self.current_worker is not None:
            return
        self.selected_pdfs.clear()
        self.file_list_widget.clear()
        logger.info("Cleared file list")

    def _save_metadata(self):
        path = self._metadata_path
        if path is not None:
            self.metadata_overrides[path] = {
                "title": self.title_input.text(),
                "author": self.author_input.text(),
                "language": self.language_combo.currentIndex(),
                "description": self.description_input.toPlainText(),
            }

    def on_file_selected(self):
        self._save_metadata()
        item = self.file_list_widget.currentItem()
        self._metadata_path = (
            Path(item.data(Qt.ItemDataRole.UserRole)) if item else None
        )
        data = self.metadata_overrides.get(self._metadata_path, {})
        self.title_input.setText(data.get("title", ""))
        self.author_input.setText(data.get("author", ""))
        self.language_combo.setCurrentIndex(data.get("language", 0))
        self.description_input.setPlainText(data.get("description", ""))

    def start_conversion(self):
        """Snapshot the queue and settings before starting its first worker."""
        if self.current_worker is not None:
            return
        if not self.selected_pdfs:
            QMessageBox.warning(self, "No Files", "Please select PDF files to convert")
            return
        directory = QFileDialog.getExistingDirectory(
            self, "Choose EPUB output directory", str(Path.home())
        )
        if not directory:
            return
        if self._metadata_path is None:
            self._metadata_path = self.selected_pdfs[0]
        self._save_metadata()
        reserved = set()
        for pdf_path in self.selected_pdfs:
            data = self.metadata_overrides.get(pdf_path, {})
            output = Path(directory) / (pdf_path.stem + ".epub")
            counter = 1
            while output.exists() or output in reserved:
                output = Path(directory) / f"{pdf_path.stem} ({counter}).epub"
                counter += 1
            reserved.add(output)
            self.conversion_jobs.append(
                ConversionJob(
                    input_pdf=pdf_path,
                    output_epub=output,
                    metadata=Metadata(
                        title=data.get("title") or pdf_path.stem,
                        author=data.get("author", ""),
                        language=self.language_combo.itemText(
                            data.get("language", 0)
                        ).split()[0],
                        description=data.get("description", ""),
                    ),
                    use_ocr=self.ocr_combo.currentIndex() == 2,
                    auto_ocr=self.ocr_combo.currentIndex() == 1,
                    ocr_language=self.ocr_lang_combo.currentText(),
                    optimize_images=self.optimize_combo.currentIndex() > 0,
                    aggressive_images=self.optimize_combo.currentIndex() == 2,
                    validate=self.validate_combo.currentIndex() == 0,
                )
            )
        self.start_btn.setEnabled(False)
        self.tabs.setEnabled(False)
        self.file_list_widget.setEnabled(False)
        self._start_next_job()

    def _start_next_job(self):
        if not self.conversion_jobs:
            self.start_btn.setEnabled(True)
            self.tabs.setEnabled(True)
            self.file_list_widget.setEnabled(True)
            return
        job = self.conversion_jobs.pop(0)
        self.current_worker = ConversionWorker(job)
        self.current_worker.progress.connect(self.on_conversion_progress)
        self.current_worker.result.connect(self.on_conversion_finished)
        self.current_worker.finished.connect(self._worker_stopped)
        self.current_worker.log.connect(self.on_log_message)
        self.progress_bar.setValue(0)
        self.current_worker.start()
        self.statusBar().showMessage(f"Converting: {job.input_pdf.name}")

    def _worker_stopped(self):
        worker = self.current_worker
        self.current_worker = None
        worker.deleteLater()
        self._start_next_job()

    def stop_conversion(self):
        self.conversion_jobs.clear()
        if self.current_worker is not None:
            self.current_worker.stop()
            self.progress_label.setText("Cancelling after the current operation…")

    def closeEvent(self, event):
        if self.current_worker is not None:
            self.stop_conversion()
            event.ignore()
            self.statusBar().showMessage(
                "Cancelling; close again when processing has stopped."
            )
        else:
            event.accept()

    @pyqtSlot(int, int, str)
    def on_conversion_progress(self, current: int, total: int, message: str):
        """Handle progress update."""
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"{message} ({current}/{total}%)")

    @pyqtSlot(str, bool, str)
    def on_conversion_finished(self, output_path: str, success: bool, message: str):
        self.statusBar().showMessage(message)
        self.on_log_message(
            f"{message}: {output_path}", logging.INFO if success else logging.WARNING
        )
        if success:
            pdf_path = self.current_worker.job.input_pdf
            self.selected_pdfs.remove(pdf_path)
            for row in range(self.file_list_widget.count()):
                item = self.file_list_widget.item(row)
                if Path(item.data(Qt.ItemDataRole.UserRole)) == pdf_path:
                    self.file_list_widget.takeItem(row)
                    break

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
        self.ocr_combo.setCurrentIndex(1 if self.ocr_action.isChecked() else 0)

    # ============ HELP ============

    def show_about(self):
        """Show about dialog."""
        QMessageBox.information(
            self,
            "About PDF to EPUB Converter",
            "PDF to EPUB Converter v0.1.0\n\n"
            "Convert PDF documents to EPUB e-books with ease.\n"
            "Supports both digital and scanned PDFs with OCR.\n\n"
            "© 2026",
        )
